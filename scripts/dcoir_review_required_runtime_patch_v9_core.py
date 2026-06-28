"""Ninth required-coverage layer for DCOIR Review.

This connector-safe layer keeps the final reviewer boring and deterministic:
OpenRouter Auto prompt-engineering preflights are visible and enforced before
Pareto calls, inline comments do not carry model footers, selected comments must
match the semantic risk at their changed line, Python pickle sinks become
required-adjacent coverage when present, and validation snippets avoid fragile
quoting.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v4 as v4
import dcoir_review_required_runtime_patch_v5 as v5
import dcoir_review_required_runtime_patch_v8 as v8

SentinelKey = tuple[str, int, str]

PYTHON_PICKLE_LOAD = "python_pickle_load"
PYTHON_PICKLE_LABEL = "Python unsafe pickle deserialization"
PYTHON_PICKLE_DETAIL = (
    "pickle.load/pickle.loads can execute code during deserialization; use a safe serialization "
    "format or a strictly validated, signed, trusted pickle source"
)
INLINE_MODEL_FOOTER_RE = re.compile(r"\n{0,2}(?:_|\*)?Reviewed with [^\n]+?\.?(?:_|\*)?\s*$", re.I)

PROMPT_REVIEW_EVENTS: list[dict[str, Any]] = []
PROMPT_REVIEW_CALLS: list[dict[str, Any]] = []
PARETO_CALL_EVENTS: list[dict[str, Any]] = []
PROMPT_REVIEW_FAILURES: list[dict[str, Any]] = []
EVENT_LIMIT = 40


def _line_number(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _normalize(value: Any) -> str:
    return v5._normalize(value)


def _canonical_kind(kind: str) -> str:
    if kind == getattr(v4, "PS_OUTBOUND_TOKEN", "ps_outbound_token"):
        return v5.PS_ENV_TOKEN
    return kind


def _key_text(key: SentinelKey) -> str:
    return f"{key[0]}:{key[1]} {key[2]}"


def _claim_text(finding: dict[str, Any]) -> str:
    return _normalize(
        "\n".join(
            str(part or "")
            for part in [
                finding.get("title"),
                finding.get("body"),
                finding.get("description"),
                finding.get("_anchored_line_text"),
            ]
        )
    )


def _line_kind(path: str, text: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    line = str(text or "")
    line_norm = _normalize(line)
    if suffix in {".yml", ".yaml"}:
        if "pull_request_target" in line_norm:
            return v4.YAML_PULL_REQUEST_TARGET
        if v4.WRITE_PERMISSION_RE.search(line):
            return v4.YAML_BROAD_WRITE
        if "github.event.pull_request.head" in line_norm or "github.head_ref" in line_norm:
            return v4.YAML_UNTRUSTED_CHECKOUT
        if v4.SHELL_PIPE_RE.search(line):
            return v4.YAML_SHELL_PIPE
        if v4._metadata_shell_line(line):
            return v4.YAML_METADATA_SHELL
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if v4.PS_START_PROCESS_RE.search(line):
            return v4.PS_PROCESS_LAUNCH
        if v4.PS_ACL_RE.search(line):
            return v4.PS_ACL
        if v5.PS_ENV_RE.search(line) and v5.OUTBOUND_RE.search(line):
            return v5.PS_ENV_TOKEN
    if suffix == ".py":
        if "pickle.loads" in line_norm or "pickle.load(" in line_norm:
            return PYTHON_PICKLE_LOAD
        if v5.PY_YAML_LOAD_RE.search(line):
            return v5.PYTHON_YAML_LOAD
        if v5.PY_SHELL_EXEC_RE.search(line):
            return v5.PYTHON_SHELL_EXEC
        if v5.PY_ENV_RE.search(line) and v5.OUTBOUND_RE.search(line):
            return v5.PYTHON_ENV_TOKEN
    return v5._line_kind(path, text)


def _claimed_kinds(finding: dict[str, Any]) -> set[str]:
    path = str(finding.get("path", "") or "")
    text = _claim_text(finding)
    suffix = Path(path.lower()).suffix
    kinds: set[str] = set()
    if suffix == ".py":
        if "pickle.loads" in text or "pickle.load(" in text or ("pickle" in text and "deserial" in text):
            kinds.add(PYTHON_PICKLE_LOAD)
        if "yaml.load" in text or "yaml.loader" in text:
            kinds.add(v5.PYTHON_YAML_LOAD)
        if "shell=true" in text or ("subprocess" in text and "shell" in text):
            kinds.add(v5.PYTHON_SHELL_EXEC)
        if ("os.getenv" in text or "os.environ" in text or "dcoir_token" in text) and (
            "callback" in text or "authorization" in text or "requests." in text
        ):
            kinds.add(v5.PYTHON_ENV_TOKEN)
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if "start-process" in text:
            kinds.add(v4.PS_PROCESS_LAUNCH)
        if "set-acl" in text or "filesystemaccessrule" in text or "fullcontrol" in text or "everyone" in text:
            kinds.add(v4.PS_ACL)
        if ("$env:" in text or "dcoir_token" in text) and (
            "invoke-webrequest" in text or "invoke-restmethod" in text or "authorization" in text or "callback" in text
        ):
            kinds.add(v5.PS_ENV_TOKEN)
    if suffix in {".yml", ".yaml"}:
        if ("metadata" in text or "pr title" in text or "pull request title" in text or "github.event.pull_request" in text) and (
            "shell" in text or "command" in text or "bash" in text or " sh" in text
        ):
            kinds.add(v4.YAML_METADATA_SHELL)
        if "github.event.pull_request.head" in text or "github.head_ref" in text or (
            "untrusted" in text and "checkout" in text
        ):
            kinds.add(v4.YAML_UNTRUSTED_CHECKOUT)
        if ("curl" in text or "wget" in text) and ("bash" in text or " sh" in text or "pipe" in text):
            kinds.add(v4.YAML_SHELL_PIPE)
        if "write-all" in text or ("permissions" in text and "write" in text) or "broad write" in text:
            kinds.add(v4.YAML_BROAD_WRITE)
        if "pull_request_target" in text:
            kinds.add(v4.YAML_PULL_REQUEST_TARGET)
    return kinds


def _semantic_kind(finding: dict[str, Any]) -> str:
    explicit = finding.get("_risk_sentinel_key")
    if isinstance(explicit, (list, tuple)) and len(explicit) == 3:
        return _canonical_kind(str(explicit[2]))
    explicit_kind = str(finding.get("_risk_sentinel_kind", "") or "")
    if explicit_kind:
        return _canonical_kind(explicit_kind)
    claimed = _claimed_kinds(finding)
    for kind in [
        v4.YAML_METADATA_SHELL,
        v4.YAML_SHELL_PIPE,
        v4.YAML_UNTRUSTED_CHECKOUT,
        v4.YAML_BROAD_WRITE,
        v4.YAML_PULL_REQUEST_TARGET,
        v4.PS_PROCESS_LAUNCH,
        v4.PS_ACL,
        v5.PS_ENV_TOKEN,
        PYTHON_PICKLE_LOAD,
        v5.PYTHON_YAML_LOAD,
        v5.PYTHON_SHELL_EXEC,
        v5.PYTHON_ENV_TOKEN,
    ]:
        if kind in claimed:
            return kind
    anchored_kind = _line_kind(str(finding.get("path", "") or ""), str(finding.get("_anchored_line_text", "") or ""))
    return _canonical_kind(anchored_kind or v5._semantic_kind(finding))


def _postable_key(finding: dict[str, Any]) -> SentinelKey:
    path = str(finding.get("path", "") or "")
    line = _line_number(finding.get("line", 0))
    return path, line, _semantic_kind(finding) or str(finding.get("title", "") or "")


def _sentinel_key(sentinel: Any) -> SentinelKey:
    path = str(getattr(sentinel, "path", "") or "")
    line = _line_number(getattr(sentinel, "line", 0))
    text = str(getattr(sentinel, "text", "") or "")
    label = str(getattr(sentinel, "label", "") or "")
    detail = str(getattr(sentinel, "detail", "") or "")
    kind = _canonical_kind(_line_kind(path, text) or v5._sentinel_kind(sentinel))
    if kind in {"", "unknown"} and ("pickle.loads" in _normalize(f"{text}\n{label}\n{detail}") or "pickle.load(" in _normalize(f"{text}\n{label}\n{detail}")):
        kind = PYTHON_PICKLE_LOAD
    return path, line, kind


def _required_sentinels(hardened: Any, risk_sentinels: list[Any]) -> list[Any]:
    required = list(hardened.required_risk_sentinels(risk_sentinels)) if callable(getattr(hardened, "required_risk_sentinels", None)) else []
    seen = {_sentinel_key(item) for item in required}
    for sentinel in risk_sentinels:
        key = _sentinel_key(sentinel)
        if key[2] == PYTHON_PICKLE_LOAD and key not in seen:
            required.append(sentinel)
            seen.add(key)
    return required


def _expected_by_line(hardened: Any, risk_sentinels: list[Any]) -> dict[tuple[str, int], set[str]]:
    expected: dict[tuple[str, int], set[str]] = {}
    for sentinel in _required_sentinels(hardened, risk_sentinels):
        path, line, kind = _sentinel_key(sentinel)
        expected.setdefault((path, line), set()).add(kind)
    return expected


def _semantic_mismatch(finding: dict[str, Any], expected: dict[tuple[str, int], set[str]]) -> bool:
    path, line, kind = _postable_key(finding)
    allowed = expected.get((path, line), set())
    if not allowed:
        return False
    explicit = finding.get("_risk_sentinel_key")
    if isinstance(explicit, (list, tuple)) and len(explicit) == 3 and str(explicit[2]) not in allowed:
        return True
    explicit_kind = str(finding.get("_risk_sentinel_kind", "") or "")
    if explicit_kind and explicit_kind not in allowed:
        return True
    claimed = _claimed_kinds(finding)
    return bool((claimed and any(item not in allowed for item in claimed)) or kind not in allowed)


def _severity_rank(finding: dict[str, Any]) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(str(finding.get("severity", "")).lower(), 4)


def _confidence(finding: dict[str, Any]) -> float:
    try:
        return float(finding.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _spare_priority(finding: dict[str, Any]) -> tuple[int, int, float, str, int]:
    path = str(finding.get("path", "") or "")
    suffix = Path(path.lower()).suffix
    optional = "/optional_" in path.lower() or path.rsplit("/", 1)[-1].startswith("optional_")
    if _postable_key(finding)[2] == PYTHON_PICKLE_LOAD:
        family = 0
    elif not optional and suffix in {".py", ".ps1", ".psm1", ".psd1", ".yml", ".yaml"}:
        family = 1
    elif not optional:
        family = 2
    else:
        family = 3
    return family, _severity_rank(finding), -_confidence(finding), path, _line_number(finding.get("line", 0))


def _dedupe(findings: list[dict[str, Any]], expected: dict[tuple[str, int], set[str]]) -> tuple[list[dict[str, Any]], list[str]]:
    kept: dict[SentinelKey, dict[str, Any]] = {}
    order: list[SentinelKey] = []
    dropped: list[str] = []
    for finding in findings:
        item = v5._normalize_comment_finding(finding)
        key = _postable_key(item)
        if _semantic_mismatch(item, expected):
            dropped.append(f"{key[0]}:{key[1]} expected={','.join(sorted(expected.get((key[0], key[1]), set())))} actual={key[2]}")
            continue
        if key not in kept:
            kept[key] = item
            order.append(key)
        else:
            dropped.append(f"{key[0]}:{key[1]} duplicate {key[2]}")
            if (_severity_rank(item), -_confidence(item)) < (_severity_rank(kept[key]), -_confidence(kept[key])):
                kept[key] = item
    return [kept[key] for key in order], dropped


def _quote_ps_string(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _ps_validation(path: str, check: str, line: int = 0) -> str:
    ps_path = _quote_ps_string(path)
    if line:
        setup = (
            f"$p = {ps_path}; $line = {max(1, line)}; $lines = Get-Content -LiteralPath $p; "
            "$start = [Math]::Max(0, $line - 4); $end = [Math]::Min($lines.Count - 1, $line + 2); "
            "$window = ($lines[$start..$end] -join \"`n\"); "
        )
    else:
        setup = f"$p = {ps_path}; $text = Get-Content -Raw -LiteralPath $p; "
    parse = "$all = Get-Content -Raw -LiteralPath $p; $errors = $null; [System.Management.Automation.PSParser]::Tokenize($all, [ref]$errors) | Out-Null; if ($errors) { throw ($errors | Out-String) }"
    return "pwsh -NoProfile -Command " + shlex.quote(setup + check + "; " + parse)


def _py_window_doc(path: str, line: int, assertions: str) -> str:
    return (
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        f"path = Path({path!r})\n"
        f"line = {max(1, line)}\n"
        "lines = path.read_text(encoding='utf-8').splitlines()\n"
        "window = '\\n'.join(lines[max(0, line - 4):min(len(lines), line + 3)])\n"
        "lower = window.lower()\n"
        f"{assertions}\n"
        "PY"
    )


def _validation_for_key(kind: str, path: str, line: int = 0) -> str:
    if kind == v5.PS_ENV_TOKEN:
        return _ps_validation(path, "if (($window -match '(?i)\\$env:DCOIR_TOKEN') -and ($window -match '(?i)Authorization|Bearer') -and ($window -match '(?i)Invoke-(RestMethod|WebRequest)|callback')) { throw 'environment token forwarded to request-controlled callback remains' }", line)
    if kind == v4.PS_PROCESS_LAUNCH:
        return _ps_validation(path, "if ($text -match '(?i)Start-Process\\s+-FilePath\\s+\\$[A-Za-z_][A-Za-z0-9_]*') { throw 'caller-controlled Start-Process remains' }")
    if kind == v4.PS_ACL:
        return _ps_validation(path, "if ($text -match '(?i)icacls.*Everyone:F|Everyone.*FullControl|FileSystemAccessRule.*Everyone|Set-Acl') { throw 'broad ACL grant remains' }")
    if kind == PYTHON_PICKLE_LOAD:
        quoted = shlex.quote(path)
        return f"python3 -m py_compile {quoted}\n" + v8._py_here_doc(path, "assert 'pickle.loads' not in text\nassert 'pickle.load(' not in text")
    if kind == v5.PYTHON_ENV_TOKEN:
        quoted = shlex.quote(path)
        checks = "has_env = 'os.getenv' in lower or 'os.environ' in lower\nhas_bearer = 'authorization' in lower or 'bearer' in lower\nhas_callback = 'requests.' in lower or 'callback' in lower\nassert not (has_env and has_bearer and has_callback)"
        return f"python3 -m py_compile {quoted}\n" + _py_window_doc(path, line, checks)
    return v8._validation_for_kind(kind, path)


def _yaml_load_arg(line_text: str) -> str:
    match = re.search(r"yaml\.load\s*\(\s*(?P<arg>[^,\n)]+)", str(line_text or ""))
    if not match:
        return "text"
    arg = match.group("arg").strip()
    return arg if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", arg) else "text"


def _rewrite_validation(findings: list[dict[str, Any]]) -> None:
    for finding in findings:
        path, line, kind = _postable_key(finding)
        validation = _validation_for_key(kind, path, line)
        if validation:
            finding["validation"] = validation
            guidance = finding.get("fix_guidance")
            if isinstance(guidance, dict):
                guidance["validation"] = validation
