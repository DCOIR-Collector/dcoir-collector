"""Fifth required-coverage layer for DCOIR Review.

This layer fixes the PR #328 failure mode: valid model findings existed under
``result.findings``, but final required-coverage/refill logic rejected several
required sentinel classes and aborted before posting inline review comments.

The patch keeps model review and Markdown rendering deterministic by enforcing a
single required-signal contract keyed by path, right-side line, and semantic kind.
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import dcoir_review_required_runtime_patch_v4 as v4

PYTHON_YAML_LOAD = v4.PYTHON_YAML_LOAD
PYTHON_SHELL_EXEC = v4.PYTHON_SHELL_EXEC
PYTHON_ENV_TOKEN = "python_env_token_callback"
PS_ENV_TOKEN = "ps_env_token_callback"

REQUIRED_KIND_TITLES = {
    **v4.HARD_REQUIRED_KIND_TITLES,
    v4.YAML_METADATA_SHELL: "Workflow executes pull request metadata in a shell",
    PYTHON_YAML_LOAD: "Unsafe YAML deserialization with `yaml.Loader`",
    PYTHON_SHELL_EXEC: "Python shell execution with caller-controlled command",
    PYTHON_ENV_TOKEN: "Environment token forwarded to request-controlled callback",
    PS_ENV_TOKEN: "Environment token forwarded to request-controlled callback",
}
REQUIRED_KIND_ORDER = (
    v4.YAML_PULL_REQUEST_TARGET,
    v4.YAML_BROAD_WRITE,
    v4.YAML_UNTRUSTED_CHECKOUT,
    v4.YAML_SHELL_PIPE,
    v4.YAML_METADATA_SHELL,
    v4.PS_ACL,
    v4.PS_PROCESS_LAUNCH,
    PS_ENV_TOKEN,
    PYTHON_YAML_LOAD,
    PYTHON_SHELL_EXEC,
    PYTHON_ENV_TOKEN,
)
RANK_KIND_ORDER = (
    *REQUIRED_KIND_ORDER,
    "python_dynamic_exec",
    "python_pickle",
    "python_archive_extract",
    "python_ssrf",
    "ps_dynamic_exec",
    "ps_archive_extract",
    "ps_outbound_token",
)

PY_YAML_LOAD_RE = re.compile(r"\byaml\.load\s*\([^\n]*(?:Loader\s*=\s*yaml\.Loader|yaml\.Loader)", re.IGNORECASE)
PY_SHELL_EXEC_RE = re.compile(r"\bsubprocess\.(?:Popen|run|call|check_call|check_output)\s*\([^\n]*shell\s*=\s*True", re.IGNORECASE)
PY_ENV_RE = re.compile(r"\b(?:os\.environ|os\.getenv)\b|DCOIR_TOKEN", re.IGNORECASE)
PS_ENV_RE = re.compile(r"\$env:|DCOIR_TOKEN|Environment::GetEnvironmentVariable", re.IGNORECASE)
OUTBOUND_RE = re.compile(r"callback|Authorization|Bearer|Invoke-WebRequest|Invoke-RestMethod|requests\.|urlopen|urllib\.request", re.IGNORECASE)
TOKEN_BAD_RE = re.compile(r"\b(?:hard[- ]?coded|literal|redacted|static credential|secret exposure|inline secret|rotate exposed credential|authentication secrets|hardcoded bearer|bearer token hardcoded)\b", re.IGNORECASE)
COMMAND_START_RE = re.compile(r"^\s*(?:python3?|pytest|bandit|pwsh|powershell|grep|rg|yamllint|npm|npx|node|bash|sh)\b")


def _normalize(value: Any) -> str:
    return v4._normalize(value)


def findings_from_result(result: Any) -> list[dict[str, Any]]:
    """Return findings from either top-level findings or nested result.findings."""
    if not isinstance(result, dict):
        return []
    nested = result.get("result")
    if isinstance(nested, dict) and isinstance(nested.get("findings"), list):
        return [finding for finding in nested["findings"] if isinstance(finding, dict)]
    if isinstance(result.get("findings"), list):
        return [finding for finding in result["findings"] if isinstance(finding, dict)]
    return []


def _line_kind(path: str, text: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    line = str(text or "")
    if suffix == ".py":
        if PY_YAML_LOAD_RE.search(line):
            return PYTHON_YAML_LOAD
        if PY_SHELL_EXEC_RE.search(line):
            return PYTHON_SHELL_EXEC
        if PY_ENV_RE.search(line) and OUTBOUND_RE.search(line):
            return PYTHON_ENV_TOKEN
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if PS_ENV_RE.search(line) and OUTBOUND_RE.search(line):
            return PS_ENV_TOKEN
    return v4._line_kind(path, text)


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
    if suffix == ".py":
        if "yaml.load" in text or "yaml.loader" in text:
            return PYTHON_YAML_LOAD
        if "shell=true" in text or ("subprocess" in text and "shell" in text):
            return PYTHON_SHELL_EXEC
        if ("os.getenv" in text or "os.environ" in text or "dcoir_token" in text) and ("callback" in text or "authorization" in text or "urlopen" in text):
            return PYTHON_ENV_TOKEN
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if ("$env:" in text or "dcoir_token" in text) and ("invoke-webrequest" in text or "invoke-restmethod" in text or "authorization" in text or "callback" in text):
            return PS_ENV_TOKEN
    return v4._semantic_kind(finding)


def _sentinel_kind(sentinel: Any) -> str:
    path = str(getattr(sentinel, "path", "") or "")
    text = str(getattr(sentinel, "text", "") or "")
    line_kind = _line_kind(path, text)
    if line_kind:
        return line_kind
    label_text = _normalize("\n".join(str(getattr(sentinel, key, "") or "") for key in ("label", "detail", "text")))
    if "python" in path.lower():
        if "unsafe deserialization" in label_text or "yaml.loader" in label_text:
            return PYTHON_YAML_LOAD
        if "shell=true" in label_text or "subprocess" in label_text:
            return PYTHON_SHELL_EXEC
    if "metadata" in label_text and "shell" in label_text:
        return v4.YAML_METADATA_SHELL
    return v4._sentinel_kind(sentinel)


def _sentinel_line(sentinel: Any) -> int:
    return v4._sentinel_line(sentinel)


def _finding_line(finding: dict[str, Any]) -> int:
    return v4._finding_line(finding)


def _is_env_kind(kind: str) -> bool:
    return kind in {PYTHON_ENV_TOKEN, PS_ENV_TOKEN, v4.PYTHON_SSRF, v4.PS_OUTBOUND_TOKEN}


def _validation_for_path(path: str, kind: str) -> str:
    lower = str(path or "").lower()
    if lower.endswith(".py"):
        return f"python3 -m py_compile {shlex.quote(str(path or ''))}"
    return v4._validation_for_path(path, kind)


def _template_fields(kind: str, path: str, line_text: str) -> dict[str, Any]:
    if kind in v4.HARD_REQUIRED_KIND_TITLES or kind == v4.YAML_METADATA_SHELL:
        return v4._template_fields(kind, path, line_text)
    notes = {
        PYTHON_YAML_LOAD: "Use `yaml.safe_load(profile_text)` or `yaml.load(..., Loader=yaml.SafeLoader)` when no Python object tags are expected.",
        PYTHON_SHELL_EXEC: "Pass an argument list to `subprocess` with `shell=False`; do not send caller-controlled strings through a shell.",
        PYTHON_ENV_TOKEN: "Keep the token server-side and allowlist callback destinations before adding authorization headers.",
        PS_ENV_TOKEN: "Keep the token server-side and allowlist callback destinations before adding authorization headers.",
    }
    bodies = {
        PYTHON_YAML_LOAD: "This line deserializes YAML with `yaml.Loader`, which can construct unsafe Python objects from untrusted input.",
        PYTHON_SHELL_EXEC: "This line invokes a system shell with caller-controlled command text. Use argument-vector execution without `shell=True`.",
        PYTHON_ENV_TOKEN: "Environment token read from env and forwarded to request-controlled callback. Keep collector tokens server-side and allowlist outbound destinations before sending authorization headers.",
        PS_ENV_TOKEN: "Environment token read from env and forwarded to request-controlled callback. Keep collector tokens server-side and allowlist outbound destinations before sending authorization headers.",
    }
    return {
        "title": REQUIRED_KIND_TITLES.get(kind, "Required DCOIR Review finding"),
        "body": bodies.get(kind, "Review this changed line before merging."),
        "validation": _validation_for_path(path, kind),
        "suggested_replacement": "",
        "fix_guidance": {"language": v4._language_hint(path), "notes": notes.get(kind, "Apply a minimal, evidence-backed fix.")},
    }


def _normalize_comment_finding(finding: dict[str, Any]) -> dict[str, Any]:
    item = v4._normalize_comment_finding(finding)
    if finding.get("_anchored_line_text") and not item.get("_anchored_line_text"):
        item["_anchored_line_text"] = finding.get("_anchored_line_text")
    kind = _semantic_kind(item)
    path = str(item.get("path", "") or "")
    line_text = str(item.get("_anchored_line_text", "") or "")
    if kind in REQUIRED_KIND_TITLES:
        item.update(_template_fields(kind, path, line_text))
    if _is_env_kind(kind):
        item["title"] = "Environment token forwarded to request-controlled callback"
        item["body"] = "Environment token read from env and forwarded to request-controlled callback. Keep collector tokens server-side and allowlist outbound destinations before sending authorization headers."
        item["suggested_replacement"] = ""
        item["fix_guidance"] = {
            "language": v4._language_hint(path),
            "notes": "Keep the token on the trusted side of the boundary and validate the callback destination against an allowlist before any request is made.",
        }
    return item


def _coverage_line(kind: str, finding_line: int, sentinel_line: int) -> bool:
    if finding_line <= 0 or sentinel_line <= 0:
        return False
    if kind == v4.PS_ACL:
        return abs(finding_line - sentinel_line) <= 4
    return finding_line == sentinel_line


def finding_covers_sentinel(finding: dict[str, Any], sentinel: Any, original_covers: Any | None = None) -> bool:
    kind = _sentinel_kind(sentinel)
    normalized = _normalize_comment_finding(finding)
    if kind in REQUIRED_KIND_TITLES:
        return (
            str(normalized.get("path", "") or "") == str(getattr(sentinel, "path", "") or "")
            and _semantic_kind(normalized) == kind
            and _coverage_line(kind, _finding_line(normalized), _sentinel_line(sentinel))
        )
    if callable(original_covers):
        return bool(original_covers(finding, sentinel))
    return False


def _dedupe_key(finding: dict[str, Any]) -> tuple[str, int, str, str]:
    normalized = _normalize_comment_finding(finding)
    kind = _semantic_kind(normalized)
    return (
        str(normalized.get("path", "") or ""),
        _finding_line(normalized),
        kind or str(normalized.get("title", "") or ""),
        _normalize(normalized.get("_anchored_line_text", "")),
    )


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
        if hasattr(hardened, "severity_sort_key"):
            by_key[key] = normalized
    return [by_key[key] for key in order]


def _rank_findings(module: Any, hardened: Any, original_rank: Any, findings: list[dict[str, Any]], config: Any) -> list[dict[str, Any]]:
    max_inline = max(0, int(getattr(config, "max_inline_comments", 12)))
    ranked_source = _dedupe_findings(hardened, findings)
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


def _required_sentinels(original_required: Any, sentinels: list[Any]) -> list[Any]:
    combined = list(original_required(sentinels)) if callable(original_required) else []
    combined.extend(sentinel for sentinel in sentinels if _sentinel_kind(sentinel) in REQUIRED_KIND_TITLES)
    seen: set[tuple[str, int, str]] = set()
    result: list[Any] = []
    for sentinel in combined:
        key = (str(getattr(sentinel, "path", "") or ""), _sentinel_line(sentinel), _sentinel_kind(sentinel))
        if key in seen:
            continue
        seen.add(key)
        result.append(sentinel)
    return result


def _fallback_finding(sentinel: Any, config: Any, original_fallback: Any | None = None) -> dict[str, Any]:
    kind = _sentinel_kind(sentinel)
    if kind in REQUIRED_KIND_TITLES:
        path = str(getattr(sentinel, "path", "") or "")
        line_text = str(getattr(sentinel, "text", "") or "")
        finding = {
            "severity": "critical" if kind in {v4.YAML_PULL_REQUEST_TARGET, v4.YAML_SHELL_PIPE, v4.PS_PROCESS_LAUNCH, PYTHON_YAML_LOAD, PYTHON_SHELL_EXEC} else "high",
            "confidence": 0.99,
            "path": path,
            "line": _sentinel_line(sentinel),
            "_anchored_line_text": line_text,
        }
        finding.update(_template_fields(kind, path, line_text))
        return finding
    if callable(original_fallback):
        result = original_fallback(sentinel, config)
        return result if isinstance(result, dict) else {}
    return {}


def add_risk_sentinel_fallback_findings(hardened: Any, original_rank: Any, original_covers: Any, original_fallback: Any, findings: list[dict[str, Any]], risk_sentinels: list[Any], config: Any, unanchored_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    required_sentinels = hardened.required_risk_sentinels(risk_sentinels)
    normalized_findings = _dedupe_findings(hardened, findings)
    coverage_pool = [*normalized_findings, *(_dedupe_findings(hardened, unanchored_findings or []) if unanchored_findings else [])]
    uncovered = [
        sentinel
        for sentinel in required_sentinels
        if not any(finding_covers_sentinel(finding, sentinel, original_covers) for finding in coverage_pool)
    ]
    fallbacks = [_fallback_finding(sentinel, config, original_fallback) for sentinel in uncovered]
    fallbacks = [finding for finding in fallbacks if finding]
    inline_limit = max(0, int(getattr(config, "max_inline_comments", 12)))
    existing_budget = max(0, inline_limit - len(fallbacks))
    existing = _rank_findings(None, hardened, original_rank, normalized_findings, config)[:existing_budget]
    return _rank_findings(None, hardened, None, [*existing, *fallbacks], config)[:inline_limit]


def final_rendered_scrub(comment: str, finding: dict[str, Any]) -> str:
    text = v4._final_rendered_scrub(comment, finding)
    if _is_env_kind(_semantic_kind(finding)):
        text = TOKEN_BAD_RE.sub("environment token", text)
        text = text.replace("environment token value", "environment token")
    return text
