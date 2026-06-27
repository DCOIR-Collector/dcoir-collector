"""Strict runtime patches for DCOIR Review fix synthesis and required YAML coverage."""

from __future__ import annotations

import ast
import json
import re
import textwrap
from pathlib import Path
from typing import Any


NATURAL_LANGUAGE_START_RE = re.compile(
    r"^\s*(?:"
    r"the\s+entire|if\s+a\s+|if\s+an\s+|when\s+|because\s+|use\s+|using\s+|"
    r"replace\s+|remove\s+|delete\s+|add\s+|ensure\s+|validate\s+|"
    r"no\s+replacement|a\s+complete|repair\s+steps|fixing\s+"
    r")\b",
    re.IGNORECASE,
)
NATURAL_LANGUAGE_WORD_RE = re.compile(
    r"\b(?:the|this|that|with|without|because|function|entire|required|"
    r"governed|evaluator|parser|allowlist|validates|before|after|safe|unsafe|"
    r"must|should|would|could|repair|fix|line|lines)\b",
    re.IGNORECASE,
)
FENCE_LINE_RE = re.compile(r"^\s*(?:```|~~~)")
YAML_CODE_RE = re.compile(r"(?m)^\s*(?:[-?]\s+)?[A-Za-z0-9_.${}/ -]+\s*:")
POWERSHELL_CODE_RE = re.compile(
    r"^\s*(?:#|param\s*\(|function\s+[A-Za-z_][A-Za-z0-9_-]*\b|"
    r"\$[A-Za-z_][A-Za-z0-9_]*\b|[A-Za-z]+-[A-Za-z]+(?:\s|$)|"
    r"(?:if|foreach|for|while|try|catch|finally)\s*(?:\(|\{))",
    re.IGNORECASE,
)
JS_TS_CODE_RE = re.compile(
    r"^\s*(?:const|let|var|return|if|for|while|throw|await|import|export|"
    r"[A-Za-z_][A-Za-z0-9_]*\s*(?:=|=>|\())\b",
)
PYTHON_DYNAMIC_EXEC_CALL_RE = re.compile(r"\b(?:eval|exec)\s*\(")
CURL_SHELL_RE = re.compile(r"\b(?:curl|wget)\b[^\n]*(?:\|\s*(?:bash|sh)\b|bash\b|sh\b)", re.IGNORECASE)
GH_WRITE_PERMISSION_RE = re.compile(
    r"^\s*(?:permissions\s*:\s*write-all|"
    r"(?:actions|checks|contents|deployments|id-token|issues|packages|pull-requests|statuses)\s*:\s*write)\b",
    re.IGNORECASE,
)
INTERNAL_LINE_RE = re.compile(r"deterministic risk sentinel", re.IGNORECASE)
MARKDOWN_DUNDER_RE = re.compile(r"(?<![`\\])\b(__[A-Za-z][A-Za-z0-9_]*__)\b(?!`)")

STRICT_FIX_SYNTHESIS_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "DCOIR Review Strict Fix Synthesis",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "suggested_replacement",
        "remove_code",
        "replace_code",
        "add_code",
        "notes",
        "validation",
        "language",
        "start_line",
        "end_line",
    ],
    "properties": {
        "suggested_replacement": {
            "type": "string",
            "description": "Exact single-line replacement code for the anchored GitHub review line only, or empty.",
        },
        "remove_code": {
            "type": "string",
            "description": "Exact code/config text copied from the file that should be removed. Empty if not exact.",
        },
        "replace_code": {
            "type": "string",
            "description": "Exact replacement code/config only. Empty if conceptual or uncertain.",
        },
        "add_code": {
            "type": "string",
            "description": "Exact code/config to add only. Empty if conceptual or uncertain.",
        },
        "notes": {
            "type": "string",
            "description": "All prose guidance, caveats, and multi-line repair explanation.",
        },
        "validation": {
            "type": "string",
            "description": "Exact validation command or commands only.",
        },
        "language": {"type": "string"},
        "start_line": {"type": "integer"},
        "end_line": {"type": "integer"},
    },
}

