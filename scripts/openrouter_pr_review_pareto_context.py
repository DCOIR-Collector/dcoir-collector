#!/usr/bin/env python3
"""Pareto routing and first-pass context wrapper for the hardened PR reviewer."""

from __future__ import annotations

import ast
import base64
import copy
import json
import os
import re
import signal
import sys
import urllib.parse
from pathlib import Path
from typing import Any, NamedTuple

import openrouter_pr_review_hardened as hardened


base = hardened.base
CONTEXT_REVIEW_MARKER = "Context mode:"
DEEP_CONTEXT_MIN_PARTIAL_CHARS = 400
DEEP_CONTEXT_BUDGET_EXHAUSTED_SUFFIX = "\n~~~\n\n[deep context budget exhausted]"
DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER = "\n\n[deep context truncated by reviewer]"


def optional_float(data: dict[str, Any], key: str) -> float | None:
    value = data.get(key)
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Config key {key!r} must be a number or empty, got {value!r}") from exc


def load_pareto_context_config(path: str) -> Any:
    config = hardened.load_hardened_config(path)
    data = hardened.parse_yaml_like_data(path)
    config.pareto_min_coding_score = optional_float(data, "pareto_min_coding_score")
    config.first_pass_deep_review = hardened.bool_value(data, "first_pass_deep_review", True)
    config.deep_review_max_files = int(data.get("deep_review_max_files", min(getattr(config, "max_files", 30), 8)))
    config.deep_review_max_file_chars = int(data.get("deep_review_max_file_chars", 12000))
    config.deep_review_max_total_chars = int(data.get("deep_review_max_total_chars", 24000))
    hardened.ensure_free_models_are_opt_in(config)
    return config


_original_build_openrouter_payload = hardened.build_openrouter_payload
_original_detect_risk_sentinels = hardened.detect_risk_sentinels

FILE_WRITE_PATH_LABEL = "unsafe file-write path construction"
FILE_WRITE_PATH_DETAIL = (
    "dynamic path segments used for file writes need segment validation, normalization, "
    "and root containment checks before writing or staging files"
)
PYTHON_PATH_TARGET_PART = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
PYTHON_PATH_ASSIGNMENT_MAX_CHARS = 10000
PYTHON_PATH_ASSIGNMENT_RE = re.compile(
    rf"\b(?P<target>{PYTHON_PATH_TARGET_PART})\s*=\s*(?P<expr>[^\n#]*(?:Path|os\.path\.join)\s*\([^\n#]*)"
)
PYTHON_FILE_WRITE_RE = re.compile(rf"\b(?P<target>{PYTHON_PATH_TARGET_PART})\.write_(?:text|bytes)\s*\(")
PYTHON_TRIPLE_QUOTE_RE = re.compile(r"(?<!\\)(?:'''|\"\"\")")


class PythonDiffLine(NamedTuple):
    path: str
    line: int
    text: str
    is_added: bool
    inside_multiline_string: bool
    inside_diff_fixture_string: bool


def build_openrouter_payload(
    prompt: str,
    schema: dict[str, Any],
    config: Any,
    ignored_providers: list[str],
    model: str,
) -> dict[str, Any]:
    payload = _original_build_openrouter_payload(prompt, schema, config, ignored_providers, model)
    if model.startswith("openrouter/pareto-code"):
        plugin: dict[str, Any] = {"id": "pareto-router"}
        min_coding_score = getattr(config, "pareto_min_coding_score", None)
        if min_coding_score is not None:
            plugin["min_coding_score"] = min_coding_score
        payload["plugins"] = [plugin]
    return payload


hardened.build_openrouter_payload = build_openrouter_payload


