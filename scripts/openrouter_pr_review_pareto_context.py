#!/usr/bin/env python3
"""Pareto routing and first-pass context wrapper for the hardened PR reviewer."""

from __future__ import annotations

import ast
import base64
import concurrent.futures
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
REVIEW_ASSIST_CONTEXT_ROOT = Path("/tmp/review-assist-context")
REVIEW_ASSIST_CONTEXT_REPORT = Path("project_sources/collector/powershell_review_assist_workflow_report.md")
REQUIRED_FINDING_FAMILIES = ("powershell", "python", "github-actions-yaml")
OPTIONAL_FINDING_FAMILIES = ("typescript", "kubernetes-yaml")


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
    config.per_file_first_pass_review = hardened.bool_value(data, "per_file_first_pass_review", True)
    config.per_file_review_concurrency = int(data.get("per_file_review_concurrency", 4))
    config.per_file_review_max_files = int(data.get("per_file_review_max_files", data.get("deep_review_max_files", 8)))
    config.per_file_review_max_file_chars = int(data.get("per_file_review_max_file_chars", data.get("deep_review_max_file_chars", 12000)))
    config.fix_synthesis_enabled = hardened.bool_value(data, "fix_synthesis_enabled", True)
    config.fix_synthesis_max_findings = int(data.get("fix_synthesis_max_findings", 8))
    config.fix_synthesis_min_confidence = float(data.get("fix_synthesis_min_confidence", 0.80))
    config.required_finding_reserved_budget = int(
        data.get("required_finding_reserved_budget", min(getattr(config, "max_inline_comments", 12), 9))
    )
    config.required_finding_min_per_family = int(data.get("required_finding_min_per_family", 2))
    config.deep_review_max_files = int(data.get("deep_review_max_files", min(getattr(config, "max_files", 30), 8)))
    config.deep_review_max_file_chars = int(data.get("deep_review_max_file_chars", 12000))
    config.deep_review_max_total_chars = int(data.get("deep_review_max_total_chars", 24000))
    hardened.ensure_free_models_are_opt_in(config)
    return config


_original_build_openrouter_payload = hardened.build_openrouter_payload
_original_detect_risk_sentinels = hardened.detect_risk_sentinels

FILE_WRITE_PATH_LABEL = "unsafe file-write path construction"
FILE_WRITE_PATH_DETAIL = (
    "dynamic path segments reached a file write; verify or add segment validation, "
    "normalization, and root containment checks before writing or staging files"
)
PYTHON_DYNAMIC_EXEC_LABEL = "Python eval/exec dynamic code execution"
PYTHON_DYNAMIC_EXEC_DETAIL = (
    "eval/exec can execute caller-controlled Python expressions; remove dynamic evaluation "
    "or replace it with ast.literal_eval, a constrained parser, or an explicit allowlist"
)
PYTHON_DYNAMIC_EXEC_CALL_NAMES = frozenset(
    {"eval", "exec", "builtins.eval", "builtins.exec", "__builtins__.eval", "__builtins__.exec"}
)
PYTHON_PATH_TARGET_PART = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
PYTHON_PATH_ASSIGNMENT_MAX_CHARS = 10000
PYTHON_PATH_ASSIGNMENT_RE = re.compile(
    rf"^\s*(?P<target>{PYTHON_PATH_TARGET_PART})\s*=\s*(?P<expr>[^\n#]*(?:Path|os\.path\.join)\s*\([^\n#]*)"
)
PYTHON_PATH_ASSIGNMENT_START_RE = re.compile(
    rf"^\s*{PYTHON_PATH_TARGET_PART}\s*(?::\s*[^=]+)?=\s*(?:Path|pathlib\.Path|os\.path\.join)\s*\("
)
PYTHON_ASSIGNMENT_CONTINUATION_START_RE = re.compile(
    rf"^\s*{PYTHON_PATH_TARGET_PART}\s*(?::\s*[^=]+)?=\s*(?:\(|\\)\s*$"
)
PYTHON_FILE_WRITE_RE = re.compile(
    rf"(?:\b(?P<target>{PYTHON_PATH_TARGET_PART})|\b(?:Path|pathlib\.Path)\s*\(\s*(?P<wrapped_target>{PYTHON_PATH_TARGET_PART})\s*\))"
    r"\.write_(?:text|bytes)\s*\("
)
PYTHON_SCOPE_BOUNDARY_RE = re.compile(r"^\s*(?:async\s+def|def|class)\s+[A-Za-z_][A-Za-z0-9_]*\b")
PYTHON_HUNK_CONTEXT_RE = re.compile(r"^@@.*?@@\s*(?P<context>.*)$")
PYTHON_TRIPLE_QUOTE_RE = re.compile(r"(?<!\\)(?:'''|\"\"\")")
DEFAULT_PYTHON_PATH_CONSTRUCTORS = frozenset({"Path", "pathlib.Path"})
DEFAULT_PYTHON_OS_MODULES = frozenset({"os"})
PYTHON_PATH_ALIAS_CONTEXT: dict[str, set[str]] = {}
PYTHON_OS_ALIAS_CONTEXT: dict[str, set[str]] = {}


class PythonDiffLine(NamedTuple):
    path: str
    hunk: int
    line: int
    text: str
    is_added: bool
    inside_multiline_string: bool
    inside_diff_fixture_string: bool
    hunk_context: str = ""


class PythonTrackedPath(NamedTuple):
    assignment: PythonDiffLine | None
    indent: int
    scope_id: int = 0


class PythonScope(NamedTuple):
    indent: int
    key: str
    scope_id: int


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
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
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
    if isinstance(statement, ast.AnnAssign) and statement.value is not None:
        target_key = python_target_key(statement.target)
        if target_key:
            return target_key, statement.value
    return None


def python_assignment_value_references_target(text: str, target: str) -> bool:
    assignment = python_simple_assignment(text)
    if not assignment or assignment[0] != target:
        return False
    for node in ast.walk(assignment[1]):
        target_key = python_target_key(node)
        if target_key == target or (target_key and target_key.startswith(f"{target}.")):
            return True
    return False


def python_augmented_assignment_targets(text: str) -> set[str]:
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return set()
    targets: set[str] = set()
    for statement in module.body:
        if isinstance(statement, ast.AugAssign):
            target_key = python_target_key(statement.target)
            if target_key:
                targets.add(target_key)
    return targets


def python_statement_is_complete(text: str) -> bool:
    try:
        ast.parse(text.lstrip())
    except SyntaxError:
        return False
    return True


def python_path_constructor_aliases(text: str) -> set[str]:
    aliases: set[str] = set()
    if len(text) > PYTHON_PATH_ASSIGNMENT_MAX_CHARS:
        return aliases
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return aliases
    for statement in ast.walk(module):
        if isinstance(statement, ast.ImportFrom) and statement.module == "pathlib":
            for alias in statement.names:
                if alias.name == "Path":
                    aliases.add(alias.asname or alias.name)
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "pathlib":
                    aliases.add(f"{alias.asname or alias.name}.Path")
    return aliases



def python_os_module_aliases(text: str) -> set[str]:
    aliases: set[str] = set()
    if len(text) > PYTHON_PATH_ASSIGNMENT_MAX_CHARS:
        return aliases
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return aliases
    for statement in ast.walk(module):
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "os":
                    aliases.add(alias.asname or alias.name)
    return aliases

def set_python_path_alias_context(path_alias_context: dict[str, set[str]] | None) -> None:
    global PYTHON_PATH_ALIAS_CONTEXT
    PYTHON_PATH_ALIAS_CONTEXT = {
        path: set(aliases)
        for path, aliases in (path_alias_context or {}).items()
        if aliases
    }


def set_python_os_alias_context(os_alias_context: dict[str, set[str]] | None) -> None:
    global PYTHON_OS_ALIAS_CONTEXT
    PYTHON_OS_ALIAS_CONTEXT = {
        path: set(aliases)
        for path, aliases in (os_alias_context or {}).items()
        if aliases
    }


def python_path_assignment_start(text: str, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> bool:
    if PYTHON_PATH_ASSIGNMENT_START_RE.search(text):
        return True
    if PYTHON_ASSIGNMENT_CONTINUATION_START_RE.search(text):
        return True
    names = sorted((path_constructor_names or set()) - DEFAULT_PYTHON_PATH_CONSTRUCTORS, key=len, reverse=True)
    os_join_names = sorted(
        f"{name}.path.join" for name in (os_module_names or set()) - DEFAULT_PYTHON_OS_MODULES
    )
    if not names and not os_join_names:
        return False
    constructors = "|".join(re.escape(name) for name in [*names, *os_join_names])
    return bool(
        re.search(
            rf"^\s*{PYTHON_PATH_TARGET_PART}\s*(?::\s*[^=]+)?=\s*(?:{constructors})\s*\(",
            text,
        )
    )


def python_is_literal_path_segment(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))


