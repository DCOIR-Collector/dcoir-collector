"""Connector-safe runtime patches for DCOIR Review entrypoints.

This module is imported by ``scripts/sitecustomize.py`` only when a DCOIR
Review script is the active Python entrypoint. It avoids rewriting the large
review scripts while still patching targeted formatter and anchoring behavior.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any


REVIEW_ENTRYPOINTS = {"openrouter_pr_review.py", "openrouter_pr_review_pareto_context.py"}

PROSE_GUIDANCE_START_RE = re.compile(
    r"^(?:"
    r"add|avoid|change|delete|do not|ensure|keep|line|lines|move|native|"
    r"on\s+line|on\s+lines|replace|remove|run|store|use|validate"
    r")\b",
    re.IGNORECASE,
)
PROSE_WORD_RE = re.compile(
    r"\b(?:the|this|that|with|without|because|comment|current|entire|line|lines|"
    r"near|safe|unsafe|stating|version|must|should)\b",
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


def _first_nonempty_line(value: str) -> str:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


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
    if _line_looks_like_code(first, language) and not PROSE_GUIDANCE_START_RE.match(first):
        return False
    if PROSE_GUIDANCE_START_RE.match(first):
        return True
    return len(first.split()) >= 5 and bool(PROSE_WORD_RE.search(first))


def patched_guidance_value_looks_like_code(value: str, language: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False
    normalized_language = str(language or "").strip().lower()
    if _guidance_value_is_prose(stripped, normalized_language):
        return False
    if normalized_language in {"yaml", "json"} and YAML_KEY_RE.search(stripped):
        return True
    lines = [line for line in stripped.splitlines() if line.strip()]
    code_line_count = sum(1 for line in lines if _line_looks_like_code(line, normalized_language))
    if not code_line_count:
        return False
    if len(lines) == 1:
        return True
    prose_line_count = sum(1 for line in lines if _guidance_value_is_prose(line, normalized_language))
    return code_line_count >= max(1, len(lines) - prose_line_count)


def _patch_base_formatter_module(module: Any) -> None:
    module.guidance_value_looks_like_code = patched_guidance_value_looks_like_code


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _finding_text(finding: dict[str, Any], key: str = "") -> str:
    values = [str(finding.get("title", "") or ""), str(finding.get("body", "") or "")]
    if key:
        values = [str(finding.get(key, "") or "")]
    return _normalize("\n".join(values))


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
    if "curl" in text and ("bash" in text or " sh" in text) and ("pipe" in text or "|" in text):
        kinds.add("yaml_curl_bash")
    return kinds


def _finding_anchor_kinds(finding: dict[str, Any]) -> set[str]:
    title_kinds = _github_actions_kinds_from_text(_finding_text(finding, "title"))
    body_kinds = _github_actions_kinds_from_text(_finding_text(finding))
    return title_kinds or body_kinds


def _candidate_anchor_kind(candidate: Any) -> str:
    text = _normalize(getattr(candidate, "text", ""))
    if "pull_request_target" in text:
        return "yaml_pull_request_target"
    if "github.head_ref" in text or "github.event.pull_request.head" in text:
        return "yaml_untrusted_checkout"
    if CURL_BASH_RE.search(str(getattr(candidate, "text", ""))):
        return "yaml_curl_bash"
    if GH_WRITE_PERMISSION_RE.search(str(getattr(candidate, "text", ""))):
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


def _patch_pareto_globals(globals_dict: dict[str, Any]) -> None:
    base = globals_dict.get("base")
    if base is not None:
        _patch_base_formatter_module(base)

    hardened = globals_dict.get("hardened")
    if hardened is None:
        return

    original_terms = globals_dict.get("finding_anchor_terms")
    if callable(original_terms):

        def patched_finding_anchor_terms(finding: dict[str, Any]) -> list[str]:
            terms = set(original_terms(finding))
            kinds = _finding_anchor_kinds(finding)
            if "yaml_untrusted_checkout" in kinds:
                terms.update(("github.head_ref", "github.event.pull_request.head.ref", "github.event.pull_request.head.sha", "ref:"))
            if "yaml_curl_bash" in kinds:
                terms.update(("curl", "bash", "|"))
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
                label = "GitHub Actions curl installer piped to bash"
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
