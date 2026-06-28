"""Required-coverage runtime patches for DCOIR Review.

This module runs after the broader runtime and strict fix-synthesis patches. It
keeps the final review output deterministic while tightening the places where
live testing still showed required findings could be crowded out or softened.
"""

from __future__ import annotations

import ast
import re
import shlex
from pathlib import Path
from typing import Any


CURL_SHELL_RE = re.compile(r"\b(?:curl|wget)\b[^\n]*(?:\|\s*(?:bash|sh)\b|\bbash\b|\bsh\b)", re.IGNORECASE)
GH_WRITE_PERMISSION_RE = re.compile(
    r"^\s*(?:permissions\s*:\s*write-all|"
    r"(?:actions|checks|contents|deployments|id-token|issues|packages|pull-requests|statuses)\s*:\s*write)\b",
    re.IGNORECASE,
)
GH_UNTRUSTED_CHECKOUT_RE = re.compile(r"github\.event\.pull_request\.head\.(?:ref|sha)|github\.head_ref", re.IGNORECASE)
PY_DYNAMIC_EXEC_RE = re.compile(r"\b(?:eval|exec)\s*\(")
PY_SHELL_EXEC_RE = re.compile(r"\bsubprocess\.\w+\([^#\n]*\bshell\s*=\s*True\b", re.IGNORECASE)
PY_SSRF_TOKEN_RE = re.compile(
    r"\b(?:requests\.(?:get|post|put|request)|urllib\.request\.(?:Request|urlopen)|httpx\.(?:get|post|request))\b|"
    r"\b(?:Authorization|Bearer|callback_url|callback|os\.environ|TOKEN|SECRET)\b",
    re.IGNORECASE,
)
PS_ACL_RE = re.compile(r"\b(?:FileSystemAccessRule|Set-Acl|Everyone|FullControl)\b", re.IGNORECASE)
PS_OUTBOUND_RE = re.compile(r"\b(?:Invoke-WebRequest|Invoke-RestMethod|iwr)\b|\b(?:Authorization|Bearer)\b", re.IGNORECASE)
INTERNAL_VALIDATION_RE = re.compile(
    r"(?:provider_pr_review|openrouter_pr_review|dcoir_review_.*selftest|reviewer runner selftest|run the relevant)",
    re.IGNORECASE,
)
HARDCODED_SECRET_RE = re.compile(r"\b(?:hard[- ]?coded|redacted)\s+(?:secret|token|credential|api key)\b", re.IGNORECASE)
REDACTED_SECRET_RE = re.compile(r"\[redacted[-_ ]?(?:secret|token|credential|api key)\]", re.IGNORECASE)
MARKDOWN_DUNDER_RE = re.compile(r"(?<![`\\])\b(__[A-Za-z][A-Za-z0-9_]*__)\b(?!`)")

YAML_REQUIRED_KIND_TITLES = {
    "yaml_pull_request_target": "Privileged `pull_request_target` workflow context",
    "yaml_broad_write": "GitHub Actions workflow grants write permissions",
    "yaml_untrusted_checkout": "Privileged workflow checks out untrusted PR code",
    "yaml_shell_pipe": "Workflow pipes a network installer into a shell",
}

YAML_SENTINEL_METADATA = {
    "yaml_pull_request_target": (
        "DCOIR YAML pull_request_target",
        "pull_request_target runs with base-repository privileges and must not execute untrusted PR code",
    ),
    "yaml_broad_write": (
        "DCOIR YAML broad write permission",
        "workflow token permissions grant write privileges and must be narrowed to required scopes",
    ),
    "yaml_untrusted_checkout": (
        "DCOIR YAML untrusted checkout ref",
        "privileged workflows must not check out PR-controlled refs or head SHAs before executing code",
    ),
    "yaml_shell_pipe": (
        "DCOIR YAML shell pipe installer",
        "network-fetched installer content is piped directly into a shell without pinning or verification",
    ),
}

COLLAPSE_TO_FILE_KINDS = {"python_ssrf", "ps_acl"}


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _clean_public_text(value: Any) -> str:
    text = str(value or "")
    text = "\n".join(line for line in text.splitlines() if "deterministic risk sentinel" not in line.lower())
    return MARKDOWN_DUNDER_RE.sub(r"`\1`", text.strip())


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