def python_call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = python_call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def python_target_key(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = python_target_key(node.value)
        if prefix:
            return f"{prefix}.{node.attr}"
    return None


def python_assignment_target_names(text: str) -> set[str]:
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return set()
    names: set[str] = set()

    def collect(node: ast.AST) -> None:
        target_key = python_target_key(node)
        if target_key:
            names.add(target_key)
            return
        if isinstance(node, (ast.Tuple, ast.List)):
            for item in node.elts:
                collect(item)
        elif isinstance(node, ast.Starred):
            collect(node.value)
        elif isinstance(node, ast.Subscript):
            collect(node.value)

    for statement in module.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                collect(target)
        elif isinstance(statement, ast.AnnAssign):
            collect(statement.target)
        elif isinstance(statement, ast.AugAssign):
            collect(statement.target)
    return names


def python_simple_assignment(text: str) -> tuple[str, ast.AST] | None:
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return None
    if not module.body:
        return None
    statement = module.body[0]
    if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
        target_key = python_target_key(statement.targets[0])
        if target_key:
            return target_key, statement.value
    if isinstance(statement, ast.AnnAssign):
        target_key = python_target_key(statement.target)
        if target_key:
            return target_key, statement.value
    return None


def python_is_literal_path_segment(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))


def python_is_dynamic_path_segment(node: ast.AST) -> bool:
    if python_is_literal_path_segment(node):
        return False
    if isinstance(node, ast.Constant):
        return False
    return True


def python_is_path_constructor(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and python_call_name(node.func) in {"Path", "pathlib.Path"}


def python_is_os_path_join(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and python_call_name(node.func) == "os.path.join"


def python_path_expr_info(node: ast.AST) -> tuple[bool, bool]:
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Add):
            left_is_path, left_has_dynamic = python_path_expr_info(node.left)
            right_is_path, right_has_dynamic = python_path_expr_info(node.right)
            if left_is_path or right_is_path:
                return True, (
                    left_has_dynamic
                    or right_has_dynamic
                    or python_is_dynamic_path_segment(node.left)
                    or python_is_dynamic_path_segment(node.right)
                )
            return False, False
        if isinstance(node.op, ast.Div):
            left_is_path, left_has_dynamic = python_path_expr_info(node.left)
            if not left_is_path:
                right_is_dynamic = python_is_dynamic_path_segment(node.right)
                return right_is_dynamic, right_is_dynamic
            return True, left_has_dynamic or python_is_dynamic_path_segment(node.right)
    if python_is_path_constructor(node) or python_is_os_path_join(node):
        args = list(node.args)
        if len(args) < 2:
            return True, False
        return True, any(python_is_dynamic_path_segment(arg) for arg in args[1:])
    return False, False


def python_path_expr_has_dynamic_write_segment(node: ast.AST) -> bool:
    _is_path, has_dynamic = python_path_expr_info(node)
    return has_dynamic


def python_single_dynamic_path_expr(node: ast.AST) -> bool:
    if not (python_is_path_constructor(node) or python_is_os_path_join(node)):
        return False
    args = list(node.args)
    if len(args) != 1:
        return False
    arg = args[0]
    arg_is_path, arg_has_dynamic = python_path_expr_info(arg)
    if arg_is_path or (isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Div)):
        return arg_has_dynamic
    return python_is_dynamic_path_segment(arg)


def python_dynamic_path_target(text: str) -> str | None:
    assignment = python_simple_assignment(text)
    if assignment:
        target, expr_node = assignment
        if python_path_expr_has_dynamic_write_segment(expr_node) or python_single_dynamic_path_expr(expr_node):
            return target
    if len(text) > PYTHON_PATH_ASSIGNMENT_MAX_CHARS:
        return None
    if "Path" not in text and "os.path.join" not in text:
        return None
    match = PYTHON_PATH_ASSIGNMENT_RE.search(text)
    if not match:
        return None
    expr = match.group("expr")
    if "/" not in expr and "os.path.join" not in expr and not re.search(r"\bPath\s*\(", expr):
        return None
    if not (re.search(r"\bf['\"]", expr) and "{" in expr):
        return None
    return match.group("target")


