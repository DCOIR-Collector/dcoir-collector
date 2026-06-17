#!/usr/bin/env python3
"""Build the DCOIR PowerShell surface inventory.

The inventory is intentionally broader than a linter target list. It records
ordinary PowerShell files, repo-specific ``.ps1.txt`` source parts, workflow
YAML files that embed PowerShell, generated/reference surfaces, and documented
exclusions so later analyzer and workflow work cannot accidentally skip them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from powershell_analyzer_contract import AnalyzerContractError, repo_relative_input_path

SCHEMA_VERSION = "dcoir_powershell_surface_inventory_v1"
ISSUE_NUMBER = 261
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_surface_inventory.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_surface_inventory.md")
REQUIRED_SOURCE_TYPES = [".ps1", ".psm1", ".psd1", ".ps1xml", ".ps1.txt", "workflow_yaml"]
KNOWN_CATEGORIES = [
    "archive_temp_vendor_artifact",
    "collector_harness_script",
    "collector_harness_source_part",
    "collector_runtime_source_part",
    "collector_runtime_wrapper",
    "collector_validation_tooling",
    "fixture_or_example",
    "generated_or_assembled_output",
    "github_workflow_support_script",
    "invalid_workflow_surface",
    "missing_authoritative_surface",
    "missing_changed_powershell_surface",
    "missing_changed_workflow_surface",
    "operator_tooling",
    "staging_artifact",
    "unclassified_powershell_surface",
    "validation_tooling",
    "workflow_embedded_powershell",
]
PRIMARY_COLLECTOR_CATEGORIES = {
    "collector_runtime_wrapper",
    "collector_runtime_source_part",
}
PRIMARY_HARNESS_CATEGORIES = {
    "collector_harness_script",
    "collector_harness_source_part",
}
REQUIRED_FULL_MODE_CATEGORIES = PRIMARY_COLLECTOR_CATEGORIES | PRIMARY_HARNESS_CATEGORIES
IGNORED_DISCOVERY_SEGMENTS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
}
POWERSHELL_FILE_SUFFIXES = (".ps1", ".psm1", ".psd1", ".ps1xml", ".ps1.txt")
WORKFLOW_MARKER_RE = re.compile(
    r"(?im)(shell:\s*(?:pwsh|powershell)\b|(?<![-.\w])pwsh(?![-.\w])|(?<![-.\w])powershell(?:\.exe)?(?![-.\w]))"
)
MANIFEST_PATH = Path("project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json")
HARNESS_PARTS_ROOT = Path("project_sources/collector/harness/source/parts")
HARNESS_GENERATED_OUTPUT = Path("project_sources/collector/harness/run_DCOIR_Tests.generated.ps1")
REQUIRED_SURFACE_PROFILES_PATH = Path("project_sources/github_actions/workflow_required_surface_profiles.json")
FLOW_STEP_KEYS = {
    "continue-on-error",
    "env",
    "id",
    "if",
    "name",
    "run",
    "shell",
    "timeout-minutes",
    "uses",
    "with",
    "working-directory",
}


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def path_parts(rel: str) -> tuple[str, ...]:
    return tuple(part.casefold() for part in Path(rel).parts)


def is_ignored_discovery_path(rel: str) -> bool:
    return any(part in IGNORED_DISCOVERY_SEGMENTS for part in path_parts(rel))


def has_prefix(rel: str, prefix: str) -> bool:
    normalized = rel.casefold()
    return normalized == prefix.casefold() or normalized.startswith(prefix.casefold().rstrip("/") + "/")


def is_powershell_file(rel: str) -> bool:
    lowered = rel.casefold()
    return lowered.endswith(POWERSHELL_FILE_SUFFIXES)


def is_workflow_yaml(rel: str) -> bool:
    lowered = rel.casefold()
    if not lowered.endswith((".yml", ".yaml")):
        return False
    return has_prefix(rel, ".github/workflows") or has_prefix(rel, ".github/actions")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def normalized_text_fact_bytes(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def workflow_yaml_shape_error(repo_root: Path, rel: str) -> str | None:
    text = read_text(repo_root / rel)
    if not text.strip():
        return f"{rel}: workflow/action YAML is empty"

    lines = text.splitlines()
    block_scalar_indent: int | None = None
    block_scalar_required_indent: int | None = None
    block_scalar_auto_indent: int | None = None

    for line_number, line in enumerate(lines, start=1):
        indent = line_indent(line)
        if line[:indent].find("\t") != -1:
            return f"{rel}: line {line_number} uses a tab for indentation"

        stripped = line.strip()
        if block_scalar_indent is not None:
            if not stripped:
                continue
            if indent > block_scalar_indent:
                if block_scalar_required_indent is not None and indent < block_scalar_required_indent:
                    return f"{rel}: line {line_number} is less indented than the YAML block scalar requires"
                if block_scalar_required_indent is None:
                    if block_scalar_auto_indent is None:
                        block_scalar_auto_indent = indent
                    elif indent < block_scalar_auto_indent:
                        return f"{rel}: line {line_number} is less indented than the YAML block scalar requires"
                continue
            block_scalar_indent = None
            block_scalar_required_indent = None
            block_scalar_auto_indent = None
        if not stripped or stripped.startswith("#"):
            continue
        if indent % 2 != 0:
            return f"{rel}: line {line_number} uses unsupported odd indentation"

        item = yaml_item_text(line)
        if not stripped.startswith("- ") and ":" not in item:
            return f"{rel}: line {line_number} has no YAML key/value separator"

        value = item.split(":", 1)[1].strip() if ":" in item else ""
        value_without_comment = strip_yaml_inline_comment(value)
        unclosed_quote = yaml_unclosed_quote(value)
        if unclosed_quote:
            return f"{rel}: line {line_number} has an unterminated quoted scalar"
        flow_error = flow_collection_shape_error(rel, line_number, item, value_without_comment)
        if flow_error:
            return flow_error
        flow_fragment_error = flow_mapping_fragment_error(rel, line_number, item, value_without_comment)
        if flow_fragment_error:
            return flow_fragment_error
        flow_step_key = unsupported_flow_step_mapping_key(
            lines,
            line_number - 1,
            item,
        )
        if flow_step_key:
            return f"{rel}: line {line_number} has unsupported flow step key {flow_step_key!r}"
        inline_steps_key = unsupported_inline_executable_steps_key(
            lines,
            line_number - 1,
            item,
            value_without_comment,
        )
        if inline_steps_key:
            return f"{rel}: line {line_number} has an unsupported inline workflow {inline_steps_key} value"
        empty_block_run_key = empty_block_scalar_run_key(lines, line_number - 1, item, value_without_comment)
        if empty_block_run_key:
            return f"{rel}: line {line_number} has an empty workflow {empty_block_run_key} value"
        unsupported_block_scalar_key = unsupported_block_scalar_workflow_string_key(
            lines,
            line_number - 1,
            item,
            value_without_comment,
        )
        if unsupported_block_scalar_key:
            return (
                f"{rel}: line {line_number} has an unsupported block-scalar workflow "
                f"{unsupported_block_scalar_key} value"
            )
        nonscalar_key = nonscalar_workflow_string_value_key(lines, line_number - 1, item, value_without_comment)
        if nonscalar_key:
            return f"{rel}: line {line_number} has a non-scalar workflow {nonscalar_key} value"
        if executable_steps_key(lines, line_number - 1) and value_without_comment:
            return f"{rel}: line {line_number} has an unsupported inline workflow steps value"
        normalized_value_without_comment = strip_yaml_node_prefixes(value_without_comment)
        if is_yaml_block_scalar_marker(normalized_value_without_comment):
            block_scalar_indent = yaml_mapping_key_indent(line)
            indicator = yaml_block_scalar_indent_indicator(normalized_value_without_comment)
            block_scalar_required_indent = block_scalar_indent + indicator if indicator is not None else None
            block_scalar_auto_indent = None
        elif is_invalid_block_scalar_like_value(normalized_value_without_comment):
            return f"{rel}: line {line_number} has an invalid YAML block scalar marker"

    for index, line in enumerate(lines):
        if not executable_steps_key(lines, index):
            continue
        steps_indent = line_indent(line)
        steps_end = block_end_line(lines, index, steps_indent)
        cursor = index + 1
        while cursor < steps_end:
            stripped = lines[cursor].strip()
            if not stripped or stripped.startswith("#"):
                cursor += 1
                continue
            if not stripped.startswith("- "):
                return f"{rel}: line {cursor + 1} has a non-list entry directly under steps"
            item = yaml_item_text_without_comment(lines[cursor])
            normalized_item = strip_yaml_node_prefixes(item)
            if normalized_item.startswith("*"):
                return f"{rel}: line {cursor + 1} has an unsupported alias workflow step value"
            if normalized_item.startswith("["):
                return f"{rel}: line {cursor + 1} has an unsupported inline workflow step value"
            if normalized_item and ":" not in normalized_item and not normalized_item.startswith("{"):
                return f"{rel}: line {cursor + 1} has a non-mapping step entry"
            step_indent = line_indent(lines[cursor])
            step_end = cursor + 1
            while step_end < steps_end:
                step_stripped = lines[step_end].strip()
                if step_stripped and line_indent(lines[step_end]) == step_indent:
                    if step_stripped.startswith("- "):
                        break
                    return f"{rel}: line {step_end + 1} has a non-list entry directly under steps"
                misindented_key = misindented_step_workflow_key(lines, cursor, step_end, step_indent)
                if misindented_key:
                    return (
                        f"{rel}: line {step_end + 1} has a misindented workflow "
                        f"{misindented_key} value"
                    )
                step_end += 1
            cursor = step_end
    return None


def path_resolves_inside_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def path_is_file_inside_repo(path: Path, repo_root: Path) -> bool:
    return path_resolves_inside_repo(path, repo_root) and path.is_file()


def path_is_dir_inside_repo(path: Path, repo_root: Path) -> bool:
    return path_resolves_inside_repo(path, repo_root) and path.is_dir()


def repo_file_exists(repo_root: Path, rel: str) -> bool:
    return path_is_file_inside_repo(repo_root / rel, repo_root)

def file_facts(repo_root: Path, rel: str, exists: bool) -> dict[str, Any]:
    path = repo_root / rel
    if not path_resolves_inside_repo(path, repo_root):
        return {
            "size_bytes": None,
            "line_count": None,
            "sha256": None,
        }
    if not exists:
        return {
            "size_bytes": None,
            "line_count": None,
            "sha256": None,
        }
    try:
        data = path.read_bytes()
    except OSError:
        return {
            "size_bytes": None,
            "line_count": None,
            "sha256": None,
        }
    fact_data = normalized_text_fact_bytes(data)
    return {
        "size_bytes": len(fact_data),
        "line_count": fact_data.count(b"\n") + (1 if fact_data and not fact_data.endswith(b"\n") else 0),
        "sha256": hashlib.sha256(fact_data).hexdigest(),
    }

def source_type_for(rel: str) -> str:
    lowered = rel.casefold()
    if lowered.endswith(".ps1.txt"):
        return ".ps1.txt"
    if is_workflow_yaml(rel):
        return "workflow_yaml"
    for suffix in (".ps1xml", ".psm1", ".psd1", ".ps1"):
        if lowered.endswith(suffix):
            return suffix
    return "unknown"


def generated_like(rel: str) -> bool:
    parts = path_parts(rel)
    generated_segments = {
        "compiled_runtime",
        "generated",
        "generated_output",
        "dist",
        "build",
        "output",
        "outputs",
    }
    if any(part in generated_segments for part in parts):
        return True
    return any(part.startswith("out_") or part.startswith("out-") for part in parts)


def fixture_like(rel: str) -> bool:
    parts = path_parts(rel)
    return any(part in {"fixture", "fixtures", "examples", "example", "samples", "sample"} for part in parts)


def staging_like(rel: str) -> bool:
    return has_prefix(rel, "chatgpt_staging")


def archive_temp_vendor_like(rel: str) -> bool:
    parts = path_parts(rel)
    return any(part in {"archive", "archived", "temp", "tmp", "vendor", "third_party"} for part in parts)


def make_surface(
    repo_root: Path,
    rel: str,
    category: str,
    status: str,
    decision: str,
    reason: str,
    exists: bool,
    marker_lines: list[int] | None = None,
    embedded_snippets: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    surface = {
        "path": rel,
        "category": category,
        "source_type": source_type_for(rel),
        "status": status,
        "inclusion_decision": decision,
        "decision_reason": reason,
        "exists": exists,
        "marker_lines": marker_lines or [],
        "embedded_snippets": embedded_snippets or [],
    }
    surface.update(file_facts(repo_root, rel, exists))
    return surface


def line_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def yaml_item_text(line: str) -> str:
    stripped = line.strip()
    return stripped[2:].strip() if stripped.startswith("- ") else stripped


def yaml_item_text_without_comment(line: str) -> str:
    return strip_yaml_inline_comment(yaml_item_text(line))


def strip_yaml_node_prefixes(item: str) -> str:
    candidate = item.strip()
    while candidate:
        if candidate.startswith("&"):
            match = re.match(r"&[^\s\[\]\{\},]+(?:\s+|$)", candidate)
            if not match:
                return candidate
            candidate = candidate[match.end():].lstrip()
            continue
        if candidate.startswith("!<"):
            end = candidate.find(">")
            if end == -1:
                return candidate
            following = candidate[end + 1:]
            if following and not following[0].isspace():
                return candidate
            candidate = following.lstrip()
            continue
        if candidate.startswith("!"):
            match = re.match(r"![^\s\[\]\{\},]+(?:\s+|$)", candidate)
            if not match:
                return candidate
            candidate = candidate[match.end():].lstrip()
            continue
        return candidate
    return candidate


def normalize_workflow_scalar(value: str) -> str:
    return clean_shell_value(strip_yaml_node_prefixes(strip_yaml_inline_comment(value))).strip()


def workflow_scalar_is_alias(value: str) -> bool:
    return strip_yaml_node_prefixes(strip_yaml_inline_comment(value)).startswith("*")


def yaml_mapping_key_indent(line: str) -> int:
    indent = line_indent(line)
    return indent + 2 if line.strip().startswith("- ") else indent


def yaml_key_name(item: str) -> str:
    if ":" not in item:
        return ""
    return clean_shell_value(item.split(":", 1)[0]).casefold()


def cleaned_workflow_string(value: str) -> str:
    return normalize_workflow_scalar(value)


def empty_workflow_string(value: str) -> bool:
    return cleaned_workflow_string(value) == ""


def previous_parent_index(lines: list[str], index: int) -> int | None:
    current_indent = line_indent(lines[index])
    for candidate in range(index - 1, -1, -1):
        stripped = lines[candidate].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line_indent(lines[candidate]) < current_indent:
            return candidate
    return None


def direct_step_mapping_key(lines: list[str], index: int) -> bool:
    for start, end, _inherited_shell in step_blocks(lines):
        if start <= index < end:
            step_indent = line_indent(lines[start])
            return index == start or line_indent(lines[index]) == step_indent + 2
    return False


def direct_child_key(parent_line: str, child_line: str, key_name: str) -> bool:
    return line_indent(child_line) == line_indent(parent_line) + 2 and yaml_key_name(
        yaml_item_text_without_comment(child_line)
    ) == key_name


def executable_steps_key(lines: list[str], index: int) -> bool:
    item = yaml_item_text_without_comment(lines[index])
    if yaml_key_name(item) != "steps":
        return False

    parent = previous_parent_index(lines, index)
    if parent is None:
        return False
    parent_item = yaml_item_text_without_comment(lines[parent])

    if (
        line_indent(lines[parent]) == 0
        and yaml_key_name(parent_item) == "runs"
        and direct_child_key(lines[parent], lines[index], "steps")
    ):
        return True

    grandparent = previous_parent_index(lines, parent)
    return (
        grandparent is not None
        and line_indent(lines[grandparent]) == 0
        and yaml_key_name(yaml_item_text_without_comment(lines[grandparent])) == "jobs"
        and direct_child_key(lines[parent], lines[index], "steps")
    )


def defaults_run_shell_key(lines: list[str], index: int) -> bool:
    parent = previous_parent_index(lines, index)
    if parent is None or not yaml_item_text_without_comment(lines[parent]).startswith("run:"):
        return False
    grandparent = previous_parent_index(lines, parent)
    return grandparent is not None and yaml_item_text_without_comment(lines[grandparent]).startswith("defaults:")


def defaults_run_mapping_key(lines: list[str], index: int) -> bool:
    parent = previous_parent_index(lines, index)
    return parent is not None and yaml_item_text_without_comment(lines[parent]).startswith("defaults:")


def unquoted_flow_collection_value(value: str) -> bool:
    stripped = strip_yaml_node_prefixes(strip_yaml_inline_comment(value))
    if len(stripped) < 2 or stripped[0] in {"'", '"'}:
        return False
    return (stripped[0] == "[" and stripped[-1] == "]") or (stripped[0] == "{" and stripped[-1] == "}")


def unsupported_workflow_shell_value(value: str) -> bool:
    cleaned = cleaned_workflow_string(value)
    return (
        cleaned == ""
        or workflow_scalar_is_alias(value)
        or "${{" in cleaned
        or unquoted_flow_collection_value(value)
        or is_yaml_block_scalar_marker(cleaned)
    )


def flow_mapping_pieces(item: str) -> list[str] | None:
    stripped = strip_yaml_node_prefixes(strip_yaml_inline_comment(item))
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return None
    content = stripped[1:-1]
    pieces: list[str] = []
    current: list[str] = []
    quote: str | None = None
    depth = 0
    index = 0
    while index < len(content):
        character = content[index]
        if quote:
            current.append(character)
            if quote == "'" and character == "'" and index + 1 < len(content) and content[index + 1] == "'":
                current.append(content[index + 1])
                index += 2
                continue
            if quote == '"' and character == "\\" and index + 1 < len(content):
                current.append(content[index + 1])
                index += 2
                continue
            if character == quote:
                quote = None
            index += 1
            continue
        if character in {"'", '"'} and yaml_quote_can_start(content, index):
            quote = character
            current.append(character)
        elif character in "[{":
            depth += 1
            current.append(character)
        elif character in "]}":
            depth = max(0, depth - 1)
            current.append(character)
        elif character == "," and depth == 0:
            pieces.append("".join(current).strip())
            current = []
        else:
            current.append(character)
        index += 1
    if current:
        pieces.append("".join(current).strip())
    return pieces


def flow_collection_shape_error(rel: str, line_number: int, item: str, value_without_comment: str) -> str | None:
    candidate = strip_yaml_node_prefixes(strip_yaml_inline_comment(item))
    if not candidate.startswith(("{", "[")):
        candidate = strip_yaml_node_prefixes(value_without_comment).strip()
    if not candidate or candidate[0] not in {"{", "["} or candidate[0] in {"'", '"'}:
        return None

    pairs = {"[": "]", "{": "}"}
    closing = {"]", "}"}
    stack: list[tuple[str, int]] = []
    quote: str | None = None
    index = 0
    while index < len(candidate):
        character = candidate[index]
        if quote:
            if quote == "'" and character == "'" and index + 1 < len(candidate) and candidate[index + 1] == "'":
                index += 2
                continue
            if quote == '"' and character == "\\" and index + 1 < len(candidate):
                index += 2
                continue
            if character == quote:
                quote = None
            index += 1
            continue
        if character in {"'", '"'} and yaml_quote_can_start(candidate, index):
            quote = character
        elif character in pairs:
            stack.append((character, line_number))
        elif character in closing:
            if not stack or pairs[stack[-1][0]] != character:
                return f"{rel}: line {line_number} has an unmatched {character!r}"
            stack.pop()
        index += 1
    if stack:
        opener, opener_line = stack[-1]
        return f"{rel}: line {opener_line} has an unclosed {opener!r}"
    return None


def flow_mapping_fragment_error(rel: str, line_number: int, item: str, value_without_comment: str) -> str | None:
    candidate = strip_yaml_node_prefixes(strip_yaml_inline_comment(item))
    if not candidate.startswith("{"):
        candidate = strip_yaml_node_prefixes(value_without_comment).strip()
    if not candidate or candidate[0] != "{" or candidate[0] in {"'", '"'}:
        return None

    pieces = flow_mapping_pieces(candidate)
    if pieces is None:
        return None
    for piece in pieces:
        if piece and ":" not in piece:
            return f"{rel}: line {line_number} has an unsupported flow mapping fragment"
    return None


def unsupported_flow_step_mapping_key(
    lines: list[str],
    index: int,
    item: str,
) -> str | None:
    if not direct_step_mapping_key(lines, index):
        return None
    candidate = strip_yaml_node_prefixes(strip_yaml_inline_comment(item))
    if not candidate.startswith("{"):
        return None

    for key in split_flow_mapping(candidate):
        if key not in FLOW_STEP_KEYS:
            return key
    return None


def flow_mapping_has_direct_key(text: str, key: str) -> bool:
    return key in split_flow_mapping(text)


def unsupported_workflow_run_value(value: str) -> bool:
    return workflow_scalar_is_alias(value) or unquoted_flow_collection_value(value)


def unsupported_inline_executable_steps_key(
    lines: list[str],
    index: int,
    item: str,
    value_without_comment: str,
) -> str | None:
    normalized_value = strip_yaml_node_prefixes(value_without_comment)
    if not normalized_value.startswith("{"):
        return None

    key = yaml_key_name(item)
    if (
        key == "runs"
        and line_indent(lines[index]) == 0
        and flow_mapping_has_direct_key(normalized_value, "steps")
    ):
        return "runs.steps"

    if key == "jobs" and line_indent(lines[index]) == 0:
        for job_value in split_flow_mapping(normalized_value).values():
            if flow_mapping_has_direct_key(job_value, "steps"):
                return "jobs.steps"

    parent = previous_parent_index(lines, index)
    if parent is None:
        return None
    parent_item = yaml_item_text_without_comment(lines[parent])
    if (
        line_indent(lines[parent]) == 0
        and yaml_key_name(parent_item) == "jobs"
        and line_indent(lines[index]) == line_indent(lines[parent]) + 2
        and flow_mapping_has_direct_key(normalized_value, "steps")
    ):
        return "jobs.steps"
    return None


def block_scalar_has_nonblank_content(lines: list[str], index: int, marker: str) -> bool:
    indent = yaml_mapping_key_indent(lines[index])
    end_line = block_end_line(lines, index, indent)
    content_indent = yaml_block_scalar_content_indent(lines, index + 1, end_line, indent, marker)
    for follow in lines[index + 1:end_line]:
        if not follow.strip():
            continue
        content = follow[content_indent:] if len(follow) >= content_indent else follow.strip()
        if content.strip():
            return True
    return False


def empty_block_scalar_run_key(
    lines: list[str],
    index: int,
    item: str,
    value_without_comment: str,
) -> str | None:
    marker = strip_yaml_node_prefixes(value_without_comment)
    if (
        yaml_key_name(item) == "run"
        and direct_step_mapping_key(lines, index)
        and is_yaml_block_scalar_marker(marker)
        and not block_scalar_has_nonblank_content(lines, index, marker)
    ):
        return "run"
    return None


def unsupported_block_scalar_workflow_string_key(
    lines: list[str],
    index: int,
    item: str,
    value_without_comment: str,
) -> str | None:
    if not is_yaml_block_scalar_marker(strip_yaml_node_prefixes(value_without_comment)):
        return None
    key = yaml_key_name(item)
    if key == "shell" and direct_step_mapping_key(lines, index):
        return "shell"
    if key == "shell" and defaults_run_shell_key(lines, index):
        return "defaults.run.shell"
    return None


def nested_content_index(lines: list[str], index: int) -> int | None:
    parent_indent = yaml_mapping_key_indent(lines[index])
    for candidate in range(index + 1, len(lines)):
        stripped = lines[candidate].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line_indent(lines[candidate]) <= parent_indent:
            return None
        return candidate
    return None


def has_block_collection_child(lines: list[str], index: int) -> bool:
    child = nested_content_index(lines, index)
    if child is None:
        return False
    child_item = yaml_item_text(lines[child])
    child_value = child_item.split(":", 1)[1].strip() if ":" in child_item else ""
    if lines[child].strip().startswith("- "):
        return True
    if child_item.startswith(("{", "[")):
        return True
    if ":" in child_item and not is_yaml_block_scalar_marker(strip_yaml_inline_comment(child_value)):
        return True
    return False


def nonscalar_workflow_string_value_key(
    lines: list[str],
    index: int,
    item: str,
    value_without_comment: str,
) -> str | None:
    flow = split_flow_mapping(item)
    if flow and direct_step_mapping_key(lines, index):
        if "run" in flow:
            if empty_workflow_string(flow["run"]) or unsupported_workflow_run_value(flow["run"]):
                return "run"
        if "shell" in flow and unsupported_workflow_shell_value(flow["shell"]):
            return "shell"

    key = yaml_key_name(item)
    if key == "run" and direct_step_mapping_key(lines, index):
        if unsupported_workflow_run_value(value_without_comment):
            return "run"
        if empty_workflow_string(value_without_comment):
            if (
                value_without_comment
                or has_block_collection_child(lines, index)
                or nested_content_index(lines, index) is None
            ):
                return "run"
    if key == "shell" and direct_step_mapping_key(lines, index):
        if unsupported_workflow_shell_value(value_without_comment):
            return "shell"
    if key == "shell" and defaults_run_shell_key(lines, index):
        if unsupported_workflow_shell_value(value_without_comment):
            return "defaults.run.shell"
    if key == "defaults":
        inline_shell = inline_shell_value(value_without_comment)
        if inline_shell is not None:
            if unsupported_workflow_shell_value(inline_shell):
                return "defaults.run.shell"
    if key == "run" and defaults_run_mapping_key(lines, index):
        inline_shell = inline_shell_value(value_without_comment)
        if inline_shell is not None:
            if unsupported_workflow_shell_value(inline_shell):
                return "defaults.run.shell"
    return None


def block_end_line(lines: list[str], start_index: int, block_indent: int, max_end: int | None = None) -> int:
    limit = max_end if max_end is not None else len(lines)
    end_line = start_index + 1
    for index in range(start_index + 1, limit):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            end_line = index + 1
            continue
        indent = line_indent(line)
        if indent <= block_indent:
            break
        end_line = index + 1
    return end_line


def collect_run_block(lines: list[str], run_index: int, max_end: int | None = None) -> tuple[int, str]:
    line = lines[run_index]
    indent = yaml_mapping_key_indent(line)
    after_colon = line.split(":", 1)[1].strip() if ":" in line else ""
    block_marker = strip_yaml_node_prefixes(strip_yaml_inline_comment(after_colon))
    if after_colon and not is_yaml_block_scalar_marker(block_marker):
        return run_index + 1, normalize_workflow_scalar(block_marker)
    end_line = block_end_line(lines, run_index, indent, max_end)
    content_indent = yaml_block_scalar_content_indent(lines, run_index + 1, end_line, indent, block_marker)
    command_lines: list[str] = []
    for follow in lines[run_index + 1:end_line]:
        if not follow.strip():
            command_lines.append("")
        else:
            command_lines.append(follow[content_indent:] if len(follow) >= content_indent else follow.strip())
    return end_line, normalize_block_scalar_command(command_lines, block_marker)


def normalize_block_scalar_command(command_lines: list[str], marker: str) -> str:
    if not marker.strip().startswith(">"):
        return "\n".join(command_lines).rstrip()

    folded_lines: list[str] = []
    paragraph: list[str] = []
    for line in command_lines:
        if line == "":
            if paragraph:
                folded_lines.append(" ".join(paragraph))
                paragraph = []
            folded_lines.append("")
        else:
            paragraph.append(line)
    if paragraph:
        folded_lines.append(" ".join(paragraph))
    return "\n".join(folded_lines).rstrip()


def strip_yaml_inline_comment(value: str) -> str:
    stripped, _quote = strip_yaml_inline_comment_with_quote(value)
    return stripped


def strip_yaml_inline_comment_with_quote(value: str) -> tuple[str, str | None]:
    quote: str | None = None
    index = 0
    while index < len(value):
        character = value[index]
        if quote:
            if quote == "'" and character == "'" and index + 1 < len(value) and value[index + 1] == "'":
                index += 2
                continue
            if quote == '"' and character == "\\" and index + 1 < len(value):
                index += 2
                continue
            if character == quote:
                quote = None
            index += 1
            continue
        if character in {"'", '"'} and yaml_quote_can_start(value, index):
            quote = character
        elif character == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip(), None
        index += 1
    return value.strip(), quote


def yaml_unclosed_quote(value: str) -> str | None:
    _stripped, quote = strip_yaml_inline_comment_with_quote(value)
    return quote


def yaml_quote_can_start(value: str, index: int) -> bool:
    prefix = value[:index]
    if not prefix.strip():
        return True
    previous_non_space = prefix.rstrip()[-1]
    return previous_non_space in {"[", "{", ",", ":"}


def is_yaml_block_scalar_marker(value: str) -> bool:
    marker = value.strip()
    if not marker or marker[0] not in {"|", ">"}:
        return False
    chomping = False
    indentation = False
    for character in marker[1:]:
        if character in "+-":
            if chomping:
                return False
            chomping = True
        elif character in "123456789":
            if indentation:
                return False
            indentation = True
        else:
            return False
    return True


def yaml_block_scalar_indent_indicator(value: str) -> int | None:
    marker = value.strip()
    if not is_yaml_block_scalar_marker(marker):
        return None
    for character in marker[1:]:
        if character in "123456789":
            return int(character)
    return None


def yaml_block_scalar_content_indent(
    lines: list[str],
    start_index: int,
    end_index: int,
    header_indent: int,
    marker: str,
) -> int:
    indicator = yaml_block_scalar_indent_indicator(marker)
    if indicator is not None:
        return header_indent + indicator
    for line in lines[start_index:end_index]:
        if line.strip():
            return line_indent(line)
    return header_indent + 2


def is_invalid_block_scalar_like_value(value: str) -> bool:
    marker = strip_yaml_node_prefixes(value).strip()
    if not marker or is_yaml_block_scalar_marker(marker):
        return False
    if marker[0] in {"|", ">"}:
        return True
    if len(marker) >= 2 and marker[0] in {"'", '"'} and marker[-1] == marker[0]:
        inner = marker[1:-1].strip()
        return bool(inner) and inner[0] in {"|", ">"}
    return False


def parent_block_start(lines: list[str], index: int) -> int:
    current_indent = line_indent(lines[index])
    for candidate in range(index - 1, -1, -1):
        stripped = lines[candidate].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line_indent(lines[candidate]) < current_indent:
            return candidate
    return 0


def clean_shell_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        inner = cleaned[1:-1]
        if cleaned[0] == "'":
            return inner.replace("''", "'")
        return inner
    return cleaned


def split_flow_mapping(item: str) -> dict[str, str]:
    pieces = flow_mapping_pieces(item)
    if pieces is None:
        return {}

    mapping: dict[str, str] = {}
    for piece in pieces:
        if ":" not in piece:
            continue
        key, value = piece.split(":", 1)
        key = clean_shell_value(key).casefold()
        if key:
            mapping[key] = normalize_workflow_scalar(value)
    return mapping


def shell_executable(value: str) -> str:
    cleaned = normalize_workflow_scalar(value)
    if not cleaned:
        return ""
    first_token = cleaned.split()[0]
    if first_token[0] not in {"'", '"'} and "\\" in first_token:
        return re.split(r"[\\/]+", first_token)[-1].casefold()
    try:
        parts = shlex.split(cleaned)
    except ValueError:
        parts = cleaned.split()
    if not parts:
        return ""
    return re.split(r"[\\/]+", parts[0])[-1].casefold()


def is_powershell_shell(value: str) -> bool:
    return shell_executable(value) in {"pwsh", "pwsh.exe", "powershell", "powershell.exe"}


def shell_line_without_comment(line: str) -> str:
    quote: str | None = None
    index = 0
    while index < len(line):
        character = line[index]
        if quote:
            if character == "\\" and index + 1 < len(line):
                index += 2
                continue
            if character == quote:
                quote = None
            index += 1
            continue
        if character in {"'", '"'}:
            quote = character
        elif character == "#" and (index == 0 or line[index - 1].isspace()):
            return line[:index].rstrip()
        index += 1
    return line


def command_text_for_marker_scan(command: str) -> str:
    command_lines: list[str] = []
    for line in command.splitlines():
        if line.strip().startswith("#"):
            continue
        stripped = shell_line_without_comment(line).strip()
        if stripped:
            command_lines.append(stripped)
    return "\n".join(command_lines)


def inline_shell_value(text: str) -> str | None:
    mapping = split_flow_mapping(text)
    if not mapping:
        return None
    if "shell" in mapping:
        return mapping["shell"]
    run_value = mapping.get("run")
    if not run_value:
        return None
    return split_flow_mapping(run_value).get("shell")


def defaults_inline_shell(item: str) -> str | None:
    if ":" not in item:
        return None
    value = item.split(":", 1)[1].strip()
    if not value:
        return None
    return inline_shell_value(value)


def run_inline_shell(item: str) -> str | None:
    if ":" not in item:
        return None
    value = item.split(":", 1)[1].strip()
    if not value:
        return None
    return inline_shell_value(value)


def direct_defaults_shell(lines: list[str], defaults_index: int, parent_end: int) -> str | None:
    defaults_item = yaml_item_text_without_comment(lines[defaults_index])
    inline = defaults_inline_shell(defaults_item)
    if inline:
        return inline

    defaults_indent = line_indent(lines[defaults_index])
    defaults_end = block_end_line(lines, defaults_index, defaults_indent, parent_end)
    run_index = None
    run_indent = 0
    for candidate in range(defaults_index + 1, defaults_end):
        if line_indent(lines[candidate]) != defaults_indent + 2:
            continue
        candidate_item = yaml_item_text_without_comment(lines[candidate])
        if candidate_item.startswith("run:"):
            inline_run_shell = run_inline_shell(candidate_item)
            if inline_run_shell:
                return inline_run_shell
            if candidate_item == "run:":
                run_index = candidate
                run_indent = line_indent(lines[candidate])
                break
    if run_index is None:
        return None

    run_end = block_end_line(lines, run_index, run_indent, defaults_end)
    for candidate in range(run_index + 1, run_end):
        if line_indent(lines[candidate]) != run_indent + 2:
            continue
        candidate_item = yaml_item_text_without_comment(lines[candidate])
        if candidate_item.startswith("shell:"):
            return normalize_workflow_scalar(candidate_item.split(":", 1)[1])
    return None


def step_line_has_ancestor_key(
    lines: list[str],
    step_start: int,
    index: int,
    ancestor_key: str,
    ancestor_indent: int,
) -> bool:
    for candidate in range(index - 1, step_start, -1):
        stripped = lines[candidate].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line_indent(lines[candidate]) != ancestor_indent:
            continue
        return yaml_key_name(yaml_item_text_without_comment(lines[candidate])) == ancestor_key
    return False


def step_child_ancestor_key(lines: list[str], step_start: int, index: int, child_indent: int) -> str | None:
    for candidate in range(index - 1, step_start, -1):
        stripped = lines[candidate].strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = line_indent(lines[candidate])
        if indent < child_indent:
            return None
        if indent == child_indent:
            return yaml_key_name(yaml_item_text_without_comment(lines[candidate]))
    return None


def line_is_within_step_run_block_scalar(
    lines: list[str],
    step_start: int,
    index: int,
    child_indent: int,
) -> bool:
    for candidate in range(index - 1, step_start, -1):
        stripped = lines[candidate].strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = line_indent(lines[candidate])
        if indent < child_indent:
            return False
        if indent != child_indent:
            continue
        item = yaml_item_text_without_comment(lines[candidate])
        if yaml_key_name(item) != "run":
            return False
        value = item.split(":", 1)[1].strip() if ":" in item else ""
        return is_yaml_block_scalar_marker(strip_yaml_node_prefixes(strip_yaml_inline_comment(value)))
    return False


def misindented_step_workflow_key(
    lines: list[str],
    step_start: int,
    index: int,
    step_indent: int,
) -> str | None:
    if index <= step_start or index >= len(lines):
        return None
    stripped = lines[index].strip()
    if not stripped or stripped.startswith("#"):
        return None
    indent = line_indent(lines[index])
    child_indent = step_indent + 2
    if indent <= child_indent:
        return None
    key = yaml_key_name(yaml_item_text_without_comment(lines[index]))
    if key not in FLOW_STEP_KEYS:
        return None
    ancestor_key = step_child_ancestor_key(lines, step_start, index, child_indent)
    if ancestor_key and ancestor_key not in FLOW_STEP_KEYS:
        return None
    if step_line_has_ancestor_key(lines, step_start, index, "env", child_indent):
        return None
    if step_line_has_ancestor_key(lines, step_start, index, "with", child_indent):
        return None
    if line_is_within_step_run_block_scalar(lines, step_start, index, child_indent):
        return None
    return key


def workflow_default_shell(lines: list[str]) -> str | None:
    for index in range(0, len(lines)):
        item = yaml_item_text_without_comment(lines[index])
        if line_indent(lines[index]) != 0 or not item.startswith("defaults:"):
            continue
        shell = direct_defaults_shell(lines, index, block_end_line(lines, index, 0))
        if shell:
            return shell
    return None


def job_default_shell(lines: list[str], job_start: int, job_end: int) -> str | None:
    job_indent = line_indent(lines[job_start])
    for index in range(job_start + 1, job_end):
        item = yaml_item_text_without_comment(lines[index])
        if line_indent(lines[index]) != job_indent + 2 or not item.startswith("defaults:"):
            continue
        shell = direct_defaults_shell(lines, index, job_end)
        if shell:
            return shell
    return None


def default_shell_for_steps(lines: list[str], steps_index: int) -> str | None:
    job_start = parent_block_start(lines, steps_index)
    job_end = block_end_line(lines, job_start, line_indent(lines[job_start]))
    return job_default_shell(lines, job_start, job_end) or workflow_default_shell(lines)


def step_blocks(lines: list[str]) -> list[tuple[int, int, str | None]]:
    blocks: list[tuple[int, int, str | None]] = []
    for index, line in enumerate(lines):
        if not executable_steps_key(lines, index):
            continue
        steps_indent = line_indent(line)
        steps_end = block_end_line(lines, index, steps_indent)
        inherited_shell = default_shell_for_steps(lines, index)
        cursor = index + 1
        while cursor < steps_end:
            stripped = lines[cursor].strip()
            if not stripped or stripped.startswith("#"):
                cursor += 1
                continue
            if stripped.startswith("- "):
                step_indent = line_indent(lines[cursor])
                end = cursor + 1
                while end < steps_end:
                    end_stripped = lines[end].strip()
                    if end_stripped and line_indent(lines[end]) == step_indent and end_stripped.startswith("- "):
                        break
                    end += 1
                blocks.append((cursor, end, inherited_shell))
                cursor = end
                continue
            cursor += 1
    return blocks


def parse_step_snippet(
    lines: list[str],
    start: int,
    end: int,
    inherited_shell: str | None,
    rel: str,
) -> dict[str, Any] | None:
    step_name = ""
    explicit_shell: tuple[int, str] | None = None
    run_line = None
    command = ""
    run_end = start + 1
    step_indent = line_indent(lines[start])
    child_indent = step_indent + 2
    for index in range(start, end):
        direct_key = index == start or line_indent(lines[index]) == child_indent
        if not direct_key:
            continue
        item = strip_yaml_node_prefixes(yaml_item_text(lines[index]))
        flow = split_flow_mapping(item) if index == start else {}
        if flow:
            if "name" in flow:
                step_name = flow["name"]
            if "shell" in flow:
                explicit_shell = (index + 1, flow["shell"])
            if "run" in flow:
                run_line = index
                run_end = index + 1
                command = flow["run"]
        elif item.startswith("name:"):
            step_name = normalize_workflow_scalar(item.split(":", 1)[1])
        elif item.startswith("shell:"):
            shell = normalize_workflow_scalar(item.split(":", 1)[1])
            explicit_shell = (index + 1, shell)
        elif item.startswith("run:"):
            run_line = index
            run_end, command = collect_run_block(lines, index, end)

    if run_line is None:
        return None
    effective_shell = explicit_shell[1] if explicit_shell else (inherited_shell or "unspecified")
    marker_command = command if is_powershell_shell(effective_shell) else command_text_for_marker_scan(command)
    if not is_powershell_shell(effective_shell) and not WORKFLOW_MARKER_RE.search(marker_command):
        return None
    line_start = min(explicit_shell[0], run_line + 1) if explicit_shell else run_line + 1
    line_end = max(run_end, explicit_shell[0]) if explicit_shell else run_end
    return {
        "source_file": rel,
        "step_or_action": step_name or "(unnamed step)",
        "shell": effective_shell,
        "line_start": line_start,
        "line_end": line_end,
        "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest() if command else "",
        "command_preview": command[:240],
    }


def extract_workflow_snippets(repo_root: Path, rel: str) -> list[dict[str, Any]]:
    lines = read_text(repo_root / rel).splitlines()
    snippets: list[dict[str, Any]] = []
    for start, end, inherited_shell in step_blocks(lines):
        snippet = parse_step_snippet(lines, start, end, inherited_shell, rel)
        if snippet is not None:
            snippets.append(snippet)
    return snippets


def classify_surface(repo_root: Path, rel: str, exists: bool = True) -> dict[str, Any] | None:
    if is_workflow_yaml(rel):
        if not exists:
            return make_surface(
                repo_root,
                rel,
                "missing_changed_workflow_surface",
                "missing",
                "fail",
                "Changed workflow/action YAML path is missing from the working tree.",
                exists,
            )
        workflow_error = workflow_yaml_shape_error(repo_root, rel)
        if workflow_error:
            return make_surface(
                repo_root,
                rel,
                "invalid_workflow_surface",
                "invalid",
                "fail",
                workflow_error,
                exists,
            )
        snippets = extract_workflow_snippets(repo_root, rel) if exists else []
        if not snippets:
            return None
        markers = sorted({snippet["line_start"] for snippet in snippets})
        return make_surface(
            repo_root,
            rel,
            "workflow_embedded_powershell",
            "workflow_embedded",
            "reference",
            "Workflow or composite-action YAML embeds PowerShell and needs later snippet-aware handling.",
            exists,
            markers,
            snippets,
        )

    if not is_powershell_file(rel):
        return None

    if not exists:
        return make_surface(
            repo_root,
            rel,
            "missing_changed_powershell_surface",
            "missing",
            "fail",
            "Changed PowerShell-relevant path is missing from the working tree.",
            exists,
        )

    if rel == "project_sources/collector/source/DCOIR_Collector.ps1":
        return make_surface(
            repo_root,
            rel,
            "collector_runtime_wrapper",
            "source",
            "include",
            "Collector runtime wrapper is a primary maintained PowerShell surface.",
            exists,
        )

    if has_prefix(rel, "project_sources/collector/source/parts"):
        return make_surface(
            repo_root,
            rel,
            "collector_runtime_source_part",
            "source",
            "include",
            "Collector runtime source part is primary maintained PowerShell source.",
            exists,
        )

    if has_prefix(rel, "project_sources/collector/harness/source/parts"):
        return make_surface(
            repo_root,
            rel,
            "collector_harness_source_part",
            "source_part",
            "include",
            "Collector harness source part is primary maintained PowerShell source.",
            exists,
        )

    if rel == HARNESS_GENERATED_OUTPUT.as_posix() or generated_like(rel):
        return make_surface(
            repo_root,
            rel,
            "generated_or_assembled_output",
            "generated",
            "reference",
            "Generated or assembled output is covered as parity/reference evidence, not source truth.",
            exists,
        )

    if has_prefix(rel, "project_sources/collector/harness"):
        return make_surface(
            repo_root,
            rel,
            "collector_harness_script",
            "source",
            "include",
            "Collector harness script is a primary maintained PowerShell surface.",
            exists,
        )

    if has_prefix(rel, "project_sources/collector/tools"):
        return make_surface(
            repo_root,
            rel,
            "collector_validation_tooling",
            "tooling",
            "include",
            "Collector validation/tooling script is maintained repo PowerShell.",
            exists,
        )

    if rel == "project_sources/collector/PSScriptAnalyzerSettings.psd1":
        return make_surface(
            repo_root,
            rel,
            "collector_validation_tooling",
            "tooling",
            "include",
            "Repository-owned PowerShell analyzer policy is maintained validation tooling.",
            exists,
        )

    if staging_like(rel):
        return make_surface(
            repo_root,
            rel,
            "staging_artifact",
            "staging",
            "exclude",
            "ChatGPT staging scripts are historical execution artifacts, not maintained source.",
            exists,
        )

    if archive_temp_vendor_like(rel):
        return make_surface(
            repo_root,
            rel,
            "archive_temp_vendor_artifact",
            "excluded_artifact",
            "exclude",
            "Archive, temp, or vendor path is not a maintained PowerShell validation target.",
            exists,
        )

    if fixture_like(rel):
        return make_surface(
            repo_root,
            rel,
            "fixture_or_example",
            "fixture",
            "reference",
            "Fixture/example PowerShell is inventoried separately from maintained source targets.",
            exists,
        )

    if has_prefix(rel, ".github/scripts"):
        return make_surface(
            repo_root,
            rel,
            "github_workflow_support_script",
            "tooling",
            "include",
            "GitHub workflow support script is maintained repo PowerShell.",
            exists,
        )

    if has_prefix(rel, "operator_tools"):
        return make_surface(
            repo_root,
            rel,
            "operator_tooling",
            "tooling",
            "include",
            "Operator tooling PowerShell is maintained repo tooling.",
            exists,
        )

    if has_prefix(rel, "project_sources/validation") or has_prefix(rel, "scripts"):
        return make_surface(
            repo_root,
            rel,
            "validation_tooling",
            "tooling",
            "include",
            "Validation PowerShell is maintained repo tooling.",
            exists,
        )

    return make_surface(
        repo_root,
        rel,
        "unclassified_powershell_surface",
        "unknown",
        "fail",
        "PowerShell-relevant path has no inventory category.",
        exists,
    )


def git_tracked_files(repo_root: Path) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            capture_output=True,
            text=False,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    paths = [path.decode("utf-8", errors="ignore") for path in completed.stdout.split(b"\0") if path]
    return sorted(path for path in paths if not is_ignored_discovery_path(path))


def filesystem_files(repo_root: Path) -> list[str]:
    files: list[str] = []
    for path in repo_root.rglob("*"):
        if not path_resolves_inside_repo(path, repo_root):
            continue
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(repo_root).as_posix()
        except (OSError, ValueError):
            continue
        if is_ignored_discovery_path(rel):
            continue
        files.append(rel)
    return sorted(files)

def discover_repo_files(repo_root: Path) -> tuple[list[str], str]:
    tracked = git_tracked_files(repo_root)
    if tracked is not None:
        return tracked, "git ls-files -z"
    return filesystem_files(repo_root), "filesystem recursive scan fallback"


def normalize_changed_files(values: list[str], repo_root: Path) -> list[str]:
    normalized: list[str] = []
    root = repo_root.resolve()
    for value in values:
        raw = value.strip()
        if not raw:
            raise ValueError("Changed-file input must not be blank")
        slash_path = raw.replace("\\", "/")
        path_parts = tuple(part for part in slash_path.split("/") if part)
        if slash_path.startswith("/") or Path(raw).is_absolute() or re.match(r"^[A-Za-z]:", slash_path) is not None:
            raise ValueError(f"Changed-file input must be repo-relative: {value}")
        if ".." in path_parts:
            raise ValueError(f"Changed-file input must not traverse parents: {value}")
        candidate = root / Path(slash_path)
        try:
            repo_relative = candidate.resolve().relative_to(root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ValueError(f"Changed-file input resolves outside repo root: {value}") from exc
        rel = repo_relative.as_posix()
        if not rel or rel == ".":
            raise ValueError(f"Changed-file input must name a file under repo root: {value}")
        normalized.append(rel)
    return sorted(dict.fromkeys(normalized))

def load_changed_files_from(path: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"Changed-files input is missing: {path}")
    try:
        records = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Changed-files input could not be read: {path}: {exc}") from exc
    return records if records else [""]

def load_manifest(repo_root: Path) -> dict[str, Any] | None:
    path = repo_root / MANIFEST_PATH
    if not path_is_file_inside_repo(path, repo_root):
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None

def manifest_error(repo_root: Path) -> str | None:
    path = repo_root / MANIFEST_PATH
    if not path_is_file_inside_repo(path, repo_root):
        return f"Collector runtime manifest is missing: {MANIFEST_PATH.as_posix()}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"Invalid JSON in collector runtime manifest {MANIFEST_PATH.as_posix()}: {exc}"
    if not isinstance(data, dict):
        return f"Collector runtime manifest must be a JSON object: {MANIFEST_PATH.as_posix()}"
    path_errors = collector_manifest_path_errors(repo_root)
    if path_errors:
        return "; ".join(path_errors)
    return None

def normalize_manifest_surface_path(value: str, repo_root: Path, field_name: str) -> tuple[str | None, str | None]:
    raw = value.strip()
    if not raw:
        return None, f"Collector runtime manifest {field_name} must not be blank"
    slash_path = raw.replace("\\", "/")
    if Path(slash_path).is_absolute():
        return None, f"Collector runtime manifest {field_name} must be repo-relative, not absolute: {value}"
    if re.match(r"^[A-Za-z]:", slash_path) is not None:
        return None, f"Collector runtime manifest {field_name} must not be drive-qualified: {value}"
    path = Path(slash_path)
    if ".." in path.parts:
        return None, f"Collector runtime manifest {field_name} must not traverse parents: {value}"
    normalized = slash_path
    while normalized.startswith("./"):
        normalized = normalized[2:]
    path = Path(normalized)
    if not normalized or normalized == ".":
        return None, f"Collector runtime manifest {field_name} must name a file under repo root: {value}"
    if ".." in path.parts:
        return None, f"Collector runtime manifest {field_name} must not traverse parents: {value}"
    root = repo_root.resolve()
    try:
        rel = (root / path).resolve().relative_to(root).as_posix()
    except (OSError, RuntimeError, ValueError):
        return None, f"Collector runtime manifest {field_name} resolves outside repo root: {value}"
    if not rel or rel == ".":
        return None, f"Collector runtime manifest {field_name} must name a file under repo root: {value}"
    return rel, None


def collector_manifest_path_entries(repo_root: Path) -> tuple[list[str], list[str]]:
    manifest = load_manifest(repo_root)
    if not manifest:
        return [], []
    paths: list[str] = []
    errors: list[str] = []

    def append_path(value: str, field_name: str) -> None:
        rel, error = normalize_manifest_surface_path(value, repo_root, field_name)
        if error is not None:
            errors.append(error)
        elif rel is not None:
            paths.append(rel)

    wrapper = manifest.get("collector_wrapper_source")
    if isinstance(wrapper, str):
        append_path(wrapper, "collector_wrapper_source")
    part_files = manifest.get("collector_part_files", [])
    if isinstance(part_files, list):
        for index, path in enumerate(part_files):
            if isinstance(path, str):
                append_path(path, f"collector_part_files[{index}]")
    return sorted(dict.fromkeys(paths)), errors


def collector_manifest_path_errors(repo_root: Path) -> list[str]:
    _paths, errors = collector_manifest_path_entries(repo_root)
    return errors


def collector_manifest_paths(repo_root: Path) -> list[str]:
    paths, _errors = collector_manifest_path_entries(repo_root)
    return paths


def harness_source_part_paths(repo_root: Path) -> list[str]:
    root = repo_root / HARNESS_PARTS_ROOT
    if not path_is_dir_inside_repo(root, repo_root):
        return []
    paths: list[str] = []
    for path in root.glob("*.ps1.txt"):
        if not path_resolves_inside_repo(path, repo_root):
            continue
        if not path.is_file():
            continue
        try:
            paths.append(path.relative_to(repo_root).as_posix())
        except (OSError, ValueError):
            continue
    return sorted(paths)

def read_required_profile_harness_paths(repo_root: Path) -> tuple[list[str], str | None]:
    path = repo_root / REQUIRED_SURFACE_PROFILES_PATH
    if not path_is_file_inside_repo(path, repo_root):
        return [], None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], f"Invalid JSON in required surface profile {REQUIRED_SURFACE_PROFILES_PATH.as_posix()}: {exc}"
    if not isinstance(data, dict):
        return [], f"Required surface profile must be a JSON object: {REQUIRED_SURFACE_PROFILES_PATH.as_posix()}"
    expected: set[str] = set()
    for profile_name, paths in data.items():
        if not isinstance(paths, list):
            return [], f"Required surface profile {profile_name!r} must be a JSON list"
        for index, candidate in enumerate(paths):
            if not isinstance(candidate, str):
                return [], f"Required surface profile {profile_name!r}[{index}] must be a string"
            if isinstance(candidate, str) and has_prefix(candidate, HARNESS_PARTS_ROOT.as_posix()) and candidate.endswith(".ps1.txt"):
                expected.add(candidate)
    return sorted(expected), None

def required_profile_harness_paths(repo_root: Path) -> list[str]:
    paths, _ = read_required_profile_harness_paths(repo_root)
    return paths


def expand_changed_files(repo_root: Path, changed_files: list[str]) -> tuple[list[str], dict[str, Any]]:
    normalized = normalize_changed_files(changed_files, repo_root)
    expanded: set[str] = set(normalized)
    rules: list[dict[str, Any]] = []
    for rel in normalized:
        added: list[str] = []
        if rel == MANIFEST_PATH.as_posix():
            added = collector_manifest_paths(repo_root)
        elif rel == "project_sources/collector/harness/assemble_run_DCOIR_Tests.ps1":
            added = harness_source_part_paths(repo_root)
        elif rel == REQUIRED_SURFACE_PROFILES_PATH.as_posix():
            added = harness_source_part_paths(repo_root)
        elif is_workflow_yaml(rel):
            added = [rel]
        if added:
            expanded.update(added)
            rules.append({"changed_path": rel, "rule": "dependency_expansion", "added_paths": added})
    return sorted(expanded), {
        "input_paths": normalized,
        "expanded_paths": sorted(expanded),
        "rules": rules,
        "boundary": "Dependency expansion covers collector manifest paths, harness assembler source parts, and PowerShell-bearing workflow/action YAML. Other changed paths are classified directly.",
    }


def append_missing_authoritative_surfaces(repo_root: Path, surfaces: list[dict[str, Any]]) -> None:
    existing = {entry["path"] for entry in surfaces}
    for rel in collector_manifest_paths(repo_root):
        if rel not in existing and not repo_file_exists(repo_root, rel):
            surfaces.append(
                make_surface(
                    repo_root,
                    rel,
                    "missing_authoritative_surface",
                    "missing",
                    "fail",
                    "Collector runtime manifest references this PowerShell surface, but the file is missing.",
                    False,
                )
            )

def collect_surfaces(repo_root: Path, changed_files: list[str] | None = None) -> tuple[list[dict[str, Any]], str, dict[str, Any] | None]:
    discovered, source = discover_repo_files(repo_root)
    dependency_expansion = None
    if changed_files is not None:
        candidates, dependency_expansion = expand_changed_files(repo_root, changed_files)
    else:
        candidates = discovered
    surfaces: list[dict[str, Any]] = []
    for rel in candidates:
        exists = repo_file_exists(repo_root, rel)
        if changed_files is not None and not exists and not (is_powershell_file(rel) or is_workflow_yaml(rel)):
            continue
        surface = classify_surface(repo_root, rel, exists)
        if surface is not None:
            surfaces.append(surface)
    if changed_files is None:
        append_missing_authoritative_surfaces(repo_root, surfaces)
    return sorted(surfaces, key=lambda entry: entry["path"]), source, dependency_expansion

def load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"JSON file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"JSON file could not be read: {path}: {exc}") from exc


def repo_relative_cli_path(repo_root: Path, value: str | Path, label: str) -> Path:
    try:
        return repo_relative_input_path(repo_root, value, label)
    except AnalyzerContractError as exc:
        raise ValueError(str(exc)) from exc


def summarize(surfaces: list[dict[str, Any]]) -> dict[str, Any]:
    by_category = Counter(entry["category"] for entry in surfaces)
    by_source_type = Counter(entry["source_type"] for entry in surfaces)
    by_status = Counter(entry["status"] for entry in surfaces)
    by_decision = Counter(entry["inclusion_decision"] for entry in surfaces)
    for source_type in REQUIRED_SOURCE_TYPES:
        by_source_type.setdefault(source_type, 0)
    for category in KNOWN_CATEGORIES:
        by_category.setdefault(category, 0)
    return {
        "total_surfaces": len(surfaces),
        "by_category": dict(sorted(by_category.items())),
        "by_source_type": dict(sorted(by_source_type.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_inclusion_decision": dict(sorted(by_decision.items())),
        "embedded_snippet_count": sum(len(entry.get("embedded_snippets", [])) for entry in surfaces),
    }


def contiguous_harness_part_errors(harness_parts: list[str]) -> list[str]:
    numbers: list[int] = []
    for rel in harness_parts:
        match = re.search(r"run_DCOIR_Tests\.part-(\d{3})\.ps1\.txt$", rel)
        if match:
            numbers.append(int(match.group(1)))
    if not numbers:
        return []
    expected = set(range(min(numbers), max(numbers) + 1))
    missing = sorted(expected - set(numbers))
    if missing:
        return ["Harness source part numbering has gaps: " + ", ".join(f"{number:03d}" for number in missing)]
    return []


def build_controls(repo_root: Path, surfaces: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_paths = collector_manifest_paths(repo_root)
    harness_parts = harness_source_part_paths(repo_root)
    profile_harness_paths, profile_error = read_required_profile_harness_paths(repo_root)
    by_path = {entry["path"]: entry for entry in surfaces}
    expected_generated = HARNESS_GENERATED_OUTPUT.as_posix()
    manifest_entries: list[dict[str, Any]] = []
    for rel in manifest_paths:
        exists = repo_file_exists(repo_root, rel)
        discovered_surface = by_path.get(rel)
        classified_surface = classify_surface(repo_root, rel, exists) if exists else None
        facts = file_facts(repo_root, rel, exists)
        manifest_entries.append(
            {
                "path": rel,
                "exists": exists,
                "in_inventory": rel in by_path,
                "category": discovered_surface.get("category") if discovered_surface else None,
                "expected_category": classified_surface.get("category") if classified_surface else None,
                "size_bytes": facts["size_bytes"],
            }
        )
    return {
        "collector_manifest": {
            "path": MANIFEST_PATH.as_posix(),
            "exists": repo_file_exists(repo_root, MANIFEST_PATH.as_posix()),
            "error": manifest_error(repo_root),
            "expected_path_count": len(manifest_paths),
            "present_path_count": sum(1 for rel in manifest_paths if repo_file_exists(repo_root, rel)),
            "paths": manifest_entries,
        },
        "harness_source_parts": {
            "root": HARNESS_PARTS_ROOT.as_posix(),
            "part_count": len(harness_parts),
            "required_profile_path": REQUIRED_SURFACE_PROFILES_PATH.as_posix(),
            "required_profile_exists": repo_file_exists(repo_root, REQUIRED_SURFACE_PROFILES_PATH.as_posix()),
            "required_profile_error": profile_error,
            "required_profile_part_count": len(profile_harness_paths),
            "required_profile_present_count": sum(1 for rel in profile_harness_paths if repo_file_exists(repo_root, rel)),
            "required_profile_parts": [
                {
                    "path": rel,
                    "exists": repo_file_exists(repo_root, rel),
                    "in_inventory": rel in by_path,
                    "category": by_path.get(rel, {}).get("category"),
                    "size_bytes": by_path.get(rel, {}).get("size_bytes"),
                }
                for rel in profile_harness_paths
            ],
            "parts": [
                {
                    "path": rel,
                    "exists": repo_file_exists(repo_root, rel),
                    "category": by_path.get(rel, {}).get("category"),
                    "size_bytes": by_path.get(rel, {}).get("size_bytes"),
                }
                for rel in harness_parts
            ],
        },
        "generated_outputs": [
            {
                "path": expected_generated,
                "expected_presence": "optional_when_generated",
                "exists": repo_file_exists(repo_root, expected_generated),
                "category": by_path.get(expected_generated, {}).get("category"),
            }
        ],
    }


def load_shrink_exceptions(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    data = load_json_file(path)
    if not isinstance(data, dict):
        raise ValueError("Shrink exception file must be a JSON object")
    exceptions = data.get("allowed_category_shrink", {})
    if not isinstance(exceptions, dict):
        raise ValueError("allowed_category_shrink must be a JSON object")
    normalized: dict[str, str] = {}
    for category, reason in exceptions.items():
        if not isinstance(category, str) or not isinstance(reason, str) or not reason.strip():
            raise ValueError("Each shrink exception must map a category to a non-empty reason")
        normalized[category] = reason.strip()
    return normalized


def validate_inventory(
    surfaces: list[dict[str, Any]],
    mode: str,
    controls: dict[str, Any],
    dependency_expansion: dict[str, Any] | None = None,
    baseline: dict[str, Any] | None = None,
    shrink_exceptions: dict[str, str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    shrink_exceptions = shrink_exceptions or {}

    paths = [entry["path"] for entry in surfaces]
    duplicate_paths = sorted(path for path, count in Counter(paths).items() if count > 1)
    if duplicate_paths:
        errors.append("Duplicate PowerShell inventory paths: " + ", ".join(duplicate_paths))

    for entry in surfaces:
        if entry["category"].startswith("unclassified") or entry["inclusion_decision"] == "fail":
            errors.append(f"{entry['path']}: {entry['decision_reason']}")
        if entry["inclusion_decision"] == "exclude" and not entry.get("decision_reason"):
            errors.append(f"{entry['path']}: excluded surface is missing a documented reason")
        if entry["source_type"] not in REQUIRED_SOURCE_TYPES:
            errors.append(f"{entry['path']}: unsupported source type {entry['source_type']}")
        if entry.get("exists") and entry.get("size_bytes") is None:
            errors.append(f"{entry['path']}: file facts could not be collected safely inside the repository root")
        if (
            entry["source_type"] != "workflow_yaml"
            and entry["inclusion_decision"] != "exclude"
            and entry.get("exists")
            and entry.get("size_bytes") == 0
        ):
            errors.append(f"{entry['path']}: included PowerShell surface is empty")
        marker_lines = entry.get("marker_lines")
        if not isinstance(marker_lines, list) or not all(isinstance(line, int) for line in marker_lines):
            errors.append(f"{entry['path']}: marker_lines must be a list of line numbers")
        if not isinstance(entry.get("embedded_snippets"), list):
            errors.append(f"{entry['path']}: embedded_snippets must be a list")
        if entry["category"] == "workflow_embedded_powershell" and not entry.get("embedded_snippets"):
            errors.append(f"{entry['path']}: workflow PowerShell surface has no extracted snippet records")

    category_counts = Counter(entry["category"] for entry in surfaces)
    input_paths = set((dependency_expansion or {}).get("input_paths", []))
    manifest_required = (
        mode == "full"
        or MANIFEST_PATH.as_posix() in input_paths
        or any(entry["category"] in PRIMARY_COLLECTOR_CATEGORIES for entry in surfaces)
    )
    if manifest_required:
        collector_control = controls.get("collector_manifest", {})
        if collector_control.get("error"):
            errors.append(str(collector_control["error"]))
        if collector_control.get("expected_path_count", 0) == 0:
            errors.append("Collector runtime manifest did not provide any expected PowerShell source paths")
        if collector_control.get("present_path_count") != collector_control.get("expected_path_count"):
            errors.append("Collector runtime manifest references missing PowerShell source paths")
        for entry in collector_control.get("paths", []):
            if mode == "full" and entry.get("exists") and not entry.get("in_inventory"):
                errors.append(f"{entry['path']}: manifest-listed collector path is missing from inventory")
            if entry.get("exists") and not entry.get("expected_category"):
                errors.append(f"{entry['path']}: manifest-listed collector path has no inventory category")
            if entry.get("exists") and entry.get("size_bytes") == 0:
                errors.append(f"{entry['path']}: manifest-listed collector path is empty")
        manifest_paths = {entry.get("path") for entry in collector_control.get("paths", [])}
        for entry in surfaces:
            if entry["category"] in PRIMARY_COLLECTOR_CATEGORIES and entry["path"] not in manifest_paths:
                errors.append(f"{entry['path']}: primary collector runtime source is not listed in {MANIFEST_PATH.as_posix()}")

    profile_control_required = REQUIRED_SURFACE_PROFILES_PATH.as_posix() in input_paths
    harness_required = (
        mode == "full"
        or profile_control_required
        or any(entry["category"] in PRIMARY_HARNESS_CATEGORIES for entry in surfaces)
    )
    if harness_required:
        harness_control = controls.get("harness_source_parts", {})
        harness_parts = [entry["path"] for entry in harness_control.get("parts", [])]
        if profile_control_required and not harness_control.get("required_profile_exists"):
            errors.append(f"Required surface profile is missing: {REQUIRED_SURFACE_PROFILES_PATH.as_posix()}")
        if harness_control.get("required_profile_error"):
            errors.append(str(harness_control["required_profile_error"]))
        if profile_control_required and harness_control.get("required_profile_part_count", 0) == 0:
            errors.append(f"Required surface profile did not provide any harness source parts: {REQUIRED_SURFACE_PROFILES_PATH.as_posix()}")
        if harness_control.get("part_count", 0) == 0:
            errors.append("Harness source parts inventory is empty")
        if harness_control.get("required_profile_part_count", 0) > 0:
            if harness_control.get("required_profile_present_count") != harness_control.get("required_profile_part_count"):
                errors.append(
                    f"Harness source parts required by {REQUIRED_SURFACE_PROFILES_PATH.as_posix()} are missing"
                )
            for entry in harness_control.get("required_profile_parts", []):
                if mode == "full" and entry.get("exists") and not entry.get("in_inventory"):
                    errors.append(f"{entry['path']}: profile-required harness source part is missing from inventory")
                if entry.get("exists") and entry.get("size_bytes") == 0:
                    errors.append(f"{entry['path']}: profile-required harness source part is empty")
        required_profile_paths = {part.get("path") for part in harness_control.get("required_profile_parts", [])}
        for entry in harness_control.get("parts", []):
            path_in_current_inventory = entry.get("path") in paths
            if mode == "full" and entry.get("exists") and not entry.get("category"):
                errors.append(f"{entry['path']}: harness source part is missing from inventory")
            if entry.get("exists") and entry.get("size_bytes") == 0:
                errors.append(f"{entry['path']}: harness source part is empty")
            if (
                harness_control.get("required_profile_part_count", 0) > 0
                and (mode == "full" or path_in_current_inventory)
                and entry.get("path") not in required_profile_paths
            ):
                errors.append(f"{entry['path']}: harness source part is not listed in {REQUIRED_SURFACE_PROFILES_PATH.as_posix()}")
        errors.extend(contiguous_harness_part_errors(harness_parts))

    if mode == "full":
        if not surfaces:
            errors.append("PowerShell inventory is empty")
        missing_categories = sorted(category for category in REQUIRED_FULL_MODE_CATEGORIES if category_counts[category] == 0)
        if missing_categories:
            errors.append("Full inventory is missing required collector/harness categories: " + ", ".join(missing_categories))
        if not any(entry["category"] in PRIMARY_COLLECTOR_CATEGORIES for entry in surfaces):
            errors.append("Full inventory has empty collector surface coverage")
        if not any(entry["category"] in PRIMARY_HARNESS_CATEGORIES for entry in surfaces):
            errors.append("Full inventory has empty harness surface coverage")

    if baseline is not None and mode != "full":
        errors.append("Baseline shrink checks require full inventory mode; changed-file mode is a subset.")
    elif baseline is not None:
        baseline_counts = baseline.get("summary", {}).get("by_category", {})
        if not isinstance(baseline_counts, dict):
            errors.append("Baseline inventory is missing summary.by_category")
        else:
            for category, old_count in sorted(baseline_counts.items()):
                if not isinstance(old_count, int):
                    errors.append(f"Baseline category {category} count is not an integer")
                    continue
                new_count = category_counts.get(category, 0)
                if new_count < old_count and category not in shrink_exceptions:
                    errors.append(
                        f"Category {category} unexpectedly shrank from {old_count} to {new_count} without an approved exception"
                    )
                elif new_count < old_count:
                    warnings.append(
                        f"Category {category} shrink allowed by exception: {shrink_exceptions[category]}"
                    )

    return {
        "success": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def build_inventory(
    repo_root: Path,
    changed_files: list[str] | None = None,
    baseline: dict[str, Any] | None = None,
    shrink_exceptions: dict[str, str] | None = None,
    json_output: Path = DEFAULT_JSON_OUTPUT,
    markdown_output: Path = DEFAULT_MARKDOWN_OUTPUT,
) -> dict[str, Any]:
    surfaces, source, dependency_expansion = collect_surfaces(repo_root, changed_files)
    mode = "changed" if changed_files is not None else "full"
    summary = summarize(surfaces)
    controls = build_controls(repo_root, surfaces)
    validation = validate_inventory(surfaces, mode, controls, dependency_expansion, baseline, shrink_exceptions)
    command_parts = [
        "python",
        "project_sources/collector/tools/build_powershell_surface_inventory.py",
        "--repo-root",
        ".",
        "--json-output",
        json_output.as_posix(),
        "--markdown-output",
        markdown_output.as_posix(),
    ]
    if changed_files is not None:
        command_parts.extend(["--changed-file", "<path>"])
    return {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "mode": mode,
        "source_of_truth": source,
        "deterministic_report": True,
        "file_facts_policy": "text_bytes_with_line_endings_normalized_to_lf",
        "discovery_command": " ".join(command_parts),
        "required_source_types": REQUIRED_SOURCE_TYPES,
        "outputs": {
            "json": json_output.as_posix(),
            "markdown": markdown_output.as_posix(),
        },
        "changed_file_dependency_expansion": dependency_expansion,
        "summary": summary,
        "controls": controls,
        "validation": validation,
        "surfaces": surfaces,
    }


def markdown_table(mapping: dict[str, Any], key_name: str, value_name: str = "Count") -> list[str]:
    lines = [f"| {key_name} | {value_name} |", "| --- | ---: |"]
    for key, value in sorted(mapping.items()):
        lines.append(f"| `{key}` | {value} |")
    return lines


def render_markdown(inventory: dict[str, Any]) -> str:
    summary = inventory["summary"]
    validation = inventory["validation"]
    lines = [
        "# PowerShell Surface Inventory",
        "",
        f"- Schema: `{inventory['schema_version']}`",
        f"- Issue: #{inventory['issue']}",
        f"- Mode: `{inventory['mode']}`",
        f"- Source of truth: `{inventory['source_of_truth']}`",
        f"- File facts policy: `{inventory['file_facts_policy']}`",
        f"- Discovery command: `{inventory['discovery_command']}`",
        f"- JSON artifact: `{inventory['outputs']['json']}`",
        f"- Validation: `{'pass' if validation['success'] else 'fail'}`",
        "",
        "## Counts By Category",
        "",
    ]
    lines.extend(markdown_table(summary["by_category"], "Category"))
    lines.extend(["", "## Counts By Source Type", ""])
    lines.extend(markdown_table(summary["by_source_type"], "Source Type"))
    lines.extend(["", "## Counts By Inclusion Decision", ""])
    lines.extend(markdown_table(summary["by_inclusion_decision"], "Decision"))
    lines.extend(["", "## Control Totals", ""])
    controls = inventory["controls"]
    collector = controls["collector_manifest"]
    harness = controls["harness_source_parts"]
    lines.extend(
        [
            f"- Collector manifest expected paths: `{collector['expected_path_count']}`",
            f"- Collector manifest present paths: `{collector['present_path_count']}`",
            f"- Harness source parts: `{harness['part_count']}`",
            f"- Profile-required harness source parts: `{harness['required_profile_part_count']}`",
            f"- Profile-required harness source parts present: `{harness['required_profile_present_count']}`",
            f"- Embedded workflow/action snippets: `{summary['embedded_snippet_count']}`",
        ]
    )
    if inventory.get("changed_file_dependency_expansion"):
        expansion = inventory["changed_file_dependency_expansion"]
        lines.extend(["", "## Changed-File Dependency Expansion", ""])
        lines.append(f"- Boundary: {expansion['boundary']}")
        lines.append(f"- Input paths: `{len(expansion['input_paths'])}`")
        lines.append(f"- Expanded paths: `{len(expansion['expanded_paths'])}`")
    exclusions = [
        entry
        for entry in inventory["surfaces"]
        if entry["inclusion_decision"] in {"exclude", "reference"}
    ]
    lines.extend(["", "## Reference And Excluded Surfaces", ""])
    if exclusions:
        lines.extend(["| Path | Category | Decision | Reason |", "| --- | --- | --- | --- |"])
        for entry in exclusions:
            lines.append(
                f"| `{entry['path']}` | `{entry['category']}` | `{entry['inclusion_decision']}` | {entry['decision_reason']} |"
            )
    else:
        lines.append("No reference or excluded PowerShell surfaces were discovered.")
    lines.extend(["", "## Validation Findings", ""])
    if validation["errors"]:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in validation["errors"])
    else:
        lines.append("- No validation errors.")
    if validation["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in validation["warnings"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, inventory: dict[str, Any], json_output: Path, markdown_output: Path) -> list[str]:
    errors: list[str] = []
    try:
        json_path = repo_relative_cli_path(repo_root, json_output, "PowerShell surface inventory JSON report output path")
        markdown_path = repo_relative_cli_path(
            repo_root,
            markdown_output,
            "PowerShell surface inventory Markdown report output path",
        )
    except ValueError as exc:
        return [str(exc)]
    if json_path == markdown_path:
        return ["PowerShell surface inventory JSON and Markdown report output paths must be different"]
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        errors.append(f"PowerShell surface inventory report write failure: {json_path}: {exc}")
        return errors
    try:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown(inventory), encoding="utf-8")
    except OSError as exc:
        errors.append(f"PowerShell surface inventory report write failure: {markdown_path}: {exc}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the DCOIR PowerShell surface inventory")
    parser.add_argument("--repo-root", default=".", help="Repository root to scan")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="JSON inventory output path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Markdown inventory output path")
    parser.add_argument("--changed-file", action="append", default=[], help="Changed file to classify; may be repeated")
    parser.add_argument("--changed-files-from", help="Newline-delimited changed-file input")
    parser.add_argument("--baseline-json", help="Previous inventory JSON for unexpected-shrink checks")
    parser.add_argument("--shrink-exception-json", help="JSON file with allowed_category_shrink reasons")
    parser.add_argument("--no-write", action="store_true", help="Validate and print JSON without writing artifacts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    input_errors: list[str] = []

    changed_files: list[str] | None = None
    if args.changed_file or args.changed_files_from:
        changed_files = list(args.changed_file)
        if args.changed_files_from:
            try:
                changed_files.extend(
                    load_changed_files_from(
                        repo_relative_cli_path(
                            repo_root,
                            args.changed_files_from,
                            "PowerShell surface inventory changed-files input path",
                        )
                    )
                )
            except ValueError as exc:
                input_errors.append(str(exc))

    baseline = None
    shrink_exceptions: dict[str, str] = {}
    try:
        baseline = (
            load_json_file(repo_relative_cli_path(repo_root, args.baseline_json, "PowerShell surface inventory baseline path"))
            if args.baseline_json
            else None
        )
    except ValueError as exc:
        input_errors.append(str(exc))
    try:
        shrink_exceptions = load_shrink_exceptions(
            repo_relative_cli_path(repo_root, args.shrink_exception_json, "PowerShell surface inventory shrink exception path")
            if args.shrink_exception_json
            else None
        )
    except ValueError as exc:
        input_errors.append(str(exc))
    inventory = build_inventory(
        repo_root=repo_root,
        changed_files=changed_files,
        baseline=baseline,
        shrink_exceptions=shrink_exceptions,
        json_output=json_output,
        markdown_output=markdown_output,
    )
    if input_errors:
        inventory["validation"]["errors"] = input_errors + inventory["validation"]["errors"]
        inventory["validation"]["success"] = False

    if not args.no_write:
        output_errors = write_outputs(repo_root, inventory, json_output, markdown_output)
        if output_errors:
            inventory["validation"]["errors"].extend(output_errors)
            inventory["validation"]["success"] = False
            rewrite_errors = write_outputs(repo_root, inventory, json_output, markdown_output)
            for error in rewrite_errors:
                if error not in inventory["validation"]["errors"]:
                    inventory["validation"]["errors"].append(error)
    print(json.dumps(inventory["summary"], indent=2))
    if inventory["validation"]["errors"]:
        for error in inventory["validation"]["errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
