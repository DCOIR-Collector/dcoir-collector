#!/usr/bin/env python3
"""YAML scalar, shell, and block parsing helpers for workflow PowerShell inventory."""
from __future__ import annotations

import re
import shlex

from powershell_surface_inventory_common import FLOW_STEP_KEYS

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


__all__ = [
    "line_indent",
    "yaml_item_text",
    "yaml_item_text_without_comment",
    "strip_yaml_node_prefixes",
    "normalize_workflow_scalar",
    "workflow_scalar_is_alias",
    "yaml_mapping_key_indent",
    "yaml_key_name",
    "cleaned_workflow_string",
    "empty_workflow_string",
    "previous_parent_index",
    "step_blocks",
    "direct_step_mapping_key",
    "direct_child_key",
    "executable_steps_key",
    "defaults_run_shell_key",
    "defaults_run_mapping_key",
    "unquoted_flow_collection_value",
    "unsupported_workflow_shell_value",
    "flow_mapping_pieces",
    "flow_collection_shape_error",
    "flow_mapping_fragment_error",
    "unsupported_flow_step_mapping_key",
    "flow_mapping_has_direct_key",
    "unsupported_workflow_run_value",
    "unsupported_inline_executable_steps_key",
    "block_scalar_has_nonblank_content",
    "empty_block_scalar_run_key",
    "unsupported_block_scalar_workflow_string_key",
    "nested_content_index",
    "has_block_collection_child",
    "nonscalar_workflow_string_value_key",
    "block_end_line",
    "collect_run_block",
    "normalize_block_scalar_command",
    "strip_yaml_inline_comment",
    "strip_yaml_inline_comment_with_quote",
    "yaml_unclosed_quote",
    "yaml_quote_can_start",
    "is_yaml_block_scalar_marker",
    "yaml_block_scalar_indent_indicator",
    "yaml_block_scalar_content_indent",
    "is_invalid_block_scalar_like_value",
    "parent_block_start",
    "clean_shell_value",
    "split_flow_mapping",
    "shell_executable",
    "is_powershell_shell",
    "shell_line_without_comment",
    "command_text_for_marker_scan",
    "inline_shell_value",
    "defaults_inline_shell",
    "run_inline_shell",
    "direct_defaults_shell",
    "step_line_has_ancestor_key",
    "step_child_ancestor_key",
    "line_is_within_step_run_block_scalar",
    "misindented_step_workflow_key",
    "workflow_default_shell",
    "job_default_shell",
    "default_shell_for_steps",
]
