"""Second required-coverage layer for DCOIR Review.

This module runs after the runtime, strict, and required patch layers. It keeps
connector-sized changes small while fixing live-test regressions around required
PowerShell ACL coverage, token wording, YAML validation formatting, and final
comment renderer ordering.
"""

from __future__ import annotations

import ast
import re
import shlex
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patches as required

PS_ACL_KIND = "ps_acl"
HARD_REQUIRED_KIND_TITLES = {
    **required.YAML_REQUIRED_KIND_TITLES,
    PS_ACL_KIND: "PowerShell broad ACL grant exposes collector output",
}
HARD_REQUIRED_KIND_ORDER = (
    "yaml_pull_request_target",
    "yaml_broad_write",
    "yaml_untrusted_checkout",
    "yaml_shell_pipe",
    PS_ACL_KIND,
)
REQUIRED_KIND_ORDER = (
    *HARD_REQUIRED_KIND_ORDER,
    "python_shell_exec",
    "python_dynamic_exec",
    "python_pickle",
    "python_yaml_load",
    "python_archive_extract",
    "python_ssrf",
    "ps_dynamic_exec",
    "ps_archive_extract",
    "ps_process_launch",
    "ps_outbound_token",
)
PS_ACL_SENTINEL_LABEL = "DCOIR PowerShell broad ACL grant"
PS_ACL_SENTINEL_DETAIL = "broad ACL grants such as Everyone or FullControl expose collector output and execution surfaces"
ENV_TOKEN_RE = re.compile(r"(?:os\.environ|os\.getenv|\$env:|process\.env|Environment::GetEnvironmentVariable|DCOIR_TOKEN)", re.IGNORECASE)
TOKEN_FORWARDING_RE = re.compile(r"(?:Authorization|Bearer|callback|Invoke-RestMethod|Invoke-WebRequest|requests\.(?:get|post|put|request)|urlopen)", re.IGNORECASE)
BRACKETED_REDACTION_RE = re.compile(r"\[redacted[-_ ]?(?:secret|token|credential|api key)?\]", re.IGNORECASE)
HARDCODED_TOKEN_RE = re.compile(
    r"\b(?:hard[- ]?coded|literal|redacted)\s+(?:bearer\s+)?(?:secret-like\s+)?(?:secret|token|credential|api key|value)\b",
    re.IGNORECASE,
)
HARDCODED_BEARER_RE = re.compile(r"\bhard[- ]?coded\s+bearer\s+token\b", re.IGNORECASE)
LITERAL_BEARER_VALUE_RE = re.compile(r"\bliteral\s+bearer\s+token\s+value\b", re.IGNORECASE)
NATURAL_LANGUAGE_START_RE = re.compile(
    r"^\s*(?:the\s+entire|if\s+|when\s+|because\s+|replace\s+|remove\s+|delete\s+|add\s+|ensure\s+|use\s+|using\s+|no\s+replacement|a\s+complete|repair\s+steps|fix\s+)",
    re.IGNORECASE,
)
NATURAL_LANGUAGE_WORD_RE = re.compile(
    r"\b(?:the|this|that|with|without|because|function|entire|required|governed|parser|allowlist|validates|before|after|safe|unsafe|must|should|would|could|repair|line|lines)\b",
    re.IGNORECASE,
)
POWERSHELL_CODE_RE = re.compile(
    r"^\s*(?:#|param\s*\(|function\s+[A-Za-z_][A-Za-z0-9_-]*\b|\$[A-Za-z_][A-Za-z0-9_]*\b|[A-Za-z]+-[A-Za-z]+(?:\s|$)|(?:if|foreach|for|while|try|catch|finally)\s*(?:\(|\{))",
    re.IGNORECASE,
)
YAML_CODE_RE = re.compile(r"(?m)^\s*(?:[-?]\s+)?[A-Za-z0-9_.${}/ -]+\s*:")
JS_TS_CODE_RE = re.compile(r"^\s*(?:const|let|var|return|if|for|while|throw|await|import|export|[A-Za-z_][A-Za-z0-9_]*\s*(?:=|=>|\())\b")


def _normalize(value: Any) -> str:
    return required._normalize(value)


