"""Sixteenth required-coverage layer for DCOIR Review.

v16 addresses the #342 live-test selector failure. The previous layers could
run successfully, but they still treated a full 12-comment review as success
while hard/core YAML, Python, and PowerShell risks were omitted. This overlay
keeps Kubernetes optional/bonus, makes workflow and PowerShell aggregate
coverage explicit, detects token-to-PR-metadata URLs, and reports every core
sentinel as posted, aggregate-covered, omitted, duplicate-covered, or
suppressed.
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
import dcoir_review_required_runtime_patch_v10 as v10
import dcoir_review_required_runtime_patch_v11 as v11
import dcoir_review_required_runtime_patch_v12 as v12
import dcoir_review_required_runtime_patch_v13 as v13
import dcoir_review_required_runtime_patch_v14 as v14
import dcoir_review_required_runtime_patch_v15 as v15

SentinelKey = tuple[str, int, str]

VERSION = "v16"
PYTHON_DYNAMIC_EXEC = "python_dynamic_exec"

CORE_REQUIRED_KINDS = set(getattr(v12, "REQUIRED_KINDS", set())) | {
    PYTHON_DYNAMIC_EXEC,
    getattr(v13, "PS_PLAINTEXT_SECURE_STRING", "ps_plaintext_secure_string"),
    getattr(v13, "PS_RUN_KEY_PERSISTENCE", "ps_run_key_persistence"),
}

TRACKED_KINDS = set(getattr(v13, "TRACKED_HIGH_RISK_KINDS", set())) | CORE_REQUIRED_KINDS
OPTIONAL_PRESSURE_KINDS = {
    getattr(v13, "TS_INNER_HTML", "ts_inner_html"),
    getattr(v13, "TS_DYNAMIC_EXECUTION", "ts_dynamic_execution"),
}

_ORIGINAL_V13_LINE_KIND = getattr(v13, "_line_kind")
_ORIGINAL_V13_SENTINEL_KEY = getattr(v13, "_sentinel_key")
_ORIGINAL_V13_POSTABLE_KEY = getattr(v13, "_postable_key")
_ORIGINAL_V13_TEMPLATE_FOR_KIND = getattr(v13, "_template_for_kind")
_ORIGINAL_V13_VALIDATION_FOR_KEY = getattr(v13, "_validation_for_key")

PR_METADATA_TOKEN_RE = re.compile(
    r"(?:secrets\.github_token|github_token|authorization\s*:?|bearer)"
    r".*(?:github\.event\.pull_request\.(?:body|title|labels|head\.ref|head\.sha)|pull_request\.(?:body|title|labels|head))"
    r"|(?:github\.event\.pull_request\.(?:body|title|labels|head\.ref|head\.sha)|pull_request\.(?:body|title|labels|head))"
    r".*(?:secrets\.github_token|github_token|authorization\s*:?|bearer)",
    re.I,
)


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _line_number(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _is_workflow_path(path: str) -> bool:
    normalized = str(path or "").replace("\\", "/").lower()
    return normalized.startswith(".github/workflows/") and normalized.endswith((".yml", ".yaml"))


def _is_optional_path(path: str) -> bool:
    normalized = str(path or "").replace("\\", "/").lower()
    basename = normalized.rsplit("/", 1)[-1]
    return "/optional_" in normalized or basename.startswith("optional_")


def _line_kind(path: str, text: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    lower = _normalize(text)
    if _is_workflow_path(path):
        if PR_METADATA_TOKEN_RE.search(lower):
            return v10.YAML_TOKEN_TO_PR_URL
        if "pull_request_target" in lower:
            return v4.YAML_PULL_REQUEST_TARGET
        if "write-all" in lower or re.search(r"\b[a-z_-]+\s*:\s*write\b", lower):
            return v4.YAML_BROAD_WRITE
        if "github.event.pull_request.head" in lower or "github.head_ref" in lower:
            return v4.YAML_UNTRUSTED_CHECKOUT
        if ("curl" in lower or "wget" in lower) and ("| sh" in lower or "| bash" in lower):
            return v4.YAML_SHELL_PIPE
        if "github.event.pull_request" in lower and any(token in lower for token in ("bash -lc", "sh -c", "run:", "shell:")):
            return v4.YAML_METADATA_SHELL
    if suffix == ".py":
        if "pickle.loads" in lower or "pickle.load(" in lower:
            return v9.PYTHON_PICKLE_LOAD
        if "yaml.load" in lower:
            return v5.PYTHON_YAML_LOAD
        if re.search(r"\b(?:eval|exec|compile)\s*\(", lower):
            return PYTHON_DYNAMIC_EXEC
        if "shell=true" in lower or "os.system(" in lower or "os.popen(" in lower:
            return v5.PYTHON_SHELL_EXEC
        if ("requests." in lower or "urlopen" in lower) and (
            "authorization" in lower or "bearer" in lower or "dcoir_token" in lower or "callback" in lower
        ):
            return v5.PYTHON_ENV_TOKEN
        if "extractall" in lower:
            return v11.PYTHON_ARCHIVE_EXTRACT
        if any(token in lower for token in ("write_text(", "write_bytes(", ".open(", "open(")):
            return v11.PYTHON_PATH_WRITE
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if "invoke-expression" in lower or re.search(r"\biex\b", lower):
            return v9.PS_DYNAMIC_EXEC
        if "convertto-securestring" in lower and "-asplaintext" in lower:
            return v13.PS_PLAINTEXT_SECURE_STRING
        if "filesystemaccessrule" in lower or "set-acl" in lower:
            return v4.PS_ACL
        if "start-process" in lower:
            return v4.PS_PROCESS_LAUNCH
        if ("invoke-webrequest" in lower or "invoke-restmethod" in lower) and (
            "authorization" in lower or "bearer" in lower or "$env:dcoir_token" in lower
        ):
            return v5.PS_ENV_TOKEN
        if "currentversion\\run" in lower:
            return v13.PS_RUN_KEY_PERSISTENCE
    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        if ".innerhtml" in lower or ".outerhtml" in lower or "insertadjacenthtml" in lower:
            return v13.TS_INNER_HTML
        if "settimeout(" in lower or "setinterval(" in lower or "new function(" in lower:
            return v13.TS_DYNAMIC_EXECUTION
    return _ORIGINAL_V13_LINE_KIND(path, text)


def _sentinel_key(sentinel: Any) -> SentinelKey:
    path = str(getattr(sentinel, "path", "") or "")
    line = _line_number(getattr(sentinel, "line", 0))
    text = str(getattr(sentinel, "text", "") or "")
    kind = _line_kind(path, text) or _ORIGINAL_V13_SENTINEL_KEY(sentinel)[2]
    return path, line, kind


def _postable_key(finding: dict[str, Any]) -> SentinelKey:
    raw = finding.get("_risk_sentinel_key")
    if isinstance(raw, (list, tuple)) and len(raw) == 3:
        return str(raw[0] or ""), _line_number(raw[1]), str(raw[2] or "")
    path, line, kind = _ORIGINAL_V13_POSTABLE_KEY(finding)
    text = "\n".join(str(finding.get(name, "") or "") for name in ("_anchored_line_text", "title", "body", "description"))
    return path, line, _line_kind(path, text) or kind


def _coverage_key(key: SentinelKey) -> SentinelKey:
    path, line, kind = key
    if kind in {v4.YAML_BROAD_WRITE, v11.PYTHON_ARCHIVE_EXTRACT}:
        return path, 0, kind
    return path, line, kind


def _coverage_from_finding(finding: dict[str, Any]) -> set[SentinelKey]:
    keys = {_coverage_key(_postable_key(finding))}
    raw_keys = finding.get("covered_risk_sentinel_keys")
    if isinstance(raw_keys, list):
        for raw in raw_keys:
            if isinstance(raw, (list, tuple)) and len(raw) == 3:
                keys.add(_coverage_key((str(raw[0] or ""), _line_number(raw[1]), str(raw[2] or ""))))
    return {key for key in keys if key[0] and key[2]}


def _kind_rank(kind: str) -> int:
    order = {
        v10.YAML_TOKEN_TO_PR_URL: 0,
        v4.YAML_METADATA_SHELL: 1,
        v4.YAML_SHELL_PIPE: 2,
        v4.YAML_PULL_REQUEST_TARGET: 3,
        v4.YAML_BROAD_WRITE: 4,
        v4.YAML_UNTRUSTED_CHECKOUT: 5,
        v9.PYTHON_PICKLE_LOAD: 10,
        v5.PYTHON_YAML_LOAD: 11,
        PYTHON_DYNAMIC_EXEC: 12,
        v5.PYTHON_SHELL_EXEC: 13,
        v5.PYTHON_ENV_TOKEN: 14,
        v11.PYTHON_ARCHIVE_EXTRACT: 15,
        v11.PYTHON_PATH_WRITE: 16,
        v9.PS_DYNAMIC_EXEC: 20,
        v4.PS_PROCESS_LAUNCH: 21,
        v5.PS_ENV_TOKEN: 22,
        v13.PS_RUN_KEY_PERSISTENCE: 23,
        v4.PS_ACL: 24,
        v13.PS_PLAINTEXT_SECURE_STRING: 25,
        v13.TS_INNER_HTML: 80,
        v13.TS_DYNAMIC_EXECUTION: 81,
    }
    return order.get(str(kind or ""), 99)


def _family(kind: str) -> str:
    if kind.startswith("yaml_"):
        return "yaml"
    if kind.startswith("python_"):
        return "python"
    if kind.startswith("ps_"):
        return "powershell"
    if kind.startswith("ts_"):
        return "typescript"
    if kind.startswith("k8s_"):
        return "kubernetes"
    return "other"


def _candidate_priority(finding: dict[str, Any]) -> tuple[int, int, int, str, int]:
    path, line, kind = _postable_key(finding)
    if finding.get("_dcoir_v16_aggregate"):
        group = 0
    elif kind in CORE_REQUIRED_KINDS:
        group = 1
    elif kind in OPTIONAL_PRESSURE_KINDS or _is_optional_path(path):
        group = 8
    else:
        group = 5
    family = {"yaml": 0, "python": 1, "powershell": 2, "other": 5, "typescript": 8, "kubernetes": 9}.get(_family(kind), 7)
    return group, family, _kind_rank(kind), path, line


def _quote(path: str) -> str:
    return shlex.quote(path)


def _validation_for_key(kind: str, path: str, line: int = 0) -> str:
    if kind.startswith("python_"):
        return f"python3 -m py_compile {_quote(path)}"
    if kind.startswith("ps_"):
        ps_path = path.replace("'", "''")
        script = (
            "$errors=$null; "
            f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath '{ps_path}'), [ref]$errors) | Out-Null; "
            "if ($errors) { throw ($errors | Out-String) }"
        )
        return "pwsh -NoProfile -Command " + shlex.quote(script)
    if kind.startswith("yaml_"):
        return "python3 -c " + shlex.quote(f"from pathlib import Path; Path({path!r}).read_text(encoding='utf-8')")
    return _ORIGINAL_V13_VALIDATION_FOR_KEY(kind, path, line)


def _template_for_kind(kind: str) -> tuple[str, str, str]:
    if kind == PYTHON_DYNAMIC_EXEC:
        return (
            "Python executes caller-controlled code",
            "This line evaluates text as Python code.",
            "Replace dynamic evaluation with explicit allowlisted behavior or a safe parser.",
        )
    return _ORIGINAL_V13_TEMPLATE_FOR_KIND(kind)


def _finding_for_sentinel(sentinel: Any) -> dict[str, Any]:
    path, line, kind = _sentinel_key(sentinel)
    title, body, notes = _template_for_kind(kind)
    return {
        "title": title,
        "body": body,
        "severity": "critical" if kind in CORE_REQUIRED_KINDS else "high",
        "confidence": 0.99,
        "path": path,
        "line": line,
        "_anchored_line_text": str(getattr(sentinel, "text", "") or ""),
        "_risk_sentinel_key": [path, line, kind],
        "_risk_sentinel_kind": kind,
        "validation": _validation_for_key(kind, path, line),
        "fix_guidance": {
            "language": "yaml" if kind.startswith("yaml_") else "powershell" if kind.startswith("ps_") else "python" if kind.startswith("python_") else "text",
            "notes": notes,
            "validation": _validation_for_key(kind, path, line),
        },
    }


def _line_label(key: SentinelKey) -> str:
    return f"`{key[0]}:{key[1]}` `{key[2]}`"


def _aggregate_finding(path: str, line: int, kind: str, title: str, body: str, notes: str, keys: list[SentinelKey]) -> dict[str, Any]:
    validation = _validation_for_key(kind, path, line)
    return {
        "title": title,
        "body": body,
        "severity": "critical",
        "confidence": 0.99,
        "path": path,
        "line": line,
        "_risk_sentinel_key": [path, line, kind],
        "_risk_sentinel_kind": kind,
        "covered_risk_sentinel_keys": [[item[0], item[1], item[2]] for item in keys],
        "_dcoir_v16_aggregate": True,
        "validation": validation,
        "fix_guidance": {"language": "yaml" if kind.startswith("yaml_") else "powershell", "notes": notes, "validation": validation},
    }


def _choose_anchor(keys: list[SentinelKey], preferred: tuple[str, ...]) -> SentinelKey:
    for kind in preferred:
        for key in keys:
            if key[2] == kind:
                return key
    return sorted(keys, key=lambda item: (item[0], item[1], _kind_rank(item[2])))[0]


def _aggregate_candidates(core_sentinels: list[Any]) -> list[dict[str, Any]]:
    by_path: dict[str, list[SentinelKey]] = {}
    for sentinel in core_sentinels:
        key = _sentinel_key(sentinel)
        by_path.setdefault(key[0], []).append(key)
    aggregates: list[dict[str, Any]] = []
    for path, keys in by_path.items():
        if _is_workflow_path(path):
            privilege = [key for key in keys if key[2] in {v4.YAML_PULL_REQUEST_TARGET, v4.YAML_BROAD_WRITE, v4.YAML_UNTRUSTED_CHECKOUT}]
            if privilege:
                anchor = _choose_anchor(privilege, (v4.YAML_PULL_REQUEST_TARGET, v4.YAML_BROAD_WRITE, v4.YAML_UNTRUSTED_CHECKOUT))
                detail = ", ".join(_line_label(key) for key in sorted(privilege, key=lambda item: item[1]))
                aggregates.append(
                    _aggregate_finding(
                        anchor[0],
                        anchor[1],
                        anchor[2],
                        "Privileged workflow combines sensitive permissions with PR-controlled code",
                        f"This workflow combines privileged pull request context, write permissions, or PR-controlled checkout. Covered signals: {detail}.",
                        "Split privileged metadata handling from untrusted code checkout/execution and reduce workflow permissions to least privilege.",
                        privilege,
                    )
                )
            metadata = [key for key in keys if key[2] in {v4.YAML_METADATA_SHELL, v10.YAML_TOKEN_TO_PR_URL, v4.YAML_SHELL_PIPE}]
            if metadata:
                anchor = _choose_anchor(metadata, (v4.YAML_METADATA_SHELL, v10.YAML_TOKEN_TO_PR_URL, v4.YAML_SHELL_PIPE))
                detail = ", ".join(_line_label(key) for key in sorted(metadata, key=lambda item: item[1]))
                aggregates.append(
                    _aggregate_finding(
                        anchor[0],
                        anchor[1],
                        anchor[2],
                        "Privileged workflow executes or exfiltrates pull request metadata",
                        f"Pull request metadata reaches shell execution, token-bearing requests, or network-fetched shell execution. Covered signals: {detail}.",
                        "Do not execute PR metadata, do not send repository tokens to PR-controlled URLs, and verify downloaded installers before execution.",
                        metadata,
                    )
                )
        ps_command = [key for key in keys if key[2] in {v4.PS_ACL, v4.PS_PROCESS_LAUNCH, v9.PS_DYNAMIC_EXEC, v13.PS_RUN_KEY_PERSISTENCE}]
        if ps_command:
            anchor = _choose_anchor(ps_command, (v4.PS_ACL, v4.PS_PROCESS_LAUNCH, v9.PS_DYNAMIC_EXEC, v13.PS_RUN_KEY_PERSISTENCE))
            detail = ", ".join(_line_label(key) for key in sorted(ps_command, key=lambda item: item[1]))
            aggregates.append(
                _aggregate_finding(
                    anchor[0],
                    anchor[1],
                    anchor[2],
                    "PowerShell combines broad access, dynamic execution, process launch, or persistence",
                    f"This script contains command execution, broad ACL, process launch, or Run-key persistence risk. Covered signals: {detail}.",
                    "Replace dynamic execution and caller-controlled launches with allowlisted commands, narrow ACLs, and remove Run-key writes unless explicitly governed.",
                    ps_command,
                )
            )
        ps_secret = [key for key in keys if key[2] in {v13.PS_PLAINTEXT_SECURE_STRING, v5.PS_ENV_TOKEN}]
        if ps_secret:
            anchor = _choose_anchor(ps_secret, (v13.PS_PLAINTEXT_SECURE_STRING, v5.PS_ENV_TOKEN))
            detail = ", ".join(_line_label(key) for key in sorted(ps_secret, key=lambda item: item[1]))
            aggregates.append(
                _aggregate_finding(
                    anchor[0],
                    anchor[1],
                    anchor[2],
                    "PowerShell handles plaintext secret material or forwards an environment token",
                    f"Secret material is accepted as plaintext or an environment token is forwarded to a request-controlled callback. Covered signals: {detail}.",
                    "Load secrets from a trusted secret store and allowlist outbound token-bearing destinations.",
                    ps_secret,
                )
            )
    return aggregates


def _coalesce_sentinels(sentinels: list[Any]) -> list[Any]:
    kept: dict[SentinelKey, Any] = {}
    for sentinel in sentinels:
        key = _sentinel_key(sentinel)
        coverage = _coverage_key(key)
        current = kept.get(coverage)
        if current is None:
            kept[coverage] = sentinel
            continue
        current_key = _sentinel_key(current)
        if (_kind_rank(key[2]), key[1]) < (_kind_rank(current_key[2]), current_key[1]):
            kept[coverage] = sentinel
    return list(kept.values())


def _core_sentinels(risk_sentinels: list[Any]) -> list[Any]:
    return _coalesce_sentinels([sentinel for sentinel in risk_sentinels if _sentinel_key(sentinel)[2] in CORE_REQUIRED_KINDS])


def _select_once(_hardened: Any, findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    limit = max(0, int(getattr(config, "max_inline_comments", 12)))
    core_targets = _core_sentinels(risk_sentinels)
    required_cov = {_coverage_key(_sentinel_key(sentinel)) for sentinel in core_targets}
    aggregate = _aggregate_candidates(core_targets)
    selected: list[dict[str, Any]] = []
    selected_cov: set[SentinelKey] = set()

    def add(item: dict[str, Any]) -> None:
        if len(selected) >= limit:
            return
        item_cov = _coverage_from_finding(item)
        if not item_cov or item_cov <= selected_cov:
            return
        selected.append(item)
        selected_cov.update(item_cov)

    for item in sorted(aggregate, key=_candidate_priority):
        add(item)
    for sentinel in sorted(core_targets, key=lambda item: (_kind_rank(_sentinel_key(item)[2]), _sentinel_key(item)[0], _sentinel_key(item)[1])):
        if _coverage_key(_sentinel_key(sentinel)) not in selected_cov:
            add(_finding_for_sentinel(sentinel))

    model_candidates: list[dict[str, Any]] = []
    for raw in findings:
        if not isinstance(raw, dict):
            continue
        try:
            item = v5._normalize_comment_finding(raw)
        except Exception:
            item = dict(raw)
        key = _postable_key(item)
        if key[2] and key[2] not in CORE_REQUIRED_KINDS:
            item["_risk_sentinel_key"] = [key[0], key[1], key[2]]
            model_candidates.append(item)
    for item in sorted(model_candidates, key=_candidate_priority):
        add(item)

    omitted_required = []
    aggregate_covered = []
    for sentinel in core_targets:
        key = _sentinel_key(sentinel)
        coverage = _coverage_key(key)
        if coverage in selected_cov:
            if not any(_postable_key(item) == key for item in selected):
                aggregate_covered.append(_sentinel_record(sentinel, "aggregate_covered", required_cov, selected_cov, limit))
            continue
        omitted_required.append(_sentinel_record(sentinel, "omitted_due_to_inline_budget", required_cov, selected_cov, limit))

    optional_overflow = []
    for sentinel in risk_sentinels:
        key = _sentinel_key(sentinel)
        coverage = _coverage_key(key)
        if coverage in selected_cov or coverage in required_cov:
            continue
        if key[2] in TRACKED_KINDS or key[2] in OPTIONAL_PRESSURE_KINDS:
            optional_overflow.append(_sentinel_record(sentinel, "omitted_due_to_inline_budget", required_cov, selected_cov, limit))

    selected_keys = [_postable_key(item) for item in selected]
    metadata = {
        "version": VERSION,
        "inline_limit": limit,
        "final_postable_count": len(selected),
        "hard_required_count": len(core_targets),
        "covered_required_count": len(required_cov),
        "selected_keys": [_key_text(key) for key in selected_keys],
        "posted_required_sentinels": [_key_text(key) for key in selected_keys if _coverage_key(key) in required_cov],
        "aggregate_covered_sentinels": aggregate_covered[:100],
        "omitted_required_sentinels": omitted_required[:100],
        "omitted_optional_high_risk_sentinels": optional_overflow[:100],
        "overflow_required_count": len(omitted_required),
        "overflow_optional_high_risk_count": len(optional_overflow),
        "partial_overflow": bool(omitted_required or optional_overflow),
        "final_uncovered": [_key_text((item["path"], int(item["line"]), item["kind"])) for item in omitted_required],
        "required_ledger_schema": "v16_posted_aggregate_covered_omitted_suppressed",
        "core_required_families": _family_counts(required_cov),
        "selected_coverage_families": _family_counts(selected_cov),
        "kubernetes_policy": "optional_bonus_only",
    }
    return selected, metadata


def _family_counts(keys: set[SentinelKey]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _path, _line, kind in keys:
        family = _family(kind)
        counts[family] = counts.get(family, 0) + 1
    return counts


def _key_text(key: SentinelKey) -> str:
    return f"{key[0]}:{key[1]} {key[2]}"


def _sentinel_record(sentinel: Any, reason: str, required: set[SentinelKey], selected: set[SentinelKey], limit: int) -> dict[str, Any]:
    key = _sentinel_key(sentinel)
    return {
        "path": key[0],
        "line": key[1],
        "kind": key[2],
        "bucket": "hard-required" if _coverage_key(key) in required else "optional-pressure",
        "reason": reason,
        "label": str(getattr(sentinel, "label", "") or ""),
        "detail": str(getattr(sentinel, "detail", "") or "")[:240],
        "text": str(getattr(sentinel, "text", "") or "")[:240],
        "selected_count": len(selected),
        "inline_limit": limit,
    }


def _select_required_postable(hardened: Any, findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    del unanchored_findings
    selected, metadata = _select_once(hardened, findings, risk_sentinels, config)
    core.SELECTION_SUMMARY.clear()
    core.SELECTION_SUMMARY.update(metadata)
    writer = getattr(hardened, "write_debug_json_artifact_safely", None)
    if callable(writer):
        writer(config, "metadata/required-v16-final-selection.json", metadata)
    v9._ensure_prompt_review(config)
    return selected


def _render_comment(finding: dict[str, Any]) -> str:
    path, line, kind = _postable_key(finding)
    title = str(finding.get("title", "") or _template_for_kind(kind)[0]).strip()
    body = str(finding.get("body", "") or _template_for_kind(kind)[1]).strip()
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    notes = str(guidance.get("notes", "") or _template_for_kind(kind)[2]).strip()
    validation = str(finding.get("validation", "") or guidance.get("validation", "") or _validation_for_key(kind, path, line)).strip()
    lines = [f"**{title}**", "", body]
    covered = finding.get("covered_risk_sentinel_keys")
    if isinstance(covered, list) and len(covered) > 1:
        rendered = []
        for raw in covered:
            if isinstance(raw, (list, tuple)) and len(raw) == 3:
                rendered.append(_line_label((str(raw[0] or ""), _line_number(raw[1]), str(raw[2] or ""))))
        if rendered:
            lines.extend(["", "**Covered signals:**", *[f"- {item}" for item in rendered]])
    if notes:
        lines.extend(["", "**Suggested fix:**", "", notes])
    if validation:
        lines.extend(["", "**Validation:**", "", "```bash", validation, "```"])
    return "\n".join(lines).strip()


def _patch_final_rendering(base: Any) -> None:
    def build_inline_comment(finding: dict[str, Any], model_used: str, config: Any) -> str:
        del model_used, config
        return _render_comment(finding)

    base.build_inline_comment = build_inline_comment


def _patch_review_body_overflow(hardened: Any) -> None:
    original = getattr(hardened, "_dcoir_v16_original_build_review_body_with_unanchored", None)
    if original is None:
        original = getattr(hardened, "build_review_body_with_unanchored", None)
        hardened._dcoir_v16_original_build_review_body_with_unanchored = original
    if not callable(original):
        return

    def build_review_body_with_unanchored(*args: Any, **kwargs: Any) -> str:
        body = str(original(*args, **kwargs) or "").strip()
        metadata = dict(core.SELECTION_SUMMARY)
        covered = list(metadata.get("aggregate_covered_sentinels", []) or [])
        omitted = list(metadata.get("omitted_required_sentinels", []) or [])
        if not covered and not omitted:
            return body
        lines = [body, "", "---", "", "### DCOIR Review Required Coverage Ledger"]
        if covered:
            lines.extend(["", "**Aggregate-covered required findings:**"])
            lines.extend(f"- `{item.get('path')}:{item.get('line')}` `{item.get('kind')}` ({item.get('reason')})" for item in covered[:20])
        if omitted:
            lines.extend(["", "**Omitted required findings:**"])
            lines.extend(f"- `{item.get('path')}:{item.get('line')}` `{item.get('kind')}` ({item.get('reason')})" for item in omitted[:20])
        return "\n".join(line for line in lines if line is not None).strip()

    hardened.build_review_body_with_unanchored = build_review_body_with_unanchored


def _patch_detect(owner: Any, sentinel_owner: Any | None = None) -> None:
    original = getattr(owner, "_dcoir_required_v16_original_detect_risk_sentinels", None)
    if original is None:
        original = getattr(owner, "detect_risk_sentinels", None)
        owner._dcoir_required_v16_original_detect_risk_sentinels = original
    if not callable(original):
        return

    def detect_risk_sentinels(diff: str, *args: Any, **kwargs: Any) -> list[Any]:
        try:
            sentinels = list(original(diff, *args, **kwargs))
        except TypeError:
            sentinels = list(original(diff))
        risk_sentinel_type = getattr(owner, "RiskSentinel", None) or getattr(sentinel_owner, "RiskSentinel", None)
        if risk_sentinel_type is None:
            return sentinels
        existing = {_sentinel_key(item) for item in sentinels}
        checker = getattr(owner, "is_comment_only_added_line", None) or getattr(sentinel_owner, "is_comment_only_added_line", None)
        for path, line, text in selection._iter_added_diff_lines(diff):
            if callable(checker) and checker(path, text):
                continue
            kind = _line_kind(path, text)
            if kind not in TRACKED_KINDS and kind not in OPTIONAL_PRESSURE_KINDS:
                continue
            key = (path, line, kind)
            if key in existing:
                continue
            title, body, _notes = _template_for_kind(kind)
            sentinels.append(risk_sentinel_type(path=path, line=line, label=title, detail=body, text=text))
            existing.add(key)
        return sentinels

    owner.detect_risk_sentinels = detect_risk_sentinels


def _patch_core_semantics() -> None:
    v12.REQUIRED_KINDS = set(getattr(v12, "REQUIRED_KINDS", set())) | CORE_REQUIRED_KINDS
    v13.REQUIRED_KINDS = set(getattr(v13, "REQUIRED_KINDS", set())) | CORE_REQUIRED_KINDS
    v13.TRACKED_HIGH_RISK_KINDS = set(getattr(v13, "TRACKED_HIGH_RISK_KINDS", set())) | TRACKED_KINDS
    v14.SELECTION_KIND_RANK.update({kind: _kind_rank(kind) for kind in CORE_REQUIRED_KINDS | {v10.YAML_TOKEN_TO_PR_URL}})
    v14.FAMILY_ORDER = ("yaml", "python", "powershell", "other", "typescript")
    v15.FAMILY_ORDER = ("yaml", "python", "powershell", "other", "typescript")
    v13._line_kind = _line_kind
    v13._sentinel_key = _sentinel_key
    v13._postable_key = _postable_key
    v13._coverage_key = _coverage_key
    v13._validation_for_key = _validation_for_key
    v13._spare_priority = _candidate_priority
    v14._family = _family
    v14._spare_priority = _candidate_priority
    core._sentinel_key = _sentinel_key
    core._postable_key = _postable_key
    core._coverage_key = _coverage_key
    core._spare_priority = _candidate_priority
    core._validation_for_key = _validation_for_key
    v11._line_kind = _line_kind
    v12._sentinel_key = _sentinel_key
    v12._postable_key = _postable_key
    v12._coverage_key = _coverage_key
    v12._spare_priority = _candidate_priority


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    _patch_core_semantics()
    _patch_detect(module, hardened)
    module.rank_findings_for_required_budget = lambda findings, config: sorted(
        [v5._normalize_comment_finding(item) for item in findings if isinstance(item, dict)],
        key=_candidate_priority,
    )[: max(0, int(getattr(config, "max_inline_comments", 12)))]
    if hardened is not None:
        _patch_detect(hardened)
        hardened.add_risk_sentinel_fallback_findings = lambda findings, risk_sentinels, config, unanchored_findings=None: _select_required_postable(
            hardened, findings, risk_sentinels, config, unanchored_findings
        )
        hardened.enforce_risk_sentinel_findings = lambda findings, risk_sentinels, config, unanchored_findings=None: findings.__setitem__(
            slice(None), _select_required_postable(hardened, findings, risk_sentinels, config, unanchored_findings)
        )
        _patch_review_body_overflow(hardened)
    if base is not None:
        _patch_final_rendering(base)
        v11._patch_progress_comment(base, hardened)