def update_python_multiline_string_state(active_delimiter: str | None, active_diff_fixture: bool, text: str) -> tuple[str | None, bool]:
    if active_delimiter is not None and not active_diff_fixture and "diff --git " in text:
        active_diff_fixture = True
    for match in PYTHON_TRIPLE_QUOTE_RE.finditer(text):
        delimiter = match.group(0)
        if active_delimiter is None:
            active_delimiter = delimiter
            active_diff_fixture = "diff --git " in text[match.end() :]
        elif delimiter == active_delimiter:
            active_delimiter = None
            active_diff_fixture = False
    return active_delimiter, active_diff_fixture


def iter_python_diff_lines_with_context(diff: str) -> list[PythonDiffLine]:
    lines: list[PythonDiffLine] = []
    current_path: str | None = None
    right_line: int | None = None
    active_delimiter: str | None = None
    active_diff_fixture = False
    for raw_line in diff.splitlines():
        if raw_line.startswith("diff --git "):
            current_path = None
            right_line = None
            active_delimiter = None
            active_diff_fixture = False
            continue
        if raw_line.startswith("+++ b/"):
            current_path = raw_line[6:]
            active_delimiter = None
            active_diff_fixture = False
            continue
        if raw_line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,\d+)?", raw_line)
            right_line = int(match.group(1)) if match else None
            active_delimiter = None
            active_diff_fixture = False
            continue
        if current_path is None or right_line is None:
            continue
        if Path(current_path).suffix.lower() != ".py":
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                right_line += 1
            elif not raw_line.startswith("-") or raw_line.startswith("---"):
                right_line += 1
            continue
        if raw_line.startswith("-") and not raw_line.startswith("---"):
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            text = raw_line[1:]
            lines.append(PythonDiffLine(current_path, right_line, text, True, active_delimiter is not None, active_diff_fixture))
            if active_delimiter is not None or not hardened.is_comment_only_added_line(current_path, text):
                active_delimiter, active_diff_fixture = update_python_multiline_string_state(active_delimiter, active_diff_fixture, text)
            right_line += 1
            continue
        if raw_line.startswith(" "):
            text = raw_line[1:]
            lines.append(PythonDiffLine(current_path, right_line, text, False, active_delimiter is not None, active_diff_fixture))
            if active_delimiter is not None or not hardened.is_comment_only_added_line(current_path, text):
                active_delimiter, active_diff_fixture = update_python_multiline_string_state(active_delimiter, active_diff_fixture, text)
            right_line += 1
            continue
        if not raw_line.startswith("\\"):
            right_line += 1
    return lines


def python_diff_fixture_added_line_keys(diff: str) -> set[tuple[str, int]]:
    return {
        (line.path, line.line)
        for line in iter_python_diff_lines_with_context(diff)
        if line.is_added and line.inside_diff_fixture_string
    }


def detect_python_file_write_path_sentinels(diff: str) -> list[hardened.RiskSentinel]:
    sentinels: list[hardened.RiskSentinel] = []
    assigned_paths: dict[str, PythonDiffLine] = {}
    current_path = ""
    for diff_line in iter_python_diff_lines_with_context(diff):
        if diff_line.path != current_path:
            current_path = diff_line.path
            assigned_paths.clear()
        if diff_line.inside_multiline_string:
            continue
        if hardened.is_comment_only_added_line(diff_line.path, diff_line.text):
            continue
        dynamic_target = python_dynamic_path_target(diff_line.text)
        if dynamic_target:
            assigned_paths[dynamic_target] = diff_line
            continue
        for assigned_target in python_assignment_target_names(diff_line.text):
            assigned_paths.pop(assigned_target, None)
            prefix = f"{assigned_target}."
            for tracked_target in list(assigned_paths):
                if tracked_target.startswith(prefix):
                    assigned_paths.pop(tracked_target, None)
        write_match = PYTHON_FILE_WRITE_RE.search(diff_line.text)
        if not write_match:
            continue
        assignment = assigned_paths.get(write_match.group("target"))
        if not assignment:
            continue
        if not assignment.is_added and not diff_line.is_added:
            continue
        anchor = assignment if assignment.is_added else diff_line
        sentinels.append(
            hardened.RiskSentinel(
                path=anchor.path,
                line=anchor.line,
                label=FILE_WRITE_PATH_LABEL,
                detail=FILE_WRITE_PATH_DETAIL,
                text=anchor.text,
            )
        )
    return sentinels


