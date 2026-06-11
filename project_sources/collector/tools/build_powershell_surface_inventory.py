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
INLINE_SHELL_RE = re.compile(r"(?:^|[,{]\s*)shell\s*:\s*(?:(['\"])(.*?)\1|([^,}]+))", re.IGNORECASE)
MANIFEST_PATH = Path("project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json")
HARNESS_PARTS_ROOT = Path("project_sources/collector/harness/source/parts")
HARNESS_GENERATED_OUTPUT = Path("project_sources/collector/harness/run_DCOIR_Tests.generated.ps1")
REQUIRED_SURFACE_PROFILES_PATH = Path("project_sources/github_actions/workflow_required_surface_profiles.json")


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def path_parts(rel: str) -> tuple[str, ...]:
    return tuple(part.casefold() for part in Path(rel).parts)


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


def workflow_yaml_shape_error(repo_root: Path, rel: str) -> str | None:
    text = read_text(repo_root / rel)
    if not text.strip():
        return f"{rel}: workflow/action YAML is empty"

    lines = text.splitlines()
    stack: list[tuple[str, int]] = []
    block_scalar_indent: int | None = None
    pairs = {"[": "]", "{": "}", "(": ")"}
    closing = {"]", "}", ")"}

    for line_number, line in enumerate(lines, start=1):
        indent = line_indent(line)
        if line[:indent].find("\t") != -1:
            return f"{rel}: line {line_number} uses a tab for indentation"

        stripped = line.strip()
        if block_scalar_indent is not None:
            if not stripped or indent > block_scalar_indent:
                continue
            block_scalar_indent = None
        if not stripped or stripped.startswith("#"):
            continue
        if indent % 2 != 0:
            return f"{rel}: line {line_number} uses unsupported odd indentation"

        item = yaml_item_text(line)
        if not stripped.startswith("- ") and ":" not in item:
            return f"{rel}: line {line_number} has no YAML key/value separator"

        quote: str | None = None
        for character in line:
            if quote:
                if character == quote:
                    quote = None
                continue
            if character in {"'", '"'}:
                quote = character
            elif character in pairs:
                stack.append((character, line_number))
            elif character in closing:
                if not stack or pairs[stack[-1][0]] != character:
                    return f"{rel}: line {line_number} has an unmatched {character!r}"
                stack.pop()

        if re.search(r":\s*[|>][-+]?\s*(?:#.*)?$", item):
            block_scalar_indent = line_indent(line)

    if stack:
        opener, line_number = stack[-1]
        return f"{rel}: line {line_number} has an unclosed {opener!r}"
    for index, line in enumerate(lines):
        if yaml_item_text(line) != "steps:":
            continue
        steps_indent = line_indent(line)
        steps_end = block_end_line(lines, index, steps_indent)
        for candidate in range(index + 1, steps_end):
            stripped = lines[candidate].strip()
            if not stripped or stripped.startswith("#"):
                continue
            if line_indent(lines[candidate]) == steps_indent + 2:
                if not stripped.startswith("- "):
                    return f"{rel}: line {candidate + 1} has a non-list entry directly under steps"
                item = yaml_item_text(lines[candidate])
                if item and ":" not in item and item != "":
                    return f"{rel}: line {candidate + 1} has a non-mapping step entry"
    return None


def file_facts(repo_root: Path, rel: str, exists: bool) -> dict[str, Any]:
    if not exists:
        return {
            "size_bytes": None,
            "line_count": None,
            "sha256": None,
        }
    path = repo_root / rel
    try:
        data = path.read_bytes()
    except OSError:
        return {
            "size_bytes": None,
            "line_count": None,
            "sha256": None,
        }
    return {
        "size_bytes": len(data),
        "line_count": data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0),
        "sha256": hashlib.sha256(data).hexdigest(),
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
    indent = line_indent(line)
    after_colon = line.split(":", 1)[1].strip() if ":" in line else ""
    if after_colon and after_colon not in {"|", ">"}:
        return run_index + 1, after_colon.strip("'\"")
    end_line = block_end_line(lines, run_index, indent, max_end)
    command_lines: list[str] = []
    for follow in lines[run_index + 1:end_line]:
        command_lines.append(follow[indent + 2:] if len(follow) > indent + 2 else follow.strip())
    return end_line, "\n".join(command_lines).rstrip()


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
        return cleaned[1:-1]
    return cleaned