def _line_kind(path: str, text: str) -> str:
    return required._line_semantic_kind(path, text)


def _semantic_kind(finding: dict[str, Any]) -> str:
    return required._semantic_kind(finding)


def _sentinel_kind(sentinel: Any) -> str:
    return required._sentinel_kind(sentinel)


def _sentinel_line(sentinel: Any) -> int:
    try:
        return int(getattr(sentinel, "line", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _finding_line(finding: dict[str, Any]) -> int:
    try:
        return int(finding.get("line", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _dedupe_sentinel_key(sentinel: Any) -> tuple[str, int, str]:
    path = str(getattr(sentinel, "path", "") or "")
    kind = _sentinel_kind(sentinel) or str(getattr(sentinel, "label", "") or "")
    line = 0 if kind == PS_ACL_KIND else _sentinel_line(sentinel)
    return path, line, kind


def _dedupe_sentinels(sentinels: list[Any]) -> list[Any]:
    deduped: list[Any] = []
    seen: set[tuple[str, int, str]] = set()
    for sentinel in sentinels:
        key = _dedupe_sentinel_key(sentinel)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sentinel)
    return deduped


def _make_ps_acl_sentinels(hardened: Any, diff: str) -> list[Any]:
    iter_added = getattr(hardened, "iter_added_diff_lines", None)
    risk_sentinel_type = getattr(hardened, "RiskSentinel", None)
    if not callable(iter_added) or risk_sentinel_type is None:
        return []
    sentinels: list[Any] = []
    for changed_line in iter_added(diff):
        path = str(getattr(changed_line, "path", "") or "")
        text = str(getattr(changed_line, "text", "") or "")
        if Path(path.lower()).suffix not in {".ps1", ".psm1", ".psd1"}:
            continue
        if callable(getattr(hardened, "is_comment_only_added_line", None)) and hardened.is_comment_only_added_line(path, text):
            continue
        if _line_kind(path, text) != PS_ACL_KIND:
            continue
        line = _sentinel_line(changed_line)
        if line <= 0:
            continue
        sentinels.append(
            risk_sentinel_type(
                path=path,
                line=line,
                label=PS_ACL_SENTINEL_LABEL,
                detail=PS_ACL_SENTINEL_DETAIL,
                text=text,
            )
        )
    return _dedupe_sentinels(sentinels)


def _select_sentinels(hardened: Any, sentinels: list[Any], max_anchors: int | None) -> list[Any]:
    deduped = _dedupe_sentinels(sentinels)
    if max_anchors is None or len(deduped) <= max_anchors:
        return deduped
    if max_anchors <= 0:
        return []
    selected: list[Any] = []
    seen: set[tuple[str, int, str]] = set()

    def add(sentinel: Any) -> None:
        key = _dedupe_sentinel_key(sentinel)
        if key not in seen and len(selected) < max_anchors:
            seen.add(key)
            selected.append(sentinel)

    for kind in HARD_REQUIRED_KIND_ORDER:
        for sentinel in deduped:
            if _sentinel_kind(sentinel) == kind:
                add(sentinel)
                break
    remaining = [sentinel for sentinel in deduped if _dedupe_sentinel_key(sentinel) not in seen]
    original_select = getattr(hardened, "_dcoir_required_v2_original_select_risk_sentinels", None)
    if not callable(original_select):
        original_select = getattr(hardened, "_dcoir_required_original_select_risk_sentinels", None)
    if not callable(original_select):
        original_select = getattr(hardened, "select_risk_sentinels", None)
    if callable(original_select):
        try:
            remaining = original_select(remaining, max_anchors - len(selected))
        except TypeError:
            remaining = original_select(remaining)
    for sentinel in remaining:
        add(sentinel)
    return selected


def _validation_for_path(path: str, kind: str = "") -> str:
    lower_path = path.lower()
    if lower_path.endswith((".yml", ".yaml")):
        checks = ["assert path.exists(), path"]
        if kind == "yaml_pull_request_target":
            checks.append("assert 'pull_request_target' not in text")
        elif kind == "yaml_broad_write":
            checks.append("assert 'write-all' not in text and ': write' not in text")
        elif kind == "yaml_untrusted_checkout":
            checks.append("assert 'github.event.pull_request.head' not in text and 'github.head_ref' not in text")
        elif kind == "yaml_shell_pipe":
            checks.append("assert '| bash' not in text and '| sh' not in text")
        else:
            checks.append("assert text.strip()")
        script = f"from pathlib import Path; path=Path({path!r}); text=path.read_text(encoding='utf-8'); " + "; ".join(checks)
        return f"python3 -c {shlex.quote(script)}"
    return required._validation_for_path(path, kind)


def _validation_needs_replacement(validation: str, path: str, kind: str) -> bool:
    if not str(validation or "").strip():
        return True
    if path.lower().endswith((".yml", ".yaml")) and ("<<'PY'" in validation or "\n" in validation):
        return True
    return required._validation_needs_replacement(validation, path)


def _token_forwarding_context(finding: dict[str, Any]) -> bool:
    haystack = "\n".join(
        str(value or "")
        for value in (
            finding.get("title"),
            finding.get("body"),
            finding.get("validation"),
            finding.get("_anchored_line_text"),
        )
    )
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    haystack += "\n" + "\n".join(str(guidance.get(key, "") or "") for key in ("remove", "replace", "add", "notes"))
    kind = _semantic_kind(finding)
    return (kind in {"python_ssrf", "ps_outbound_token"} and TOKEN_FORWARDING_RE.search(haystack) is not None) or (
        ENV_TOKEN_RE.search(haystack) is not None and TOKEN_FORWARDING_RE.search(haystack) is not None
    )


def _normalize_token_text(value: Any) -> str:
    text = str(value or "")
    text = text.replace("shorn", "should")
    text = BRACKETED_REDACTION_RE.sub("environment token value", text)
    text = HARDCODED_BEARER_RE.sub("environment token", text)
    text = LITERAL_BEARER_VALUE_RE.sub("environment Bearer token value", text)
    text = HARDCODED_TOKEN_RE.sub("environment token value", text)
    text = re.sub(r"\bliteral\s+Bearer\s+token\b", "environment Bearer token", text, flags=re.IGNORECASE)
    lines = [line for line in text.splitlines() if "syntax error" not in line.lower()]
    return "\n".join(lines).strip()


def _language_hint(path: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    return {
        ".cjs": "javascript",
        ".js": "javascript",
        ".mjs": "javascript",
        ".ps1": "powershell",
        ".psd1": "powershell",
        ".psm1": "powershell",
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix, "text")


def _strip_fences(value: Any) -> str:
    lines = []
    for line in str(value or "").splitlines():
        if line.strip().startswith(("```", "~~~")):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def _is_natural_language(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    first = next((line.strip() for line in stripped.splitlines() if line.strip()), "")
    if NATURAL_LANGUAGE_START_RE.match(first):
        return True
    return len(first.split()) >= 5 and bool(NATURAL_LANGUAGE_WORD_RE.search(first))


def _python_is_code(value: str) -> bool:
    try:
        ast.parse(value.strip() + "\n")
        return True
    except SyntaxError:
        return False


def _looks_like_code(value: str, language: str) -> bool:
    text = _strip_fences(value)
    if not text or _is_natural_language(text):
        return False
    language = str(language or "").lower()
    if language == "python":
        return _python_is_code(text)
    if language == "powershell":
        lines = [line for line in text.splitlines() if line.strip()]
        return bool(lines) and all(POWERSHELL_CODE_RE.match(line) or line.strip() in {"}", "};"} for line in lines)
    if language in {"yaml", "json"}:
        return bool(YAML_CODE_RE.search(text))
    if language in {"typescript", "javascript"}:
        lines = [line for line in text.splitlines() if line.strip()]
        return bool(lines) and any(JS_TS_CODE_RE.match(line) for line in lines)
    return any(signal in text for signal in ("=", "$", ":", "(", "{", "|", ";"))


def _sanitize_fix_guidance(finding: dict[str, Any]) -> dict[str, Any]:
    raw = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    if not raw:
        return {}
    path = str(finding.get("path", "") or "")
    language = str(raw.get("language") or _language_hint(path)).lower()
    cleaned: dict[str, Any] = {"language": language}
    notes: list[str] = []
    for key in ("remove", "replace", "add"):
        value = _strip_fences(raw.get(key, ""))
        if not value:
            continue
        value = _normalize_token_text(value) if _token_forwarding_context(finding) else value.replace("shorn", "should")
        if _looks_like_code(value, language):
            cleaned[key] = value
        else:
            notes.append(value)
    raw_notes = str(raw.get("notes", "") or "").strip()
    if raw_notes:
        notes.append(raw_notes)
    if notes:
        normalized_notes: list[str] = []
        seen: set[str] = set()
        for note in notes:
            note = _normalize_token_text(note) if _token_forwarding_context(finding) else note.replace("shorn", "should")
            note = required._clean_public_text(note)
            key = _normalize(note)
            if note and key not in seen:
                seen.add(key)
                normalized_notes.append(note)
        if normalized_notes:
            cleaned["notes"] = "\n\n".join(normalized_notes)
    return cleaned if any(key in cleaned for key in ("remove", "replace", "add", "notes")) else {}


def _normalize_comment_finding(finding: dict[str, Any]) -> dict[str, Any]:
    item = required._normalize_comment_finding(finding)
    kind = _semantic_kind(item)
    if kind in HARD_REQUIRED_KIND_TITLES:
        item["title"] = HARD_REQUIRED_KIND_TITLES[kind]
    token_context = _token_forwarding_context(item)
    if token_context:
        if kind in {"python_ssrf", "ps_outbound_token"}:
            item["title"] = "Environment token forwarded to request-controlled callback"
        else:
            item["title"] = _normalize_token_text(item.get("title", ""))
        item["body"] = _normalize_token_text(item.get("body", ""))
    else:
        item["title"] = str(item.get("title", "") or "Finding").replace("shorn", "should")
        item["body"] = str(item.get("body", "") or "").replace("shorn", "should")
    path = str(item.get("path", "") or "")
    validation = str(item.get("validation", "") or "")
    if _validation_needs_replacement(validation, path, kind):
        validation = _validation_for_path(path, kind)
    item["validation"] = validation.replace("shorn", "should")
    guidance = _sanitize_fix_guidance(item)
    if guidance:
        item["fix_guidance"] = guidance
    else:
        item.pop("fix_guidance", None)
    return item


def _dedupe_line_key(kind: str, finding: dict[str, Any]) -> str:
    if kind in {"python_ssrf", PS_ACL_KIND}:
        return ""
    return str(finding.get("line", "") or "").strip()


def _dedupe_key(finding: dict[str, Any]) -> tuple[str, str, str, str]:
    kind = _semantic_kind(finding)
    path = str(finding.get("path", "") or "").strip()
    if kind:
        return path, _dedupe_line_key(kind, finding), kind, ""
    return required._dedupe_key(finding)


def _dedupe_findings(hardened: Any, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str, str]] = []
    for finding in findings:
        key = _dedupe_key(finding)
        if key not in by_key:
            by_key[key] = finding
            order.append(key)
            continue
        if required._finding_quality_score(hardened, finding) >= required._finding_quality_score(hardened, by_key[key]):
            by_key[key] = finding
    return [by_key[key] for key in order]


def _rank_findings(module: Any, hardened: Any, original_rank: Any, findings: list[dict[str, Any]], config: Any) -> list[dict[str, Any]]:
    max_inline = max(0, int(getattr(config, "max_inline_comments", 12)))
    ranked_source = _dedupe_findings(hardened, findings)
    severity_sort = getattr(hardened, "severity_sort_key", None)
    if callable(severity_sort):
        ranked_source = sorted(ranked_source, key=severity_sort)
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    def add(finding: dict[str, Any]) -> None:
        key = _dedupe_key(finding)
        if key not in seen and len(selected) < max_inline:
            seen.add(key)
            selected.append(finding)

    for kind in REQUIRED_KIND_ORDER:
        for finding in ranked_source:
            if _semantic_kind(finding) == kind:
                add(finding)
                break
    remainder = [finding for finding in ranked_source if _dedupe_key(finding) not in seen]
    if callable(original_rank):
        try:
            remainder = original_rank(remainder, config)
        except TypeError:
            remainder = original_rank(remainder)
    for finding in remainder:
        add(finding)
    return selected[:max_inline]


def _finding_covers_sentinel(finding: dict[str, Any], sentinel: Any) -> bool:
    kind = _sentinel_kind(sentinel)
    if kind in required.YAML_REQUIRED_KIND_TITLES:
        return required._finding_covers_sentinel(finding, sentinel)
    if kind == PS_ACL_KIND:
        if str(finding.get("path", "") or "") != str(getattr(sentinel, "path", "") or ""):
            return False
        if _semantic_kind(finding) != PS_ACL_KIND:
            return False
        finding_line = _finding_line(finding)
        sentinel_line = _sentinel_line(sentinel)
        if finding_line <= 0 or sentinel_line <= 0:
            return False
        return abs(finding_line - sentinel_line) <= 4
    return False


def _required_sentinels(original_required: Any, sentinels: list[Any]) -> list[Any]:
    original_items = original_required(sentinels) if callable(original_required) else []
    combined = [*original_items, *(sentinel for sentinel in sentinels if _sentinel_kind(sentinel) in HARD_REQUIRED_KIND_TITLES)]
    return _dedupe_sentinels(combined)


def _ps_acl_fallback_body(sentinel: Any) -> str:
    changed = str(getattr(sentinel, "text", "") or "").strip()
    detail = f" The changed line is `{changed}`." if changed else ""
    return "This PowerShell change grants broad filesystem ACL rights. Narrow the identity and rights to the minimum collector path access required, and avoid Everyone or FullControl grants." + detail


def _risk_sentinel_fallback_finding(hardened: Any, original_fallback: Any, sentinel: Any, config: Any) -> dict[str, Any]:
    kind = _sentinel_kind(sentinel)
    if kind == PS_ACL_KIND:
        path = str(getattr(sentinel, "path", "") or "")
        return {
            "title": HARD_REQUIRED_KIND_TITLES[kind],
            "severity": "high",
            "confidence": 0.99,
            "path": path,
            "line": _sentinel_line(sentinel),
            "body": _ps_acl_fallback_body(sentinel),
            "suggested_replacement": "",
            "validation": _validation_for_path(path, kind),
            "_anchored_line_text": str(getattr(sentinel, "text", "") or ""),
        }
    if kind in required.YAML_REQUIRED_KIND_TITLES:
        return required._risk_sentinel_fallback_finding(hardened, original_fallback, sentinel, config)
    return original_fallback(sentinel, config) if callable(original_fallback) else {}


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    if hardened is None:
        return

    if not hasattr(hardened, "_dcoir_required_v2_original_select_risk_sentinels") and callable(getattr(hardened, "select_risk_sentinels", None)):
        hardened._dcoir_required_v2_original_select_risk_sentinels = hardened.select_risk_sentinels

    original_detect = getattr(module, "_dcoir_required_v2_original_detect_risk_sentinels", None)
    if original_detect is None:
        original_detect = getattr(module, "detect_risk_sentinels", getattr(hardened, "detect_risk_sentinels", None))
        module._dcoir_required_v2_original_detect_risk_sentinels = original_detect
    if callable(original_detect):
        def required_v2_detect_risk_sentinels(diff: str, max_anchors: int | None = None) -> list[Any]:
            existing = original_detect(diff, None)
            ps_acl = _make_ps_acl_sentinels(hardened, diff)
            return _select_sentinels(hardened, [*existing, *ps_acl], max_anchors)

        module.detect_risk_sentinels = required_v2_detect_risk_sentinels
        hardened.detect_risk_sentinels = required_v2_detect_risk_sentinels
        hardened.select_risk_sentinels = lambda sentinels, max_anchors=None: _select_sentinels(hardened, sentinels, max_anchors)

    original_required = getattr(hardened, "_dcoir_required_v2_original_required_risk_sentinels", None)
    if original_required is None:
        original_required = getattr(hardened, "required_risk_sentinels", None)
        hardened._dcoir_required_v2_original_required_risk_sentinels = original_required
    hardened.required_risk_sentinels = lambda sentinels: _required_sentinels(original_required, sentinels)

    original_is_required = getattr(hardened, "_dcoir_required_v2_original_is_required_risk_sentinel", None)
    if original_is_required is None:
        original_is_required = getattr(hardened, "is_required_risk_sentinel", None)
        hardened._dcoir_required_v2_original_is_required_risk_sentinel = original_is_required

    def required_v2_is_required_risk_sentinel(sentinel: Any) -> bool:
        if _sentinel_kind(sentinel) in HARD_REQUIRED_KIND_TITLES:
            return True
        return bool(original_is_required(sentinel)) if callable(original_is_required) else False

    hardened.is_required_risk_sentinel = required_v2_is_required_risk_sentinel

    original_covers = getattr(hardened, "_dcoir_required_v2_original_finding_covers_risk_sentinel", None)
    if original_covers is None:
        original_covers = getattr(hardened, "finding_covers_risk_sentinel", None)
        hardened._dcoir_required_v2_original_finding_covers_risk_sentinel = original_covers

    def required_v2_finding_covers_risk_sentinel(finding: dict[str, Any], sentinel: Any) -> bool:
        if _sentinel_kind(sentinel) in HARD_REQUIRED_KIND_TITLES:
            return _finding_covers_sentinel(finding, sentinel)
        return bool(original_covers(finding, sentinel)) if callable(original_covers) else False

    hardened.finding_covers_risk_sentinel = required_v2_finding_covers_risk_sentinel

    original_fallback = getattr(hardened, "_dcoir_required_v2_original_risk_sentinel_fallback_finding", None)
    if original_fallback is None:
        original_fallback = getattr(hardened, "risk_sentinel_fallback_finding", None)
        hardened._dcoir_required_v2_original_risk_sentinel_fallback_finding = original_fallback
    hardened.risk_sentinel_fallback_finding = lambda sentinel, config: _risk_sentinel_fallback_finding(hardened, original_fallback, sentinel, config)

    original_add = getattr(hardened, "_dcoir_required_v2_original_add_risk_sentinel_fallback_findings", None)
    if original_add is None:
        original_add = getattr(hardened, "add_risk_sentinel_fallback_findings", None)
        hardened._dcoir_required_v2_original_add_risk_sentinel_fallback_findings = original_add

    def required_v2_add_risk_sentinel_fallback_findings(
        findings: list[dict[str, Any]],
        risk_sentinels: list[Any],
        config: Any,
        unanchored_findings: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        required_sentinels = hardened.required_risk_sentinels(risk_sentinels)
        coverage_pool = [*findings, *(unanchored_findings or [])]
        uncovered = [
            sentinel
            for sentinel in required_sentinels
            if not any(hardened.finding_covers_risk_sentinel(finding, sentinel) for finding in coverage_pool)
        ]
        inline_limit = max(0, int(getattr(config, "max_inline_comments", 12)))
        fallback_findings = [hardened.risk_sentinel_fallback_finding(sentinel, config) for sentinel in uncovered[:inline_limit]]
        fallback_findings = [finding for finding in fallback_findings if finding]
        existing_budget = max(0, inline_limit - len(fallback_findings))
        existing = _rank_findings(module, hardened, getattr(module, "_dcoir_required_v2_original_rank_findings_for_required_budget", None), findings, config)[:existing_budget]
        return _rank_findings(module, hardened, None, [*existing, *fallback_findings], config)

    hardened.add_risk_sentinel_fallback_findings = required_v2_add_risk_sentinel_fallback_findings

    review_quality_error = getattr(hardened, "ReviewQualityError", RuntimeError)

    def required_v2_enforce_risk_sentinel_findings(
        findings: list[dict[str, Any]],
        risk_sentinels: list[Any],
        config: Any,
        unanchored_findings: list[dict[str, Any]] | None = None,
    ) -> None:
        findings[:] = required_v2_add_risk_sentinel_fallback_findings(findings, risk_sentinels, config, unanchored_findings)
        uncovered = [
            sentinel
            for sentinel in hardened.required_risk_sentinels(risk_sentinels)
            if not any(hardened.finding_covers_risk_sentinel(finding, sentinel) for finding in findings)
        ]
        if uncovered:
            digest = getattr(hardened, "risk_sentinel_coverage_digest", lambda items: "; ".join(str(item) for item in items))(uncovered)
            raise review_quality_error(f"DCOIR Review quality failure: required changed-line signals remain uncovered: {digest}.")

    hardened.enforce_risk_sentinel_findings = required_v2_enforce_risk_sentinel_findings

    original_merge_key = getattr(hardened, "_dcoir_required_v2_original_finding_merge_key", None)
    if original_merge_key is None:
        original_merge_key = getattr(hardened, "finding_merge_key", None)
        hardened._dcoir_required_v2_original_finding_merge_key = original_merge_key

    def required_v2_finding_merge_key(finding: dict[str, Any]) -> tuple[str, int, str]:
        kind = _semantic_kind(finding)
        if kind:
            line = 0 if kind in {"python_ssrf", PS_ACL_KIND} else _finding_line(finding)
            return str(finding.get("path", "") or ""), line, kind
        return original_merge_key(finding) if callable(original_merge_key) else (str(finding.get("path", "") or ""), _finding_line(finding), "unknown")

    hardened.finding_merge_key = required_v2_finding_merge_key
    module.finding_dedupe_key = _dedupe_key
    module.dedupe_findings_for_ranking = lambda findings: _dedupe_findings(hardened, findings)

    original_rank = getattr(module, "_dcoir_required_v2_original_rank_findings_for_required_budget", None)
    if original_rank is None:
        original_rank = getattr(module, "rank_findings_for_required_budget", None)
        module._dcoir_required_v2_original_rank_findings_for_required_budget = original_rank
    module.rank_findings_for_required_budget = lambda findings, config: _rank_findings(module, hardened, original_rank, findings, config)

    original_score = getattr(module, "_dcoir_required_v2_original_anchor_candidate_score", None)
    if original_score is None:
        original_score = getattr(module, "anchor_candidate_score", None)
        module._dcoir_required_v2_original_anchor_candidate_score = original_score
    if callable(original_score):
        def required_v2_anchor_candidate_score(finding: dict[str, Any], candidate: Any, original_line: int, terms: list[str], risk_sentinels: list[Any]) -> int:
            score = int(original_score(finding, candidate, original_line, terms, risk_sentinels))
            finding_kind = _semantic_kind(finding)
            candidate_kind = _line_kind(str(getattr(candidate, "path", "") or ""), str(getattr(candidate, "text", "") or ""))
            candidate_text = _normalize(getattr(candidate, "text", ""))
            if finding_kind == PS_ACL_KIND:
                if candidate_kind == PS_ACL_KIND:
                    score += 320
                elif candidate_kind == "ps_outbound_token":
                    score -= 240
            if finding_kind in {"python_ssrf", "ps_outbound_token"} and ENV_TOKEN_RE.search(candidate_text):
                score += 220
            return score

        module.anchor_candidate_score = required_v2_anchor_candidate_score

    original_synthesize = getattr(module, "_dcoir_required_v2_original_synthesize_fix_for_finding", None)
    if original_synthesize is None:
        original_synthesize = getattr(module, "synthesize_fix_for_finding", None)
        module._dcoir_required_v2_original_synthesize_fix_for_finding = original_synthesize
    if callable(original_synthesize):
        def required_v2_synthesize_fix_for_finding(index: int, finding: dict[str, Any], file_text: str, schema: dict[str, Any], config: Any) -> dict[str, Any]:
            enriched = original_synthesize(index, finding, file_text, schema, config)
            return _normalize_comment_finding(enriched)

        module.synthesize_fix_for_finding = required_v2_synthesize_fix_for_finding

    if base is not None and callable(getattr(base, "build_inline_comment", None)):
        original_build = getattr(base, "_dcoir_required_v2_original_build_inline_comment", None)
        if original_build is None:
            original_build = getattr(base, "_dcoir_strict_original_build_inline_comment", None)
            if original_build is None:
                original_build = getattr(base, "_dcoir_original_build_inline_comment", None)
            if original_build is None:
                original_build = base.build_inline_comment
            base._dcoir_required_v2_original_build_inline_comment = original_build

        def required_v2_build_inline_comment(finding: dict[str, Any], model_used: str, config: Any) -> str:
            return original_build(_normalize_comment_finding(finding), model_used, config)

        base.build_inline_comment = required_v2_build_inline_comment
