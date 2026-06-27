"""Connector-safe runtime patches for DCOIR Review entrypoints.

The large reviewer scripts are intentionally left connector-safe by patching narrow
runtime hooks from this module. ``openrouter_pr_review_entrypoint.py`` imports the
Pareto reviewer, calls ``apply_pareto_context_module()``, then invokes the real
main function.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REVIEW_ENTRYPOINTS = {"openrouter_pr_review.py", "openrouter_pr_review_pareto_context.py"}

PROSE_GUIDANCE_START_RE = re.compile(
    r"^(?:"
    r"add|avoid|change|delete|do not|ensure|example|keep|line|lines|move|native|"
    r"on\s+line|on\s+lines|replace|remove|run|store|use|validate"
    r")\b",
    re.IGNORECASE,
)
PROSE_WORD_RE = re.compile(
    r"\b(?:the|this|that|with|without|because|comment|current|entire|line|lines|"
    r"near|safe|unsafe|stating|version|must|should|would|could)\b",
    re.IGNORECASE,
)
YAML_KEY_RE = re.compile(r"(?m)^\s*[A-Za-z0-9_.-]+\s*:")
PYTHON_CODE_LINE_RE = re.compile(
    r"^\s*(?:"
    r"@|from\s+\S+\s+import\s+|import\s+|def\s+|async\s+def\s+|class\s+|"
    r"if\s+|elif\s+|else:|for\s+|while\s+|try:|except\b|finally:|with\s+|"
    r"return\b|raise\b|assert\b|[A-Za-z_][A-Za-z0-9_]*\s*(?::\s*[^=]+)?="
    r")"
)
POWERSHELL_CODE_LINE_RE = re.compile(
    r"^\s*(?:#|\$[A-Za-z_][A-Za-z0-9_]*|"
    r"[A-Za-z]+-[A-Za-z]+(?:\s|$)|"
    r"(?:if|foreach|for|while|try|catch|finally|param|function)\b)",
    re.IGNORECASE,
)
CURL_BASH_RE = re.compile(r"\b(?:curl|wget)\b[^\n]*(?:\|\s*(?:bash|sh)\b|bash\b|sh\b)", re.IGNORECASE)
GH_WRITE_PERMISSION_RE = re.compile(
    r"^\s*(?:permissions\s*:\s*write-all|"
    r"(?:actions|checks|contents|deployments|id-token|issues|packages|pull-requests|statuses)\s*:\s*write)\b",
    re.IGNORECASE,
)
PYTHON_DYNAMIC_EXEC_CALL_RE = re.compile(r"\b(?:eval|exec)\s*\(")
INLINE_DUNDER_RE = re.compile(r"(?<![`\\])\b(__[A-Za-z][A-Za-z0-9_]*__)\b(?!`)")
FENCE_LINE_RE = re.compile(r"^\s*(?:```|~~~)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")


_KIND_TITLES = {
    "python_pickle": "Unsafe Python pickle deserialization",
    "python_yaml_load": "Unsafe YAML loader for untrusted input",
    "python_ssrf": "Outbound request can be steered by untrusted input",
    "python_dynamic_exec": "Dynamic Python execution of untrusted input",
    "ps_securestring": "Plaintext SecureString conversion",
    "ps_start_process": "Unvalidated process launch",
    "ps_run_key": "Windows Run key persistence change",
    "yaml_pull_request_target": "Privileged pull_request_target workflow context",
    "yaml_broad_write": "GitHub Actions workflow grants write permissions",
    "yaml_untrusted_checkout": "Privileged workflow checks out untrusted PR code",
    "yaml_shell_pipe": "Workflow pipes a network installer into a shell",
}

_KIND_DEFAULT_NOTES = {
    "python_pickle": "Use a non-executing serialization format such as JSON or a typed schema for untrusted data; do not deserialize untrusted pickle payloads.",
    "python_yaml_load": "Use yaml.safe_load or SafeLoader for untrusted YAML input.",
    "python_ssrf": "Validate outbound URLs against an allowlist and block private, loopback, link-local, and metadata-service ranges before making the request.",
    "ps_start_process": "Validate the executable path and arguments against an allowlist before launching a process.",
    "yaml_shell_pipe": "Download to a file, verify a pinned checksum or signature, then execute only verified content.",
}

_INTERNAL_LINE_RE = re.compile(
    r"(?:deterministic risk sentinel|dcoir-review-guard\.yml|guard workflow|non-evidenced guard)",
    re.IGNORECASE,
)
MISMATCHED_DYNAMIC_RE = re.compile(
    r"\b(?:dynamic python execution|dynamic evaluation|eval\s+or\s+exec|eval/exec|ast\.literal_eval|restricted globals)\b",
    re.IGNORECASE,
)


def _first_nonempty_line(value: str) -> str:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _strip_markdown_fence_lines(text: str) -> str:
    lines: list[str] = []
    for line in str(text or "").splitlines():
        if FENCE_LINE_RE.match(line):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def _line_looks_like_code(line: str, language: str) -> bool:
    stripped = line.strip()
    lowered = stripped.lower()
    if not stripped:
        return False
    if language in {"yaml", "json"} and YAML_KEY_RE.match(stripped):
        return True
    if language == "python" and PYTHON_CODE_LINE_RE.match(stripped):
        return True
    if language == "powershell" and POWERSHELL_CODE_LINE_RE.match(stripped):
        return True
    code_signals = (
        "$",
        "=",
        "(",
        ")",
        "{",
        "}",
        "[",
        "]",
        ";",
        "|",
        "=>",
        "&&",
        "||",
        "import ",
        "from ",
        "def ",
        "class ",
        "return ",
        "raise ",
        "throw ",
        "if ",
        "for ",
        "while ",
        "on:",
        "permissions:",
        "uses:",
        "run:",
        "set-",
        "invoke-",
        "start-",
        "convertto-",
    )
    return any(signal_text in lowered for signal_text in code_signals)


def _guidance_value_is_prose(value: str, language: str) -> bool:
    first = _first_nonempty_line(value)
    if not first:
        return False
    if PROSE_GUIDANCE_START_RE.match(first):
        return True
    if _line_looks_like_code(first, language):
        return False
    return len(first.split()) >= 5 and bool(PROSE_WORD_RE.search(first))


def patched_guidance_value_looks_like_code(value: str, language: str) -> bool:
    stripped = _strip_markdown_fence_lines(value)
    if not stripped:
        return False
    normalized_language = str(language or "").strip().lower()
    if _guidance_value_is_prose(stripped, normalized_language):
        return False
    if normalized_language in {"yaml", "json"} and YAML_KEY_RE.search(stripped):
        return True
    lines = [line for line in stripped.splitlines() if line.strip()]
    if not lines:
        return False
    code_line_count = sum(1 for line in lines if _line_looks_like_code(line, normalized_language))
    if not code_line_count:
        return False
    prose_line_count = sum(1 for line in lines if _guidance_value_is_prose(line, normalized_language))
    return code_line_count >= max(1, len(lines) - prose_line_count)


def _protect_markdown_identifiers(value: str) -> str:
    return INLINE_DUNDER_RE.sub(r"`\1`", str(value or ""))


def _remove_internal_lines(value: str) -> str:
    kept: list[str] = []
    for line in str(value or "").splitlines():
        if _INTERNAL_LINE_RE.search(line):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def _clean_user_text(value: str) -> str:
    return _protect_markdown_identifiers(_remove_internal_lines(value))


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _finding_text(finding: dict[str, Any], key: str = "") -> str:
    values = [
        str(finding.get("title", "") or ""),
        str(finding.get("body", "") or ""),
        str(finding.get("validation", "") or ""),
    ]
    fix_guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    if fix_guidance:
        values.extend(str(fix_guidance.get(name, "") or "") for name in ("remove", "replace", "add", "notes"))
    if key:
        values = [str(finding.get(key, "") or "")]
    return _normalize("\n".join(values))


def _semantic_kind(finding: dict[str, Any]) -> str:
    path = str(finding.get("path", "") or "").strip().lower()
    text = _finding_text(finding)
    suffix = Path(path).suffix
    if suffix == ".py":
        if "pickle.loads" in text or "pickle.load" in text or ("pickle" in text and "deserial" in text):
            return "python_pickle"
        if "yaml.load" in text or "yaml.loader" in text or "loader=yaml.loader" in text:
            return "python_yaml_load"
        if "requests.get" in text or "requests.post" in text or "requests.request" in text or "ssrf" in text:
            return "python_ssrf"
        if PYTHON_DYNAMIC_EXEC_CALL_RE.search(text):
            return "python_dynamic_exec"
    if suffix in {".ps1", ".psm1", ".psd1"}:
        if "convertto-securestring" in text and "asplaintext" in text:
            return "ps_securestring"
        if "start-process" in text:
            return "ps_start_process"
        if "currentversion\\run" in text or "run key" in text or ("set-itemproperty" in text and "\\run" in text):
            return "ps_run_key"
    if suffix in {".yml", ".yaml"}:
        if "pull_request_target" in text:
            return "yaml_pull_request_target"
        if "github.head_ref" in text or "github.event.pull_request.head" in text or ("untrusted" in text and "checkout" in text):
            return "yaml_untrusted_checkout"
        if ("curl" in text or "wget" in text) and ("|" in text or "pipe" in text) and ("bash" in text or " sh" in text):
            return "yaml_shell_pipe"
        if "write-all" in text or "broad write" in text or ("permissions" in text and "write" in text):
            return "yaml_broad_write"
    return ""


def _github_actions_kinds_from_text(text: str) -> set[str]:
    kinds: set[str] = set()
    if "pull_request_target" in text:
        kinds.add("yaml_pull_request_target")
    if "write-all" in text or "broad write" in text or ("permissions" in text and "write" in text):
        kinds.add("yaml_broad_write")
    if (
        "github.head_ref" in text
        or "github.event.pull_request.head" in text
        or ("untrusted" in text and "checkout" in text)
        or "head ref" in text
        or "head sha" in text
    ):
        kinds.add("yaml_untrusted_checkout")
    if ("curl" in text or "wget" in text) and ("bash" in text or " sh" in text) and ("pipe" in text or "|" in text):
        kinds.add("yaml_shell_pipe")
    return kinds


def _finding_anchor_kinds(finding: dict[str, Any]) -> set[str]:
    title_kinds = _github_actions_kinds_from_text(_finding_text(finding, "title"))
    body_kinds = _github_actions_kinds_from_text(_finding_text(finding))
    return title_kinds or body_kinds


def _candidate_anchor_kind(candidate: Any) -> str:
    raw_text = str(getattr(candidate, "text", ""))
    text = _normalize(raw_text)
    if "pull_request_target" in text:
        return "yaml_pull_request_target"
    if "github.head_ref" in text or "github.event.pull_request.head" in text:
        return "yaml_untrusted_checkout"
    if CURL_BASH_RE.search(raw_text):
        return "yaml_shell_pipe"
    if GH_WRITE_PERMISSION_RE.search(raw_text):
        return "yaml_broad_write"
    return ""


def _sentinel_anchor_kind(sentinel: Any) -> str:
    text = _normalize(
        "\n".join(
            [
                str(getattr(sentinel, "label", "") or ""),
                str(getattr(sentinel, "detail", "") or ""),
                str(getattr(sentinel, "text", "") or ""),
            ]
        )
    )
    kinds = _github_actions_kinds_from_text(text)
    return sorted(kinds)[0] if kinds else ""


def _language_hint_for_path(path: str) -> str:
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


def _clean_language(language: Any, fallback: str) -> str:
    text = str(language or "").strip().lower()
    return text if re.fullmatch(r"[a-z0-9_+.-]{1,32}", text) else fallback


def _extract_code_candidate(value: str, language: str) -> str:
    cleaned = _strip_markdown_fence_lines(value)
    first = _first_nonempty_line(cleaned)
    if not first:
        return ""
    if PROSE_GUIDANCE_START_RE.match(first):
        colon_tail = first.split(":", 1)[1].strip() if ":" in first else ""
        if colon_tail and patched_guidance_value_looks_like_code(colon_tail, language):
            return colon_tail
        candidate_lines: list[str] = []
        for line in cleaned.splitlines()[1:]:
            if not line.strip():
                continue
            if _guidance_value_is_prose(line, language):
                return ""
            if _line_looks_like_code(line, language):
                candidate_lines.append(line.rstrip())
        candidate = "\n".join(candidate_lines).strip()
        if candidate and patched_guidance_value_looks_like_code(candidate, language):
            return candidate
    for match in INLINE_CODE_RE.finditer(cleaned):
        candidate = match.group(1).strip()
        if len(candidate) > 12 and patched_guidance_value_looks_like_code(candidate, language):
            return candidate
    return ""


def _is_mismatched_python_dynamic_guidance(kind: str, value: str) -> bool:
    return kind in {"python_pickle", "python_yaml_load", "python_ssrf"} and bool(MISMATCHED_DYNAMIC_RE.search(value or ""))


def _normalize_fix_guidance(finding: dict[str, Any]) -> dict[str, str]:
    path = str(finding.get("path", "") or "")
    kind = _semantic_kind(finding)
    raw_guidance = finding.get("fix_guidance") if isinstance(finding.get("fix_guidance"), dict) else {}
    if not raw_guidance:
        return {}
    fallback_language = _language_hint_for_path(path)
    language = _clean_language(raw_guidance.get("language", ""), fallback_language)
    normalized: dict[str, str] = {"language": language}
    notes: list[str] = []

    for key in ("remove", "replace", "add"):
        raw_value = _strip_markdown_fence_lines(str(raw_guidance.get(key, "") or ""))
        if not raw_value:
            continue
        candidate = _extract_code_candidate(raw_value, language)
        if _is_mismatched_python_dynamic_guidance(kind, raw_value):
            if key == "remove" and candidate:
                normalized[key] = candidate
            continue
        if patched_guidance_value_looks_like_code(raw_value, language):
            normalized[key] = raw_value
        elif candidate:
            normalized[key] = candidate
            if key != "remove":
                notes.append(raw_value)
        else:
            notes.append(raw_value)

    raw_notes = _strip_markdown_fence_lines(str(raw_guidance.get("notes", "") or ""))
    if raw_notes and not _is_mismatched_python_dynamic_guidance(kind, raw_notes):
        notes.append(raw_notes)
    default_note = _KIND_DEFAULT_NOTES.get(kind, "")
    if default_note and (not notes or any(_is_mismatched_python_dynamic_guidance(kind, item) for item in notes)):
        notes = [item for item in notes if not _is_mismatched_python_dynamic_guidance(kind, item)]
        notes.insert(0, default_note)
    cleaned_notes: list[str] = []
    seen_notes: set[str] = set()
    for note in notes:
        cleaned = _clean_user_text(note)
        if not cleaned:
            continue
        key = _normalize(cleaned)
        if key in seen_notes:
            continue
        seen_notes.add(key)
        cleaned_notes.append(cleaned)
    if cleaned_notes:
        normalized["notes"] = "\n\n".join(cleaned_notes)
    return normalized if any(key in normalized for key in ("remove", "replace", "add", "notes")) else {}


def _normalize_finding_for_comment(finding: dict[str, Any]) -> dict[str, Any]:
    item = dict(finding)
    kind = _semantic_kind(item)
    title = str(item.get("title", "") or "")
    body = str(item.get("body", "") or "")
    if kind and ("deterministic risk sentinel" in title.lower() or "deterministic risk sentinel" in body.lower()):
        item["title"] = _KIND_TITLES.get(kind, title.replace("Deterministic risk sentinel:", "").strip() or "Finding")
    else:
        item["title"] = title.replace("Deterministic risk sentinel:", "").strip() or title
    item["title"] = _clean_user_text(str(item.get("title", "") or "Finding"))
    cleaned_body = _clean_user_text(body)
    if cleaned_body:
        item["body"] = cleaned_body
    elif kind:
        item["body"] = _KIND_DEFAULT_NOTES.get(kind, _KIND_TITLES.get(kind, "Review the changed line for this security issue."))
    item["validation"] = _clean_user_text(str(item.get("validation", "") or ""))
    suggestion = str(item.get("suggested_replacement", "") or "").strip()
    if suggestion and _guidance_value_is_prose(suggestion, _language_hint_for_path(str(item.get("path", "") or ""))):
        item["suggested_replacement"] = ""
        guidance = item.get("fix_guidance") if isinstance(item.get("fix_guidance"), dict) else {}
        guidance = dict(guidance)
        guidance["notes"] = "\n\n".join(filter(None, [str(guidance.get("notes", "") or "").strip(), suggestion]))
        item["fix_guidance"] = guidance
    fix_guidance = _normalize_fix_guidance(item)
    if fix_guidance:
        item["fix_guidance"] = fix_guidance
    elif "fix_guidance" in item:
        item.pop("fix_guidance", None)
    return item


def _fix_result_has_invalid_code_fields(result: dict[str, Any], finding: dict[str, Any], path: str) -> bool:
    kind = _semantic_kind({**finding, "path": path, "fix_guidance": result})
    language = _language_hint_for_path(path)
    for key in ("remove", "replace", "add"):
        value = _strip_markdown_fence_lines(str(result.get(key, "") or ""))
        if not value:
            continue
        if _is_mismatched_python_dynamic_guidance(kind, value):
            return True
        if patched_guidance_value_looks_like_code(value, language):
            continue
        if _extract_code_candidate(value, language):
            return True
        return True
    return False


def _build_fix_repair_prompt(
    finding: dict[str, Any],
    path: str,
    line: int,
    line_text: str,
    previous_result: dict[str, Any],
    config: Any,
) -> str:
    payload = json.dumps(previous_result, ensure_ascii=False, indent=2)
    prompt = f"""