def split_flow_mapping(item: str) -> dict[str, str]:
    stripped = item.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return {}
    content = stripped[1:-1]
    pieces: list[str] = []
    current: list[str] = []
    quote: str | None = None
    depth = 0
    for character in content:
        if quote:
            current.append(character)
            if character == quote:
                quote = None
            continue
        if character in {"'", '"'}:
            quote = character
            current.append(character)
        elif character in "[{(":
            depth += 1
            current.append(character)
        elif character in "]})":
            depth = max(0, depth - 1)
            current.append(character)
        elif character == "," and depth == 0:
            pieces.append("".join(current).strip())
            current = []
        else:
            current.append(character)
    if current:
        pieces.append("".join(current).strip())

    mapping: dict[str, str] = {}
    for piece in pieces:
        if ":" not in piece:
            continue
        key, value = piece.split(":", 1)
        key = clean_shell_value(key).casefold()
        if key:
            mapping[key] = clean_shell_value(value)
    return mapping


def shell_executable(value: str) -> str:
    cleaned = clean_shell_value(value)
    if not cleaned:
        return ""
    try:
        parts = shlex.split(cleaned)
    except ValueError:
        parts = cleaned.split()
    if not parts:
        return ""
    return re.split(r"[\\/]+", parts[0])[-1].casefold()


def is_powershell_shell(value: str) -> bool:
    return shell_executable(value) in {"pwsh", "pwsh.exe", "powershell", "powershell.exe"}


def inline_shell_value(text: str) -> str | None:
    match = INLINE_SHELL_RE.search(text)
    if not match:
        return None
    return clean_shell_value(match.group(2) or match.group(3) or "")


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
    defaults_item = yaml_item_text(lines[defaults_index])
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
        candidate_item = yaml_item_text(lines[candidate])
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
        candidate_item = yaml_item_text(lines[candidate])
        if candidate_item.startswith("shell:"):
            return clean_shell_value(candidate_item.split(":", 1)[1])
    return None


def workflow_default_shell(lines: list[str]) -> str | None:
    for index in range(0, len(lines)):
        item = yaml_item_text(lines[index])
        if line_indent(lines[index]) != 0 or not item.startswith("defaults:"):
            continue
        shell = direct_defaults_shell(lines, index, block_end_line(lines, index, 0))
        if shell:
            return shell
    return None