def python_is_dynamic_path_segment(node: ast.AST) -> bool:
    if python_is_literal_path_segment(node):
        return False
    if isinstance(node, ast.Constant):
        return False
    return True


def python_is_directory_base_path_name(name: str) -> bool:
    leaf = name.rsplit(".", 1)[-1].lower()
    return bool(re.search(r"(?:^|_)(?:base|dir|directory|folder|root|workspace|repo)(?:_|$)", leaf))


def python_single_arg_path_has_dynamic_write_segment(node: ast.AST) -> bool:
    if python_is_literal_path_segment(node):
        return False
    if isinstance(node, ast.Constant):
        return False
    target = python_target_key(node)
    if target and python_is_directory_base_path_name(target):
        return False
    return python_is_dynamic_path_segment(node)


def python_is_path_constructor(node: ast.AST, path_constructor_names: set[str] | None = None) -> bool:
    constructors = path_constructor_names or DEFAULT_PYTHON_PATH_CONSTRUCTORS
    return isinstance(node, ast.Call) and python_call_name(node.func) in constructors


def python_is_os_path_join(node: ast.AST, os_module_names: set[str] | None = None) -> bool:
    modules = os_module_names or DEFAULT_PYTHON_OS_MODULES
    return isinstance(node, ast.Call) and python_call_name(node.func) in {f"{name}.path.join" for name in modules}


def python_is_joinpath_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "joinpath"


def python_path_expr_info(node: ast.AST, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> tuple[bool, bool]:
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Add):
            left_is_path, left_has_dynamic = python_path_expr_info(node.left, path_constructor_names, os_module_names)
            right_is_path, right_has_dynamic = python_path_expr_info(node.right, path_constructor_names, os_module_names)
            if left_is_path or right_is_path:
                return True, (
                    left_has_dynamic
                    or right_has_dynamic
                    or python_is_dynamic_path_segment(node.left)
                    or python_is_dynamic_path_segment(node.right)
                )
            return False, False
        if isinstance(node.op, ast.Div):
            left_is_path, left_has_dynamic = python_path_expr_info(node.left, path_constructor_names, os_module_names)
            if not left_is_path:
                right_is_dynamic = python_is_dynamic_path_segment(node.right)
                return right_is_dynamic, right_is_dynamic
            return True, left_has_dynamic or python_is_dynamic_path_segment(node.right)
    if python_is_joinpath_call(node):
        base_is_path, base_has_dynamic = python_path_expr_info(node.func.value, path_constructor_names, os_module_names)
        if not base_is_path:
            return False, False
        return True, base_has_dynamic or any(python_is_dynamic_path_segment(arg) for arg in node.args)
    if python_is_path_constructor(node, path_constructor_names) or python_is_os_path_join(node, os_module_names):
        args = list(node.args)
        if len(args) == 1:
            arg = args[0]
            arg_is_path, arg_has_dynamic = python_path_expr_info(arg, path_constructor_names, os_module_names)
            if arg_is_path or (isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Div)):
                return True, arg_has_dynamic
            return True, python_single_arg_path_has_dynamic_write_segment(arg)
        if len(args) < 1:
            return True, False
        return True, any(python_is_dynamic_path_segment(arg) for arg in args[1:])
    return False, False