def detect_risk_sentinels(diff: str, max_anchors: int | None = None) -> list[hardened.RiskSentinel]:
    diff_fixture_added_lines = python_diff_fixture_added_line_keys(diff)
    combined = [
        *[
            sentinel
            for sentinel in _original_detect_risk_sentinels(diff, None)
            if (sentinel.path, sentinel.line) not in diff_fixture_added_lines
        ],
        *detect_python_file_write_path_sentinels(diff),
    ]
    deduped: list[hardened.RiskSentinel] = []
    seen: set[tuple[str, int, str]] = set()
    for sentinel in combined:
        key = (sentinel.path, sentinel.line, sentinel.label)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sentinel)
    if max_anchors is not None:
        return deduped[:max_anchors]
    return deduped


hardened.detect_risk_sentinels = detect_risk_sentinels


def command_option_tokens(body: str, command: str) -> set[str]:
    first_line = body.strip().splitlines()[0].strip() if body.strip() else ""
    if not first_line.startswith(command):
        return set()
    suffix = first_line[len(command) :].strip().lower()
    return {token for token in re.split(r"[\s,]+", suffix) if token}


def review_mode_for_command(body: str, command: str, config: Any, prior_successful_review: bool) -> str:
    tokens = command_option_tokens(body, command)
    if {"deep", "exhaustive"} & tokens:
        return "deep-forced"
    if "diff" in tokens:
        return "diff"
    if getattr(config, "first_pass_deep_review", True) and not prior_successful_review:
        return "first-pass-deep"
    return "diff"


def list_pr_reviews(gh: Any, pr_number: int) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = gh.request("GET", f"/repos/{gh.repo}/pulls/{pr_number}/reviews?per_page=100&page={page}")
        if not batch:
            break
        reviews.extend(batch)
        if len(batch) < 100:
            break
        # Exact multiples of 100 cost one extra empty-page readback, which is
        # acceptable for the small PR review counts this workflow expects.
        page += 1
    return reviews


def has_prior_successful_context_review(gh: Any, pr_number: int) -> bool:
    for review in list_pr_reviews(gh, pr_number):
        body = str(review.get("body", ""))
        if base.MARKER in body and CONTEXT_REVIEW_MARKER in body:
            return True
    return False


