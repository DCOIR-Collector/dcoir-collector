"""Third required-coverage layer for DCOIR Review.

This layer keeps the previous connector-sized patches intact and fixes the next
set of live-test regressions: required Start-Process coverage, final token-wording
scrubbing, prose validation rejection, PR-metadata shell anchoring, whole-file
fallback guidance, and Python replacement indentation.
"""

from __future__ import annotations

import ast
import re
import shlex
import textwrap
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v2 as v2

_strip_fences = v2._strip_fences
import dcoir_review_required_runtime_patches as required

PS_PROCESS_KIND = "ps_process_launch"
YAML_METADATA_SHELL_KIND = "yaml_metadata_shell"
HARD_REQUIRED_KIND_TITLES = {
    **v2.HARD_REQUIRED_KIND_TITLES,
    PS_PROCESS_KIND: "PowerShell caller-controlled process launch",
}
OPTIONAL_KIND_TITLES = {
    YAML_METADATA_SHELL_KIND: "Workflow executes pull request metadata in a shell",
}
HARD_REQUIRED_KIND_ORDER = (
    "yaml_pull_request_target",
    "yaml_broad_write",
    "yaml_untrusted_checkout",
    "yaml_shell_pipe",
    v2.PS_ACL_KIND,
    PS_PROCESS_KIND,
)
RANK_KIND_ORDER = (
    *HARD_REQUIRED_KIND_ORDER,
    "python_shell_exec",
    "python_dynamic_exec",
    "python_pickle",
    "python_yaml_load",
    "python_archive_extract",
    "python_ssrf",
    "ps_dynamic_exec",
    "ps_archive_extract",
    "ps_outbound_token",
    YAML_METADATA_SHELL_KIND,
)
PS_PROCESS_LABEL = "DCOIR PowerShell process launch"
PS_PROCESS_DETAIL = "caller-controlled Start-Process execution must be allowlisted or removed"
YAML_METADATA_LABEL = "DCOIR YAML pull request metadata shell execution"
YAML_METADATA_DETAIL = "pull request metadata is piped or passed into a shell command"
PR_METADATA_SHELL_RE = re.compile(
    r"github\.event\.pull_request\.(?:body|title|head\.ref|head\.sha)[^\n]*(?:\|\s*(?:bash|sh)\b|\bbash\b|\bsh\b)",
    re.IGNORECASE,
)
PS_START_PROCESS_RE = re.compile(r"\bStart-Process\b", re.IGNORECASE)
ENV_TOKEN_RE = re.compile(r"(?:os\.environ|os\.getenv|\$env:|process\.env|Environment::GetEnvironmentVariable|DCOIR_TOKEN)", re.IGNORECASE)
TOKEN_CONTEXT_RE = re.compile(r"(?:Authorization|Bearer|callback|Invoke-RestMethod|Invoke-WebRequest|requests\.(?:get|post|put|request)|urlopen)", re.IGNORECASE)
REDACTED_RE = re.compile(r"\[redacted[-_ ]?(?:secret|token|credential|api key)?\]", re.IGNORECASE)
PROSE_VALIDATION_RE = re.compile(r"\b(?:scan for|without validatation|without validation|after correction|manually verify|guidance|expected after fix)\b", re.IGNORECASE)
COMMAND_START_RE = re.compile(r"^\s*(?:python3?|pytest|bandit|pwsh|powershell|grep|rg|yamllint|npm|npx|node|bash|sh)\b")


def _normalize(value: Any) -> str:
    return required._normalize(value)