def python_path_expr_has_dynamic_write_segment(node: ast.AST, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> bool:
    _is_path, has_dynamic = python_path_expr_info(node, path_constructor_names, os_module_names)
    return has_dynamic


def python_single_dynamic_path_expr(node: ast.AST, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> bool:
    if not (python_is_path_constructor(node, path_constructor_names) or python_is_os_path_join(node, os_module_names)):
        return False
    args = list(node.args)
    if len(args) != 1:
        return False
    arg = args[0]
    arg_is_path, arg_has_dynamic = python_path_expr_info(arg, path_constructor_names, os_module_names)
    if arg_is_path or (isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Div)):
        return arg_has_dynamic
    return python_single_arg_path_has_dynamic_write_segment(arg)


def python_dynamic_path_target(text: str, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> str | None:
    assignment = python_simple_assignment(text)
    if assignment:
        target, expr_node = assignment
        if python_path_expr_has_dynamic_write_segment(expr_node, path_constructor_names, os_module_names) or python_single_dynamic_path_expr(
            expr_node,
            path_constructor_names,
            os_module_names,
        ):
            return target
    if len(text) > PYTHON_PATH_ASSIGNMENT_MAX_CHARS:
        return None
    constructor_names = path_constructor_names or DEFAULT_PYTHON_PATH_CONSTRUCTORS
    os_modules = os_module_names or DEFAULT_PYTHON_OS_MODULES
    os_join_names = {f"{name}.path.join" for name in os_modules}
    if "Path" not in text and not any(name in text for name in os_join_names) and not any(f"{name}(" in text for name in constructor_names):
        return None
    match = PYTHON_PATH_ASSIGNMENT_RE.search(text)
    if not match:
        return None
    expr = match.group("expr")
    if "/" not in expr and not any(name in expr for name in os_join_names) and not re.search(r"\bPath\s*\(", expr):
        return None
    if not (re.search(r"\bf['\"]", expr) and "{" in expr):
        return None
    return match.group("target")


def python_augmented_dynamic_path_target(text: str, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> str | None:
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return None
    if not module.body or not isinstance(module.body[0], ast.AugAssign):
        return None
    statement = module.body[0]
    target = python_target_key(statement.target)
    if not target:
        return None
    if isinstance(statement.op, ast.Div) and python_is_dynamic_path_segment(statement.value):
        return target
    if isinstance(statement.op, ast.Add):
        value_is_path, value_has_dynamic = python_path_expr_info(statement.value, path_constructor_names, os_module_names)
        if value_is_path and value_has_dynamic:
            return target
    return None


def python_direct_dynamic_file_write(text: str, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> bool:
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return False
    constructor_names = path_constructor_names or DEFAULT_PYTHON_PATH_CONSTRUCTORS
    for node in ast.walk(module):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"write_text", "write_bytes"}:
            continue
        value = node.func.value
        if python_target_key(value):
            continue
        value_is_path, value_has_dynamic = python_path_expr_info(value, constructor_names, os_module_names)
        if value_is_path and value_has_dynamic:
            return True
    return False


def python_file_write_target(text: str, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> str | None:
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        write_match = PYTHON_FILE_WRITE_RE.search(text)
        if not write_match:
            return None
        return write_match.group("target") or write_match.group("wrapped_target")
    for node in ast.walk(module):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"write_text", "write_bytes"}:
            continue
        target = python_target_key(node.func.value)
        if target:
            return target
    return None


def python_wrapped_file_write_target(text: str, path_constructor_names: set[str] | None = None, os_module_names: set[str] | None = None) -> str | None:
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return None
    constructor_names = path_constructor_names or DEFAULT_PYTHON_PATH_CONSTRUCTORS
    for node in ast.walk(module):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"write_text", "write_bytes"}:
            continue
        value = node.func.value
        if python_is_path_constructor(value, constructor_names) and value.args:
            return python_target_key(value.args[0])
    return None


def append_file_write_sentinel(sentinels: list[hardened.RiskSentinel], anchor: PythonDiffLine) -> None:
    sentinels.append(
        hardened.RiskSentinel(
            path=anchor.path,
            line=anchor.line,
            label=FILE_WRITE_PATH_LABEL,
            detail=FILE_WRITE_PATH_DETAIL,
            text=anchor.text,
        )
    )


def python_dynamic_exec_call_name(text: str) -> str | None:
    if "eval" not in text and "exec" not in text:
        return None
    try:
        module = ast.parse(text.lstrip())
    except SyntaxError:
        return None
    for node in ast.walk(module):
        if not isinstance(node, ast.Call):
            continue
        call_name = python_call_name(node.func)
        if call_name in PYTHON_DYNAMIC_EXEC_CALL_NAMES:
            return call_name
    return None


def detect_python_dynamic_exec_sentinels(diff: str) -> list[hardened.RiskSentinel]:
    sentinels: list[hardened.RiskSentinel] = []
    for diff_line in iter_python_diff_lines_with_context(diff):
        if not diff_line.is_added or diff_line.inside_multiline_string:
            continue
        if hardened.is_comment_only_added_line(diff_line.path, diff_line.text):
            continue
        call_name = python_dynamic_exec_call_name(diff_line.text)
        if not call_name:
            continue
        sentinels.append(
            hardened.RiskSentinel(
                path=diff_line.path,
                line=diff_line.line,
                label=PYTHON_DYNAMIC_EXEC_LABEL,
                detail=(
                    f"{call_name} can execute caller-controlled Python code; "
                    "replace dynamic evaluation with literal parsing, a constrained parser, or an explicit allowlist"
                ),
                text=diff_line.text,
            )
        )
    return sentinels


def python_is_scope_boundary(text: str) -> bool:
    return bool(PYTHON_SCOPE_BOUNDARY_RE.match(text))


def python_scope_key(text: str) -> str:
    if not python_is_scope_boundary(text):
        return ""
    signature = text.strip().split("#", 1)[0].rstrip(":").strip()
    return re.sub(r"\s+", " ", signature)


def python_hunk_context_scope(raw_line: str) -> str:
    match = PYTHON_HUNK_CONTEXT_RE.match(raw_line)
    if not match:
        return ""
    return python_scope_key(match.group("context"))


def current_python_scope_id(scope_stack: list[PythonScope]) -> int:
    return scope_stack[-1].scope_id if scope_stack else 0


def active_python_scope_ids(scope_stack: list[PythonScope]) -> set[int]:
    return {0, *(scope.scope_id for scope in scope_stack)}


def pop_python_scopes_for_indent(scope_stack: list[PythonScope], indent: int | None) -> None:
    if indent is None:
        return
    while scope_stack and indent <= scope_stack[-1].indent:
        scope_stack.pop()


def seed_python_hunk_scope(scope_stack: list[PythonScope], hunk_context: str, next_scope_id: int) -> int:
    if not hunk_context or any(scope.key == hunk_context for scope in scope_stack):
        return next_scope_id
    next_scope_id += 1
    scope_stack.append(PythonScope(0, hunk_context, next_scope_id))
    return next_scope_id


def trim_python_scope_stack_to_hunk(scope_stack: list[PythonScope], hunk_context: str) -> bool:
    if not hunk_context:
        return False
    for index in range(len(scope_stack) - 1, -1, -1):
        if scope_stack[index].key == hunk_context:
            del scope_stack[index + 1 :]
            return True
    return False


def python_code_line_indent(text: str) -> int | None:
    stripped = text.strip()
    if not stripped or stripped.startswith("#"):
        return None
    return len(text) - len(text.lstrip(" \t"))


def prune_assigned_paths_for_active_scopes(assigned_paths: dict[str, list[PythonTrackedPath]], active_scope_ids: set[int]) -> None:
    for target, assignments in list(assigned_paths.items()):
        while assignments and assignments[-1].scope_id not in active_scope_ids:
            assignments.pop()
        if not assignments:
            assigned_paths.pop(target, None)


def python_scope_boundary_shadowed_names(text: str) -> set[str]:
    stripped = text.lstrip()
    if not re.match(r"^(?:async\s+def|def|class)\s+", stripped):
        return set()
    source = f"{stripped}\n    pass\n" if stripped.rstrip().endswith(":") else stripped
    try:
        module = ast.parse(source)
    except SyntaxError:
        return set()
    if not module.body:
        return set()
    statement = module.body[0]
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
        names = {arg.arg for arg in [*statement.args.posonlyargs, *statement.args.args, *statement.args.kwonlyargs]}
        if statement.args.vararg:
            names.add(statement.args.vararg.arg)
        if statement.args.kwarg:
            names.add(statement.args.kwarg.arg)
        return names
    if isinstance(statement, ast.ClassDef):
        return {statement.name}
    return set()


def push_assigned_path(
    assigned_paths: dict[str, list[PythonTrackedPath]],
    target: str,
    assignment: PythonDiffLine,
    scope_id: int,
) -> None:
    indent = python_code_line_indent(assignment.text) or 0
    assignments = assigned_paths.setdefault(target, [])
    while assignments and assignments[-1].scope_id == scope_id:
        assignments.pop()
    assignments.append(PythonTrackedPath(assignment, indent, scope_id))


def push_shadowed_assigned_path(
    assigned_paths: dict[str, list[PythonTrackedPath]],
    target: str,
    line: PythonDiffLine,
    scope_id: int,
) -> None:
    indent = (python_code_line_indent(line.text) or 0) + 1
    assignments = assigned_paths.setdefault(target, [])
    while assignments and assignments[-1].scope_id == scope_id:
        assignments.pop()
    assignments.append(PythonTrackedPath(None, indent, scope_id))


def clear_assigned_path_in_scope(
    assigned_paths: dict[str, list[PythonTrackedPath]],
    target: str,
    indent: int,
    scope_id: int,
) -> None:
    assignments = assigned_paths.get(target)
    if assignments is not None:
        while assignments and assignments[-1].scope_id == scope_id:
            assignments.pop()
        assignments.append(PythonTrackedPath(None, indent, scope_id))
    else:
        assigned_paths[target] = [PythonTrackedPath(None, indent, scope_id)]
    prefix = f"{target}."
    for tracked_target, tracked_assignments in list(assigned_paths.items()):
        if not tracked_target.startswith(prefix):
            continue
        while tracked_assignments and tracked_assignments[-1].scope_id == scope_id:
            tracked_assignments.pop()
        tracked_assignments.append(PythonTrackedPath(None, indent, scope_id))


def current_assigned_path(assigned_paths: dict[str, list[PythonTrackedPath]], target: str) -> PythonDiffLine | None:
    assignments = assigned_paths.get(target)
    if not assignments:
        return None
    return assignments[-1].assignment


def remove_shadowed_assigned_paths(
    assigned_paths: dict[str, list[PythonTrackedPath]],
    shadowed_names: set[str],
    line: PythonDiffLine,
    scope_id: int,
) -> None:
    for shadowed_name in shadowed_names:
        push_shadowed_assigned_path(assigned_paths, shadowed_name, line, scope_id)
        prefix = f"{shadowed_name}."
        for tracked_target in list(assigned_paths):
            if tracked_target.startswith(prefix):
                push_shadowed_assigned_path(assigned_paths, tracked_target, line, scope_id)


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
    hunk_index = 0
    hunk_context = ""
    active_delimiter: str | None = None
    active_diff_fixture = False
    for raw_line in diff.splitlines():
        if raw_line.startswith("diff --git "):
            current_path = None
            right_line = None
            hunk_index = 0
            hunk_context = ""
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
            hunk_index += 1
            hunk_context = python_hunk_context_scope(raw_line)
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
            lines.append(
                PythonDiffLine(
                    current_path,
                    hunk_index,
                    right_line,
                    text,
                    True,
                    active_delimiter is not None,
                    active_diff_fixture,
                    hunk_context,
                )
            )
            if active_delimiter is not None or not hardened.is_comment_only_added_line(current_path, text):
                active_delimiter, active_diff_fixture = update_python_multiline_string_state(active_delimiter, active_diff_fixture, text)
            right_line += 1
            continue
        if raw_line.startswith(" "):
            text = raw_line[1:]
            lines.append(
                PythonDiffLine(
                    current_path,
                    hunk_index,
                    right_line,
                    text,
                    False,
                    active_delimiter is not None,
                    active_diff_fixture,
                    hunk_context,
                )
            )
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
    assigned_paths: dict[str, list[PythonTrackedPath]] = {}
    scope_stack: list[PythonScope] = []
    next_scope_id = 0
    path_constructor_names = set(DEFAULT_PYTHON_PATH_CONSTRUCTORS)
    os_module_names = set(DEFAULT_PYTHON_OS_MODULES)
    current_path = ""
    current_hunk = 0
    current_alias_path = ""
    pending_path_assignment: list[PythonDiffLine] = []

    def flush_pending_path_assignment() -> None:
        nonlocal pending_path_assignment
        if not pending_path_assignment:
            return
        statement = "\n".join(line.text for line in pending_path_assignment)
        dynamic_target = python_dynamic_path_target(statement, path_constructor_names, os_module_names)
        if dynamic_target:
            push_assigned_path(
                assigned_paths,
                dynamic_target,
                pending_path_assignment[0],
                current_python_scope_id(scope_stack),
            )
        pending_path_assignment = []

    for diff_line in iter_python_diff_lines_with_context(diff):
        if diff_line.path != current_alias_path:
            path_constructor_names = set(DEFAULT_PYTHON_PATH_CONSTRUCTORS)
            path_constructor_names.update(PYTHON_PATH_ALIAS_CONTEXT.get(diff_line.path, set()))
            os_module_names = set(DEFAULT_PYTHON_OS_MODULES)
            os_module_names.update(PYTHON_OS_ALIAS_CONTEXT.get(diff_line.path, set()))
            current_alias_path = diff_line.path
        if diff_line.path != current_path:
            flush_pending_path_assignment()
            current_path = diff_line.path
            current_hunk = diff_line.hunk
            assigned_paths.clear()
            scope_stack.clear()
            next_scope_id = seed_python_hunk_scope(scope_stack, diff_line.hunk_context, next_scope_id)
        elif diff_line.hunk != current_hunk:
            flush_pending_path_assignment()
            if not trim_python_scope_stack_to_hunk(scope_stack, diff_line.hunk_context):
                assigned_paths.clear()
                scope_stack.clear()
                next_scope_id = seed_python_hunk_scope(scope_stack, diff_line.hunk_context, next_scope_id)
            current_hunk = diff_line.hunk
        diff_line_indent = python_code_line_indent(diff_line.text)
        pop_python_scopes_for_indent(scope_stack, diff_line_indent)
        prune_assigned_paths_for_active_scopes(assigned_paths, active_python_scope_ids(scope_stack))
        if diff_line.inside_multiline_string:
            continue
        if hardened.is_comment_only_added_line(diff_line.path, diff_line.text):
            continue
        path_constructor_names.update(python_path_constructor_aliases(diff_line.text))
        os_module_names.update(python_os_module_aliases(diff_line.text))
        if pending_path_assignment:
            pending_path_assignment.append(diff_line)
            statement = "\n".join(line.text for line in pending_path_assignment)
            if python_statement_is_complete(statement):
                flush_pending_path_assignment()
            continue
        if python_is_scope_boundary(diff_line.text):
            next_scope_id += 1
            scope_indent = diff_line_indent or 0
            scope_stack.append(PythonScope(scope_indent, python_scope_key(diff_line.text), next_scope_id))
            remove_shadowed_assigned_paths(
                assigned_paths,
                python_scope_boundary_shadowed_names(diff_line.text),
                diff_line,
                current_python_scope_id(scope_stack),
            )
        current_scope_id = current_python_scope_id(scope_stack)
        dynamic_target = python_dynamic_path_target(diff_line.text, path_constructor_names, os_module_names)
        if dynamic_target:
            push_assigned_path(assigned_paths, dynamic_target, diff_line, current_scope_id)
            continue
        augmented_dynamic_target = python_augmented_dynamic_path_target(diff_line.text, path_constructor_names, os_module_names)
        if augmented_dynamic_target:
            push_assigned_path(assigned_paths, augmented_dynamic_target, diff_line, current_scope_id)
            continue
        if python_path_assignment_start(diff_line.text, path_constructor_names, os_module_names) and not python_statement_is_complete(diff_line.text):
            pending_path_assignment = [diff_line]
            continue
        augmented_targets = python_augmented_assignment_targets(diff_line.text)
        assignment_indent = diff_line_indent or 0
        for assigned_target in python_assignment_target_names(diff_line.text):
            keep_exact_target = current_assigned_path(assigned_paths, assigned_target) is not None and (
                assigned_target in augmented_targets
                or python_assignment_value_references_target(
                    diff_line.text,
                    assigned_target,
                )
            )
            if keep_exact_target:
                assignment = current_assigned_path(assigned_paths, assigned_target)
                if diff_line.is_added and assignment is not None and not assignment.is_added:
                    push_assigned_path(assigned_paths, assigned_target, diff_line, current_scope_id)
            else:
                clear_assigned_path_in_scope(assigned_paths, assigned_target, assignment_indent, current_scope_id)
        write_target = python_file_write_target(diff_line.text, path_constructor_names, os_module_names)
        if not write_target:
            write_target = python_wrapped_file_write_target(diff_line.text, path_constructor_names, os_module_names)
        if not write_target:
            if diff_line.is_added and python_direct_dynamic_file_write(diff_line.text, path_constructor_names, os_module_names):
                append_file_write_sentinel(sentinels, diff_line)
            continue
        assignment = current_assigned_path(assigned_paths, write_target)
        if not assignment:
            if diff_line.is_added and python_direct_dynamic_file_write(diff_line.text, path_constructor_names, os_module_names):
                append_file_write_sentinel(sentinels, diff_line)
            continue
        if not assignment.is_added and not diff_line.is_added:
            continue
        anchor = assignment if assignment.is_added else diff_line
        append_file_write_sentinel(sentinels, anchor)
    flush_pending_path_assignment()
    return sentinels


def detect_risk_sentinels(diff: str, max_anchors: int | None = None) -> list[hardened.RiskSentinel]:
    diff_fixture_added_lines = python_diff_fixture_added_line_keys(diff)
    combined = [
        *detect_python_file_write_path_sentinels(diff),
        *detect_python_dynamic_exec_sentinels(diff),
        *[
            sentinel
            for sentinel in _original_detect_risk_sentinels(diff, None)
            if (sentinel.path, sentinel.line) not in diff_fixture_added_lines
        ],
    ]
    deduped: list[hardened.RiskSentinel] = []
    seen: set[tuple[str, int, str]] = set()
    for sentinel in combined:
        key = (sentinel.path, sentinel.line, sentinel.label)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sentinel)
    return hardened.select_risk_sentinels(deduped, max_anchors)


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
    markers = (base.MARKER, *getattr(base, "LEGACY_MARKERS", ()))
    for review in list_pr_reviews(gh, pr_number):
        body = str(review.get("body", ""))
        if any(marker in body for marker in markers) and CONTEXT_REVIEW_MARKER in body:
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


FIX_SYNTHESIS_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "DCOIR Review Fix Synthesis",
    "type": "object",
    "additionalProperties": False,
    "required": ["suggested_replacement", "remove", "replace", "add", "notes", "validation"],
    "properties": {
        "suggested_replacement": {
            "type": "string",
            "description": "Exact replacement code for the anchored review line only. Empty string if unsafe or not exact.",
        },
        "remove": {"type": "string", "description": "Code or behavior to remove when no native suggestion is safe."},
        "replace": {"type": "string", "description": "Replacement code or behavior when no native suggestion is safe."},
        "add": {"type": "string", "description": "Additional guard, validation, or test code to add when needed."},
        "notes": {"type": "string", "description": "Short implementation caveat. Empty when unnecessary."},
        "validation": {"type": "string", "description": "Exact validation command or commands that should pass after the fix."},
    },
}