def language_hint(path: str) -> str:
    suffix = Path(path).suffix.lower()
    # Common review surfaces get language hints; uncommon suffixes safely fall
    # back to plain text instead of expanding the prompt grammar surface.
    return {
        ".bash": "bash",
        ".cjs": "javascript",
        ".js": "javascript",
        ".json": "json",
        ".md": "markdown",
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


def fetch_pr_file_text(gh: Any, path: str, ref: str) -> str:
    encoded_path = urllib.parse.quote(path, safe="/")
    encoded_ref = urllib.parse.quote(ref, safe="")
    payload = gh.request("GET", f"/repos/{gh.repo}/contents/{encoded_path}?ref={encoded_ref}")
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise RuntimeError("content API did not return a file")
    encoding = payload.get("encoding")
    content = payload.get("content")
    if content is None or (content == "" and encoding == "none"):
        raise RuntimeError("file exceeds GitHub content API limit (>1 MB); omitting from deep context")
    if encoding != "base64":
        raise RuntimeError("content API did not return base64 text")
    raw = base64.b64decode(str(content).replace("\n", ""))
    return raw.decode("utf-8")


def build_deep_context_block(gh: Any, pr: dict[str, Any], files: list[dict[str, Any]], config: Any, review_mode: str) -> tuple[str, str]:
    if review_mode == "diff":
        return "", "diff-focused review; no full changed-file context requested"
    head_sha = str(pr.get("head", {}).get("sha", "") or "")
    if not head_sha:
        return "", "deep context requested but PR head SHA was unavailable"

    max_files = max(0, int(getattr(config, "deep_review_max_files", 8)))
    max_file_chars = max(0, int(getattr(config, "deep_review_max_file_chars", 12000)))
    max_total_chars = max(0, int(getattr(config, "deep_review_max_total_chars", 24000)))
    lines = [
        "Deep changed-file context:",
        f"Mode: {review_mode}.",
        "Use this full changed-file context to reason about whole-file behavior and downstream effects, while anchoring actionable findings to changed lines when practical.",
    ]
    included: list[str] = []
    omitted: list[str] = []
    remaining = max_total_chars

    for item in files:
        if len(included) >= max_files:
            break
        path = str(item.get("filename", "")).strip()
        status = str(item.get("status", "")).strip()
        if not path:
            continue
        if status in {"removed", "deleted"}:
            omitted.append(f"{path} (deleted)")
            continue
        try:
            text = base.sanitize_text(fetch_pr_file_text(gh, path, head_sha), config)
        except UnicodeDecodeError:
            omitted.append(f"{path} (not utf-8 text)")
            continue
        except Exception as exc:
            omitted.append(f"{path} ({str(exc)[:120]})")
            continue
        truncated = len(text) > max_file_chars
        snippet = text[:max_file_chars]
        if truncated:
            snippet = f"{snippet}\n\n[full-file context truncated for this file]"
        block = f"### {path}\nStatus: {status}; head ref: {head_sha[:12]}\n~~~{language_hint(path)}\n{snippet}\n~~~"
        if len(block) > remaining:
            if not included and remaining > DEEP_CONTEXT_MIN_PARTIAL_CHARS + len(DEEP_CONTEXT_BUDGET_EXHAUSTED_SUFFIX):
                partial = block[: remaining - len(DEEP_CONTEXT_BUDGET_EXHAUSTED_SUFFIX)].rstrip()
                fence_suffix = "\n~~~" if partial.count("~~~") % 2 == 1 else ""
                block = f"{partial}{fence_suffix}\n\n[deep context budget exhausted]"
            else:
                omitted.append(f"{path} (deep context budget)")
                continue
        lines.append(block)
        included.append(f"{path}{' (truncated)' if truncated else ''}")
        remaining -= len(block)
        if remaining <= DEEP_CONTEXT_MIN_PARTIAL_CHARS:
            # Keep a floor for useful context; below this, the next block would
            # usually be a tiny fragment rather than actionable file context.
            break

    if not included:
        return "", f"{review_mode}; no changed-file context included; omitted: {', '.join(omitted) or 'none'}"
    summary = f"{review_mode}; included {len(included)} file context block(s): {', '.join(included[:6])}"
    if len(included) > 6:
        summary += f", and {len(included) - 6} more"
    if omitted:
        summary += f"; omitted {len(omitted)}: {', '.join(omitted[:4])}"
    return "\n\n".join(lines), summary


def truncate_with_balanced_fences(text: str, max_chars: int, marker: str) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= len(marker):
        return marker[:max_chars]
    fence_close = "\n~~~"
    partial_limit = max(0, max_chars - len(marker))
    partial = text[:partial_limit].rstrip()
    if partial.count("~~~") % 2 == 1:
        partial_limit = max(0, max_chars - len(marker) - len(fence_close))
        partial = text[:partial_limit].rstrip()
        if partial.count("~~~") % 2 == 1:
            partial = f"{partial}{fence_close}"
    return f"{partial}{marker}"


def build_prompt(
    pr: dict[str, Any],
    files: list[dict[str, Any]],
    diff: str,
    config: Any,
    risk_sentinels: list[hardened.RiskSentinel],
    deep_context_block: str,
    review_mode: str,
    context_summary: str,
) -> str:
    mode_lines = [
        f"{CONTEXT_REVIEW_MARKER} {review_mode}",
        f"Context readback: {context_summary}",
        "When deep context is present, use it to reason about full changed-file behavior, but anchor actionable findings to changed lines when practical.",
        "Inspect dynamic path construction and file writes for traversal, arbitrary overwrite, missing root-containment checks, and unsafe staging side effects.",
    ]
    context = base.sanitize_text(deep_context_block.strip(), config)
    suffix = ""
    # Extremely small budgets preserve the hardened core review prompt and rely
    # on workflow progress/review readback for context-mode visibility.
    if config.max_prompt_chars >= 3000:
        suffix_budget = config.max_prompt_chars // 3
        budget = max(0, min(len(context), int(getattr(config, "deep_review_max_total_chars", 24000)), suffix_budget))
        if len(context) > budget:
            context = truncate_with_balanced_fences(context, budget, DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER)
        suffix = "\n\n".join(["\n".join(mode_lines), context]).strip()
        if len(suffix) > suffix_budget:
            suffix = truncate_with_balanced_fences(suffix, suffix_budget, DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER)

    prompt_config = copy.copy(config)
    separator = "\n\n"
    reserve = min(len(suffix), config.max_prompt_chars // 3) if suffix else 0
    prompt_config.max_prompt_chars = max(0, config.max_prompt_chars - reserve - len(separator))
    prompt = hardened.build_prompt(pr, files, diff, prompt_config, risk_sentinels)
    if not suffix:
        return prompt[: config.max_prompt_chars]
    if len(prompt) + len(separator) + len(suffix) <= config.max_prompt_chars:
        return f"{prompt}{separator}{suffix}"
    remaining = config.max_prompt_chars - len(prompt) - len(separator)
    if remaining <= len(DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER):
        retained_prompt = max(0, config.max_prompt_chars - len(DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER))
        return f"{prompt[:retained_prompt]}{DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER}"
    return f"{prompt}{separator}{truncate_with_balanced_fences(suffix, remaining, DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER)}"


def neutralize_github_mentions(text: str) -> str:
    return re.sub(r"@(?=[A-Za-z0-9])", "@<!-- -->", text)


def sanitize_context_summary(context_summary: str, config: Any) -> str:
    return neutralize_github_mentions(hardened.sanitize_github_output(context_summary, config))


def append_context_to_review_body(body: str, review_mode: str, context_summary: str, config: Any) -> str:
    safe_context_summary = sanitize_context_summary(context_summary, config)
    return base.github_safe_body(f"{body}\n\n{CONTEXT_REVIEW_MARKER} `{review_mode}`\n\nContext readback: {safe_context_summary}")


def main() -> None:
    repo = base.env_required("GITHUB_REPOSITORY")
    pr_number = int(base.env_required("PR_NUMBER"))
    token = base.env_required("GITHUB_TOKEN")
    trigger_comment_id = int(base.env_required("TRIGGER_COMMENT_ID"))
    comment_body = os.environ.get("TRIGGER_COMMENT_BODY", "")
    author = os.environ.get("TRIGGER_AUTHOR", "")
    config_path = os.environ.get("OPENROUTER_REVIEW_CONFIG", ".github/openrouter-pr-review-pareto.yml")
    config = load_pareto_context_config(config_path)

    if author in config.ignored_authors:
        print(f"Ignoring denied author {author}")
        return
    if config.allowed_authors and author not in config.allowed_authors:
        print(f"Ignoring unauthorized author {author}")
        return
    command = hardened.matching_command(comment_body, config.commands)
    if not command:
        print("Comment does not match configured review commands")
        return

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise hardened.ReviewTimeoutError(f"OpenRouter PR review exceeded script timeout of {config.script_timeout_seconds} seconds")

    schema = json.loads(base.read_text("schemas/openrouter-pr-review.schema.json"))
    gh = base.GitHubClient(token, repo)
    reporter = hardened.ProgressReporter(gh, pr_number, command, config)
    reaction_id = 0
    reaction_status = {"added": "not attempted", "removed": "not attempted"}

    try:
        reaction = gh.create_issue_comment_reaction(trigger_comment_id, "eyes")
        reaction_id = int(reaction.get("id", 0))
        reaction_status["added"] = f"success id={reaction_id}" if reaction_id else "success without returned id"
    except Exception as exc:
        reaction_status["added"] = f"failed: {str(exc)[:500]}"
        print(f"WARN: unable to add eyes reaction: {exc}", file=sys.stderr, flush=True)

    try:
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(config.script_timeout_seconds)
        base.env_required("OPENROUTER_API_KEY")  # Validate required secret; request code reads it again.
        reporter.start()
        reporter.update("reaction", f"eyes add: {reaction_status['added']}")
        reporter.update("github", "fetching PR metadata")
        pr = gh.get_pr(pr_number)
        reporter.update("github", "fetching PR diff")
        diff = gh.get_pr_diff(pr_number)
        reporter.update("github", "fetching changed file list")
        files = gh.list_files(pr_number)
        try:
            prior_successful_review = has_prior_successful_context_review(gh, pr_number)
            reporter.update("review-mode", f"prior context review found: {str(prior_successful_review).lower()}")
        except Exception as exc:
            prior_successful_review = False
            reporter.update("review-mode", f"prior context review readback failed; using first-pass posture: {str(exc)[:240]}")
        review_mode = review_mode_for_command(comment_body, command, config, prior_successful_review)
        deep_context_block, context_summary = build_deep_context_block(gh, pr, files, config, review_mode)
        safe_context_summary = sanitize_context_summary(context_summary, config)
        reporter.update("context", safe_context_summary)
        risk_sentinels = hardened.detect_risk_sentinels(diff, getattr(config, "risk_sentinel_max_anchors", 12))
        if risk_sentinels and getattr(config, "risk_sentinel_quality_gate", True):
            reporter.update("risk-sentinel", f"detected {len(risk_sentinels)} high-risk changed-line signals: {hardened.risk_sentinel_digest(risk_sentinels)}")
        reporter.update("prompt", f"building bounded prompt from {len(files)} changed files")
        prompt = build_prompt(pr, files, diff, config, risk_sentinels, deep_context_block, review_mode, context_summary)
        result, model_used, service_tier = hardened.openrouter_review_with_quality_retry(prompt, schema, config, reporter, risk_sentinels)
        reporter.update("normalize", "mapping model findings to changed diff lines")
        line_index = base.build_diff_line_index(diff)
        findings = hardened.normalize_findings(result, config, line_index)
        hardened.enforce_risk_sentinel_findings(findings, risk_sentinels, config)

        comments: list[dict[str, Any]] = []
        for finding in findings:
            path = str(finding["path"])
            line = int(finding["line"])
            comments.append({"path": path, "position": line_index[(path, line)], "body": base.build_inline_comment(finding, model_used, config)})

        event = "REQUEST_CHANGES" if comments and config.request_changes_on_findings else "COMMENT"
        review_body = append_context_to_review_body(base.build_review_body(result, findings, model_used, config), review_mode, context_summary, config)
        reporter.update("github-review", f"posting GitHub review with {len(comments)} inline comments")
        gh.create_review(pr_number, review_body, event, comments, str(pr.get("head", {}).get("sha", "")))
        hardened.remove_eyes_reaction(gh, trigger_comment_id, reaction_id, reaction_status)
        tier_note = f"; service_tier={service_tier}" if service_tier else ""
        reporter.update("reaction", f"eyes add: {reaction_status['added']}; eyes remove: {reaction_status['removed']}")
        reporter.complete(f"{model_used}{tier_note}", len(comments), event)
    except Exception as exc:
        hardened.remove_eyes_reaction(gh, trigger_comment_id, reaction_id, reaction_status)
        try:
            reporter.update("reaction", f"eyes add: {reaction_status['added']}; eyes remove: {reaction_status['removed']}")
        except Exception as reporter_exc:
            print(f"WARN: unable to update reaction status: {reporter_exc}", file=sys.stderr, flush=True)
        reporter.fail(hardened.sanitize_github_output(str(exc), config))
        raise
    finally:
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.alarm(0)


if __name__ == "__main__":
    main()