def _line_kind(path: str, text: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    if suffix in {".ps1", ".psm1", ".psd1"} and PS_START_PROCESS_RE.search(str(text or "")):
        return PS_PROCESS_KIND
    if suffix in {".yml", ".yaml"} and PR_METADATA_SHELL_RE.search(str(text or "")):
        return YAML_METADATA_SHELL_KIND
    return v2._line_kind(path, text)


def _semantic_kind(finding: dict[str, Any]) -> str:
    path = str(finding.get("path", "") or "")
    anchored = str(finding.get("_anchored_line_text", "") or "")
    anchored_kind = _line_kind(path, anchored)
    if anchored_kind:
        return anchored_kind
    text = _normalize("\n".join(str(finding.get(key, "") or "") for key in ("title", "body", "validation")))
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    text += "\n" + _normalize("\n".join(str(guidance.get(key, "") or "") for key in ("remove", "replace", "add", "notes")))
    if Path(path.lower()).suffix in {".yml", ".yaml"}:
        if PR_METADATA_SHELL_RE.search(text) or ("pull_request.body" in text and "bash" in text) or ("pull request body" in text and "bash" in text):
            return YAML_METADATA_SHELL_KIND
    return v2._semantic_kind(finding)


def _sentinel_kind(sentinel: Any) -> str:
    path = str(getattr(sentinel, "path", "") or "")
    text = str(getattr(sentinel, "text", "") or "")
    line_kind = _line_kind(path, text)
    if line_kind:
        return line_kind
    combined = _normalize("\n".join(str(getattr(sentinel, key, "") or "") for key in ("label", "detail")))
    if "process launch" in combined or "start-process" in combined:
        return PS_PROCESS_KIND
    if "metadata" in combined and "shell" in combined:
        return YAML_METADATA_SHELL_KIND
    return v2._sentinel_kind(sentinel)


def _finding_line(finding: dict[str, Any]) -> int:
    try:
        return int(finding.get("line", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _sentinel_line(sentinel: Any) -> int:
    try:
        return int(getattr(sentinel, "line", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _sentinel_key(sentinel: Any) -> tuple[str, int, str]:
    kind = _sentinel_kind(sentinel) or str(getattr(sentinel, "label", "") or "")
    line = 0 if kind == v2.PS_ACL_KIND else _sentinel_line(sentinel)
    return str(getattr(sentinel, "path", "") or ""), line, kind


def _dedupe_sentinels(sentinels: list[Any]) -> list[Any]:
    deduped: list[Any] = []
    seen: set[tuple[str, int, str]] = set()
    for sentinel in sentinels:
        key = _sentinel_key(sentinel)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sentinel)
    return deduped


def _make_v3_sentinels(hardened: Any, diff: str) -> list[Any]:
    iter_added = getattr(hardened, "iter_added_diff_lines", None)
    risk_sentinel_type = getattr(hardened, "RiskSentinel", None)
    if not callable(iter_added) or risk_sentinel_type is None:
        return []
    sentinels: list[Any] = []
    for changed_line in iter_added(diff):
        path = str(getattr(changed_line, "path", "") or "")
        text = str(getattr(changed_line, "text", "") or "")
        if callable(getattr(hardened, "is_comment_only_added_line", None)) and hardened.is_comment_only_added_line(path, text):
            continue
        kind = _line_kind(path, text)
        if kind == PS_PROCESS_KIND:
            sentinels.append(risk_sentinel_type(path=path, line=_sentinel_line(changed_line), label=PS_PROCESS_LABEL, detail=PS_PROCESS_DETAIL, text=text))
        elif kind == YAML_METADATA_SHELL_KIND:
            sentinels.append(risk_sentinel_type(path=path, line=_sentinel_line(changed_line), label=YAML_METADATA_LABEL, detail=YAML_METADATA_DETAIL, text=text))
    return _dedupe_sentinels(sentinels)


def _select_sentinels(hardened: Any, sentinels: list[Any], max_anchors: int | None) -> list[Any]:
    deduped = _dedupe_sentinels(sentinels)
    if max_anchors is None or len(deduped) <= max_anchors:
        return deduped
    selected: list[Any] = []
    seen: set[tuple[str, int, str]] = set()

    def add(sentinel: Any) -> None:
        key = _sentinel_key(sentinel)
        if key not in seen and len(selected) < max_anchors:
            seen.add(key)
            selected.append(sentinel)

    for kind in HARD_REQUIRED_KIND_ORDER:
        for sentinel in deduped:
            if _sentinel_kind(sentinel) == kind:
                add(sentinel)
                break
    remaining = [sentinel for sentinel in deduped if _sentinel_key(sentinel) not in seen]
    original_select = getattr(hardened, "_dcoir_required_v3_original_select_risk_sentinels", None)
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


def _token_context(finding: dict[str, Any]) -> bool:
    haystack = "\n".join(str(finding.get(key, "") or "") for key in ("title", "body", "validation", "_anchored_line_text"))
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    haystack += "\n" + "\n".join(str(guidance.get(key, "") or "") for key in ("remove", "replace", "add", "notes"))
    kind = _semantic_kind(finding)
    return kind in {"python_ssrf", "ps_outbound_token"} and (ENV_TOKEN_RE.search(haystack) is not None or TOKEN_CONTEXT_RE.search(haystack) is not None)


def _scrub_token_text(value: Any) -> str:
    text = str(value or "")
    text = REDACTED_RE.sub("environment token value", text)
    replacements = [
        (r"\bhard[- ]?coded\s+bearer\s+token\b", "environment token"),
        (r"\bliteral\s+bearer\s+token\s+value\b", "environment Bearer token value"),
        (r"\b(?:hard[- ]?coded|literal|redacted|inline)\s+(?:bearer\s+)?(?:secret-like\s+)?(?:secret|token|credential|api key|value)\b", "environment token value"),
        (r"\bthe\s+secret\s+is\s+hard[- ]?coded\b", "the environment token is forwarded"),
        (r"\bsecret\s+is\s+hard[- ]?coded\b", "environment token is forwarded"),
        (r"\bhard[- ]?coded\b", "environment-derived"),
        (r"\bliteral\b", "environment-derived"),
        (r"\binline\s+secret\b", "environment token"),
        (r"\bexposed\s+credential\b", "forwarded environment token"),
        (r"\bRotate any exposed credential\.?", "Validate token handling and do not forward environment tokens to untrusted endpoints."),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\ba environment\b", "an environment", text, flags=re.IGNORECASE)
    text = "\n".join(line for line in text.splitlines() if "syntax error" not in line.lower()).strip()
    return text


def _validation_for_path(path: str, kind: str = "") -> str:
    lower = path.lower()
    if lower.endswith((".ps1", ".psm1", ".psd1")):
        ps_path = "'" + path.replace("'", "''") + "'"
        return (
            "pwsh -NoProfile -Command \"$errors=$null; "
            f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath {ps_path}), [ref]$errors) | Out-Null; "
            "if ($errors) { throw ($errors | Out-String) }\""
        )
    if lower.endswith((".yml", ".yaml")) and kind == YAML_METADATA_SHELL_KIND:
        script = (
            "import re; from pathlib import Path; "
            f"path=Path({path!r}); text=path.read_text(encoding='utf-8'); "
            "assert not re.search(r'github\\.event\\.pull_request\\.(body|title|head\\.ref|head\\.sha).*\\|\\s*(bash|sh)', text)"
        )
        return f"python3 -c {shlex.quote(script)}"
    return v2._validation_for_path(path, kind)


def _clean_validation(value: Any, path: str, kind: str, token_context: bool) -> str:
    if token_context:
        return _validation_for_path(path, kind)
    lines: list[str] = []
    for raw_line in str(value or "").replace("```", "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if PROSE_VALIDATION_RE.search(line):
            continue
        if COMMAND_START_RE.match(line):
            lines.append(line)
    if not lines:
        return _validation_for_path(path, kind)
    return "\n".join(lines)


def _dedent_python_code(value: str, finding: dict[str, Any]) -> str:
    code = textwrap.dedent(str(value or "")).strip("\n")
    anchored = str(finding.get("_anchored_line_text", "") or "")
    base_indent = re.match(r"\s*", anchored).group(0) if anchored else ""
    if "\n" not in code:
        return code
    return "\n".join((base_indent + line if line.strip() else "") for line in code.splitlines())


def _python_code_is_valid_for_display(value: str) -> bool:
    try:
        ast.parse(textwrap.dedent(value).strip() + "\n")
        return True
    except SyntaxError:
        return False


def _sanitize_fix_guidance(finding: dict[str, Any]) -> dict[str, Any]:
    raw = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    if not raw:
        return {}
    path = str(finding.get("path", "") or "")
    language = str(raw.get("language") or v2._language_hint(path)).lower()
    token = _token_context(finding)
    cleaned: dict[str, Any] = {"language": language}
    notes: list[str] = []
    for key in ("remove", "replace", "add"):
        value = v2._strip_fences(raw.get(key, ""))
        if not value:
            continue
        if token:
            value = _scrub_token_text(value)
        if key == "remove" and len([line for line in value.splitlines() if line.strip()]) > 3:
            notes.append("Broad or whole-file removal guidance was moved out of the line-specific code block because it is not an exact line-range suggestion.")
            notes.append(value)
            continue
        if language == "python" and key in {"replace", "add"} and "\n" in value:
            value = _dedent_python_code(value, finding)
            if not _python_code_is_valid_for_display(value):
                notes.append(value)
                continue
        cleaned[key] = value
    raw_notes = str(raw.get("notes", "") or "").strip()
    if raw_notes:
        notes.append(raw_notes)
    if notes:
        seen: set[str] = set()
        normalized: list[str] = []
        for note in notes:
            note = _scrub_token_text(note) if token else note
            note = required._clean_public_text(note).replace("validatation", "validation")
            key = _normalize(note)
            if note and key not in seen:
                seen.add(key)
                normalized.append(note)
        if normalized:
            cleaned["notes"] = "\n\n".join(normalized)
    return cleaned if any(key in cleaned for key in ("remove", "replace", "add", "notes")) else {}


def _normalize_comment_finding(finding: dict[str, Any]) -> dict[str, Any]:
    item = v2._normalize_comment_finding(finding)
    kind = _semantic_kind(item)
    if kind in HARD_REQUIRED_KIND_TITLES:
        item["title"] = HARD_REQUIRED_KIND_TITLES[kind]
    elif kind in OPTIONAL_KIND_TITLES:
        item["title"] = OPTIONAL_KIND_TITLES[kind]
    token = _token_context(item)
    if token:
        item["title"] = "Environment token forwarded to request-controlled callback"
        item["body"] = _scrub_token_text(item.get("body", ""))
    path = str(item.get("path", "") or "")
    item["validation"] = _clean_validation(item.get("validation", ""), path, kind, token)
    guidance = _sanitize_fix_guidance(item)
    if guidance:
        item["fix_guidance"] = guidance
    else:
        item.pop("fix_guidance", None)
    return item


def _rendered_comment_scrub(comment: str, finding: dict[str, Any]) -> str:
    if _token_context(finding):
        comment = _scrub_token_text(comment)
    return comment.replace("validatation", "validation")


def _dedupe_key(finding: dict[str, Any]) -> tuple[str, str, str, str]:
    kind = _semantic_kind(finding)
    path = str(finding.get("path", "") or "").strip()
    if kind:
        line = "" if kind in {"python_ssrf", v2.PS_ACL_KIND} else str(finding.get("line", "") or "").strip()
        return path, line, kind, ""
    return v2._dedupe_key(finding)


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

    for kind in RANK_KIND_ORDER:
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
    if kind in v2.HARD_REQUIRED_KIND_TITLES:
        return v2._finding_covers_sentinel(finding, sentinel)
    if kind == PS_PROCESS_KIND:
        return (
            str(finding.get("path", "") or "") == str(getattr(sentinel, "path", "") or "")
            and _semantic_kind(finding) == PS_PROCESS_KIND
            and _finding_line(finding) == _sentinel_line(sentinel)
        )
    return False


def _required_sentinels(original_required: Any, sentinels: list[Any]) -> list[Any]:
    original_items = original_required(sentinels) if callable(original_required) else []
    combined = [*original_items, *(sentinel for sentinel in sentinels if _sentinel_kind(sentinel) in HARD_REQUIRED_KIND_TITLES)]
    return _dedupe_sentinels(combined)