def safe_artifact_name(path: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", path).strip("-")
    return (cleaned or fallback)[:120]


def added_diff_lines_for_path(diff: str, path: str) -> list[hardened.ChangedLine]:
    return [line for line in hardened.iter_added_diff_lines(diff) if line.path == path]


def is_probably_github_actions_workflow(path: str, text: str) -> bool:
    lower_path = path.lower()
    if lower_path.startswith(".github/workflows/"):
        return True
    if Path(lower_path).suffix not in {".yml", ".yaml"}:
        return False
    if "workflow" in Path(lower_path).name or "github" in lower_path or "actions" in lower_path:
        return True
    return bool(re.search(r"(?m)^\s*on\s*:\s*$", text) and re.search(r"(?m)^\s*jobs\s*:\s*$", text))


def file_specialization(path: str, text: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".ps1", ".psm1", ".psd1"}:
        return (
            "PowerShell specialization: inspect Invoke-Expression, Start-Process, Invoke-WebRequest/Invoke-RestMethod, "
            "Expand-Archive, Set-Content/Add-Content/Out-File/Copy-Item/Move-Item, Remove-Item, Set-Acl, request-controlled "
            "paths, credential forwarding, Windows PowerShell 5.1 compatibility, parser behavior, and PSScriptAnalyzer-style risks."
        )
    if suffix == ".py":
        return (
            "Python specialization: inspect unsafe deserialization, eval/exec/dynamic code evaluation, subprocess/shell execution, tar/zip/archive extraction, "
            "pathlib/os.path containment, raw SQL/query construction, requests/urllib/httpx outbound requests, secret/env persistence, "
            "temporary files, exception handling, and focused py_compile/Bandit/unit validation."
        )
    if suffix in {".yml", ".yaml"}:
        if is_probably_github_actions_workflow(path, text):
            return (
                "GitHub Actions YAML specialization: inspect pull_request_target, broad permissions, checkout of untrusted refs, "
                "untrusted github.event metadata in shell, token or secret forwarding, action pinning, command injection, and workflow "
                "inventory/readback validation."
            )
        return (
            "YAML specialization: inspect security-sensitive configuration, secret material, command fields, path or URL sinks, "
            "privilege settings, schema validity, and whether the file appears to define CI/CD or operational behavior."
        )
    if suffix in {".ts", ".js", ".mjs", ".cjs"}:
        return (
            "TypeScript/JavaScript specialization: inspect child_process execution, dynamic Function/eval, path joins/resolves before "
            "file writes, fetch/webhook token forwarding, raw SQL strings, async error handling, and TypeScript validation."
        )
    if suffix == ".json":
        return "JSON specialization: inspect schema validity, generated-report markers, duplicated or conflicting keys, and secret material."
    if suffix == ".md":
        return "Markdown/governance specialization: inspect misleading operator guidance, missing validation evidence, stale authority, and unsafe instructions."
    return "Generic specialization: inspect correctness, security, validation, and governance risk in the changed file."


def per_file_priority(item: dict[str, Any], file_text: str) -> tuple[int, int, str]:
    path = str(item.get("filename", "") or "")
    suffix = Path(path.lower()).suffix
    if suffix in {".ps1", ".psm1", ".psd1", ".py"}:
        family = 0
    elif suffix in {".yml", ".yaml"} and is_probably_github_actions_workflow(path, file_text):
        family = 0
    elif suffix in {".yml", ".yaml"}:
        family = 1
    elif suffix in {".ts", ".js", ".mjs", ".cjs"}:
        family = 2
    else:
        family = 3
    changes = int(item.get("changes") or 0)
    return family, -changes, path


def normalized_finding_text(value: Any, max_chars: int = 240) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())[:max_chars]