def _line_semantic_kind(path: str, text: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    normalized = _normalize(text)
    if suffix in {".yml", ".yaml"}:
        if "pull_request_target" in normalized:
            return "yaml_pull_request_target"
        if GH_WRITE_PERMISSION_RE.search(text):
            return "yaml_broad_write"
        if GH_UNTRUSTED_CHECKOUT_RE.search(text):
            return "yaml_untrusted_checkout"
        if CURL_SHELL_RE.search(text):
            return "yaml_shell_pipe"
    if suffix == ".py":
        if PY_SHELL_EXEC_RE.search(text):
            return "python_shell_exec"
        if "extractall" in normalized or "tarfile" in normalized or "shutil.unpack_archive" in normalized:
            return "python_archive_extract"
        if PY_SSRF_TOKEN_RE.search(text):
            return "python_ssrf"
        if PY_DYNAMIC_EXEC_RE.search(text):
            return "python_dynamic_exec"
        if "pickle.loads" in normalized or "pickle.load" in normalized:
            return "python_pickle"
        if "yaml.load" in normalized or "yaml.loader" in normalized:
            return "python_yaml_load"
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if "invoke-expression" in normalized:
            return "ps_dynamic_exec"
        if "expand-archive" in normalized:
            return "ps_archive_extract"
        if PS_ACL_RE.search(text):
            return "ps_acl"
        if PS_OUTBOUND_RE.search(text):
            return "ps_outbound_token"
        if "start-process" in normalized:
            return "ps_process_launch"
    if suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        if "exec(" in normalized or "execsync(" in normalized or "spawn(" in normalized:
            return "ts_command_exec"
    return ""


def _semantic_kind(finding: dict[str, Any]) -> str:
    path = str(finding.get("path", "") or "")
    anchored = str(finding.get("_anchored_line_text", "") or "")
    line_kind = _line_semantic_kind(path, anchored)
    if line_kind:
        return line_kind
    text = _finding_text(finding)
    suffix = Path(path.lower()).suffix
    if suffix in {".yml", ".yaml"}:
        if "shell pipe" in text or (("curl" in text or "wget" in text) and ("bash" in text or " sh" in text)):
            return "yaml_shell_pipe"
        if "untrusted checkout" in text or "github.event.pull_request.head" in text or "github.head_ref" in text or "head ref" in text or "head sha" in text:
            return "yaml_untrusted_checkout"
        if "write-all" in text or ("permissions" in text and "write" in text):
            return "yaml_broad_write"
        if "pull_request_target" in text:
            return "yaml_pull_request_target"
    if suffix == ".py":
        if "shell=true" in text or "shell true" in text or "subprocess" in text and "shell" in text:
            return "python_shell_exec"
        if "extractall" in text or "tarfile" in text or "archive extraction" in text:
            return "python_archive_extract"
        if "ssrf" in text or "callback" in text or "urlopen" in text or "authorization" in text or "bearer" in text or "token exfil" in text:
            return "python_ssrf"
        if "eval" in text or "exec" in text or "dynamic code" in text:
            return "python_dynamic_exec"
        if "pickle" in text:
            return "python_pickle"
        if "yaml.load" in text or "yaml.loader" in text:
            return "python_yaml_load"
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if "invoke-expression" in text:
            return "ps_dynamic_exec"
        if "expand-archive" in text:
            return "ps_archive_extract"
        if "acl" in text or "everyone" in text or "fullcontrol" in text or "set-acl" in text:
            return "ps_acl"
        if "invoke-webrequest" in text or "invoke-restmethod" in text or "bearer" in text:
            return "ps_outbound_token"
        if "start-process" in text:
            return "ps_process_launch"
    return ""


def _sentinel_kind(sentinel: Any) -> str:
    path = str(getattr(sentinel, "path", "") or "")
    text = str(getattr(sentinel, "text", "") or "")
    line_kind = _line_semantic_kind(path, text)
    if line_kind:
        return line_kind
    label = _normalize(getattr(sentinel, "label", ""))
    detail = _normalize(getattr(sentinel, "detail", ""))
    combined = f"{label}\n{detail}\n{_normalize(text)}"
    if "shell pipe" in combined or "curl" in combined and ("bash" in combined or " sh" in combined):
        return "yaml_shell_pipe"
    if "untrusted checkout" in combined or "head ref" in combined or "head sha" in combined or "github.event.pull_request.head" in combined:
        return "yaml_untrusted_checkout"
    if "broad write" in combined or "write permission" in combined or "write-all" in combined:
        return "yaml_broad_write"
    if "pull_request_target" in combined:
        return "yaml_pull_request_target"
    return _semantic_kind({"path": path, "title": combined, "body": combined})


def _candidate_kind(candidate: Any) -> str:
    return _line_semantic_kind(str(getattr(candidate, "path", "") or ""), str(getattr(candidate, "text", "") or ""))


def _make_yaml_sentinels(hardened: Any, diff: str) -> list[Any]:
    sentinels: list[Any] = []
    seen: set[tuple[str, int, str]] = set()
    iter_added = getattr(hardened, "iter_added_diff_lines", None)
    if not callable(iter_added):
        return sentinels
    risk_sentinel_type = getattr(hardened, "RiskSentinel", None)
    if risk_sentinel_type is None:
        return sentinels
    for changed_line in iter_added(diff):
        path = str(getattr(changed_line, "path", "") or "")
        text = str(getattr(changed_line, "text", "") or "")
        if Path(path.lower()).suffix not in {".yml", ".yaml"}:
            continue
        if callable(getattr(hardened, "is_comment_only_added_line", None)) and hardened.is_comment_only_added_line(path, text):
            continue
        kind = _line_semantic_kind(path, text)
        if kind not in YAML_SENTINEL_METADATA:
            continue
        try:
            line = int(getattr(changed_line, "line", 0) or 0)
        except (TypeError, ValueError):
            continue
        key = (path, line, kind)
        if key in seen:
            continue
        seen.add(key)
        label, detail = YAML_SENTINEL_METADATA[kind]
        sentinels.append(risk_sentinel_type(path=path, line=line, label=label, detail=detail, text=text))
    return sentinels


def _dedupe_sentinels(sentinels: list[Any]) -> list[Any]:
    deduped: list[Any] = []
    seen: set[tuple[str, int, str]] = set()
    for sentinel in sentinels:
        try:
            line = int(getattr(sentinel, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        key = (str(getattr(sentinel, "path", "") or ""), line, _sentinel_kind(sentinel) or str(getattr(sentinel, "label", "") or ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sentinel)
    return deduped


def _select_sentinels(hardened: Any, sentinels: list[Any], max_anchors: int | None) -> list[Any]:
    deduped = _dedupe_sentinels(sentinels)
    if max_anchors is None or len(deduped) <= max_anchors:
        return deduped
    if max_anchors <= 0:
        return []
    required_yaml = [sentinel for sentinel in deduped if _sentinel_kind(sentinel) in YAML_REQUIRED_KIND_TITLES]
    selected: list[Any] = []
    seen: set[tuple[str, int, str]] = set()

    def add(item: Any) -> None:
        try:
            line = int(getattr(item, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        key = (str(getattr(item, "path", "") or ""), line, _sentinel_kind(item) or str(getattr(item, "label", "") or ""))
        if key not in seen and len(selected) < max_anchors:
            seen.add(key)
            selected.append(item)

    for sentinel in required_yaml:
        add(sentinel)
    remaining = [sentinel for sentinel in deduped if sentinel not in selected]
    original_select = getattr(hardened, "_dcoir_required_original_select_risk_sentinels", None)
    if not callable(original_select):
        original_select = getattr(hardened, "select_risk_sentinels", None)
    if callable(original_select):
        remaining = original_select(remaining, max_anchors - len(selected))
    for sentinel in remaining:
        add(sentinel)
    return selected


def _yaml_fallback_body(kind: str, sentinel: Any) -> str:
    changed = str(getattr(sentinel, "text", "") or "").strip()
    if kind == "yaml_pull_request_target":
        return "`pull_request_target` runs with base-repository privileges. Do not execute untrusted pull request code in this context."
    if kind == "yaml_broad_write":
        return "This workflow grants broad write permissions. Narrow the token permissions to the minimum scopes needed."
    if kind == "yaml_untrusted_checkout":
        return "This privileged workflow checks out pull request controlled code. Use an unprivileged event, avoid checking out PR head refs in privileged jobs, or split trusted labeling from untrusted code execution."
    if kind == "yaml_shell_pipe":
        return f"This workflow pipes network-fetched content into a shell: `{changed}`. Download a pinned artifact, verify its checksum or signature, then execute only verified content."
    return "Review this GitHub Actions security boundary before merging."


def _validation_for_path(path: str, kind: str = "") -> str:
    lower_path = path.lower()
    quoted = shlex.quote(path)
    if lower_path.endswith(".py"):
        return f"python3 -m py_compile {quoted}"
    if lower_path.endswith((".ps1", ".psm1", ".psd1")):
        ps_path = "'" + path.replace("'", "''") + "'"
        return (
            "pwsh -NoProfile -Command \"$errors=$null; "
            f"[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw -LiteralPath {ps_path}), [ref]$errors) | Out-Null; "
            "if ($errors) { throw ($errors | Out-String) }\""
        )
    if lower_path.endswith((".yml", ".yaml")):
        assertions = ["assert path.exists(), path"]
        if kind == "yaml_pull_request_target":
            assertions.append("assert 'pull_request_target' not in text")
        elif kind == "yaml_broad_write":
            assertions.append("assert 'write-all' not in text and ': write' not in text")
        elif kind == "yaml_untrusted_checkout":
            assertions.append("assert 'github.event.pull_request.head' not in text and 'github.head_ref' not in text")
        elif kind == "yaml_shell_pipe":
            assertions.append("assert '| bash' not in text and '| sh' not in text")
        else:
            assertions.append("assert text.strip()")
        body = "\n".join(assertions)
        return f"python3 - <<'PY'\nfrom pathlib import Path\npath = Path({path!r})\ntext = path.read_text(encoding='utf-8')\n{body}\nPY"
    if lower_path.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
        return f"npx tsc --noEmit --pretty false  # include {quoted} in the nearest project tsconfig"
    return f"Run the nearest syntax/static check for {quoted} and a focused test for the changed behavior."


def _validation_needs_replacement(validation: str, path: str) -> bool:
    if not validation.strip():
        return True
    if INTERNAL_VALIDATION_RE.search(validation) and not path.startswith("scripts/"):
        return True
    return False


def _normalize_token_hallucinations(value: str) -> str:
    value = REDACTED_SECRET_RE.sub("the environment token value", value)
    value = HARDCODED_SECRET_RE.sub("environment token value", value)
    lines = [line for line in value.splitlines() if "syntax error" not in line.lower()]
    return "\n".join(lines).strip()


def _normalize_comment_finding(finding: dict[str, Any]) -> dict[str, Any]:
    item = dict(finding)
    kind = _semantic_kind(item)
    title = _clean_public_text(item.get("title", "") or "Finding").replace("Deterministic risk sentinel:", "").strip()
    if kind in YAML_REQUIRED_KIND_TITLES:
        title = YAML_REQUIRED_KIND_TITLES[kind]
    item["title"] = title or "Finding"
    body = _clean_public_text(item.get("body", ""))
    if kind == "python_ssrf":
        body = _normalize_token_hallucinations(body)
    item["body"] = body
    validation = _clean_public_text(item.get("validation", ""))
    if _validation_needs_replacement(validation, str(item.get("path", "") or "")):
        validation = _validation_for_path(str(item.get("path", "") or ""), kind)
    item["validation"] = validation
    guidance = item.get("fix_guidance") if isinstance(item.get("fix_guidance"), dict) else {}
    if guidance:
        cleaned_guidance = dict(guidance)
        notes = _clean_public_text(cleaned_guidance.get("notes", ""))
        if kind == "python_ssrf":
            notes = _normalize_token_hallucinations(notes)
        if notes:
            cleaned_guidance["notes"] = notes
        item["fix_guidance"] = cleaned_guidance
    return item


def _dedupe_line_key(kind: str, finding: dict[str, Any]) -> str:
    if kind in COLLAPSE_TO_FILE_KINDS:
        return ""
    return str(finding.get("line", "") or "").strip()


def _dedupe_key(finding: dict[str, Any]) -> tuple[str, str, str, str]:
    kind = _semantic_kind(finding)
    path = str(finding.get("path", "") or "").strip()
    if kind:
        return (path, _dedupe_line_key(kind, finding), kind, "")
    return (
        path,
        str(finding.get("line", "") or "").strip(),
        _normalize(finding.get("title", ""))[:120],
        _normalize(finding.get("body", ""))[:120],
    )


def _finding_quality_score(hardened: Any, finding: dict[str, Any]) -> tuple[int, float, int]:
    scorer = getattr(hardened, "finding_quality_score", None)
    if callable(scorer):
        return scorer(finding)
    try:
        confidence = float(finding.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    severity = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(str(finding.get("severity", "")).lower(), 0)
    return severity, confidence, len(str(finding.get("body", "") or ""))


def _dedupe_findings(hardened: Any, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str, str]] = []
    for finding in findings:
        key = _dedupe_key(finding)
        if key not in by_key:
            by_key[key] = finding
            order.append(key)
            continue
        if _finding_quality_score(hardened, finding) >= _finding_quality_score(hardened, by_key[key]):
            by_key[key] = finding
    return [by_key[key] for key in order]
