"""Required sentinel fallback and ranking hooks for DCOIR Review v9."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v4 as v4
import dcoir_review_required_runtime_patch_v5 as v5

from dcoir_review_required_runtime_patch_v9_core import (
    PYTHON_PICKLE_LABEL,
    PYTHON_PICKLE_LOAD,
    PYTHON_PICKLE_DETAIL,
    SentinelKey,
    _dedupe,
    _expected_by_line,
    _key_text,
    _line_number,
    _normalize,
    _postable_key,
    _required_sentinels,
    _rewrite_validation,
    _semantic_mismatch,
    _sentinel_key,
    _spare_priority,
    _validation_for_key,
    _yaml_load_arg,
)
from dcoir_review_required_runtime_patch_v9_prompting import _ensure_prompt_review

def _iter_added_diff_lines(diff: str) -> list[tuple[str, int, str]]:
    result: list[tuple[str, int, str]] = []
    current_path = ""
    new_line = 0
    for raw_line in str(diff or "").splitlines():
        if raw_line.startswith("+++ b/"):
            current_path = raw_line[6:]
        elif raw_line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,\d+)?", raw_line)
            new_line = int(match.group(1)) if match else 0
        elif current_path and new_line:
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                result.append((current_path, new_line, raw_line[1:]))
                new_line += 1
            elif raw_line.startswith(" ") or raw_line == "":
                new_line += 1
    return result


def _patch_pickle_sentinels(hardened: Any) -> None:
    original = getattr(hardened, "_dcoir_required_v9_original_detect_risk_sentinels", None)
    if original is None:
        original = getattr(hardened, "detect_risk_sentinels", None)
        hardened._dcoir_required_v9_original_detect_risk_sentinels = original
    if not callable(original):
        return

    def detect_risk_sentinels(diff: str, *args: Any, **kwargs: Any) -> list[Any]:
        sentinels = list(original(diff, *args, **kwargs))
        existing = {_sentinel_key(item) for item in sentinels}
        risk_sentinel_type = getattr(hardened, "RiskSentinel", None)
        if risk_sentinel_type is None:
            return sentinels
        for path, line, text in _iter_added_diff_lines(diff):
            if Path(path.lower()).suffix != ".py":
                continue
            if "pickle.loads" not in _normalize(text) and "pickle.load(" not in _normalize(text):
                continue
            if callable(getattr(hardened, "is_comment_only_added_line", None)) and hardened.is_comment_only_added_line(path, text):
                continue
            key = (path, line, PYTHON_PICKLE_LOAD)
            if key in existing:
                continue
            sentinels.append(risk_sentinel_type(path=path, line=line, label=PYTHON_PICKLE_LABEL, detail=PYTHON_PICKLE_DETAIL, text=text))
            existing.add(key)
        return sentinels

    hardened.detect_risk_sentinels = detect_risk_sentinels


def _fallback_for_sentinel(hardened: Any, sentinel: Any, config: Any) -> dict[str, Any]:
    key = _sentinel_key(sentinel)
    fallback = _known_fallback_for_key(key, str(getattr(sentinel, "text", "") or ""))
    if not fallback:
        fallback_fn = getattr(hardened, "risk_sentinel_fallback_finding", None)
        fallback = fallback_fn(sentinel, config) if callable(fallback_fn) else {}
    if not isinstance(fallback, dict) or not fallback:
        fallback = {
            "title": f"Required changed-line risk: {getattr(sentinel, 'label', key[2])}",
            "severity": "high",
            "confidence": 0.99,
            "path": key[0],
            "line": key[1],
            "body": str(getattr(sentinel, "detail", "") or "This changed line matched a required deterministic risk sentinel."),
            "suggested_replacement": "",
            "validation": getattr(hardened, "primary_validation_command", lambda _config: "")(config),
        }
    fallback["_risk_sentinel_key"] = [key[0], key[1], key[2]]
    fallback["_risk_sentinel_kind"] = key[2]
    fallback["_anchored_line_text"] = str(getattr(sentinel, "text", "") or "")
    return fallback


def _known_fallback_for_key(key: SentinelKey, line_text: str) -> dict[str, Any]:
    path, line, kind = key
    titles = {
        v4.YAML_PULL_REQUEST_TARGET: "Privileged `pull_request_target` workflow context",
        v4.YAML_BROAD_WRITE: "GitHub Actions workflow grants write permissions",
        v4.YAML_UNTRUSTED_CHECKOUT: "Privileged workflow checks out untrusted PR code",
        v4.YAML_SHELL_PIPE: "Workflow pipes a network installer into a shell",
        v4.YAML_METADATA_SHELL: "Workflow executes pull request metadata in a shell",
        v4.PS_ACL: "PowerShell broad ACL grant exposes collector output",
        v4.PS_PROCESS_LAUNCH: "PowerShell caller-controlled process launch",
        v5.PS_ENV_TOKEN: "Environment token forwarded to request-controlled callback",
        PYTHON_PICKLE_LOAD: "Unsafe pickle deserialization",
        v5.PYTHON_YAML_LOAD: "Unsafe YAML deserialization",
        v5.PYTHON_SHELL_EXEC: "Python shell execution with caller-controlled command",
        v5.PYTHON_ENV_TOKEN: "Environment token forwarded to request-controlled callback",
    }
    bodies = {
        v4.YAML_PULL_REQUEST_TARGET: "`pull_request_target` runs with base-repository privileges. Do not execute untrusted PR code in this workflow context.",
        v4.YAML_BROAD_WRITE: "This workflow grants broad write token permissions. Narrow `permissions` to the minimum scopes required.",
        v4.YAML_UNTRUSTED_CHECKOUT: "This privileged workflow checks out PR-controlled code. Do not combine privileged workflow context with PR-controlled refs or head SHAs.",
        v4.YAML_SHELL_PIPE: "This workflow pipes network-fetched content directly into a shell. Download the content to a file, verify a pinned checksum or signature, and execute only verified content.",
        v4.YAML_METADATA_SHELL: "This workflow passes pull request metadata to a shell. Pull request title, body, and head metadata are attacker-controlled and must not be executed.",
        v4.PS_ACL: "This PowerShell change grants broad filesystem ACL rights. Narrow the identity and rights to the minimum collector path access required.",
        v4.PS_PROCESS_LAUNCH: "This line launches a caller-controlled executable or argument string. Use an allowlisted command table or remove the launch from the collector path.",
        v5.PS_ENV_TOKEN: "Environment token read from env and forwarded to request-controlled callback. Keep collector tokens server-side and allowlist outbound destinations before sending authorization headers.",
        PYTHON_PICKLE_LOAD: "Pickle deserialization can execute code. Replace pickle input with a safe serialization format, or only load signed data from a trusted source.",
        v5.PYTHON_YAML_LOAD: "This line uses unsafe YAML deserialization. Use `yaml.safe_load(...)` unless trusted Python object tags are required.",
        v5.PYTHON_SHELL_EXEC: "This line invokes a system shell with caller-controlled command text. Use argument-vector execution without `shell=True`.",
        v5.PYTHON_ENV_TOKEN: "Environment token read from env and forwarded to request-controlled callback. Keep collector tokens server-side and allowlist outbound destinations before sending authorization headers.",
    }
    notes = {
        v4.YAML_UNTRUSTED_CHECKOUT: "Use a trusted base ref or avoid checkout in privileged `pull_request_target` jobs.",
        v5.PYTHON_YAML_LOAD: f"Use `yaml.safe_load({_yaml_load_arg(line_text)})` when no Python object tags are expected.",
        PYTHON_PICKLE_LOAD: "Prefer JSON, YAML safe loading, or another data format that does not execute code during parsing.",
    }
    if kind not in titles:
        return {}
    return {
        "_dcoir_v9_known_fallback": True,
        "title": titles[kind],
        "severity": "critical" if kind in {v4.YAML_PULL_REQUEST_TARGET, v4.YAML_SHELL_PIPE, v4.PS_PROCESS_LAUNCH, PYTHON_PICKLE_LOAD} else "high",
        "confidence": 0.99,
        "path": path,
        "line": line,
        "body": bodies[kind],
        "suggested_replacement": "",
        "validation": _validation_for_key(kind, path, line),
        "fix_guidance": {
            "language": "yaml" if Path(path.lower()).suffix in {".yml", ".yaml"} else "powershell" if Path(path.lower()).suffix in {".ps1", ".psm1", ".psd1"} else "python" if Path(path.lower()).suffix == ".py" else "text",
            "notes": notes.get(kind, "Apply a minimal, evidence-backed fix for the changed line."),
        },
    }


def _select_required_postable(hardened: Any, findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    limit = max(0, int(getattr(config, "max_inline_comments", 12)))
    required = _required_sentinels(hardened, risk_sentinels)
    expected = _expected_by_line(hardened, risk_sentinels)
    sentinel_lines = {(getattr(item, "path", ""), _line_number(getattr(item, "line", 0))) for item in risk_sentinels}
    if len(required) > limit:
        metadata = {
            "hard_required_count": len(required),
            "inline_limit": limit,
            "capacity_failure": True,
            "required_keys": [_key_text(_sentinel_key(item)) for item in required],
        }
        hardened.write_debug_json_artifact_safely(config, "metadata/required-v9-final-selection.json", metadata)
        raise getattr(hardened, "ReviewQualityError", RuntimeError)(
            f"DCOIR Review quality failure: required changed-line signals ({len(required)}) exceed inline comment budget ({limit})."
        )
    raw = [item for item in findings if isinstance(item, dict)]
    candidates, dropped = _dedupe(raw, expected)
    by_key = {_postable_key(item): item for item in candidates}
    for sentinel in required:
        key = _sentinel_key(sentinel)
        if key not in by_key:
            fallback = _fallback_for_sentinel(hardened, sentinel, config)
            normalized = dict(fallback) if fallback.get("_dcoir_v9_known_fallback") else v5._normalize_comment_finding(fallback)
            by_key[key] = normalized
            candidates.append(normalized)
    selected: list[dict[str, Any]] = []
    selected_keys: set[SentinelKey] = set()
    for sentinel in required:
        key = _sentinel_key(sentinel)
        if key in by_key and key not in selected_keys and len(selected) < limit:
            selected.append(by_key[key])
            selected_keys.add(key)
    for item in sorted(candidates, key=_spare_priority):
        key = _postable_key(item)
        if len(selected) >= limit:
            break
        if key not in selected_keys and key[2]:
            selected.append(item)
            selected_keys.add(key)
    selected = selected[:limit]
    _rewrite_validation(selected)
    final_invalid = [_key_text(_postable_key(item)) for item in selected if _semantic_mismatch(item, expected)]
    final_uncovered = [key for key in (_sentinel_key(item) for item in required) if key not in selected_keys]
    hardened.write_debug_json_artifact_safely(
        config,
        "metadata/required-v9-final-selection.json",
        {
            "hard_required_count": len(required),
            "final_postable_count": len(selected),
            "selected_keys": [_key_text(_postable_key(item)) for item in selected],
            "spare_budget_selected": [_key_text(_postable_key(item)) for item in selected if _postable_key(item) not in {_sentinel_key(s) for s in required}],
            "dropped_invalid_or_duplicate_candidates": dropped[:80],
            "final_invalid_selected_keys": final_invalid,
            "final_uncovered": [_key_text(key) for key in final_uncovered],
        },
    )
    if final_invalid:
        raise getattr(hardened, "ReviewQualityError", RuntimeError)(
            "DCOIR Review quality failure: final selected findings have semantic mismatches: " + "; ".join(final_invalid)
        )
    if final_uncovered:
        raise getattr(hardened, "ReviewQualityError", RuntimeError)(
            "DCOIR Review quality failure: required changed-line signals remain uncovered after v9 final selection: "
            + "; ".join(_key_text(key) for key in final_uncovered)
        )
    _ensure_prompt_review(config)
    return selected


def _patch_required_selection(module: Any, hardened: Any) -> None:
    def add_risk_sentinel_fallback_findings(findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        return _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)

    def enforce_risk_sentinel_findings(findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> None:
        findings[:] = _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)

    hardened.add_risk_sentinel_fallback_findings = add_risk_sentinel_fallback_findings
    hardened.enforce_risk_sentinel_findings = enforce_risk_sentinel_findings
    module.rank_findings_for_required_budget = lambda findings, config: sorted(
        [v5._normalize_comment_finding(item) for item in findings if isinstance(item, dict)],
        key=_spare_priority,
    )[: max(0, int(getattr(config, "max_inline_comments", 12)))]


def _patch_yaml_safe_load_note() -> None:
    original = getattr(v5, "_dcoir_required_v9_original_template_fields", None)
    if original is None:
        original = getattr(v5, "_template_fields", None)
        v5._dcoir_required_v9_original_template_fields = original
    if not callable(original):
        return

    def template_fields(kind: str, path: str, line_text: str) -> dict[str, Any]:
        fields = original(kind, path, line_text)
        if kind == v5.PYTHON_YAML_LOAD:
            arg = _yaml_load_arg(line_text)
            guidance = dict(fields.get("fix_guidance") or {})
            guidance["notes"] = f"Use `yaml.safe_load({arg})` or `yaml.load({arg}, Loader=yaml.SafeLoader)` when no Python object tags are expected."
            fields["fix_guidance"] = guidance
        return fields

    v5._template_fields = template_fields
