"""Eighth required-coverage layer for DCOIR Review.

This layer tightens the final, user-facing review output after v7. It rejects
postable findings whose rendered semantic kind does not match the anchored
required line, fills spare budget with unique high-risk findings before
duplicates or optional pressure findings, renders native suggestions for exact
single-line replacements, and emits readable deterministic validation commands.
"""

from __future__ import annotations

import re
import shlex
from typing import Any

import dcoir_review_required_runtime_patch_v4 as v4
import dcoir_review_required_runtime_patch_v5 as v5
import dcoir_review_required_runtime_patch_v6 as v6
import dcoir_review_required_runtime_patch_v7 as v7

SentinelKey = tuple[str, int, str]


def _line_number(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _key_text(key: SentinelKey) -> str:
    return f"{key[0]}:{key[1]} {key[2]}"


def _finding_text(finding: dict[str, Any]) -> str:
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    parts = [
        str(finding.get("title", "") or ""),
        str(finding.get("body", "") or ""),
        str(finding.get("description", "") or ""),
        str(guidance.get("notes", "") or ""),
        str(guidance.get("remove", "") or ""),
        str(guidance.get("replace", "") or ""),
        str(guidance.get("add", "") or ""),
    ]
    return v5._normalize("\n".join(parts))


def _site_key(finding: dict[str, Any]) -> tuple[str, int]:
    return str(finding.get("path", "") or ""), _line_number(finding.get("line", 0))


def _severity_rank(finding: dict[str, Any]) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(str(finding.get("severity", "")).lower(), 4)


def _confidence(finding: dict[str, Any]) -> float:
    try:
        return float(finding.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _path_is_optional_pressure(path: str) -> bool:
    lowered = path.lower()
    return "/optional_" in lowered or lowered.rsplit("/", 1)[-1].startswith("optional_")


def _is_pickle_finding(finding: dict[str, Any]) -> bool:
    return "pickle" in _finding_text(finding) or "pickle.loads" in str(finding.get("_anchored_line_text", "") or "").lower()


def _optional_priority(finding: dict[str, Any]) -> tuple[int, int, float]:
    path = str(finding.get("path", "") or "")
    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if _is_pickle_finding(finding):
        family = 0
    elif not _path_is_optional_pressure(path) and suffix in {"py", "ps1", "psm1", "psd1", "yml", "yaml"}:
        family = 1
    elif not _path_is_optional_pressure(path):
        family = 2
    else:
        family = 3
    return (family, _severity_rank(finding), -_confidence(finding))


def _required_site_map(risk_sentinels: list[Any], hardened: Any) -> dict[tuple[str, int], list[Any]]:
    result: dict[tuple[str, int], list[Any]] = {}
    required = list(hardened.required_risk_sentinels(risk_sentinels)) if callable(getattr(hardened, "required_risk_sentinels", None)) else []
    for sentinel in required:
        result.setdefault((str(getattr(sentinel, "path", "") or ""), _line_number(getattr(sentinel, "line", 0))), []).append(sentinel)
    return result


def _required_key_set(risk_sentinels: list[Any], hardened: Any) -> set[SentinelKey]:
    required = list(hardened.required_risk_sentinels(risk_sentinels)) if callable(getattr(hardened, "required_risk_sentinels", None)) else []
    return {v7._sentinel_key(sentinel) for sentinel in required}


def _covers_any_site_required(finding: dict[str, Any], site_map: dict[tuple[str, int], list[Any]], original_covers: Any | None) -> bool:
    site = _site_key(finding)
    sentinels = site_map.get(site, [])
    return any(v7._covers_required_sentinel(finding, sentinel, original_covers) for sentinel in sentinels)


def _is_required_site_mismatch(finding: dict[str, Any], site_map: dict[tuple[str, int], list[Any]], original_covers: Any | None) -> bool:
    site = _site_key(finding)
    if site not in site_map:
        return False
    return not _covers_any_site_required(finding, site_map, original_covers)


def _dedupe_final(findings: list[dict[str, Any]], site_map: dict[tuple[str, int], list[Any]], original_covers: Any | None) -> tuple[list[dict[str, Any]], list[str]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()
    dropped: list[str] = []
    for finding in findings:
        normalized = v5._normalize_comment_finding(finding)
        if _is_required_site_mismatch(normalized, site_map, original_covers):
            dropped.append(f"{normalized.get('path', '')}:{normalized.get('line', '')} semantic_mismatch {normalized.get('title', '')}")
            continue
        key = v7._postable_key(normalized)
        if key in seen:
            dropped.append(f"{key[0]}:{key[1]} duplicate {key[2]}")
            continue
        seen.add(key)
        selected.append(normalized)
    return selected, dropped


def _select_required_postable_v8(
    hardened: Any,
    original_rank: Any,
    original_covers: Any,
    original_fallback: Any,
    findings: list[dict[str, Any]],
    risk_sentinels: list[Any],
    config: Any,
    unanchored_findings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    site_map = _required_site_map(risk_sentinels, hardened)
    required_keys = _required_key_set(risk_sentinels, hardened)
    inline_limit = max(0, int(getattr(config, "max_inline_comments", 12)))

    base_selection = v7._select_required_postable(
        hardened,
        original_rank,
        original_covers,
        original_fallback,
        findings,
        risk_sentinels,
        config,
        unanchored_findings,
    )
    selected, dropped = _dedupe_final(base_selection, site_map, original_covers)

    selected_keys = {v7._postable_key(finding) for finding in selected}
    normalized_pool = [v5._normalize_comment_finding(finding) for finding in [*findings, *(unanchored_findings or [])] if isinstance(finding, dict)]
    candidates, candidate_drops = _dedupe_final(normalized_pool, site_map, original_covers)
    dropped.extend(candidate_drops)
    candidates = [finding for finding in candidates if v7._postable_key(finding) not in selected_keys]
    candidates.sort(key=_optional_priority)

    for candidate in candidates:
        if len(selected) >= inline_limit:
            break
        key = v7._postable_key(candidate)
        if key in selected_keys:
            continue
        if key[2] in {"", "hardcoded secrets bypass validation"}:
            continue
        selected.append(candidate)
        selected_keys.add(key)

    selected = selected[:inline_limit]
    required_uncovered = [
        key for key in required_keys if not any(tuple(v7._postable_key(finding)) == key or key == tuple(finding.get("_risk_sentinel_key", ())) for finding in selected)
    ]
    required_uncovered = [
        key
        for key in required_uncovered
        if not any(
            str(finding.get("path", "") or "") == key[0]
            and _line_number(finding.get("line", 0)) == key[1]
            and str(finding.get("_risk_sentinel_kind", "") or "") == key[2]
            for finding in selected
        )
    ]
    metadata = {
        "hard_required_count": len(required_keys),
        "input_finding_count": len(findings),
        "final_postable_count": len(selected),
        "dropped_final_findings": dropped[:50],
        "selected_keys": [_key_text(v7._postable_key(finding)) for finding in selected],
        "final_uncovered": [_key_text(key) for key in required_uncovered],
        "spare_budget_selected": [
            _key_text(v7._postable_key(finding))
            for finding in selected
            if v7._postable_key(finding) not in required_keys
        ],
    }
    hardened.write_debug_json_artifact_safely(config, "metadata/required-v8-final-selection.json", metadata)
    if required_uncovered:
        digest = "; ".join(_key_text(key) for key in required_uncovered)
        raise getattr(hardened, "ReviewQualityError", RuntimeError)(
            f"DCOIR Review quality failure: required changed-line signals remain uncovered after v8 final selection: {digest}."
        )
    return selected


def _patch_required_selection(module: Any, hardened: Any) -> None:
    original_rank = getattr(module, "_dcoir_required_v7_original_rank_findings_for_required_budget", None)
    original_covers = getattr(hardened, "_dcoir_required_v7_original_finding_covers_risk_sentinel", None)
    original_fallback = getattr(hardened, "_dcoir_required_v7_original_risk_sentinel_fallback_finding", None)

    def required_v8_add(findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        return _select_required_postable_v8(hardened, original_rank, original_covers, original_fallback, findings, risk_sentinels, config, unanchored_findings)

    def required_v8_enforce(findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> None:
        findings[:] = required_v8_add(findings, risk_sentinels, config, unanchored_findings)

    hardened.add_risk_sentinel_fallback_findings = required_v8_add
    hardened.enforce_risk_sentinel_findings = required_v8_enforce
    module.rank_findings_for_required_budget = lambda findings, config: required_v8_add(findings, [], config, None)


def _single_line(value: Any) -> str:
    text = str(value or "").strip("\n")
    return text if text and "\n" not in text else ""


def _native_suggestion_replacement(finding: dict[str, Any], base: Any) -> str:
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    remove_code = _single_line(guidance.get("remove", ""))
    replace_code = _single_line(guidance.get("replace", ""))
    if not remove_code or not replace_code:
        return ""
    if not base.guidance_value_looks_like_code(replace_code, base.language_hint_for_path(str(finding.get("path", "") or ""))):
        return ""
    return replace_code.rstrip()


def _patch_inline_comment_renderer(base: Any) -> None:
    original = getattr(base, "_dcoir_required_v8_original_build_inline_comment", None)
    if original is None:
        original = getattr(base, "build_inline_comment", None)
        base._dcoir_required_v8_original_build_inline_comment = original
    if not callable(original):
        return

    def required_v8_build_inline_comment(finding: dict[str, Any], model_used: str, config: Any) -> str:
        item = dict(finding)
        replacement = _native_suggestion_replacement(item, base)
        if replacement and not str(item.get("suggested_replacement", "") or "").strip():
            item["suggested_replacement"] = replacement
            guidance = dict(item.get("fix_guidance") or {})
            guidance["remove"] = ""
            guidance["replace"] = ""
            item["fix_guidance"] = guidance
        return original(item, model_used, config)

    base.build_inline_comment = required_v8_build_inline_comment


def _py_here_doc(path: str, body: str) -> str:
    return "\n".join(["python3 - <<'PY'", "from pathlib import Path", "import re", f"path = Path({path!r})", "text = path.read_text(encoding='utf-8')", body, "PY"])


def _validation_for_kind(kind: str, path: str) -> str:
    quoted = shlex.quote(path)
    if kind == v4.YAML_PULL_REQUEST_TARGET:
        return _py_here_doc(path, "assert 'pull_request_target' not in text")
    if kind == v4.YAML_BROAD_WRITE:
        return _py_here_doc(path, "assert 'write-all' not in text\nassert not re.search(r'(?m)^\\s*(actions|checks|contents|deployments|id-token|issues|packages|pull-requests|statuses)\\s*:\\s*write\\b', text)")
    if kind == v4.YAML_UNTRUSTED_CHECKOUT:
        return _py_here_doc(path, "assert 'github.event.pull_request.head' not in text\nassert 'github.head_ref' not in text")
    if kind == v4.YAML_SHELL_PIPE:
        return _py_here_doc(path, "assert not re.search(r'\\b(curl|wget)\\b[^\\n]*\\|\\s*(bash|sh)\\b', text, re.I)")
    if kind == v4.YAML_METADATA_SHELL:
        return _py_here_doc(path, "metadata = re.search(r'github\\.event\\.pull_request\\.(body|title|head\\.ref|head\\.sha)', text, re.I)\nshell = re.search(r'(\\|\\s*(bash|sh)\\b|\\b(bash|sh)\\s+-c\\b)', text, re.I)\nassert not (metadata and shell)")
    if kind == v4.PS_ACL:
        return f"pwsh -NoProfile -Command '$p = {path!r}; $text = Get-Content -Raw -LiteralPath $p; if ($text -match \"(?i)icacls.*Everyone:F|Everyone.*FullControl|FileSystemAccessRule.*Everyone|Set-Acl\") {{ throw \"broad ACL grant remains\" }}; $errors=$null; [System.Management.Automation.PSParser]::Tokenize($text, [ref]$errors) | Out-Null; if ($errors) {{ throw ($errors | Out-String) }}'"
    if kind == v4.PS_PROCESS_LAUNCH:
        return f"pwsh -NoProfile -Command '$p = {path!r}; $text = Get-Content -Raw -LiteralPath $p; if ($text -match \"(?i)Start-Process\\s+-FilePath\\s+\\$RequestedTool\") {{ throw \"caller-controlled Start-Process remains\" }}; $errors=$null; [System.Management.Automation.PSParser]::Tokenize($text, [ref]$errors) | Out-Null; if ($errors) {{ throw ($errors | Out-String) }}'"
    if kind == v5.PS_ENV_TOKEN:
        return f"pwsh -NoProfile -Command '$p = {path!r}; $text = Get-Content -Raw -LiteralPath $p; if ($text -match \"(?i)Bearer\\s+\\$env:DCOIR_TOKEN|Authorization.*DCOIR_TOKEN\") {{ throw \"environment token callback header remains\" }}; $errors=$null; [System.Management.Automation.PSParser]::Tokenize($text, [ref]$errors) | Out-Null; if ($errors) {{ throw ($errors | Out-String) }}'"
    if kind == v5.PYTHON_YAML_LOAD:
        return f"python3 -m py_compile {quoted}\n" + _py_here_doc(path, "assert 'yaml.Loader' not in text\nassert 'Loader=yaml.Loader' not in text")
    if kind == v5.PYTHON_SHELL_EXEC:
        return f"python3 -m py_compile {quoted}\n" + _py_here_doc(path, "assert 'shell=True' not in text")
    if kind == v5.PYTHON_ENV_TOKEN:
        return f"python3 -m py_compile {quoted}\n" + _py_here_doc(path, "assert not re.search(r'Authorization.*Bearer.*DCOIR_TOKEN|Bearer\\s*\\{?token\\}?', text)")
    if kind == "python_pickle_load":
        return f"python3 -m py_compile {quoted}\n" + _py_here_doc(path, "assert 'pickle.loads' not in text\nassert 'pickle.load(' not in text")
    return ""


def _kind_for_validation(finding: dict[str, Any]) -> str:
    explicit = str(finding.get("_risk_sentinel_kind", "") or "")
    if explicit:
        return explicit
    text = _finding_text(finding)
    if "pickle" in text:
        return "python_pickle_load"
    return v5._semantic_kind(finding)


def _patch_validation_text(base: Any) -> None:
    original = getattr(base, "_dcoir_required_v8_original_validation_text_for_finding", None)
    if original is None:
        original = getattr(base, "validation_text_for_finding", None)
        base._dcoir_required_v8_original_validation_text_for_finding = original
    if not callable(original):
        return

    def required_v8_validation_text_for_finding(finding: dict[str, Any]) -> str:
        path = str(finding.get("path", "") or "")
        validation = _validation_for_kind(_kind_for_validation(finding), path)
        return validation or original(finding)

    base.validation_text_for_finding = required_v8_validation_text_for_finding


def _patch_progress_body(base: Any) -> None:
    original = getattr(base.ProgressReporter, "_dcoir_required_v8_original_body", None)
    if original is None:
        original = getattr(base.ProgressReporter, "_body", None)
        base.ProgressReporter._dcoir_required_v8_original_body = original
    if not callable(original):
        return

    def required_v8_body(self: Any, state: str, final_lines: list[str] | None = None) -> str:
        lines = [
            base.MARKER,
            f"{base.REVIEW_DISPLAY_NAME} {state}.",
            "",
            f"- Command: `{self.command}`.",
            f"- Debug progress: `{str(getattr(self.config, 'debug', False)).lower()}`.",
            *base.workflow_run_status_lines(self.config),
            "- Branch changes: none; this workflow only posts review output.",
            "- Gate role: internal review-assist signal before any separately approved external review request.",
        ]
        if final_lines:
            lines.extend(["", *final_lines])
        lines.extend(["", "Progress:"])
        for stage, message in self.steps[-30:]:
            lines.append(f"- `{base.sanitize_public_identity(stage)}`: {message}")
        return base.github_safe_body("\n".join(lines), limit=18000)

    base.ProgressReporter._body = required_v8_body


def _patch_prompt_review_budget() -> None:
    original = getattr(v6, "_dcoir_required_v8_original_candidate_with_addendum", None)
    if original is None:
        original = getattr(v6, "_candidate_with_addendum", None)
        v6._dcoir_required_v8_original_candidate_with_addendum = original
    if not callable(original):
        return

    def required_v8_candidate_with_addendum(original_prompt: str, addendum: str, config: Any) -> str:
        if "review quality retry" in str(original_prompt or "").lower() and str(addendum or "").strip():
            cleaned = v6._clean_addendum(addendum)
            if not cleaned:
                return original_prompt
            return f"{original_prompt}\n\n{v6.PROMPT_REVIEW_SECTION_TITLE}:\n{cleaned}"
        return original(original_prompt, addendum, config)

    v6._candidate_with_addendum = required_v8_candidate_with_addendum


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    if base is not None:
        _patch_inline_comment_renderer(base)
        _patch_validation_text(base)
        _patch_progress_body(base)
    _patch_prompt_review_budget()
    if hardened is not None:
        _patch_required_selection(module, hardened)
