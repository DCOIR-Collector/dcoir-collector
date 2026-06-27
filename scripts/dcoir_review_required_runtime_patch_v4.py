"""Fourth required-coverage layer for DCOIR Review.

This final connector-sized layer owns the deterministic user-facing shape for
hard-required findings. Earlier layers may detect, synthesize, and repair, but
v4 is the last authority for required semantic templates, exact remove blocks,
rendered-output safety, final dedupe, and required refill before optional
findings are allowed to consume review budget.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v2 as v2
import dcoir_review_required_runtime_patch_v3 as v3
import dcoir_review_required_runtime_patches as required

YAML_PULL_REQUEST_TARGET = "yaml_pull_request_target"
YAML_BROAD_WRITE = "yaml_broad_write"
YAML_UNTRUSTED_CHECKOUT = "yaml_untrusted_checkout"
YAML_SHELL_PIPE = "yaml_shell_pipe"
YAML_METADATA_SHELL = v3.YAML_METADATA_SHELL_KIND
PS_ACL = v2.PS_ACL_KIND
PS_PROCESS_LAUNCH = v3.PS_PROCESS_KIND
PYTHON_SHELL_EXEC = "python_shell_exec"
PYTHON_YAML_LOAD = "python_yaml_load"
PYTHON_SSRF = "python_ssrf"
PS_OUTBOUND_TOKEN = "ps_outbound_token"

HARD_REQUIRED_KIND_TITLES = {
    YAML_PULL_REQUEST_TARGET: "Privileged `pull_request_target` workflow context",
    YAML_BROAD_WRITE: "GitHub Actions workflow grants write permissions",
    YAML_UNTRUSTED_CHECKOUT: "Privileged workflow checks out untrusted PR code",
    YAML_SHELL_PIPE: "Workflow pipes a network installer into a shell",
    PS_ACL: "PowerShell broad ACL grant exposes collector output",
    PS_PROCESS_LAUNCH: "PowerShell caller-controlled process launch",
}
OPTIONAL_KIND_TITLES = {
    YAML_METADATA_SHELL: "Workflow executes pull request metadata in a shell",
}
HARD_REQUIRED_KIND_ORDER = (
    YAML_PULL_REQUEST_TARGET,
    YAML_BROAD_WRITE,
    YAML_UNTRUSTED_CHECKOUT,
    YAML_SHELL_PIPE,
    PS_ACL,
    PS_PROCESS_LAUNCH,
)
RANK_KIND_ORDER = (
    *HARD_REQUIRED_KIND_ORDER,
    PYTHON_YAML_LOAD,
    PYTHON_SHELL_EXEC,
    PYTHON_SSRF,
    PS_OUTBOUND_TOKEN,
    "python_dynamic_exec",
    "python_pickle",
    "python_archive_extract",
    "ps_dynamic_exec",
    "ps_archive_extract",
    YAML_METADATA_SHELL,
)

WRITE_PERMISSION_RE = re.compile(
    r"^\s*(?:permissions\s*:\s*write-all|"
    r"(?:actions|checks|contents|deployments|id-token|issues|packages|pull-requests|statuses)\s*:\s*write)\b",
    re.IGNORECASE,
)
SHELL_PIPE_RE = re.compile(r"\b(?:curl|wget)\b[^\n]*(?:\|\s*(?:bash|sh)\b)", re.IGNORECASE)
PR_METADATA_RE = re.compile(r"github\.event\.pull_request\.(?:body|title|head\.ref|head\.sha)", re.IGNORECASE)
SHELL_EXEC_RE = re.compile(r"(?:\|\s*(?:bash|sh)\b|\b(?:bash|sh)\s+-c\b|\b(?:bash|sh)\b)", re.IGNORECASE)
PS_START_PROCESS_RE = re.compile(r"\bStart-Process\b", re.IGNORECASE)
PS_ACL_RE = re.compile(r"\b(?:Set-Acl|FileSystemAccessRule|FullControl|Everyone)\b", re.IGNORECASE)
ENV_TOKEN_RE = re.compile(
    r"(?:os\.environ|os\.getenv|\$env:|process\.env|Environment::GetEnvironmentVariable|DCOIR_TOKEN)",
    re.IGNORECASE,
)
OUTBOUND_RE = re.compile(
    r"(?:callback|Authorization|Bearer|Invoke-WebRequest|Invoke-RestMethod|requests\.(?:get|post|put|request)|urlopen)",
    re.IGNORECASE,
)
COMMAND_START_RE = re.compile(r"^\s*(?:python3?|pytest|bandit|pwsh|powershell|grep|rg|yamllint|npm|npx|node|bash|sh)\b")
PROSE_VALIDATION_RE = re.compile(r"\b(?:scan for|without validatation|without validation|manually verify|guidance|expected after fix|assert text\.strip)\b", re.IGNORECASE)
YAML_CODE_LINE_RE = re.compile(r"^\s*(?:[-?]\s+)?[A-Za-z0-9_.${}/ -]+\s*:")
POWERSHELL_CODE_LINE_RE = re.compile(r"^\s*(?:#|\$[A-Za-z_][A-Za-z0-9_]*\b|[A-Za-z]+-[A-Za-z]+(?:\s|$)|(?:if|foreach|for|while|try|catch|finally|param|function)\b)", re.IGNORECASE)
PYTHON_CODE_LINE_RE = re.compile(r"^\s*(?:#|from\s+\S+\s+import\s+|import\s+|def\s+|class\s+|if\s+|elif\s+|else:|for\s+|while\s+|try:|except\b|finally:|with\s+|return\b|raise\b|assert\b|[A-Za-z_][A-Za-z0-9_]*\s*=)")
BANNED_ENV_PROSE_RE = re.compile(
    r"\b(?:static credential|secret exposure|environment token value|hard[- ]?coded|literal bearer|literal token|inline secret|redacted[-_ ]?secret|rotate exposed credential|authentication secrets)\b",
    re.IGNORECASE,
)
DUPLICATE_WHITESPACE_RE = re.compile(r"\n{3,}")


def _normalize(value: Any) -> str:
    return required._normalize(value)


def _line_number(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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
        ".sh": "bash",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix, "text")


def _metadata_shell_line(text: str) -> bool:
    line = str(text or "")
    return PR_METADATA_RE.search(line) is not None and SHELL_EXEC_RE.search(line) is not None


def _line_kind(path: str, text: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    line = str(text or "")
    normalized = _normalize(line)
    if suffix in {".yml", ".yaml"}:
        if "pull_request_target" in normalized:
            return YAML_PULL_REQUEST_TARGET
        if WRITE_PERMISSION_RE.search(line):
            return YAML_BROAD_WRITE
        if "github.event.pull_request.head" in normalized or "github.head_ref" in normalized:
            return YAML_UNTRUSTED_CHECKOUT
        if SHELL_PIPE_RE.search(line):
            return YAML_SHELL_PIPE
        if _metadata_shell_line(line):
            return YAML_METADATA_SHELL
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if PS_START_PROCESS_RE.search(line):
            return PS_PROCESS_LAUNCH
        if PS_ACL_RE.search(line):
            return PS_ACL
    return v3._line_kind(path, text)


def _finding_text(finding: dict[str, Any]) -> str:
    parts = [
        str(finding.get("title", "") or ""),
        str(finding.get("body", "") or ""),
        str(finding.get("validation", "") or ""),
        str(finding.get("_anchored_line_text", "") or ""),
    ]
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    parts.extend(str(guidance.get(key, "") or "") for key in ("remove", "replace", "add", "notes"))
    return _normalize("\n".join(parts))


def _semantic_kind(finding: dict[str, Any]) -> str:
    path = str(finding.get("path", "") or "")
    anchored = str(finding.get("_anchored_line_text", "") or "")
    anchored_kind = _line_kind(path, anchored)
    if anchored_kind:
        return anchored_kind
    text = _finding_text(finding)
    suffix = Path(path.lower()).suffix
    if suffix in {".yml", ".yaml"}:
        if "pull_request_target" in text:
            return YAML_PULL_REQUEST_TARGET
        if "write-all" in text or ("permissions" in text and " write" in text) or "broad write" in text:
            return YAML_BROAD_WRITE
        if "github.event.pull_request.head" in text or "github.head_ref" in text or ("untrusted" in text and "checkout" in text):
            return YAML_UNTRUSTED_CHECKOUT
        if ("curl" in text or "wget" in text) and ("|" in text or "pipe" in text) and ("bash" in text or " sh" in text):
            return YAML_SHELL_PIPE
        if "pull request metadata" in text or ("github.event.pull_request" in text and "bash" in text):
            return YAML_METADATA_SHELL
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if "start-process" in text:
            return PS_PROCESS_LAUNCH
        if "set-acl" in text or "filesystemaccessrule" in text or "fullcontrol" in text or "everyone" in text:
            return PS_ACL
        if "invoke-webrequest" in text or "invoke-restmethod" in text or "bearer" in text:
            return PS_OUTBOUND_TOKEN
    if suffix == ".py":
        if "yaml.load" in text or "yaml.loader" in text:
            return PYTHON_YAML_LOAD
        if "shell=true" in text or "subprocess" in text and "shell" in text:
            return PYTHON_SHELL_EXEC
        if "requests." in text or "callback" in text or "ssrf" in text:
            return PYTHON_SSRF
    return v3._semantic_kind(finding)


def _sentinel_kind(sentinel: Any) -> str:
    path = str(getattr(sentinel, "path", "") or "")
    text = str(getattr(sentinel, "text", "") or "")
    line_kind = _line_kind(path, text)
    if line_kind:
        return line_kind
    return v3._sentinel_kind(sentinel)


def _sentinel_line(sentinel: Any) -> int:
    return _line_number(getattr(sentinel, "line", 0))


def _finding_line(finding: dict[str, Any]) -> int:
    return _line_number(finding.get("line", 0))


def _is_env_token_callback(finding: dict[str, Any]) -> bool:
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
    return ENV_TOKEN_RE.search(haystack) is not None and OUTBOUND_RE.search(haystack) is not None


def _path_expr(path: str) -> str:
    return repr(str(path or ""))


def _validation_for_path(path: str, kind: str = "") -> str:
    lower = str(path or "").lower()
    if lower.endswith((".ps1", ".psm1", ".psd1")):
        ps_path = "'" + str(path or "").replace("'", "''") + "'"
        return (
            "pwsh -NoProfile -Command \"$errors=$null; "
            f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath {ps_path}), [ref]$errors) | Out-Null; "
            "if ($errors) { throw ($errors | Out-String) }\""
        )
    if lower.endswith((".yml", ".yaml")):
        checks = {
            YAML_PULL_REQUEST_TARGET: "assert 'pull_request_target' not in text",
            YAML_BROAD_WRITE: "assert 'write-all' not in text and not re.search(r'(?m)^\\s*(actions|checks|contents|deployments|id-token|issues|packages|pull-requests|statuses)\\s*:\\s*write\\b', text)",
            YAML_UNTRUSTED_CHECKOUT: "assert 'github.event.pull_request.head' not in text and 'github.head_ref' not in text",
            YAML_SHELL_PIPE: "assert not re.search(r'\\b(curl|wget)\\b[^\\n]*\\|\\s*(bash|sh)\\b', text, re.I)",
            YAML_METADATA_SHELL: "assert not (re.search(r'github\\.event\\.pull_request\\.(body|title|head\\.ref|head\\.sha)', text, re.I) and re.search(r'(\\|\\s*(bash|sh)\\b|\\b(bash|sh)\\s+-c\\b)', text, re.I))",
        }
        check = checks.get(kind, "assert text.strip()")
        script = f"import re; from pathlib import Path; path=Path({_path_expr(path)}); text=path.read_text(encoding='utf-8'); assert path.exists(), path; {check}"
        return f"python3 -c {shlex.quote(script)}"
    if lower.endswith(".py"):
        return f"python3 -m py_compile {shlex.quote(str(path or ''))}"
    return v3._validation_for_path(path, kind)


def _clean_validation(value: Any, path: str, kind: str) -> str:
    if kind in HARD_REQUIRED_KIND_TITLES or kind == YAML_METADATA_SHELL:
        return _validation_for_path(path, kind)
    kept: list[str] = []
    seen: set[str] = set()
    for raw_line in str(value or "").replace("```", "").splitlines():
        line = raw_line.strip()
        if not line or PROSE_VALIDATION_RE.search(line) or not COMMAND_START_RE.match(line):
            continue
        if line in seen:
            continue
        seen.add(line)
        kept.append(line)
    if kept:
        return "\n".join(kept)
    return _validation_for_path(path, kind)


def _note_line_is_code(line: str, language: str) -> bool:
    stripped = line.rstrip()
    if not stripped.strip():
        return False
    if stripped.lstrip().startswith("#") or "${{" in stripped:
        return True
    if language == "yaml" and (YAML_CODE_LINE_RE.match(stripped) or stripped.lstrip().startswith("- ")):
        return True
    if language == "powershell" and POWERSHELL_CODE_LINE_RE.match(stripped):
        return True
    if language == "python" and PYTHON_CODE_LINE_RE.match(stripped):
        return True
    return False


def _format_notes(value: Any, path: str) -> str:
    text = required._clean_public_text(str(value or "").replace("validatation", "validation")).strip()
    if not text or "```" in text:
        return text
    language = _language_hint(path)
    lines = text.splitlines()
    output: list[str] = []
    code_block: list[str] = []

    def flush_code() -> None:
        nonlocal code_block
        if code_block:
            while output and not output[-1].strip():
                output.pop()
            output.append(f"```{language}")
            output.extend(code_block)
            output.append("```")
            code_block = []

    for line in lines:
        if _note_line_is_code(line, language):
            code_block.append(line.rstrip())
            continue
        flush_code()
        output.append(line.rstrip())
    flush_code()
    return DUPLICATE_WHITESPACE_RE.sub("\n\n", "\n".join(output)).strip()


def _exact_remove_matches(finding: dict[str, Any], remove_code: str) -> bool:
    anchored = str(finding.get("_anchored_line_text", "") or "").rstrip()
    candidate = str(remove_code or "").rstrip()
    if not candidate:
        return False
    return bool(anchored) and candidate.strip() == anchored.strip()


def _sanitize_fix_guidance(finding: dict[str, Any]) -> dict[str, Any]:
    raw = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    if not raw:
        return {}
    path = str(finding.get("path", "") or "")
    language = str(raw.get("language") or _language_hint(path)).lower()
    cleaned: dict[str, Any] = {"language": language}
    notes: list[str] = []
    remove_code = v3._strip_fences(raw.get("remove", ""))
    if remove_code:
        if _exact_remove_matches(finding, remove_code):
            cleaned["remove"] = remove_code
        else:
            notes.append("Line-specific removal guidance was omitted because it did not exactly match the anchored line/range.")
    for key in ("replace", "add"):
        value = v3._strip_fences(raw.get(key, ""))
        if value:
            cleaned[key] = value
    if raw.get("notes"):
        notes.append(str(raw.get("notes", "")))
    if notes:
        formatted = _format_notes("\n\n".join(notes), path)
        if formatted:
            cleaned["notes"] = formatted
    return cleaned if any(key in cleaned for key in ("remove", "replace", "add", "notes")) else {}


def _shell_pipe_body(line_text: str) -> str:
    changed = str(line_text or "").strip()
    scheme_note = " over unencrypted HTTP" if "http://" in changed.lower() else ""
    return (
        f"This workflow pipes network-fetched content{scheme_note} directly into a shell. "
        "Download the content to a file, verify a pinned checksum or signature, and execute only verified content."
    )


def _template_fields(kind: str, path: str, line_text: str) -> dict[str, Any]:
    notes = {
        YAML_PULL_REQUEST_TARGET: "Use `pull_request` for untrusted code paths, or keep `pull_request_target` jobs limited to metadata-only operations that do not check out or execute PR-controlled code.",
        YAML_BROAD_WRITE: "Set explicit least-privilege `permissions` for the job or workflow instead of broad write scopes.",
        YAML_UNTRUSTED_CHECKOUT: "Do not check out PR-controlled refs or head SHAs in a privileged workflow context.",
        YAML_SHELL_PIPE: "Replace curl/wget-to-shell with download, verification, and execution of pinned content.",
        PS_ACL: "Grant only the specific identity and filesystem rights the collector needs. Avoid `Everyone` and `FullControl` on collector output or execution paths.",
        PS_PROCESS_LAUNCH: "Use an allowlisted command table and validated arguments, or remove caller-controlled process launch from the collector path.",
        YAML_METADATA_SHELL: "Treat PR title, body, branch, and head metadata as attacker-controlled data. Do not pass it to `bash`, `sh`, or `bash -c`.",
    }
    bodies = {
        YAML_PULL_REQUEST_TARGET: "`pull_request_target` runs with base-repository privileges. Do not execute untrusted PR code in this workflow context.",
        YAML_BROAD_WRITE: "This workflow grants broad write token permissions. Narrow `permissions` to the minimum scopes required.",
        YAML_UNTRUSTED_CHECKOUT: "This privileged workflow checks out PR-controlled code. Do not combine privileged workflow context with PR-controlled refs or head SHAs.",
        YAML_SHELL_PIPE: _shell_pipe_body(line_text),
        PS_ACL: "This PowerShell change grants broad filesystem ACL rights. Narrow the identity and rights to the minimum collector path access required.",
        PS_PROCESS_LAUNCH: "This line launches a caller-controlled executable or argument string. Use an allowlisted command table or remove the launch from the collector path.",
        YAML_METADATA_SHELL: "This workflow passes pull request metadata to a shell. Pull request title, body, and head metadata are attacker-controlled and must not be executed.",
    }
    return {
        "title": HARD_REQUIRED_KIND_TITLES.get(kind, OPTIONAL_KIND_TITLES.get(kind, "Finding")),
        "body": bodies.get(kind, "Review this changed line before merging."),
        "validation": _validation_for_path(path, kind),
        "suggested_replacement": "",
        "fix_guidance": {"language": _language_hint(path), "notes": notes.get(kind, "Use a minimal, evidence-backed fix for this finding.")},
    }


def _env_token_fields(path: str) -> dict[str, Any]:
    return {
        "title": "Environment token forwarded to request-controlled callback",
        "body": "Environment token read from env and forwarded to request-controlled callback. Keep collector tokens server-side and allowlist outbound destinations before sending authorization headers.",
        "validation": _validation_for_path(path, _language_hint(path)),
        "suggested_replacement": "",
        "fix_guidance": {
            "language": _language_hint(path),
            "notes": "Keep the token on the trusted side of the boundary and validate the callback destination against an allowlist before any request is made.",
        },
    }


def _normalize_comment_finding(finding: dict[str, Any]) -> dict[str, Any]:
    raw_kind = _semantic_kind(finding)
    item = v3._normalize_comment_finding(finding)
    if finding.get("_anchored_line_text") and not item.get("_anchored_line_text"):
        item["_anchored_line_text"] = finding.get("_anchored_line_text")
    kind = _semantic_kind(item) or raw_kind
    path = str(item.get("path", "") or "")
    line_text = str(item.get("_anchored_line_text", "") or "")
    if _is_env_token_callback({**item, "_anchored_line_text": line_text}):
        item.update(_env_token_fields(path))
        return item
    if kind in HARD_REQUIRED_KIND_TITLES or kind == YAML_METADATA_SHELL:
        item.update(_template_fields(kind, path, line_text))
        return item
    item["title"] = required._clean_public_text(str(item.get("title", "") or "Finding").replace("validatation", "validation"))
    item["body"] = required._clean_public_text(str(item.get("body", "") or "").replace("validatation", "validation"))
    item["validation"] = _clean_validation(item.get("validation", ""), path, kind)
    guidance = _sanitize_fix_guidance(item)
    if guidance:
        item["fix_guidance"] = guidance
    else:
        item.pop("fix_guidance", None)
    return item


def _render_deterministic_comment(finding: dict[str, Any], model_used: str) -> str:
    title = str(finding.get("title", "") or "Finding")
    body = str(finding.get("body", "") or "").strip()
    validation = str(finding.get("validation", "") or "").strip()
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    notes = _format_notes(guidance.get("notes", ""), str(finding.get("path", "") or "")) if guidance else ""
    parts = [f"**{title}**"]
    if body:
        parts.extend(["", body])
    if notes:
        parts.extend(["", "**Suggested fix:**", "", notes])
    if validation:
        parts.extend(["", "**Validation:**", "", "```bash", validation, "```"])
    if model_used:
        parts.extend(["", f"_Reviewed with {model_used}._"])
    return _final_rendered_scrub("\n".join(parts), finding)


def _final_rendered_scrub(comment: str, finding: dict[str, Any]) -> str:
    text = str(comment or "").replace("validatation", "validation")
    text = text.replace("environment token value value", "environment token")
    if _is_env_token_callback(finding):
        text = BANNED_ENV_PROSE_RE.sub("environment token", text)
        text = text.replace("environment token value", "environment token")
    if _semantic_kind(finding) == YAML_SHELL_PIPE and "https://" in str(finding.get("_anchored_line_text", "") or "").lower():
        text = re.sub(r"\bplain HTTP\b", "network-fetched content", text, flags=re.IGNORECASE)
    return DUPLICATE_WHITESPACE_RE.sub("\n\n", text).strip()


def _dedupe_key(finding: dict[str, Any]) -> tuple[str, int, str, str]:
    kind = _semantic_kind(finding)
    path = str(finding.get("path", "") or "")
    line = _finding_line(finding)
    sink = _normalize(finding.get("_anchored_line_text", ""))
    if kind:
        return path, line, kind, sink
    return path, line, str(finding.get("title", "") or ""), sink


def _dedupe_findings(hardened: Any, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, int, str, str], dict[str, Any]] = {}
    order: list[tuple[str, int, str, str]] = []
    for finding in findings:
        normalized = _normalize_comment_finding(finding)
        key = _dedupe_key(normalized)
        if key not in by_key:
            by_key[key] = normalized
            order.append(key)
            continue
        if required._finding_quality_score(hardened, normalized) >= required._finding_quality_score(hardened, by_key[key]):
            by_key[key] = normalized
    return [by_key[key] for key in order]


def _rank_findings(module: Any, hardened: Any, original_rank: Any, findings: list[dict[str, Any]], config: Any) -> list[dict[str, Any]]:
    max_inline = max(0, int(getattr(config, "max_inline_comments", 12)))
    ranked_source = _dedupe_findings(hardened, findings)
    severity_sort = getattr(hardened, "severity_sort_key", None)
    if callable(severity_sort):
        ranked_source = sorted(ranked_source, key=severity_sort)
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str, str]] = set()

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
        add(_normalize_comment_finding(finding))
    return selected[:max_inline]


def _sentinel_key(sentinel: Any) -> tuple[str, int, str]:
    return str(getattr(sentinel, "path", "") or ""), _sentinel_line(sentinel), _sentinel_kind(sentinel)


def _dedupe_sentinels(sentinels: list[Any]) -> list[Any]:
    seen: set[tuple[str, int, str]] = set()
    result: list[Any] = []
    for sentinel in sentinels:
        key = _sentinel_key(sentinel)
        if key in seen:
            continue
        seen.add(key)
        result.append(sentinel)
    return result


def _required_sentinels(original_required: Any, sentinels: list[Any]) -> list[Any]:
    existing = original_required(sentinels) if callable(original_required) else []
    required_items = [sentinel for sentinel in sentinels if _sentinel_kind(sentinel) in HARD_REQUIRED_KIND_TITLES]
    return _dedupe_sentinels([*existing, *required_items])


def _finding_covers_sentinel(finding: dict[str, Any], sentinel: Any) -> bool:
    kind = _sentinel_kind(sentinel)
    if kind not in HARD_REQUIRED_KIND_TITLES:
        return False
    if str(finding.get("path", "") or "") != str(getattr(sentinel, "path", "") or ""):
        return False
    if _semantic_kind(finding) != kind:
        return False
    finding_line = _finding_line(finding)
    sentinel_line = _sentinel_line(sentinel)
    if kind == PS_ACL:
        return finding_line > 0 and sentinel_line > 0 and abs(finding_line - sentinel_line) <= 4
    return finding_line == sentinel_line


def _fallback_finding(sentinel: Any, config: Any) -> dict[str, Any]:
    kind = _sentinel_kind(sentinel)
    path = str(getattr(sentinel, "path", "") or "")
    line_text = str(getattr(sentinel, "text", "") or "")
    if kind in HARD_REQUIRED_KIND_TITLES:
        finding = {
            "severity": "critical" if kind in {YAML_PULL_REQUEST_TARGET, YAML_SHELL_PIPE, PS_PROCESS_LAUNCH} else "high",
            "confidence": 0.99,
            "path": path,
            "line": _sentinel_line(sentinel),
            "_anchored_line_text": line_text,
        }
        finding.update(_template_fields(kind, path, line_text))
        return finding
    return {}


def _add_risk_sentinel_fallback_findings(hardened: Any, original_rank: Any, findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    required_sentinels = hardened.required_risk_sentinels(risk_sentinels)
    normalized_findings = _dedupe_findings(hardened, findings)
    uncovered = [
        sentinel
        for sentinel in required_sentinels
        if not any(_finding_covers_sentinel(finding, sentinel) for finding in normalized_findings)
    ]
    fallback_findings = [_fallback_finding(sentinel, config) for sentinel in uncovered]
    fallback_findings = [finding for finding in fallback_findings if finding]
    inline_limit = max(0, int(getattr(config, "max_inline_comments", 12)))
    if fallback_findings:
        try:
            message = "; ".join(f"{finding.get('path')}:{finding.get('line')} {_semantic_kind(finding)}" for finding in fallback_findings)
            base = getattr(hardened, "base", None)
            if base is not None and callable(getattr(base, "emit_status", None)):
                base.emit_status("required-v4-fallback-inserted", message)
        except Exception:
            pass
    existing_budget = max(0, inline_limit - len(fallback_findings))
    existing = _rank_findings(None, hardened, original_rank, normalized_findings, config)[:existing_budget]
    return _rank_findings(None, hardened, None, [*existing, *fallback_findings], config)[:inline_limit]


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    if hardened is None:
        return

    original_required = getattr(hardened, "_dcoir_required_v4_original_required_risk_sentinels", None)
    if original_required is None:
        original_required = getattr(hardened, "required_risk_sentinels", None)
        hardened._dcoir_required_v4_original_required_risk_sentinels = original_required
    hardened.required_risk_sentinels = lambda sentinels: _required_sentinels(original_required, sentinels)
    hardened.is_required_risk_sentinel = lambda sentinel: _sentinel_kind(sentinel) in HARD_REQUIRED_KIND_TITLES or (bool(getattr(hardened, "_dcoir_required_v4_original_is_required_risk_sentinel", lambda _s: False)(sentinel)))
    if not hasattr(hardened, "_dcoir_required_v4_original_is_required_risk_sentinel"):
        hardened._dcoir_required_v4_original_is_required_risk_sentinel = getattr(hardened, "is_required_risk_sentinel", None)

    hardened.finding_covers_risk_sentinel = lambda finding, sentinel: _finding_covers_sentinel(finding, sentinel) if _sentinel_kind(sentinel) in HARD_REQUIRED_KIND_TITLES else bool(getattr(hardened, "_dcoir_required_v4_original_finding_covers_risk_sentinel", lambda _f, _s: False)(finding, sentinel))
    if not hasattr(hardened, "_dcoir_required_v4_original_finding_covers_risk_sentinel"):
        hardened._dcoir_required_v4_original_finding_covers_risk_sentinel = getattr(hardened, "finding_covers_risk_sentinel", None)

    hardened.risk_sentinel_fallback_finding = lambda sentinel, config: _fallback_finding(sentinel, config) or getattr(hardened, "_dcoir_required_v4_original_risk_sentinel_fallback_finding", lambda _s, _c: {})(sentinel, config)
    if not hasattr(hardened, "_dcoir_required_v4_original_risk_sentinel_fallback_finding"):
        hardened._dcoir_required_v4_original_risk_sentinel_fallback_finding = getattr(hardened, "risk_sentinel_fallback_finding", None)

    original_rank = getattr(module, "_dcoir_required_v4_original_rank_findings_for_required_budget", None)
    if original_rank is None:
        original_rank = getattr(module, "rank_findings_for_required_budget", None)
        module._dcoir_required_v4_original_rank_findings_for_required_budget = original_rank
    module.finding_dedupe_key = _dedupe_key
    module.dedupe_findings_for_ranking = lambda findings: _dedupe_findings(hardened, findings)
    module.rank_findings_for_required_budget = lambda findings, config: _rank_findings(module, hardened, original_rank, findings, config)
    hardened.finding_merge_key = lambda finding: (str(finding.get("path", "") or ""), _finding_line(finding), _semantic_kind(finding) or "unknown")

    hardened.add_risk_sentinel_fallback_findings = lambda findings, risk_sentinels, config, unanchored_findings=None: _add_risk_sentinel_fallback_findings(hardened, original_rank, findings, risk_sentinels, config, unanchored_findings)

    review_quality_error = getattr(hardened, "ReviewQualityError", RuntimeError)

    def required_v4_enforce_risk_sentinel_findings(findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> None:
        findings[:] = hardened.add_risk_sentinel_fallback_findings(findings, risk_sentinels, config, unanchored_findings)
        uncovered = [sentinel for sentinel in hardened.required_risk_sentinels(risk_sentinels) if not any(_finding_covers_sentinel(finding, sentinel) for finding in findings)]
        if uncovered:
            digest = "; ".join(f"{getattr(s, 'path', '')}:{getattr(s, 'line', '')} {_sentinel_kind(s)}" for s in uncovered)
            raise review_quality_error(f"DCOIR Review quality failure: required changed-line signals remain uncovered after v4 refill: {digest}.")

    hardened.enforce_risk_sentinel_findings = required_v4_enforce_risk_sentinel_findings

    original_synthesize = getattr(module, "_dcoir_required_v4_original_synthesize_fix_for_finding", None)
    if original_synthesize is None:
        original_synthesize = getattr(module, "synthesize_fix_for_finding", None)
        module._dcoir_required_v4_original_synthesize_fix_for_finding = original_synthesize
    if callable(original_synthesize):
        module.synthesize_fix_for_finding = lambda index, finding, file_text, schema, config: _normalize_comment_finding(original_synthesize(index, finding, file_text, schema, config))

    if base is not None and callable(getattr(base, "build_inline_comment", None)):
        original_build = getattr(base, "_dcoir_required_v4_original_build_inline_comment", None)
        if original_build is None:
            original_build = base.build_inline_comment
            base._dcoir_required_v4_original_build_inline_comment = original_build

        def required_v4_build_inline_comment(finding: dict[str, Any], model_used: str, config: Any) -> str:
            normalized = _normalize_comment_finding(finding)
            kind = _semantic_kind(normalized)
            if kind in HARD_REQUIRED_KIND_TITLES or kind == YAML_METADATA_SHELL or _is_env_token_callback(normalized):
                try:
                    if callable(getattr(base, "emit_status", None)):
                        base.emit_status("required-v4-deterministic-comment", f"{normalized.get('path')}:{normalized.get('line')} {kind}")
                except Exception:
                    pass
                return _render_deterministic_comment(normalized, model_used)
            return _final_rendered_scrub(original_build(normalized, model_used, config), normalized)

        base.build_inline_comment = required_v4_build_inline_comment
