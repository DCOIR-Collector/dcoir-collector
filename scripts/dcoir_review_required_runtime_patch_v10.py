"""Tenth required-coverage layer for DCOIR Review.

This layer fixes the #334 overflow failure without widening the large reviewer
script. It keeps v9 prompt accounting and rendering, then adds:

- ranked required selection when required sentinels exceed the inline budget
- explicit omitted-sentinel overflow metadata instead of a pre-post crash
- workflow token-to-PR-body URL classification
- workflow PR-label shell metadata classification
- broad write-permission coalescing
- final wording cleanup for HTTPS shell-pipe findings
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v4 as v4
import dcoir_review_required_runtime_patch_v5 as v5
import dcoir_review_required_runtime_patch_v9 as v9
import dcoir_review_required_runtime_patch_v9_core as core
import dcoir_review_required_runtime_patch_v9_selection as selection

SentinelKey = tuple[str, int, str]

YAML_TOKEN_TO_PR_URL = "yaml_token_to_pr_body_url"
YAML_PR_LABEL_SHELL = v4.YAML_METADATA_SHELL

TOKEN_TO_PR_URL_RE = re.compile(
    r"(?:secrets\.github_token|authorization\s*:?\s*bearer|\bauthorization\b).*(?:github\.event\.pull_request\.body|pull_request\.body)"
    r"|(?:github\.event\.pull_request\.body|pull_request\.body).*(?:secrets\.github_token|authorization\s*:?\s*bearer|\bauthorization\b)",
    re.I,
)
PR_LABEL_SHELL_RE = re.compile(
    r"(?:\b(?:bash|sh|pwsh|powershell)\b|-\s*(?:lc|c)\b).*(?:github\.event\.pull_request\.labels|pull_request\.labels)"
    r"|(?:github\.event\.pull_request\.labels|pull_request\.labels).*(?:\b(?:bash|sh|pwsh|powershell)\b|-\s*(?:lc|c)\b)",
    re.I,
)
RUN_LABEL_RE = re.compile(r"\brun\s*:\s*.*(?:github\.event\.pull_request\.labels|pull_request\.labels)", re.I)

REQUIRED_KIND_PRIORITY = {
    YAML_TOKEN_TO_PR_URL: 0,
    v4.YAML_METADATA_SHELL: 1,
    v4.YAML_SHELL_PIPE: 2,
    v4.YAML_PULL_REQUEST_TARGET: 3,
    v4.YAML_UNTRUSTED_CHECKOUT: 4,
    v4.YAML_BROAD_WRITE: 5,
    v9.PYTHON_PICKLE_LOAD: 6,
    v5.PYTHON_YAML_LOAD: 7,
    v5.PYTHON_SHELL_EXEC: 8,
    v5.PYTHON_ENV_TOKEN: 9,
    v9.PS_DYNAMIC_EXEC: 10,
    v4.PS_ACL: 11,
    v5.PS_ENV_TOKEN: 12,
    v4.PS_PROCESS_LAUNCH: 13,
}


def _normalize(value: Any) -> str:
    return v5._normalize(value)


def _original_line_kind(path: str, text: str) -> str:
    original = getattr(core, "_dcoir_required_v10_original_line_kind", None)
    if callable(original):
        return original(path, text)
    return core._line_kind(path, text)


def _workflow_token_to_pr_url(text: str) -> bool:
    normalized = _normalize(text)
    return bool(TOKEN_TO_PR_URL_RE.search(normalized))


def _workflow_pr_label_shell(text: str) -> bool:
    normalized = _normalize(text)
    return bool(RUN_LABEL_RE.search(normalized) or PR_LABEL_SHELL_RE.search(normalized))


def _line_kind(path: str, text: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    if suffix in {".yml", ".yaml"}:
        if _workflow_token_to_pr_url(text):
            return YAML_TOKEN_TO_PR_URL
        if _workflow_pr_label_shell(text):
            return v4.YAML_METADATA_SHELL
    return _original_line_kind(path, text)


def _original_claimed_kinds(finding: dict[str, Any]) -> set[str]:
    original = getattr(core, "_dcoir_required_v10_original_claimed_kinds", None)
    if callable(original):
        return set(original(finding))
    return set(core._claimed_kinds(finding))


def _claimed_kinds(finding: dict[str, Any]) -> set[str]:
    kinds = _original_claimed_kinds(finding)
    text = "\n".join(
        str(finding.get(name, "") or "")
        for name in ("title", "body", "description", "_anchored_line_text")
    )
    if _workflow_token_to_pr_url(text):
        kinds.add(YAML_TOKEN_TO_PR_URL)
    if _workflow_pr_label_shell(text):
        kinds.add(v4.YAML_METADATA_SHELL)
    return kinds


def _coverage_key(key: SentinelKey) -> SentinelKey:
    path, line, kind = key
    if kind == v4.YAML_BROAD_WRITE:
        return path, 0, kind
    return path, line, kind


def _required_sort_key(item: Any) -> tuple[int, str, int]:
    path, line, kind = core._sentinel_key(item)
    return REQUIRED_KIND_PRIORITY.get(kind, 50), path, line


def _coalesce_required(required: list[Any]) -> tuple[list[Any], list[dict[str, Any]]]:
    targets: list[Any] = []
    seen: set[SentinelKey] = set()
    duplicates: list[dict[str, Any]] = []
    for sentinel in sorted(required, key=_required_sort_key):
        key = core._sentinel_key(sentinel)
        coverage = _coverage_key(key)
        if coverage in seen:
            duplicates.append(
                {
                    "path": key[0],
                    "line": key[1],
                    "kind": key[2],
                    "reason": "duplicate_covered",
                    "label": str(getattr(sentinel, "label", "") or ""),
                    "detail": str(getattr(sentinel, "detail", "") or "")[:240],
                    "text": str(getattr(sentinel, "text", "") or "")[:240],
                }
            )
            continue
        seen.add(coverage)
        targets.append(sentinel)
    return targets, duplicates


def _priority_bucket_for_key(key: SentinelKey, required_coverage: set[SentinelKey]) -> str:
    path, _line, kind = key
    suffix = Path(path.lower()).suffix
    if _coverage_key(key) in required_coverage:
        return "hard-required"
    if kind in {v9.PYTHON_PICKLE_LOAD, v9.PS_DYNAMIC_EXEC, YAML_TOKEN_TO_PR_URL}:
        return "required-adjacent"
    if suffix in {".py", ".ps1", ".psm1", ".psd1", ".yml", ".yaml"}:
        return "high-risk"
    return "optional"


def _sentinel_summary_record(
    sentinel: Any,
    required_coverage: set[SentinelKey],
    selected_coverage: set[SentinelKey],
    limit: int,
) -> dict[str, Any]:
    key = core._sentinel_key(sentinel)
    covered = _coverage_key(key) in selected_coverage
    return {
        "path": key[0],
        "line": key[1],
        "kind": key[2],
        "priority_bucket": _priority_bucket_for_key(key, required_coverage),
        "reason": "duplicate_covered" if covered else "omitted_due_to_inline_budget" if len(selected_coverage) >= limit else "not_selected",
        "label": str(getattr(sentinel, "label", "") or ""),
        "detail": str(getattr(sentinel, "detail", "") or "")[:240],
        "text": str(getattr(sentinel, "text", "") or "")[:240],
    }


def _quote_py(value: str) -> str:
    return repr(str(value))


def _validation_for_token_to_pr_url(path: str) -> str:
    return (
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        f"path = Path({_quote_py(path)})\n"
        "text = path.read_text(encoding='utf-8')\n"
        "lower = text.lower()\n"
        "has_token = 'secrets.github_token' in lower or 'authorization' in lower or 'bearer' in lower\n"
        "has_pr_body_url = 'github.event.pull_request.body' in lower or 'pull_request.body' in lower\n"
        "assert not (has_token and has_pr_body_url), 'workflow token can still be sent to a PR-controlled URL'\n"
        "PY"
    )


def _validation_for_pr_metadata_shell(path: str) -> str:
    return (
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        "import re\n"
        f"path = Path({_quote_py(path)})\n"
        "text = path.read_text(encoding='utf-8')\n"
        "lower = text.lower()\n"
        "label_in_run = re.search(r'\\brun\\s*:\\s*.*github\\.event\\.pull_request\\.labels', lower)\n"
        "label_in_shell = 'github.event.pull_request.labels' in lower and any(token in lower for token in ('bash', ' sh ', 'sh -c', 'pwsh', 'powershell', '-lc', '-c'))\n"
        "title_body_in_shell = any(token in lower for token in ('github.event.pull_request.title', 'github.event.pull_request.body', 'github.head_ref')) and any(shell in lower for shell in ('bash', ' sh ', 'sh -c', 'pwsh', 'powershell', '-lc', '-c'))\n"
        "assert not (label_in_run or label_in_shell or title_body_in_shell), 'pull request metadata can still reach shell execution'\n"
        "PY"
    )


def _original_validation_for_key(kind: str, path: str, line: int = 0) -> str:
    original = getattr(core, "_dcoir_required_v10_original_validation_for_key", None)
    if callable(original):
        return original(kind, path, line)
    return core._validation_for_key(kind, path, line)


def _validation_for_key(kind: str, path: str, line: int = 0) -> str:
    if kind == YAML_TOKEN_TO_PR_URL:
        return _validation_for_token_to_pr_url(path)
    if kind == v4.YAML_METADATA_SHELL:
        return _validation_for_pr_metadata_shell(path)
    return _original_validation_for_key(kind, path, line)


def _fallback_for_sentinel(hardened: Any, sentinel: Any, config: Any) -> dict[str, Any]:
    key = core._sentinel_key(sentinel)
    path, line, kind = key
    line_text = str(getattr(sentinel, "text", "") or "")
    if kind == YAML_TOKEN_TO_PR_URL:
        fallback = {
            "_dcoir_v10_known_fallback": True,
            "title": "Workflow sends GitHub token to PR-controlled URL",
            "severity": "critical",
            "confidence": 0.99,
            "path": path,
            "line": line,
            "body": (
                "This line sends an authorization header or GitHub token to a URL taken from pull request body text. "
                "Pull request body content is attacker-controlled; keep token-bearing requests on trusted, allowlisted destinations."
            ),
            "suggested_replacement": "",
            "validation": _validation_for_token_to_pr_url(path),
            "fix_guidance": {
                "language": "yaml",
                "notes": "Use a trusted allowlisted endpoint or remove the token-bearing request from the pull request workflow.",
                "validation": _validation_for_token_to_pr_url(path),
            },
        }
    else:
        fallback = selection._fallback_for_sentinel(hardened, sentinel, config)
    fallback["_risk_sentinel_key"] = [path, line, kind]
    fallback["_risk_sentinel_kind"] = kind
    fallback["_anchored_line_text"] = line_text
    return fallback


def _scrub_shell_pipe_wording(finding: dict[str, Any]) -> None:
    if core._postable_key(finding)[2] != v4.YAML_SHELL_PIPE:
        return
    anchored = str(finding.get("_anchored_line_text", "") or "")
    if "https://" not in anchored.lower():
        return
    replacement = "network-fetched, unverified"
    for field in ("title", "body", "description", "suggested_replacement", "validation"):
        value = finding.get(field)
        if isinstance(value, str):
            finding[field] = re.sub(r"\bplain\s+http\b", replacement, value, flags=re.I)
    guidance = finding.get("fix_guidance")
    if isinstance(guidance, dict):
        for field, value in list(guidance.items()):
            if isinstance(value, str):
                guidance[field] = re.sub(r"\bplain\s+http\b", replacement, value, flags=re.I)


def _select_required_postable(
    hardened: Any,
    findings: list[dict[str, Any]],
    risk_sentinels: list[Any],
    config: Any,
    unanchored_findings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    del unanchored_findings
    limit = max(0, int(getattr(config, "max_inline_comments", 12)))
    required_all = core._required_sentinels(hardened, risk_sentinels)
    required_targets, duplicate_covered = _coalesce_required(required_all)
    expected = core._expected_by_line(hardened, risk_sentinels)
    required_coverage = {_coverage_key(core._sentinel_key(item)) for item in required_targets}

    raw = [item for item in findings if isinstance(item, dict)]
    candidates, dropped = core._dedupe(raw, expected)
    by_key = {core._postable_key(item): item for item in candidates}

    for sentinel in required_targets:
        key = core._sentinel_key(sentinel)
        if key not in by_key:
            fallback = _fallback_for_sentinel(hardened, sentinel, config)
            normalized = dict(fallback) if fallback.get("_dcoir_v10_known_fallback") else v5._normalize_comment_finding(fallback)
            by_key[key] = normalized
            candidates.append(normalized)

    selected: list[dict[str, Any]] = []
    selected_coverage: set[SentinelKey] = set()

    for sentinel in sorted(required_targets, key=_required_sort_key):
        key = core._sentinel_key(sentinel)
        coverage = _coverage_key(key)
        if coverage in selected_coverage or len(selected) >= limit:
            continue
        item = by_key.get(key)
        if item:
            selected.append(item)
            selected_coverage.add(coverage)

    for item in sorted(candidates, key=core._spare_priority):
        key = core._postable_key(item)
        coverage = _coverage_key(key)
        if len(selected) >= limit:
            break
        if coverage in selected_coverage or not key[2]:
            continue
        selected.append(item)
        selected_coverage.add(coverage)

    selected = selected[:limit]
    core._rewrite_validation(selected)
    for item in selected:
        path, line, kind = core._postable_key(item)
        validation = _validation_for_key(kind, path, line)
        if validation:
            item["validation"] = validation
            guidance = item.get("fix_guidance")
            if isinstance(guidance, dict):
                guidance["validation"] = validation
    for item in selected:
        _scrub_shell_pipe_wording(item)

    final_invalid = [core._key_text(core._postable_key(item)) for item in selected if core._semantic_mismatch(item, expected)]
    selected_keys = [core._postable_key(item) for item in selected]
    selected_coverage = {_coverage_key(key) for key in selected_keys}
    omitted = [
        _sentinel_summary_record(item, required_coverage, selected_coverage, limit)
        for item in risk_sentinels
        if _coverage_key(core._sentinel_key(item)) not in selected_coverage
    ]
    omitted_required = [item for item in omitted if item.get("priority_bucket") == "hard-required"]
    omitted_high_risk = [
        item
        for item in omitted
        if item.get("priority_bucket") in {"hard-required", "required-adjacent", "high-risk"}
    ]
    metadata = {
        "hard_required_count": len(required_all),
        "coalesced_required_count": len(required_targets),
        "final_postable_count": len(selected),
        "inline_limit": limit,
        "partial_overflow": bool(omitted_high_risk),
        "overflow_required_count": len(omitted_required),
        "overflow_high_risk_count": len(omitted_high_risk),
        "selected_keys": [core._key_text(key) for key in selected_keys],
        "spare_budget_selected": [
            core._key_text(key)
            for key in selected_keys
            if _coverage_key(key) not in required_coverage
        ],
        "duplicate_covered_sentinels": duplicate_covered[:80],
        "dropped_invalid_or_duplicate_candidates": dropped[:80],
        "final_invalid_selected_keys": final_invalid,
        "final_uncovered": [f"{item.get('path')}:{item.get('line')} {item.get('kind')}" for item in omitted_required],
        "omitted_sentinel_count": len(omitted),
        "omitted_required_count": len(omitted_required),
        "omitted_sentinels": omitted[:80],
    }
    core.SELECTION_SUMMARY.clear()
    core.SELECTION_SUMMARY.update(metadata)
    writer = getattr(hardened, "write_debug_json_artifact_safely", None)
    if callable(writer):
        writer(config, "metadata/required-v10-final-selection.json", metadata)
        writer(config, "metadata/required-v9-final-selection.json", metadata)

    if final_invalid:
        raise getattr(hardened, "ReviewQualityError", RuntimeError)(
            "DCOIR Review quality failure: final selected findings have semantic mismatches: " + "; ".join(final_invalid)
        )
    v9._ensure_prompt_review(config)
    return selected


def _patch_required_selection(module: Any, hardened: Any) -> None:
    def add_risk_sentinel_fallback_findings(
        findings: list[dict[str, Any]],
        risk_sentinels: list[Any],
        config: Any,
        unanchored_findings: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        return _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)

    def enforce_risk_sentinel_findings(
        findings: list[dict[str, Any]],
        risk_sentinels: list[Any],
        config: Any,
        unanchored_findings: list[dict[str, Any]] | None = None,
    ) -> None:
        findings[:] = _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)

    hardened.add_risk_sentinel_fallback_findings = add_risk_sentinel_fallback_findings
    hardened.enforce_risk_sentinel_findings = enforce_risk_sentinel_findings
    module.rank_findings_for_required_budget = lambda findings, config: sorted(
        [v5._normalize_comment_finding(item) for item in findings if isinstance(item, dict)],
        key=core._spare_priority,
    )[: max(0, int(getattr(config, "max_inline_comments", 12)))]


def _patch_yaml_extra_sentinels(owner: Any, sentinel_owner: Any | None = None) -> None:
    original = getattr(owner, "_dcoir_required_v10_original_detect_risk_sentinels", None)
    if original is None:
        original = getattr(owner, "detect_risk_sentinels", None)
    owner._dcoir_required_v10_original_detect_risk_sentinels = original
    if not callable(original):
        return

    def detect_risk_sentinels(diff: str, *args: Any, **kwargs: Any) -> list[Any]:
        widened_args = list(args)
        if widened_args and isinstance(widened_args[0], int):
            widened_args[0] = None
        widened_kwargs = dict(kwargs)
        for name in ("max_anchors", "max_sentinels", "limit"):
            if name in widened_kwargs:
                widened_kwargs[name] = None
        try:
            sentinels = list(original(diff, *widened_args, **widened_kwargs))
        except TypeError:
            sentinels = list(original(diff, *args, **kwargs))
        existing = {core._sentinel_key(item) for item in sentinels}
        risk_sentinel_type = getattr(owner, "RiskSentinel", None) or getattr(sentinel_owner, "RiskSentinel", None)
        if risk_sentinel_type is None:
            return sentinels
        for path, line, text in selection._iter_added_diff_lines(diff):
            if Path(path.lower()).suffix not in {".yml", ".yaml"}:
                continue
            comment_checker = getattr(owner, "is_comment_only_added_line", None) or getattr(sentinel_owner, "is_comment_only_added_line", None)
            if callable(comment_checker) and comment_checker(path, text):
                continue
            kind = _line_kind(path, text)
            if kind not in {YAML_TOKEN_TO_PR_URL, v4.YAML_METADATA_SHELL}:
                continue
            key = (path, line, kind)
            if key in existing:
                continue
            if kind == YAML_TOKEN_TO_PR_URL:
                label = "Workflow token forwarded to PR-controlled URL"
                detail = "A GitHub token or authorization header is sent to a URL read from pull request body text."
            else:
                label = "Workflow executes pull request metadata in a shell"
                detail = "Pull request label metadata is attacker-controlled and must not be executed by a shell."
            sentinels.append(risk_sentinel_type(path=path, line=line, label=label, detail=detail, text=text))
            existing.add(key)
        return sentinels

    owner.detect_risk_sentinels = detect_risk_sentinels


def _patch_core_semantics() -> None:
    if not hasattr(core, "_dcoir_required_v10_original_line_kind"):
        core._dcoir_required_v10_original_line_kind = core._line_kind
    if not hasattr(core, "_dcoir_required_v10_original_claimed_kinds"):
        core._dcoir_required_v10_original_claimed_kinds = core._claimed_kinds
    if not hasattr(core, "_dcoir_required_v10_original_validation_for_key"):
        core._dcoir_required_v10_original_validation_for_key = core._validation_for_key
    core._line_kind = _line_kind
    core._claimed_kinds = _claimed_kinds
    core._validation_for_key = _validation_for_key
    v9._line_kind = _line_kind
    v9._claimed_kinds = _claimed_kinds
    v9._validation_for_key = _validation_for_key


def apply_pareto_context_module(module: Any) -> None:
    hardened = getattr(module, "hardened", None)
    _patch_core_semantics()
    _patch_yaml_extra_sentinels(module, hardened)
    if hardened is not None:
        _patch_yaml_extra_sentinels(hardened)
        _patch_required_selection(module, hardened)