Repair the fix synthesis JSON for one DCOIR Review finding.

Return the same JSON schema. Do not identify new findings.

Strict field rules:
- suggested_replacement: exact single-line replacement code for the anchored line only, or empty string.
- remove, replace, add: raw code or config snippets only. No prose, labels, Markdown fences, or sentences.
- notes: prose explanation belongs here.
- validation: exact commands only.
- If exact replacement code is not known, leave code fields empty and put the guidance in notes.
- Do not recommend eval, exec, or dynamic execution unless the original changed line already contains eval(...) or exec(...), and even then recommend removing it.

File: `{path}`
Anchored line: {line}
Current anchored line text:
```text
{line_text}
```

Finding title: {finding.get('title', '')}
Finding body: {finding.get('body', '')}

Previous invalid JSON:
```json
{payload}
```
""".strip()
    try:
        return str(config.max_prompt_chars and prompt[: config.max_prompt_chars])
    except Exception:
        return prompt


def _strict_fix_guidance_from_result(result: dict[str, Any], finding: dict[str, Any], path: str) -> dict[str, str]:
    synthetic = dict(finding)
    synthetic["path"] = path
    synthetic["fix_guidance"] = {
        "language": _language_hint_for_path(path),
        "remove": str(result.get("remove", "") or ""),
        "replace": str(result.get("replace", "") or ""),
        "add": str(result.get("add", "") or ""),
        "notes": str(result.get("notes", "") or ""),
    }
    return _normalize_fix_guidance(synthetic)


def _patch_base_formatter_module(module: Any) -> None:
    module.guidance_value_looks_like_code = patched_guidance_value_looks_like_code
    original = getattr(module, "_dcoir_original_build_inline_comment", None)
    if original is None and hasattr(module, "build_inline_comment"):
        original = module.build_inline_comment
        module._dcoir_original_build_inline_comment = original
    if callable(original):

        def patched_build_inline_comment(finding: dict[str, Any], model_used: str, config: Any) -> str:
            return original(_normalize_finding_for_comment(finding), model_used, config)

        module.build_inline_comment = patched_build_inline_comment


def _patched_dynamic_exec_scope(finding: dict[str, Any], path: str, line_text: str) -> bool:
    if Path(path).suffix.lower() != ".py":
        return False
    if PYTHON_DYNAMIC_EXEC_CALL_RE.search(line_text or ""):
        return True
    haystack = "\n".join(
        [
            str(finding.get("title", "") or ""),
            str(finding.get("body", "") or ""),
            str(finding.get("validation", "") or ""),
        ]
    )
    return bool(PYTHON_DYNAMIC_EXEC_CALL_RE.search(haystack))


def _patch_pareto_globals(globals_dict: dict[str, Any]) -> None:
    base = globals_dict.get("base")
    if base is not None:
        _patch_base_formatter_module(base)

    globals_dict["is_python_dynamic_exec_fix_scope"] = _patched_dynamic_exec_scope

    original_dedupe_key = globals_dict.get("finding_dedupe_key")
    if callable(original_dedupe_key):

        def patched_finding_dedupe_key(finding: dict[str, Any]) -> tuple[str, str, str, str]:
            kind = _semantic_kind(finding)
            path = str(finding.get("path", "") or "").strip()
            line = "" if kind == "yaml_broad_write" else str(finding.get("line", "") or "").strip()
            if kind:
                return (path, line, kind, "")
            return original_dedupe_key(finding)

        globals_dict["finding_dedupe_key"] = patched_finding_dedupe_key

    hardened = globals_dict.get("hardened")
    if hardened is None:
        return

    original_synthesize = globals_dict.get("synthesize_fix_for_finding")
    if callable(original_synthesize):
        build_prompt = globals_dict.get("build_fix_synthesis_prompt")
        file_line_text = globals_dict.get("file_line_text")
        safe_artifact_name = globals_dict.get("safe_artifact_name")
        verified_suggestion = globals_dict.get("verified_suggested_replacement")
        harden_dynamic = globals_dict.get("harden_python_dynamic_exec_fix_result")

        def patched_synthesize_fix_for_finding(
            index: int,
            finding: dict[str, Any],
            file_text: str,
            schema: dict[str, Any],
            config: Any,
        ) -> dict[str, Any]:
            path = str(finding.get("path", "") or "").strip()
            line = int(finding.get("line", 0) or 0)
            line_text = file_line_text(file_text, line) if callable(file_line_text) else ""
            if not path or not line_text or not callable(build_prompt):
                return original_synthesize(index, finding, file_text, schema, config)
            prompt = build_prompt(finding, path, line, line_text, file_text, config)
            artifact_id = safe_artifact_name(f"{path}-{line}", f"fix-{index:02d}") if callable(safe_artifact_name) else f"fix-{index:02d}"
            hardened.write_debug_text_artifact_safely(config, f"prompts/fix-synthesis/{index:02d}-{artifact_id}.txt", prompt)
            result, model_used, service_tier = hardened.openrouter_review(prompt, schema, config, reporter=None)
            repair_attempted = False
            if _fix_result_has_invalid_code_fields(result, finding, path):
                repair_attempted = True
                repair_prompt = _build_fix_repair_prompt(finding, path, line, line_text, result, config)
                hardened.write_debug_text_artifact_safely(
                    config,
                    f"prompts/fix-synthesis/{index:02d}-{artifact_id}-repair.txt",
                    repair_prompt,
                )
                try:
                    repaired, repair_model, repair_tier = hardened.openrouter_review(repair_prompt, schema, config, reporter=None)
                    result = repaired
                    model_used = f"{model_used}; repair={repair_model}"
                    service_tier = repair_tier or service_tier
                except Exception as exc:
                    hardened.write_debug_json_artifact_safely(
                        config,
                        f"responses/fix-synthesis/{index:02d}-{artifact_id}-repair-error.json",
                        {"path": path, "line": line, "error": str(exc)[:500]},
                    )
            if callable(harden_dynamic) and _patched_dynamic_exec_scope(finding, path, line_text):
                result = harden_dynamic(result, finding, path, line_text)
            guidance = _strict_fix_guidance_from_result(result, finding, path)
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
            suggestion = verified_suggestion(result, file_text, line, config) if callable(verified_suggestion) else ""
            if suggestion:
                enriched["suggested_replacement"] = suggestion
            elif guidance:
                enriched["fix_guidance"] = guidance
                enriched["suggested_replacement"] = ""
            validation = _clean_user_text(str(result.get("validation", "") or "").strip())
            if validation:
                enriched["validation"] = validation
            return enriched

        globals_dict["synthesize_fix_for_finding"] = patched_synthesize_fix_for_finding

    original_terms = globals_dict.get("finding_anchor_terms")
    if callable(original_terms):

        def patched_finding_anchor_terms(finding: dict[str, Any]) -> list[str]:
            terms = set(original_terms(finding))
            kinds = _finding_anchor_kinds(finding)
            if "yaml_untrusted_checkout" in kinds:
                terms.update(("github.head_ref", "github.event.pull_request.head.ref", "github.event.pull_request.head.sha", "ref:"))
            if "yaml_shell_pipe" in kinds:
                terms.update(("curl", "wget", "bash", "sh", "|"))
            if "yaml_broad_write" in kinds:
                terms.update(("permissions:", "write-all", "contents:", "pull-requests:"))
            return sorted(terms, key=lambda term: (-len(term), term))[:28]

        globals_dict["finding_anchor_terms"] = patched_finding_anchor_terms

    original_match = globals_dict.get("finding_text_matches_sentinel")
    if callable(original_match):

        def patched_finding_text_matches_sentinel(finding: dict[str, Any], sentinel: Any) -> bool:
            if original_match(finding, sentinel):
                return True
            sentinel_kind = _sentinel_anchor_kind(sentinel)
            return bool(sentinel_kind and sentinel_kind in _finding_anchor_kinds(finding))

        globals_dict["finding_text_matches_sentinel"] = patched_finding_text_matches_sentinel

    original_score = globals_dict.get("anchor_candidate_score")
    if callable(original_score):

        def patched_anchor_candidate_score(
            finding: dict[str, Any],
            candidate: Any,
            original_line: int,
            terms: list[str],
            risk_sentinels: list[Any],
        ) -> int:
            score = int(original_score(finding, candidate, original_line, terms, risk_sentinels))
            candidate_kind = _candidate_anchor_kind(candidate)
            finding_kinds = _finding_anchor_kinds(finding)
            if candidate_kind and finding_kinds:
                if candidate_kind in finding_kinds:
                    score += 140
                elif any(kind.startswith("yaml_") for kind in finding_kinds):
                    score -= 75
            return score

        globals_dict["anchor_candidate_score"] = patched_anchor_candidate_score

    original_detect_yaml = globals_dict.get("detect_github_actions_yaml_sentinels")
    if callable(original_detect_yaml):

        def patched_detect_github_actions_yaml_sentinels(diff: str) -> list[Any]:
            sentinels = list(original_detect_yaml(diff))
            seen = {(sentinel.path, sentinel.line, sentinel.label) for sentinel in sentinels}
            for changed_line in hardened.iter_added_diff_lines(diff):
                if Path(changed_line.path).suffix.lower() not in {".yml", ".yaml"}:
                    continue
                if hardened.is_comment_only_added_line(changed_line.path, changed_line.text):
                    continue
                if not CURL_BASH_RE.search(changed_line.text):
                    continue
                label = "GitHub Actions shell-piped network installer"
                key = (changed_line.path, changed_line.line, label)
                if key in seen:
                    continue
                seen.add(key)
                sentinels.append(
                    hardened.RiskSentinel(
                        path=changed_line.path,
                        line=changed_line.line,
                        label=label,
                        detail=(
                            "network-fetched scripts are piped directly into a shell; "
                            "download, verify, and execute only pinned or checksum-verified content"
                        ),
                        text=changed_line.text,
                    )
                )
            return sentinels

        globals_dict["detect_github_actions_yaml_sentinels"] = patched_detect_github_actions_yaml_sentinels


def apply_pareto_context_module(module: Any) -> None:
    """Apply explicit runtime patches to an imported Pareto context module."""
    _patch_pareto_globals(vars(module))


def _patch_main_globals(frame_globals: dict[str, Any], script_name: str) -> None:
    if script_name == "openrouter_pr_review.py":
        _patch_base_formatter_module(sys.modules["__main__"])
    elif script_name == "openrouter_pr_review_pareto_context.py":
        _patch_pareto_globals(frame_globals)


def activate(entrypoint: str | None = None) -> None:
    script_name = Path(entrypoint or sys.argv[0] or "").name
    if script_name not in REVIEW_ENTRYPOINTS:
        return
    try:
        import openrouter_pr_review as base

        _patch_base_formatter_module(base)
    except Exception:
        pass

    def patch_on_main_call(frame: Any, event: str, arg: Any) -> Any:
        if event == "call" and frame.f_code.co_name == "main":
            current_script = Path(frame.f_code.co_filename).name
            if current_script in REVIEW_ENTRYPOINTS:
                _patch_main_globals(frame.f_globals, current_script)
                sys.setprofile(None)
        return patch_on_main_call

    sys.setprofile(patch_on_main_call)