def job_default_shell(lines: list[str], job_start: int, job_end: int) -> str | None:
    job_indent = line_indent(lines[job_start])
    for index in range(job_start + 1, job_end):
        item = yaml_item_text(lines[index])
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
        if yaml_item_text(line) != "steps:":
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
        item = yaml_item_text(lines[index])
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
            step_name = item.split(":", 1)[1].strip().strip("'\"")
        elif item.startswith("shell:"):
            shell = clean_shell_value(item.split(":", 1)[1])
            explicit_shell = (index + 1, shell)
        elif item.startswith("run:"):
            run_line = index
            run_end, command = collect_run_block(lines, index, end)

    if run_line is None:
        return None
    effective_shell = explicit_shell[1] if explicit_shell else (inherited_shell or "unspecified")
    if not is_powershell_shell(effective_shell) and not WORKFLOW_MARKER_RE.search(command):
        return None
    line_start = min(explicit_shell[0], run_line + 1) if explicit_shell else run_line + 1
    return {
        "source_file": rel,
        "step_or_action": step_name or "(unnamed step)",
        "shell": effective_shell,
        "line_start": line_start,
        "line_end": run_end,
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
    return sorted(path.decode("utf-8", errors="ignore") for path in completed.stdout.split(b"\0") if path)


def filesystem_files(repo_root: Path) -> list[str]:
    files: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = relpath(path, repo_root)
        if any(part in IGNORED_DISCOVERY_SEGMENTS for part in path_parts(rel)):
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
    for value in values:
        path = Path(value)
        if path.is_absolute():
            try:
                normalized.append(path.resolve().relative_to(repo_root.resolve()).as_posix())
            except ValueError:
                normalized.append(path.as_posix().lstrip("/"))
        else:
            normalized.append(path.as_posix())
    return sorted(dict.fromkeys(normalized))


def load_changed_files_from(path: Path) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(f"Changed-files input is missing: {path}")
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_manifest(repo_root: Path) -> dict[str, Any] | None:
    path = repo_root / MANIFEST_PATH
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def manifest_error(repo_root: Path) -> str | None:
    path = repo_root / MANIFEST_PATH
    if not path.is_file():
        return f"Collector runtime manifest is missing: {MANIFEST_PATH.as_posix()}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"Invalid JSON in collector runtime manifest {MANIFEST_PATH.as_posix()}: {exc}"
    if not isinstance(data, dict):
        return f"Collector runtime manifest must be a JSON object: {MANIFEST_PATH.as_posix()}"
    return None


def collector_manifest_paths(repo_root: Path) -> list[str]:
    manifest = load_manifest(repo_root)
    if not manifest:
        return []
    paths: list[str] = []
    wrapper = manifest.get("collector_wrapper_source")
    if isinstance(wrapper, str):
        paths.append(wrapper)
    part_files = manifest.get("collector_part_files", [])
    if isinstance(part_files, list):
        paths.extend(path for path in part_files if isinstance(path, str))
    return sorted(dict.fromkeys(paths))


def harness_source_part_paths(repo_root: Path) -> list[str]:
    root = repo_root / HARNESS_PARTS_ROOT
    if not root.is_dir():
        return []
    return sorted(relpath(path, repo_root) for path in root.glob("*.ps1.txt") if path.is_file())


def read_required_profile_harness_paths(repo_root: Path) -> tuple[list[str], str | None]:
    path = repo_root / REQUIRED_SURFACE_PROFILES_PATH
    if not path.is_file():
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
        if rel not in existing and not (repo_root / rel).is_file():
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
        exists = (repo_root / rel).is_file()
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
        exists = (repo_root / rel).is_file()
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
            "exists": (repo_root / MANIFEST_PATH).is_file(),
            "error": manifest_error(repo_root),
            "expected_path_count": len(manifest_paths),
            "present_path_count": sum(1 for rel in manifest_paths if (repo_root / rel).is_file()),
            "paths": manifest_entries,
        },
        "harness_source_parts": {
            "root": HARNESS_PARTS_ROOT.as_posix(),
            "part_count": len(harness_parts),
            "required_profile_path": REQUIRED_SURFACE_PROFILES_PATH.as_posix(),
            "required_profile_exists": (repo_root / REQUIRED_SURFACE_PROFILES_PATH).is_file(),
            "required_profile_error": profile_error,
            "required_profile_part_count": len(profile_harness_paths),
            "required_profile_present_count": sum(1 for rel in profile_harness_paths if (repo_root / rel).is_file()),
            "required_profile_parts": [
                {
                    "path": rel,
                    "exists": (repo_root / rel).is_file(),
                    "in_inventory": rel in by_path,
                    "category": by_path.get(rel, {}).get("category"),
                    "size_bytes": by_path.get(rel, {}).get("size_bytes"),
                }
                for rel in profile_harness_paths
            ],
            "parts": [
                {
                    "path": rel,
                    "exists": (repo_root / rel).is_file(),
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
                "exists": (repo_root / expected_generated).is_file(),
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
        if (
            entry["source_type"] != "workflow_yaml"
            and entry["inclusion_decision"] != "exclude"
            and entry.get("exists")
            and entry.get("size_bytes") == 0
        ):
            errors.append(f"{entry['path']}: included PowerShell surface is empty")
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


def write_outputs(repo_root: Path, inventory: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_path = repo_root / json_output
    markdown_path = repo_root / markdown_output
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(inventory), encoding="utf-8")


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

    changed_files: list[str] | None = None
    if args.changed_file or args.changed_files_from:
        changed_files = list(args.changed_file)
        if args.changed_files_from:
            changed_files.extend(load_changed_files_from(Path(args.changed_files_from)))

    baseline = load_json_file(Path(args.baseline_json)) if args.baseline_json else None
    shrink_exceptions = load_shrink_exceptions(Path(args.shrink_exception_json) if args.shrink_exception_json else None)
    inventory = build_inventory(
        repo_root=repo_root,
        changed_files=changed_files,
        baseline=baseline,
        shrink_exceptions=shrink_exceptions,
        json_output=json_output,
        markdown_output=markdown_output,
    )

    if not args.no_write:
        write_outputs(repo_root, inventory, json_output, markdown_output)
    print(json.dumps(inventory["summary"], indent=2))
    if inventory["validation"]["errors"]:
        for error in inventory["validation"]["errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