def finding_review_family(finding: dict[str, Any]) -> str:
    path = str(finding.get("path", "") or "").strip()
    lower_path = path.lower()
    suffix = Path(lower_path).suffix
    title = str(finding.get("title", "") or "")
    body = str(finding.get("body", "") or "")
    haystack = f"{title}\n{body}".lower()
    if suffix in {".ps1", ".psm1", ".psd1"}:
        return "powershell"
    if suffix == ".py":
        return "python"
    if suffix in {".yml", ".yaml"}:
        if (
            lower_path.startswith(".github/workflows/")
            or "github action" in haystack
            or "workflow" in Path(lower_path).name
            or "/actions/" in lower_path
        ):
            return "github-actions-yaml"
        if (
            "kubernetes" in lower_path
            or lower_path.startswith("k8s/")
            or "/k8s/" in lower_path
            or "kubernetes" in haystack
            or "kubectl" in haystack
        ):
            return "kubernetes-yaml"
        return "yaml"
    if suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        return "typescript"
    return "other"


def finding_dedupe_key(finding: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(finding.get("path", "") or "").strip(),
        str(finding.get("line", "") or "").strip(),
        normalized_finding_text(finding.get("title", "")),
        normalized_finding_text(finding.get("body", "")),
    )


def dedupe_findings_for_ranking(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for finding in findings:
        key = finding_dedupe_key(finding)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped


def rank_findings_for_required_budget(findings: list[dict[str, Any]], config: Any) -> list[dict[str, Any]]:
    max_inline = max(0, int(getattr(config, "max_inline_comments", 12)))
    if max_inline <= 0:
        return []
    ranked = sorted(dedupe_findings_for_ranking(findings), key=hardened.severity_sort_key)
    if len(ranked) <= max_inline:
        return ranked
    reserved_budget = min(
        max_inline,
        max(0, int(getattr(config, "required_finding_reserved_budget", min(max_inline, 9)))),
    )
    min_per_family = max(0, int(getattr(config, "required_finding_min_per_family", 2)))
    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, str, str, str]] = set()

    def maybe_select(finding: dict[str, Any]) -> bool:
        key = finding_dedupe_key(finding)
        if key in selected_keys:
            return False
        selected.append(finding)
        selected_keys.add(key)
        return True

    if min_per_family > 0:
        for family in REQUIRED_FINDING_FAMILIES:
            family_count = 0
            for finding in ranked:
                if len(selected) >= reserved_budget or family_count >= min_per_family:
                    break
                if finding_review_family(finding) == family and maybe_select(finding):
                    family_count += 1
    for finding in ranked:
        if len(selected) >= reserved_budget:
            break
        if finding_review_family(finding) in REQUIRED_FINDING_FAMILIES:
            maybe_select(finding)
    for finding in ranked:
        if len(selected) >= max_inline:
            break
        maybe_select(finding)
    return selected


def build_per_file_review_prompt(
    pr: dict[str, Any],
    item: dict[str, Any],
    file_text: str,
    diff: str,
    config: Any,
    path_sentinels: list[hardened.RiskSentinel],
    review_mode: str,
) -> str:
    path = str(item.get("filename", "") or "")
    max_file_chars = max(0, int(getattr(config, "per_file_review_max_file_chars", getattr(config, "deep_review_max_file_chars", 12000))))
    visible_text = base.sanitize_text(file_text, config)
    truncated = len(visible_text) > max_file_chars
    if truncated:
        visible_text = f"{visible_text[:max_file_chars]}\n\n[full-file context truncated for this file]"
    patch = base.sanitize_text(str(item.get("patch", "") or ""), config)
    added_lines = added_diff_lines_for_path(diff, path)
    added_line_block = "\n".join(f"{line.line}: {line.text}" for line in added_lines[:80]) or "(no added lines parsed)"
    sentinel_block = hardened.risk_sentinel_block(path_sentinels, config) if path_sentinels else "No deterministic risk anchors detected for this file."
    prompt = f"""
Context mode: {review_mode}
Per-file detector pass for `{path}`.

Repository: {base.sanitize_text(os.environ.get('GITHUB_REPOSITORY', ''), config)}
PR number: {pr.get('number')}
PR title: {base.sanitized_prompt_value(pr.get('title'), config)}

Specialized review instructions:
{file_specialization(path, file_text)}

Review rules:
- Review this single file deeply using the full file context and the file diff.
- Return only high-signal findings that matter for correctness, security, validation, or DCOIR governance.
- Anchor every finding to a changed RIGHT-side line from this file whenever possible.
- Keep findings generalizable. Do not tune to a known test fixture or exact previous conversation.
- Provide exact correction guidance and validation. Use `suggested_replacement` only when the replacement is exact code for the anchored line.
- If this file has no actionable issue, return an empty findings array and a clean summary.

{sentinel_block}

Changed RIGHT-side lines in this file:
```text
{added_line_block}
```

File diff patch:
```diff
{patch}
```

Full head-file context:
```{language_hint(path)}
{visible_text}
```
""".strip()
    prompt = base.sanitize_text(prompt, config)
    if len(prompt) > config.max_prompt_chars:
        prompt = prompt[: config.max_prompt_chars - len(DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER)] + DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER
    return prompt


def build_file_contexts(gh: Any, pr: dict[str, Any], files: list[dict[str, Any]], config: Any) -> list[dict[str, Any]]:
    head_sha = str(pr.get("head", {}).get("sha", "") or "")
    if not head_sha:
        return []
    contexts: list[dict[str, Any]] = []
    for item in files:
        path = str(item.get("filename", "") or "").strip()
        status = str(item.get("status", "") or "").strip()
        if not path or status in {"removed", "deleted"}:
            continue
        try:
            file_text = fetch_pr_file_text(gh, path, head_sha)
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
        contexts.append({"item": item, "path": path, "text": file_text})
    contexts.sort(key=lambda context: per_file_priority(context["item"], context["text"]))
    return contexts[: max(0, int(getattr(config, "per_file_review_max_files", getattr(config, "deep_review_max_files", 8))))]


def review_single_file_context(
    index: int,
    context: dict[str, Any],
    pr: dict[str, Any],
    diff: str,
    schema: dict[str, Any],
    config: Any,
    risk_sentinels: list[hardened.RiskSentinel],
    review_mode: str,
) -> dict[str, Any]:
    path = str(context["path"])
    path_sentinels = [sentinel for sentinel in risk_sentinels if sentinel.path == path]
    prompt = build_per_file_review_prompt(pr, context["item"], context["text"], diff, config, path_sentinels, review_mode)
    artifact_id = safe_artifact_name(path, f"file-{index:02d}")
    hardened.write_debug_text_artifact_safely(config, f"prompts/per-file/{index:02d}-{artifact_id}.txt", prompt)
    hardened.write_debug_json_artifact_safely(
        config,
        f"metadata/per-file/{index:02d}-{artifact_id}.json",
        {
            "path": path,
            "prompt_chars": len(prompt),
            "risk_sentinel_count": len(path_sentinels),
            "risk_sentinel_digest": hardened.risk_sentinel_digest(path_sentinels) if path_sentinels else "",
        },
    )
    result, model_used, service_tier = hardened.openrouter_review(prompt, schema, config, reporter=None)
    result = harden_python_dynamic_exec_fix_result(result, finding, path, line_text)
    hardened.write_debug_json_artifact_safely(
        config,
        f"responses/per-file/{index:02d}-{artifact_id}.json",
        {"path": path, "model_used": model_used, "service_tier": service_tier, "result": result},
    )
    return {"path": path, "prompt_chars": len(prompt), "result": result, "model_used": model_used, "service_tier": service_tier}


def merge_many_review_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {"summary": "Per-file detector pass completed.", "findings": []}
    for result in results:
        merged = hardened.merge_review_results(merged, result)
    return merged


def compact_model_label(results: list[dict[str, Any]], fallback: str) -> str:
    models: list[str] = []
    seen: set[str] = set()
    for item in results:
        model = str(item.get("model_used", "") or "").strip()
        if model and model not in seen:
            seen.add(model)
            models.append(model)
    if not models:
        return fallback
    if len(models) == 1:
        return models[0]
    return f"per-file model set: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}"


def should_use_per_file_first_pass(review_mode: str, config: Any) -> bool:
    return bool(getattr(config, "per_file_first_pass_review", True)) and review_mode in {"first-pass-deep", "deep-forced"}