YAML_REQUIRED_KIND_TITLES = {
    "yaml_pull_request_target": "Privileged `pull_request_target` workflow context",
    "yaml_broad_write": "GitHub Actions workflow grants write permissions",
    "yaml_untrusted_checkout": "Privileged workflow checks out untrusted PR code",
    "yaml_shell_pipe": "Workflow pipes a network installer into a shell",
}


def _strip_fences(value: Any) -> str:
    lines: list[str] = []
    for line in str(value or "").splitlines():
        if FENCE_LINE_RE.match(line):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def _clean_public_text(value: str) -> str:
    lines = [line for line in str(value or "").splitlines() if not INTERNAL_LINE_RE.search(line)]
    return MARKDOWN_DUNDER_RE.sub(r"`\1`", "\n".join(lines).strip())


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _language_hint(path: str) -> str:
    suffix = Path(str(path or "").lower()).suffix
    return {
        ".bash": "bash",
        ".cjs": "javascript",
        ".js": "javascript",
        ".json": "json",
        ".mjs": "javascript",
        ".ps1": "powershell",
        ".psd1": "powershell",
        ".psm1": "powershell",
        ".py": "python",
        ".sh": "bash",
        ".ts": "typescript",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix, "text")


def _finding_text(finding: dict[str, Any]) -> str:
    parts = [
        str(finding.get("title", "") or ""),
        str(finding.get("body", "") or ""),
        str(finding.get("validation", "") or ""),
    ]
    guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    parts.extend(str(guidance.get(key, "") or "") for key in ("remove", "replace", "add", "notes"))
    return _normalize("\n".join(parts))


def _semantic_kind(finding: dict[str, Any]) -> str:
    path = str(finding.get("path", "") or "").strip().lower()
    suffix = Path(path).suffix
    text = _finding_text(finding)
    if suffix == ".py":
        if "extractall" in text or "tarfile" in text or "archive extraction" in text:
            return "python_archive_extract"
        if "requests." in text or "ssrf" in text or "callback" in text:
            return "python_ssrf"
        if PYTHON_DYNAMIC_EXEC_CALL_RE.search(text) or "dynamic code execution" in text:
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
        if "invoke-webrequest" in text or "invoke-restmethod" in text or "bearer" in text:
            return "ps_outbound_token"
    if suffix in {".yml", ".yaml"}:
        if "pull_request_target" in text:
            return "yaml_pull_request_target"
        if "github.head_ref" in text or "github.event.pull_request.head" in text or "untrusted checkout" in text:
            return "yaml_untrusted_checkout"
        if ("curl" in text or "wget" in text) and ("|" in text or "pipe" in text) and ("bash" in text or " sh" in text):
            return "yaml_shell_pipe"
        if "write-all" in text or ("permissions" in text and "write" in text):
            return "yaml_broad_write"
    return ""


def _sentinel_kind(sentinel: Any) -> str:
    text = _normalize(
        "\n".join(
            [
                str(getattr(sentinel, "label", "") or ""),
                str(getattr(sentinel, "detail", "") or ""),
                str(getattr(sentinel, "text", "") or ""),
            ]
        )
    )
    path = str(getattr(sentinel, "path", "") or "")
    return _semantic_kind({"path": path, "title": text, "body": text})


def _candidate_kind(candidate: Any) -> str:
    text = str(getattr(candidate, "text", "") or "")
    path = str(getattr(candidate, "path", "") or "")
    normalized = _normalize(text)
    if "pull_request_target" in normalized:
        return "yaml_pull_request_target"
    if GH_WRITE_PERMISSION_RE.search(text):
        return "yaml_broad_write"
    if "github.event.pull_request.head" in normalized or "github.head_ref" in normalized:
        return "yaml_untrusted_checkout"
    if CURL_SHELL_RE.search(text):
        return "yaml_shell_pipe"
    if "extractall" in normalized:
        return "python_archive_extract"
    return _semantic_kind({"path": path, "title": normalized, "body": normalized})


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
        ast.parse(textwrap.dedent(value).strip() + "\n")
        return True
    except SyntaxError:
        return False