def openrouter_review_with_hybrid_first_pass(
    pr: dict[str, Any],
    files: list[dict[str, Any]],
    diff: str,
    schema: dict[str, Any],
    config: Any,
    reporter: Any,
    risk_sentinels: list[hardened.RiskSentinel],
    line_index: dict[tuple[str, int], int],
    deep_context_block: str,
    review_mode: str,
    context_summary: str,
    gh: Any,
) -> tuple[dict[str, Any], str, str]:
    if not should_use_per_file_first_pass(review_mode, config):
        prompt = build_prompt(pr, files, diff, config, risk_sentinels, deep_context_block, review_mode, context_summary)
        return hardened.openrouter_review_with_quality_retry(prompt, schema, config, reporter, risk_sentinels, line_index)

    contexts = build_file_contexts(gh, pr, files, config)
    if not contexts:
        reporter.update("per-file", "no full-file contexts available; using bounded whole-PR prompt")
        prompt = build_prompt(pr, files, diff, config, risk_sentinels, deep_context_block, review_mode, context_summary)
        return hardened.openrouter_review_with_quality_retry(prompt, schema, config, reporter, risk_sentinels, line_index)

    reporter.update("per-file", f"running first-pass detector across {len(contexts)} file prompt(s)")
    per_file_manifest = "\n".join(
        [
            "Per-file first-pass detector prompt manifest.",
            "Individual prompts are written under prompts/per-file/.",
            "",
            *[f"- {context['path']}" for context in contexts],
        ]
    )
    hardened.write_debug_text_artifact_safely(config, "prompts/01-initial-prompt.txt", per_file_manifest)
    hardened.write_debug_json_artifact_safely(
        config,
        "metadata/01-initial-request.json",
        {
            "prompt_mode": "per-file",
            "file_prompt_count": len(contexts),
            "risk_sentinel_count": len(risk_sentinels),
            "risk_sentinel_digest": hardened.risk_sentinel_digest(risk_sentinels) if risk_sentinels else "",
            "line_index_entries": len(line_index),
        },
    )
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    max_workers = max(1, int(getattr(config, "per_file_review_concurrency", 4)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(contexts))) as executor:
        future_map = {
            executor.submit(
                review_single_file_context,
                index,
                context,
                pr,
                diff,
                schema,
                config,
                risk_sentinels,
                review_mode,
            ): (index, context)
            for index, context in enumerate(contexts, start=1)
        }
        for future in concurrent.futures.as_completed(future_map):
            index, context = future_map[future]
            path = str(context["path"])
            try:
                results.append(future.result())
                reporter.update("per-file-result", f"{path}: completed")
            except Exception as exc:
                failures.append(f"{path}: {str(exc)[:240]}")
                hardened.write_debug_json_artifact_safely(
                    config,
                    f"responses/per-file/{index:02d}-{safe_artifact_name(path, f'file-{index:02d}')}-error.json",
                    {"path": path, "error": str(exc)},
                )
                reporter.update("per-file-result", f"{path}: failed; continuing with remaining files")

    if not results:
        if failures:
            reporter.update("per-file", f"all per-file calls failed; using bounded whole-PR prompt. First failure: {failures[0]}")
        prompt = build_prompt(pr, files, diff, config, risk_sentinels, deep_context_block, review_mode, context_summary)
        return hardened.openrouter_review_with_quality_retry(prompt, schema, config, reporter, risk_sentinels, line_index)

    merged_result = merge_many_review_results([item["result"] for item in results])
    model_used = compact_model_label(results, getattr(config, "model", "openrouter/pareto-code"))
    service_tier = ", ".join(sorted({str(item.get("service_tier", "") or "") for item in results if item.get("service_tier")}))
    total_prompt_chars = sum(int(item.get("prompt_chars") or 0) for item in results)
    hardened.write_debug_json_artifact_safely(
        config,
        "metadata/01-initial-request.json",
        {
            "prompt_mode": "per-file",
            "file_prompt_count": len(contexts),
            "completed_file_prompt_count": len(results),
            "failed_file_count": len(failures),
            "prompt_chars": total_prompt_chars,
            "risk_sentinel_count": len(risk_sentinels),
            "risk_sentinel_digest": hardened.risk_sentinel_digest(risk_sentinels) if risk_sentinels else "",
            "line_index_entries": len(line_index),
        },
    )
    hardened.write_debug_json_artifact_safely(
        config,
        "responses/01-initial-result.json",
        {
            "model_used": model_used,
            "service_tier": service_tier,
            "prompt_mode": "per-file",
            "file_result_count": len(results),
            "failed_file_count": len(failures),
            "total_prompt_chars": total_prompt_chars,
            "result": merged_result,
        },
    )
    hardened.write_debug_json_artifact_safely(
        config,
        "responses/per-file/merged-detector-result.json",
        {
            "file_result_count": len(results),
            "failed_file_count": len(failures),
            "failures": failures,
            "model_used": model_used,
            "service_tier": service_tier,
            "result": merged_result,
        },
    )

    retry_reason = hardened.review_quality_retry_reason(merged_result, config, risk_sentinels, line_index)
    if retry_reason:
        safe_reason = hardened.sanitize_github_output(retry_reason, config)
        reporter.update("quality-retry", f"{safe_reason}; retrying with whole-PR repair prompt")
        aggregate_prompt = build_prompt(pr, files, diff, config, risk_sentinels, deep_context_block, review_mode, context_summary)
        retry_sentinels = hardened.required_risk_sentinels(risk_sentinels) or risk_sentinels
        retry_prompt = hardened.build_quality_retry_prompt(aggregate_prompt, merged_result, retry_sentinels, config, retry_reason)
        hardened.write_debug_text_artifact_safely(config, "prompts/02-quality-retry-prompt.txt", retry_prompt)
        retry_result, retry_model_used, retry_service_tier = hardened.openrouter_review(retry_prompt, schema, config, reporter)
        hardened.write_debug_json_artifact_safely(
            config,
            "responses/02-quality-retry-result.json",
            {"model_used": retry_model_used, "service_tier": retry_service_tier, "result": retry_result},
        )
        merged_result = hardened.merge_review_results(merged_result, retry_result)
        hardened.write_debug_json_artifact_safely(
            config,
            "responses/03-quality-retry-merged-result.json",
            {
                "model_used": retry_model_used,
                "service_tier": retry_service_tier,
                "merged_finding_count": len(hardened.result_findings(merged_result)),
                "result": merged_result,
            },
        )
        model_used = retry_model_used
        service_tier = retry_service_tier

    return merged_result, model_used, service_tier


def file_line_text(file_text: str, line_number: int) -> str:
    if line_number <= 0:
        return ""
    lines = file_text.splitlines()
    if line_number > len(lines):
        return ""
    return lines[line_number - 1]


def build_fix_synthesis_prompt(finding: dict[str, Any], path: str, line: int, line_text: str, file_text: str, config: Any) -> str:
    max_file_chars = max(0, int(getattr(config, "per_file_review_max_file_chars", getattr(config, "deep_review_max_file_chars", 12000))))
    visible_text = base.sanitize_text(file_text, config)
    if len(visible_text) > max_file_chars:
        visible_text = f"{visible_text[:max_file_chars]}\n\n[full-file context truncated for fix synthesis]"
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
Fix synthesis pass for one already-detected DCOIR Review finding.

Goal:
- Produce a minimal, safe fix for this single finding.
- Do not identify new findings.
- Do not broaden the fix beyond the anchored line unless fallback guidance is needed.
- Use `suggested_replacement` only when the exact replacement for the anchored GitHub review line is safe, syntactically plausible, and does not require modifying other files.
- If a native GitHub suggestion is not safe, leave `suggested_replacement` empty and fill one or more of `remove`, `replace`, and `add` with concise code-oriented guidance.
- Do not include Markdown fences in JSON fields.
- For eval/exec/dynamic code execution findings, do not propose another eval or exec call, even with restricted globals. Prefer removal, ast.literal_eval for literal-only data, a constrained parser/AST allowlist, or an explicit allowlist.
- Do not repeat secret-like literal values.

File: `{path}`
Language: {language_hint(path)}
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
```{language_hint(path)}
{visible_text}
```
""".strip()
    prompt = base.sanitize_text(prompt, config)
    if len(prompt) > config.max_prompt_chars:
        prompt = prompt[: config.max_prompt_chars - len(DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER)] + DEEP_CONTEXT_PROMPT_TRUNCATED_MARKER
    return prompt


def verified_suggested_replacement(fix_result: dict[str, Any], file_text: str, line_number: int, config: Any) -> str:
    suggestion = str(fix_result.get("suggested_replacement", "") or "").rstrip()
    if not suggestion:
        return ""
    unsafe_suggestion_markers = ("```", "~~~", "\r", "\n")
    if any(marker in suggestion for marker in unsafe_suggestion_markers):
        return ""
    if len(suggestion) > 1000:
        return ""
    if not base.is_safe_suggestion(suggestion):
        return ""
    original_line = file_line_text(file_text, line_number)
    if not original_line:
        return ""
    if suggestion.strip() == original_line.strip():
        return ""
    lines = file_text.splitlines()
    if line_number <= 0 or line_number > len(lines):
        return ""
    updated_lines = list(lines)
    updated_lines[line_number - 1] = suggestion
    changed_lines = [
        index
        for index, (before, after) in enumerate(zip(lines, updated_lines), start=1)
        if before != after
    ]
    if changed_lines != [line_number]:
        return ""
    return suggestion


PYTHON_DYNAMIC_EXEC_REPLACEMENT_PATTERN = re.compile(r"\b(?:eval|exec)\s*\(")


def is_python_dynamic_exec_fix_scope(finding: dict[str, Any], path: str, line_text: str) -> bool:
    if Path(path).suffix.lower() != ".py":
        return False
    haystack = "\n".join(
        [
            str(finding.get("title", "") or ""),
            str(finding.get("body", "") or ""),
            str(finding.get("validation", "") or ""),
            line_text,
        ]
    ).lower()
    if PYTHON_DYNAMIC_EXEC_REPLACEMENT_PATTERN.search(line_text):
        return True
    return ("eval" in haystack or "exec" in haystack) and (
        "dynamic" in haystack or "code execution" in haystack or "arbitrary code" in haystack
    )


def harden_python_dynamic_exec_fix_result(
    fix_result: dict[str, Any],
    finding: dict[str, Any],
    path: str,
    line_text: str,
) -> dict[str, Any]:
    if not isinstance(fix_result, dict) or not is_python_dynamic_exec_fix_scope(finding, path, line_text):
        return fix_result
    result = dict(fix_result)
    result["suggested_replacement"] = ""
    result["remove"] = str(
        result.get("remove")
        or f"Remove the dynamic Python execution call on the anchored line: {line_text.strip()}"
    ).strip()
    result["replace"] = (
        "Replace the dynamic evaluation with a non-executing parser or explicit allowlist. "
        "Use ast.literal_eval only for literal data; for expression-like input, implement a constrained AST "
        "or grammar allowlist. Do not use eval or exec, even with restricted globals."
    )
    add_text = str(result.get("add", "") or "").strip()
    if not add_text or PYTHON_DYNAMIC_EXEC_REPLACEMENT_PATTERN.search(add_text):
        result["add"] = (
            "Add tests proving os, __import__, open, and filesystem side effects are rejected "
            "without being executed."
        )
    else:
        result["add"] = add_text
    result["notes"] = (
        "Native GitHub suggestion suppressed because the safe repair depends on approved expression semantics; "
        "do not replace eval or exec with another dynamic execution primitive."
    )
    return result


def fix_guidance_from_result(fix_result: dict[str, Any], path: str, config: Any) -> dict[str, str]:
    guidance: dict[str, str] = {"language": language_hint(path)}
    for key in ("remove", "replace", "add", "notes"):
        value = str(fix_result.get(key, "") or "").strip()
        if value:
            guidance[key] = value
    return guidance if any(key in guidance for key in ("remove", "replace", "add", "notes")) else {}


def synthesize_fix_for_finding(
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
    prompt = build_fix_synthesis_prompt(finding, path, line, line_text, file_text, config)
    artifact_id = safe_artifact_name(f"{path}-{line}", f"fix-{index:02d}")
    hardened.write_debug_text_artifact_safely(config, f"prompts/fix-synthesis/{index:02d}-{artifact_id}.txt", prompt)
    result, model_used, service_tier = hardened.openrouter_review(prompt, schema, config, reporter=None)
    result = harden_python_dynamic_exec_fix_result(result, finding, path, line_text)
    hardened.write_debug_json_artifact_safely(
        config,
        f"responses/fix-synthesis/{index:02d}-{artifact_id}.json",
        {"path": path, "line": line, "model_used": model_used, "service_tier": service_tier, "result": result},
    )
    enriched = dict(finding)
    suggestion = verified_suggested_replacement(result, file_text, line, config)
    if suggestion:
        enriched["suggested_replacement"] = suggestion
    else:
        guidance = fix_guidance_from_result(result, path, config)
        if guidance:
            enriched["fix_guidance"] = guidance
            enriched["suggested_replacement"] = ""
    validation = str(result.get("validation", "") or "").strip()
    if validation:
        enriched["validation"] = validation
    return enriched


def strip_detector_suggested_replacements(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for finding in findings:
        item = dict(finding)
        detector_suggestion = str(item.get("suggested_replacement", "") or "")
        if detector_suggestion.strip():
            item["_detector_suggested_replacement"] = detector_suggestion
            item["suggested_replacement"] = ""
        enriched.append(item)
    return enriched


def synthesize_fixes_for_findings(
    findings: list[dict[str, Any]],
    gh: Any,
    pr: dict[str, Any],
    schema: dict[str, Any],
    config: Any,
    reporter: Any,
) -> list[dict[str, Any]]:
    enriched = strip_detector_suggested_replacements(findings)
    if not getattr(config, "fix_synthesis_enabled", True) or not enriched:
        return enriched
    head_sha = str(pr.get("head", {}).get("sha", "") or "")
    if not head_sha:
        return enriched
    max_findings = max(0, int(getattr(config, "fix_synthesis_max_findings", 8)))
    min_confidence = float(getattr(config, "fix_synthesis_min_confidence", 0.80))
    candidates: list[tuple[int, dict[str, Any]]] = []
    for index, finding in enumerate(enriched):
        try:
            confidence = float(finding.get("confidence", 0) or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence >= min_confidence:
            candidates.append((index, finding))
        if len(candidates) >= max_findings:
            break
    if not candidates:
        return enriched

    reporter.update("fix-synthesis", f"building repair guidance for {len(candidates)} finding(s)")
    file_cache: dict[str, str] = {}
    failures: list[str] = []
    for _index, finding in candidates:
        path = str(finding.get("path", "") or "").strip()
        if not path or path in file_cache:
            continue
        try:
            file_cache[path] = fetch_pr_file_text(gh, path, head_sha)
        except Exception as exc:
            failures.append(f"{path}: {str(exc)[:160]}")

    max_workers = min(max(1, int(getattr(config, "per_file_review_concurrency", 4))), max(1, len(candidates)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {}
        for ordinal, (index, finding) in enumerate(candidates, start=1):
            path = str(finding.get("path", "") or "").strip()
            file_text = file_cache.get(path)
            if not file_text:
                continue
            future = executor.submit(synthesize_fix_for_finding, ordinal, finding, file_text, schema, config)
            future_map[future] = index
        for future in concurrent.futures.as_completed(future_map):
            index = future_map[future]
            try:
                enriched[index] = future.result()
            except Exception as exc:
                path = str(enriched[index].get("path", "") or "")
                failures.append(f"{path}: {str(exc)[:160]}")
    if failures:
        hardened.write_debug_json_artifact_safely(config, "responses/fix-synthesis/failures.json", {"failures": failures})
        reporter.update("fix-synthesis", f"completed with {len(failures)} fallback-only failure(s)")
    else:
        reporter.update("fix-synthesis", "completed repair guidance pass")
    return enriched


def build_python_path_alias_context(gh: Any, pr: dict[str, Any], files: list[dict[str, Any]]) -> dict[str, set[str]]:
    head_sha = str(pr.get("head", {}).get("sha", "") or "")
    if not head_sha:
        return {}
    path_alias_context: dict[str, set[str]] = {}
    for item in files:
        path = str(item.get("filename", "")).strip()
        status = str(item.get("status", "")).strip()
        if not path or status in {"removed", "deleted"} or Path(path).suffix.lower() != ".py":
            continue
        try:
            aliases = python_path_constructor_aliases(fetch_pr_file_text(gh, path, head_sha))
        except Exception:
            continue
        if aliases:
            path_alias_context[path] = aliases
    return path_alias_context


def build_python_os_alias_context(gh: Any, pr: dict[str, Any], files: list[dict[str, Any]]) -> dict[str, set[str]]:
    head_sha = str(pr.get("head", {}).get("sha", "") or "")
    if not head_sha:
        return {}
    os_alias_context: dict[str, set[str]] = {}
    for item in files:
        path = str(item.get("filename", "")).strip()
        status = str(item.get("status", "")).strip()
        if not path or status in {"removed", "deleted"} or Path(path).suffix.lower() != ".py":
            continue
        try:
            aliases = python_os_module_aliases(fetch_pr_file_text(gh, path, head_sha))
        except Exception:
            continue
        if aliases:
            os_alias_context[path] = aliases
    return os_alias_context


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
        "Every finding must include exact correction guidance or the smallest safe patch direction, plus validation/readback guidance.",
        "Prefer GitHub apply-ready suggestions only when a finding has a precise single-line replacement for the commented line; put only that exact replacement code in suggested_replacement so the renderer emits a Suggested fix with a ```suggestion block; leave suggested_replacement empty for multiline, range, or speculative fixes.",
        "Inspect dynamic path construction and file writes for traversal, arbitrary overwrite, missing root-containment checks, and unsafe staging side effects.",
        "For this repository, give extra attention to PowerShell, Python, and GitHub Actions/YAML because they carry most operational and workflow risk; keep findings generalizable and do not tune to any single fixture.",
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


def split_findings_with_review_body_fallback(
    result: dict[str, Any],
    config: Any,
    line_index: dict[tuple[str, int], int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_findings = result.get("findings", [])
    if not isinstance(raw_findings, list) or not raw_findings:
        return hardened.split_findings(result, config, line_index)
    changed_paths = {path for path, _line in line_index}
    findings: list[dict[str, Any]] = []
    unanchored_findings: list[dict[str, Any]] = []
    track_unanchored = bool(getattr(config, "fail_on_unanchored_findings", True))
    for item in raw_findings:
        try:
            confidence = float(item.get("confidence", 0))
            line = int(item.get("line", 0))
            path = str(item.get("path", "")).strip()
        except (AttributeError, TypeError, ValueError):
            continue
        if not path or line <= 0:
            continue
        if confidence < config.minimum_confidence or hardened.non_actionable_finding_reason(item):
            continue
        if path not in changed_paths:
            continue
        if (path, line) in line_index:
            findings.append(dict(item))
            continue
        if track_unanchored:
            unanchored = dict(item)
            location_text = hardened.finding_location_text(path, line)
            unanchored["_unanchored_reason"] = f"{location_text} is not an added changed line for this PR"
            unanchored_findings.append(unanchored)
    findings = rank_findings_for_required_budget(findings, config)
    unanchored_findings = dedupe_findings_for_ranking(unanchored_findings)
    unanchored_findings.sort(key=hardened.severity_sort_key)
    unanchored_findings = unanchored_findings[: config.max_inline_comments]
    if findings or unanchored_findings:
        return findings, unanchored_findings
    return hardened.split_findings(result, config, line_index)



def review_assist_context_path(raw_path: str) -> Path | None:
    """Return the trusted review-assist context path or reject unexpected paths."""
    if not raw_path.strip():
        return None

    root = REVIEW_ASSIST_CONTEXT_ROOT.resolve(strict=False)
    expected = (root / REVIEW_ASSIST_CONTEXT_REPORT).resolve(strict=False)
    candidate = Path(raw_path).resolve(strict=False)
    if candidate != expected:
        raise ValueError(f"unexpected review-assist context path: {candidate}")
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"review-assist context path escapes trusted extraction root: {candidate}")
    return candidate


def load_review_assist_context(config: Any) -> str:
    """Read the trusted PSScriptAnalyzer/review-assist markdown context if set."""
    context_path = os.environ.get("REVIEW_ASSIST_CONTEXT_PATH", "").strip()
    if not context_path:
        return ""
    try:
        trusted_context_path = review_assist_context_path(context_path)
        if trusted_context_path is None:
            return ""
        content = trusted_context_path.read_text(encoding="utf-8")
        max_chars = int(getattr(config, "deep_review_max_total_chars", 24000)) // 2
        if len(content) > max_chars:
            content = content[:max_chars] + "\n...(review-assist context truncated)"
        return content.strip()
    except Exception as exc:
        print(f"WARN: could not load review-assist context from {context_path}: {exc}", file=sys.stderr, flush=True)
        return ""


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
    if hasattr(base, "apply_debug_flag"):
        base.apply_debug_flag(config, comment_body, command)

    def timeout_handler(_signum: int, _frame: Any) -> None:
        raise hardened.ReviewTimeoutError(f"{base.REVIEW_DISPLAY_NAME} exceeded script timeout of {config.script_timeout_seconds} seconds")

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
        set_python_path_alias_context(build_python_path_alias_context(gh, pr, files))
        set_python_os_alias_context(build_python_os_alias_context(gh, pr, files))
        try:
            prior_successful_review = has_prior_successful_context_review(gh, pr_number)
            reporter.update("review-mode", f"prior context review found: {str(prior_successful_review).lower()}")
        except Exception as exc:
            prior_successful_review = False
            reporter.update("review-mode", f"prior context review readback failed; using first-pass posture: {str(exc)[:240]}")
        review_mode = review_mode_for_command(comment_body, command, config, prior_successful_review)
        deep_context_block, context_summary = build_deep_context_block(gh, pr, files, config, review_mode)
        review_assist_ctx = load_review_assist_context(config)
        if review_assist_ctx:
            ra_header = "PowerShell static analysis context from last validate-on-pr run (PSScriptAnalyzer + review-assist):"
            deep_context_block = f"{ra_header}\n\n{review_assist_ctx}\n\n---\n\n{deep_context_block}".strip()
            reporter.update("review-assist-context", f"injected {len(review_assist_ctx)} chars of PSScriptAnalyzer context")
        safe_context_summary = sanitize_context_summary(context_summary, config)
        reporter.update("context", safe_context_summary)
        risk_sentinels = hardened.detect_risk_sentinels(diff, getattr(config, "risk_sentinel_max_anchors", 12))
        if risk_sentinels and getattr(config, "risk_sentinel_quality_gate", True):
            reporter.update("risk-sentinel", f"detected {len(risk_sentinels)} high-risk changed-line signals: {hardened.risk_sentinel_digest(risk_sentinels)}")
        line_index = hardened.build_added_line_index(diff)
        prompt_mode = "per-file first-pass prompts" if should_use_per_file_first_pass(review_mode, config) else "bounded whole-PR prompt"
        reporter.update("prompt", f"building {prompt_mode} from {len(files)} changed files")
        hardened.write_debug_json_artifact_safely(
            config,
            "metadata/review-context.json",
            {
                "pr_number": pr_number,
                "reviewed_head_sha": str(pr.get("head", {}).get("sha", "") or ""),
                "command": command,
                "debug": bool(getattr(config, "debug", False)),
                "workflow_run_id": base.workflow_run_id() if hasattr(base, "workflow_run_id") else os.environ.get("GITHUB_RUN_ID", ""),
                "workflow_run_url": base.workflow_run_url() if hasattr(base, "workflow_run_url") else "",
                "review_mode": review_mode,
                "context_summary": context_summary,
                "review_assist_context_chars": len(review_assist_ctx),
                "deep_context_chars": len(deep_context_block),
                "prompt_mode": prompt_mode,
                "prompt_chars": 0 if should_use_per_file_first_pass(review_mode, config) else "",
                "risk_sentinel_count": len(risk_sentinels),
                "risk_sentinel_digest": hardened.risk_sentinel_digest(risk_sentinels) if risk_sentinels else "",
                "line_index_entries": len(line_index),
                "changed_files": [
                    {
                        "filename": str(item.get("filename", "")),
                        "status": str(item.get("status", "")),
                        "additions": item.get("additions"),
                        "deletions": item.get("deletions"),
                        "changes": item.get("changes"),
                    }
                    for item in files
                ],
            },
        )
        hardened.write_debug_text_artifact_safely(config, "context/deep-context.md", deep_context_block or "(no deep context block)")
        if review_assist_ctx:
            hardened.write_debug_text_artifact_safely(config, "context/static-validation-context.md", review_assist_ctx)
        result, model_used, service_tier = openrouter_review_with_hybrid_first_pass(
            pr,
            files,
            diff,
            schema,
            config,
            reporter,
            risk_sentinels,
            line_index,
            deep_context_block,
            review_mode,
            context_summary,
            gh,
        )
        reporter.update("normalize", "mapping model findings to changed diff lines")
        findings, unanchored_findings = split_findings_with_review_body_fallback(result, config, line_index)
        findings = hardened.add_risk_sentinel_fallback_findings(findings, risk_sentinels, config, unanchored_findings)
        hardened.enforce_risk_sentinel_findings(findings, risk_sentinels, config, unanchored_findings)
        findings = synthesize_fixes_for_findings(findings, gh, pr, FIX_SYNTHESIS_SCHEMA, config, reporter)

        comments: list[dict[str, Any]] = []
        for finding in findings:
            path = str(finding["path"])
            line = int(finding["line"])
            comments.append({"path": path, "position": line_index[(path, line)], "body": base.build_inline_comment(finding, model_used, config)})

        event = "REQUEST_CHANGES" if comments and config.request_changes_on_findings else "COMMENT"
        reviewed_commit = str(pr.get("head", {}).get("sha", "") or "")
        review_body = append_context_to_review_body(
            hardened.build_review_body_with_unanchored(result, findings, unanchored_findings, model_used, config, reviewed_commit),
            review_mode,
            context_summary,
            config,
        )
        unanchored_note = f" and {len(unanchored_findings)} unanchored review-body findings" if unanchored_findings else ""
        reporter.update("github-review", f"posting GitHub review with {len(comments)} inline comments{unanchored_note}")
        gh.create_review(pr_number, review_body, event, comments, reviewed_commit)
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
        set_python_path_alias_context({})
        set_python_os_alias_context({})
        if config.script_timeout_seconds > 0 and hasattr(signal, "SIGALRM"):
            signal.alarm(0)


if __name__ == "__main__":
    main()