def _powershell_is_code(value: str) -> bool:
    lines = [line for line in value.splitlines() if line.strip()]
    return bool(lines) and all(POWERSHELL_CODE_RE.match(line) or line.strip() in {"}", "};"} for line in lines)


def _yaml_is_code(value: str) -> bool:
    lines = [line for line in value.splitlines() if line.strip()]
    return bool(lines) and any(YAML_CODE_RE.match(line) for line in lines) and not _is_natural_language(value)


def _js_ts_is_code(value: str) -> bool:
    lines = [line for line in value.splitlines() if line.strip()]
    return bool(lines) and any(JS_TS_CODE_RE.match(line) for line in lines) and not _is_natural_language(value)


def _strict_code_value_is_valid(value: Any, language: str) -> bool:
    text = _strip_fences(value)
    if not text or _is_natural_language(text):
        return False
    language = str(language or "").lower()
    if language == "python":
        return _python_is_code(text)
    if language == "powershell":
        return _powershell_is_code(text)
    if language in {"yaml", "json"}:
        return _yaml_is_code(text)
    if language in {"typescript", "javascript"}:
        return _js_ts_is_code(text)
    return not _is_natural_language(text) and any(signal in text for signal in ("=", "$", ":", "(", "{", "|", ";"))


def _code_field_invalid(result: dict[str, Any], path: str) -> bool:
    language = str(result.get("language") or _language_hint(path)).lower()
    for key in ("remove_code", "replace_code", "add_code"):
        value = _strip_fences(result.get(key, ""))
        if value and not _strict_code_value_is_valid(value, language):
            return True
    return False


def _strict_fix_guidance(result: dict[str, Any], finding: dict[str, Any], path: str) -> dict[str, str]:
    language = str(result.get("language") or _language_hint(path)).lower()
    guidance: dict[str, str] = {"language": language}
    notes: list[str] = []
    for result_key, guidance_key in (
        ("remove_code", "remove"),
        ("replace_code", "replace"),
        ("add_code", "add"),
        ("remove", "remove"),
        ("replace", "replace"),
        ("add", "add"),
    ):
        value = _strip_fences(result.get(result_key, ""))
        if not value:
            continue
        if _strict_code_value_is_valid(value, language):
            guidance[guidance_key] = value
        else:
            notes.append(value)
    raw_notes = _clean_public_text(str(result.get("notes", "") or ""))
    if raw_notes:
        notes.append(raw_notes)
    kind = _semantic_kind({**finding, "path": path})
    if kind == "python_ssrf":
        notes = [
            re.sub(r"\bhardcoded secret\b", "secret or token value", note, flags=re.IGNORECASE)
            for note in notes
            if "syntax error" not in note.lower()
        ]
    cleaned_notes: list[str] = []
    seen: set[str] = set()
    for note in notes:
        cleaned = _clean_public_text(note)
        key = _normalize(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            cleaned_notes.append(cleaned)
    if cleaned_notes:
        guidance["notes"] = "\n\n".join(cleaned_notes)
    return guidance if any(key in guidance for key in ("remove", "replace", "add", "notes")) else {}


def _normalize_existing_fix_guidance(finding: dict[str, Any]) -> dict[str, str]:
    path = str(finding.get("path", "") or "")
    raw = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    if not raw:
        return {}
    language = str(raw.get("language") or _language_hint(path)).lower()
    synthetic = {
        "language": language,
        "remove_code": raw.get("remove", ""),
        "replace_code": raw.get("replace", ""),
        "add_code": raw.get("add", ""),
        "notes": raw.get("notes", ""),
    }
    return _strict_fix_guidance(synthetic, finding, path)


def _build_strict_fix_synthesis_prompt(
    base: Any,
    finding: dict[str, Any],
    path: str,
    line: int,
    line_text: str,
    file_text: str,
    config: Any,
) -> str:
    max_file_chars = max(0, int(getattr(config, "per_file_review_max_file_chars", getattr(config, "deep_review_max_file_chars", 12000))))
    visible_text = base.sanitize_text(file_text, config)
    if len(visible_text) > max_file_chars:
        visible_text = f"{visible_text[:max_file_chars]}\n\n[full-file context truncated for fix synthesis]"
    language = _language_hint(path)
    finding_payload = json.dumps(
        {
            "title": finding.get("title", ""),
            "severity": finding.get("severity", ""),
            "confidence": finding.get("confidence", 0),
            "path": path,
            "line": line,
            "body": finding.get("body", ""),
            "validation": finding.get("validation", ""),
        },
        ensure_ascii=False,
        indent=2,
    )
    prompt = f"""
Strict fix synthesis pass for one already-detected DCOIR Review finding.

Return JSON matching the schema exactly. Do not return Markdown.

Field rules:
- suggested_replacement: exact single-line replacement code for the anchored GitHub review line only, or empty.
- remove_code: exact code/config text copied from this file that should be removed, or empty.
- replace_code: exact replacement code/config only, or empty.
- add_code: exact code/config to add only, or empty.
- notes: all prose guidance, caveats, rationale, multi-line conceptual repair steps, and any explanation.
- validation: exact validation command(s) only.
- language: the code fence language for exact code/config fields.
- start_line/end_line: the affected file line range when known; otherwise both equal the anchored line.

Hard constraints:
- Never put English sentences, labels, "the entire function", "if a governed parser...", or conceptual repair text in remove_code, replace_code, add_code, or suggested_replacement.
- If the repair is conceptual, broad, multi-file, or not exact, leave code fields empty and put the explanation in notes.
- For remove_code, prefer copying the exact anchored line text when that line is the code to remove.
- Do not invent facts not supported by the file. If a token is read from os.environ, do not call it a hardcoded secret. Do not claim syntax errors unless the shown file text is syntactically invalid.
- Do not recommend eval, exec, or dynamic execution.

File: `{path}`
Language: {language}
Anchored line: {line}
Current anchored line text:
```text
{base.sanitize_text(line_text, config)}
```

Finding:
```json
{base.sanitize_text(finding_payload, config)}
```

Full head-file context:
```{language}
{visible_text}
```
""".strip()
    prompt = base.sanitize_text(prompt, config)
    max_prompt = int(getattr(config, "max_prompt_chars", len(prompt)))
    return prompt[:max_prompt]


def _build_repair_prompt(
    base: Any,
    finding: dict[str, Any],
    path: str,
    line: int,
    line_text: str,
    previous_result: dict[str, Any],
    config: Any,
) -> str:
    prompt = f"""
Repair the strict fix synthesis JSON for one DCOIR Review finding.

The previous JSON put prose in one or more code fields. Return the same schema.

Required correction:
- remove_code, replace_code, add_code, and suggested_replacement must contain only exact code/config.
- Move every sentence, label, conceptual instruction, or non-code phrase to notes.
- If no exact code is safe, leave code fields empty.

File: `{path}`
Anchored line: {line}
Current anchored line text:
```text
{base.sanitize_text(line_text, config)}
```

Finding title: {finding.get('title', '')}
Finding body: {finding.get('body', '')}

Previous invalid JSON:
```json
{json.dumps(previous_result, ensure_ascii=False, indent=2)}
```
""".strip()
    prompt = base.sanitize_text(prompt, config)
    max_prompt = int(getattr(config, "max_prompt_chars", len(prompt)))
    return prompt[:max_prompt]


def _strict_normalize_finding_for_comment(finding: dict[str, Any]) -> dict[str, Any]:
    item = dict(finding)
    kind = _semantic_kind(item)
    title = str(item.get("title", "") or "Finding").replace("Deterministic risk sentinel:", "").strip()
    if kind in YAML_REQUIRED_KIND_TITLES:
        title = YAML_REQUIRED_KIND_TITLES[kind]
    item["title"] = _clean_public_text(title or "Finding")
    body = _clean_public_text(str(item.get("body", "") or ""))
    if kind == "python_ssrf":
        body = re.sub(r"\bhardcoded secret\b", "secret or token value", body, flags=re.IGNORECASE)
        body = "\n".join(line for line in body.splitlines() if "syntax error" not in line.lower()).strip()
    item["body"] = body
    item["validation"] = _clean_public_text(str(item.get("validation", "") or ""))
    suggestion = _strip_fences(item.get("suggested_replacement", ""))
    if suggestion and not _strict_code_value_is_valid(suggestion, _language_hint(str(item.get("path", "") or ""))):
        guidance = item.get("fix_guidance") if isinstance(item.get("fix_guidance"), dict) else {}
        item["fix_guidance"] = {**guidance, "notes": "\n\n".join(filter(None, [str(guidance.get("notes", "") or ""), suggestion]))}
        item["suggested_replacement"] = ""
    guidance = _normalize_existing_fix_guidance(item)
    if guidance:
        item["fix_guidance"] = guidance
    else:
        item.pop("fix_guidance", None)
    return item


def _yaml_required_fallback_body(kind: str, sentinel: Any) -> str:
    changed = str(getattr(sentinel, "text", "") or "").strip()
    if kind == "yaml_pull_request_target":
        return "`pull_request_target` runs with base-repository privileges. Do not execute untrusted PR code in this context."
    if kind == "yaml_broad_write":
        return "This workflow grants broad write permissions. Narrow the token permissions to the minimum scopes needed."
    if kind == "yaml_untrusted_checkout":
        return "This privileged workflow checks out an untrusted pull request head ref or SHA. Do not combine privileged workflow context with PR-controlled code checkout."
    if kind == "yaml_shell_pipe":
        return f"This workflow pipes network-fetched content into a shell: `{changed}`. Download, verify a pinned checksum or signature, then execute only verified content."
    return "Review this GitHub Actions security boundary before merging."


def apply_pareto_context_module(module: Any) -> None:
    base = getattr(module, "base", None)
    hardened = getattr(module, "hardened", None)
    if base is not None:
        original = getattr(base, "_dcoir_strict_original_build_inline_comment", None)
        if original is None:
            original = getattr(base, "_dcoir_original_build_inline_comment", getattr(base, "build_inline_comment", None))
            base._dcoir_strict_original_build_inline_comment = original
        if callable(original):

            def strict_build_inline_comment(finding: dict[str, Any], model_used: str, config: Any) -> str:
                return original(_strict_normalize_finding_for_comment(finding), model_used, config)

            base.build_inline_comment = strict_build_inline_comment
        base.guidance_value_looks_like_code = _strict_code_value_is_valid

    if hardened is not None:
        original_is_required = getattr(hardened, "is_required_risk_sentinel", None)

        def strict_is_required_risk_sentinel(sentinel: Any) -> bool:
            if _sentinel_kind(sentinel) in YAML_REQUIRED_KIND_TITLES:
                return True
            return bool(original_is_required(sentinel)) if callable(original_is_required) else False

        hardened.is_required_risk_sentinel = strict_is_required_risk_sentinel

        def strict_required_risk_sentinels(sentinels: list[Any]) -> list[Any]:
            return [sentinel for sentinel in sentinels if strict_is_required_risk_sentinel(sentinel)]

        hardened.required_risk_sentinels = strict_required_risk_sentinels

        original_covers = getattr(hardened, "finding_covers_risk_sentinel", None)

        def strict_finding_covers_risk_sentinel(finding: dict[str, Any], sentinel: Any) -> bool:
            sentinel_kind = _sentinel_kind(sentinel)
            if sentinel_kind in YAML_REQUIRED_KIND_TITLES:
                try:
                    return (
                        str(finding.get("path", "") or "") == str(getattr(sentinel, "path", "") or "")
                        and int(finding.get("line", 0) or 0) == int(getattr(sentinel, "line", 0) or 0)
                        and _semantic_kind(finding) == sentinel_kind
                    )
                except (TypeError, ValueError):
                    return False
            return bool(original_covers(finding, sentinel)) if callable(original_covers) else False

        hardened.finding_covers_risk_sentinel = strict_finding_covers_risk_sentinel

        def strict_risk_sentinel_fallback_finding(sentinel: Any, config: Any) -> dict[str, Any]:
            kind = _sentinel_kind(sentinel)
            if kind in YAML_REQUIRED_KIND_TITLES:
                return {
                    "title": YAML_REQUIRED_KIND_TITLES[kind],
                    "severity": "high",
                    "confidence": 0.99,
                    "path": getattr(sentinel, "path", ""),
                    "line": getattr(sentinel, "line", 0),
                    "body": _yaml_required_fallback_body(kind, sentinel),
                    "suggested_replacement": "",
                    "validation": getattr(hardened, "primary_validation_command", lambda _config: "")(config),
                }
            fallback = getattr(hardened, "_dcoir_strict_original_risk_sentinel_fallback_finding", None)
            return fallback(sentinel, config) if callable(fallback) else {}

        if not hasattr(hardened, "_dcoir_strict_original_risk_sentinel_fallback_finding"):
            hardened._dcoir_strict_original_risk_sentinel_fallback_finding = hardened.risk_sentinel_fallback_finding
        hardened.risk_sentinel_fallback_finding = strict_risk_sentinel_fallback_finding

        original_select = getattr(hardened, "select_findings_for_inline", None)

        def strict_add_risk_sentinel_fallback_findings(
            findings: list[dict[str, Any]],
            risk_sentinels: list[Any],
            config: Any,
            unanchored_findings: list[dict[str, Any]] | None = None,
        ) -> list[dict[str, Any]]:
            uncovered = [
                sentinel
                for sentinel in strict_required_risk_sentinels(risk_sentinels)
                if not any(strict_finding_covers_risk_sentinel(finding, sentinel) for finding in [*findings, *(unanchored_findings or [])])
            ]
            inline_limit = int(getattr(config, "max_inline_comments", 12))
            fallback_findings = [strict_risk_sentinel_fallback_finding(sentinel, config) for sentinel in uncovered[:inline_limit]]
            if not fallback_findings:
                return findings
            existing_budget = max(0, inline_limit - len(fallback_findings))
            required_existing = [
                finding
                for finding in findings
                if Path(str(finding.get("path", "") or "").lower()).suffix in {".py", ".ps1", ".psm1", ".psd1"}
                or _semantic_kind(finding) in YAML_REQUIRED_KIND_TITLES
            ]
            if callable(original_select):
                existing = original_select(required_existing, existing_budget)
                if len(existing) < existing_budget:
                    extras = [finding for finding in findings if finding not in existing]
                    existing = [*existing, *original_select(extras, existing_budget - len(existing))]
            else:
                existing = required_existing[:existing_budget]
            deduped: list[dict[str, Any]] = []
            seen: set[tuple[str, int, str]] = set()
            for finding in [*existing, *fallback_findings]:
                key = (str(finding.get("path", "") or ""), int(finding.get("line", 0) or 0), _semantic_kind(finding) or str(finding.get("title", "")))
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(finding)
            return deduped[:inline_limit]

        hardened.add_risk_sentinel_fallback_findings = strict_add_risk_sentinel_fallback_findings

    original_score = getattr(module, "anchor_candidate_score", None)
    if callable(original_score):

        def strict_anchor_candidate_score(
            finding: dict[str, Any],
            candidate: Any,
            original_line: int,
            terms: list[str],
            risk_sentinels: list[Any],
        ) -> int:
            score = int(original_score(finding, candidate, original_line, terms, risk_sentinels))
            finding_kind = _semantic_kind(finding)
            candidate_kind = _candidate_kind(candidate)
            if finding_kind and candidate_kind:
                if finding_kind == candidate_kind:
                    score += 180
                elif finding_kind.startswith("yaml_") and candidate_kind.startswith("yaml_"):
                    score -= 120
            return score

        module.anchor_candidate_score = strict_anchor_candidate_score

    original_dedupe = getattr(module, "finding_dedupe_key", None)
    if callable(original_dedupe):

        def strict_finding_dedupe_key(finding: dict[str, Any]) -> tuple[str, str, str, str]:
            kind = _semantic_kind(finding)
            if kind:
                path = str(finding.get("path", "") or "").strip()
                line = "" if kind == "yaml_broad_write" else str(finding.get("line", "") or "").strip()
                return (path, line, kind, "")
            return original_dedupe(finding)

        module.finding_dedupe_key = strict_finding_dedupe_key

    file_line_text = getattr(module, "file_line_text", None)
    safe_artifact_name = getattr(module, "safe_artifact_name", None)
    verified_suggestion = getattr(module, "verified_suggested_replacement", None)
    fetch_module_base = base
    if callable(file_line_text) and callable(safe_artifact_name) and hardened is not None and fetch_module_base is not None:

        def strict_synthesize_fix_for_finding(
            index: int,
            finding: dict[str, Any],
            file_text: str,
            schema: dict[str, Any],
            config: Any,
        ) -> dict[str, Any]:
            path = str(finding.get("path", "") or "").strip()
            line = int(finding.get("line", 0) or 0)
            line_text = file_line_text(file_text, line)
            if not path or not line_text:
                return finding
            prompt = _build_strict_fix_synthesis_prompt(fetch_module_base, finding, path, line, line_text, file_text, config)
            artifact_id = safe_artifact_name(f"{path}-{line}", f"fix-{index:02d}")
            hardened.write_debug_text_artifact_safely(config, f"prompts/fix-synthesis/{index:02d}-{artifact_id}.txt", prompt)
            result, model_used, service_tier = hardened.openrouter_review(prompt, STRICT_FIX_SYNTHESIS_SCHEMA, config, reporter=None)
            repair_attempted = False
            if _code_field_invalid(result, path):
                repair_attempted = True
                repair_prompt = _build_repair_prompt(fetch_module_base, finding, path, line, line_text, result, config)
                hardened.write_debug_text_artifact_safely(config, f"prompts/fix-synthesis/{index:02d}-{artifact_id}-repair.txt", repair_prompt)
                try:
                    repaired, repair_model, repair_tier = hardened.openrouter_review(
                        repair_prompt,
                        STRICT_FIX_SYNTHESIS_SCHEMA,
                        config,
                        reporter=None,
                    )
                    result = repaired
                    model_used = f"{model_used}; repair={repair_model}"
                    service_tier = repair_tier or service_tier
                except Exception as exc:
                    hardened.write_debug_json_artifact_safely(
                        config,
                        f"responses/fix-synthesis/{index:02d}-{artifact_id}-repair-error.json",
                        {"path": path, "line": line, "error": str(exc)[:500]},
                    )
            guidance = _strict_fix_guidance(result, finding, path)
            hardened.write_debug_json_artifact_safely(
                config,
                f"responses/fix-synthesis/{index:02d}-{artifact_id}.json",
                {
                    "path": path,
                    "line": line,
                    "model_used": model_used,
                    "service_tier": service_tier,
                    "repair_attempted": repair_attempted,
                    "result": result,
                    "normalized_fix_guidance": guidance,
                },
            )
            enriched = dict(finding)
            enriched["_anchored_line_text"] = line_text
            suggestion = verified_suggestion(result, file_text, line, config) if callable(verified_suggestion) else ""
            if suggestion:
                enriched["suggested_replacement"] = suggestion
            elif guidance:
                enriched["fix_guidance"] = guidance
                enriched["suggested_replacement"] = ""
            validation = _clean_public_text(str(result.get("validation", "") or ""))
            if validation:
                enriched["validation"] = validation
            return enriched

        module.synthesize_fix_for_finding = strict_synthesize_fix_for_finding
