#!/usr/bin/env python3
"""Validate PowerShell source-part and generated-output assembly parity.

This #265 runner stays local and source-focused. It maps collector runtime and
harness source parts, regenerates the runnable text in memory, checks stale
checked-in generated output when present, and writes JSON/Markdown evidence for
later workflow integration work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "dcoir_powershell_assembly_parity_report_v1"
ISSUE_NUMBER = 265
PARENT_ISSUE_NUMBER = 260
DEFAULT_MANIFEST = Path("project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json")
DEFAULT_INVENTORY = Path("project_sources/collector/powershell_surface_inventory.json")
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_assembly_parity_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_assembly_parity_report.md")
HARNESS_PARTS_ROOT = Path("project_sources/collector/harness/source/parts")
HARNESS_GENERATED_OUTPUT = Path("project_sources/collector/harness/run_DCOIR_Tests.generated.ps1")
COLLECTOR_IMPORT_BLOCK = re.compile(
    r"(?ms)^\$collectorPartsRoot = .*?^foreach \(\$partFile in \$collectorPartFiles\) \{.*?^\}\s*"
)
POWERSHELL_PARSE_SCRIPT = """\
param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$parseErrors) | Out-Null
if ($parseErrors -and $parseErrors.Count -gt 0) {
    $parseErrors | ForEach-Object {
        '{0}:{1}: {2}' -f $_.Extent.StartLineNumber, $_.Extent.StartColumnNumber, $_.Message
    }
    exit 1
}
"""


class AssemblyParityError(RuntimeError):
    """Raised for fail-closed #265 assembly parity validation errors."""


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AssemblyParityError(f"{label} missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AssemblyParityError(f"{label} invalid JSON: {path}: {exc}") from exc


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def safe_relpath(path: Path, repo_root: Path) -> str:
    try:
        return relpath(path, repo_root)
    except ValueError:
        return path.as_posix()


def file_facts(path: Path, repo_root: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "path": safe_relpath(path, repo_root),
            "exists": False,
            "size_bytes": None,
            "line_count": None,
            "sha256": None,
        }
    data = path.read_bytes()
    return {
        "path": safe_relpath(path, repo_root),
        "exists": True,
        "size_bytes": len(data),
        "line_count": data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def normalize_repo_path(value: str) -> str:
    slash_path = value.replace("\\", "/")
    while slash_path.startswith("./"):
        slash_path = slash_path[2:]
    return Path(slash_path).as_posix()


def is_absolute_repo_input(value: str) -> bool:
    raw = value.strip()
    slash_path = raw.replace("\\", "/")
    return slash_path.startswith("/") or re.match(r"^[A-Za-z]:/", slash_path) is not None or Path(raw).is_absolute()


def validate_manifest_repo_path(value: str, key: str, label: str, errors: list[str]) -> str:
    raw = value.strip()
    rel = normalize_repo_path(raw)
    raw_parts = Path(raw.replace("\\", "/")).parts
    parts = Path(rel).parts
    if not raw or is_absolute_repo_input(raw) or ".." in raw_parts or rel.startswith("../") or ".." in parts or Path(rel).is_absolute():
        errors.append(f"{label}: {key} must be a repo-relative path without traversal")
    return rel


def require_non_empty_string(mapping: dict[str, Any], key: str, label: str, errors: list[str]) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: {key} must be a non-empty string")
        return ""
    return validate_manifest_repo_path(value, key, label, errors)


def require_non_empty_string_list(mapping: dict[str, Any], key: str, label: str, errors: list[str]) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value:
        errors.append(f"{label}: {key} must be a non-empty list")
        return []
    normalized: list[str] = []
    for index, raw_item in enumerate(value, start=1):
        item_key = f"{key}[{index}]"
        if not isinstance(raw_item, str) or not raw_item.strip():
            errors.append(f"{label}: {item_key} must be a non-empty string")
            continue
        normalized.append(validate_manifest_repo_path(raw_item, item_key, label, errors))
    return normalized


def part_entry(path: Path, repo_root: Path) -> dict[str, Any]:
    facts = file_facts(path, repo_root)
    facts["empty"] = bool(facts["exists"] and facts["size_bytes"] == 0)
    return facts


def static_powershell_parse(text: str) -> dict[str, Any]:
    """A deterministic local parse surrogate used when pwsh is unavailable."""
    normalized = normalize_text(text)
    lines = normalized.splitlines()
    errors: list[str] = []
    stack: list[tuple[str, int, int]] = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = {")": "(", "]": "[", "}": "{"}
    quote: str | None = None
    block_comment = False
    here_string_end: str | None = None
    line = 1
    column = 0
    index = 0
    at_line_start = True
    while index < len(normalized):
        char = normalized[index]
        next_char = normalized[index + 1] if index + 1 < len(normalized) else ""
        column += 1

        if char == "\n":
            line += 1
            column = 0
            at_line_start = True
            index += 1
            continue

        if here_string_end is not None:
            if at_line_start and normalized.startswith(here_string_end, index):
                index += len(here_string_end)
                column += len(here_string_end) - 1
                here_string_end = None
                at_line_start = False
                continue
            index += 1
            at_line_start = False
            continue

        if block_comment:
            if char == "#" and next_char == ">":
                block_comment = False
                index += 2
                column += 1
                at_line_start = False
                continue
            index += 1
            at_line_start = False
            continue

        if quote:
            if char == "`":
                index += 2
                column += 1
                at_line_start = False
                continue
            if char == quote:
                if quote == "'" and next_char == "'":
                    index += 2
                    column += 1
                    at_line_start = False
                    continue
                quote = None
            index += 1
            at_line_start = False
            continue

        if char.isspace():
            index += 1
            continue

        if char == "<" and next_char == "#":
            block_comment = True
            index += 2
            column += 1
            at_line_start = False
            continue

        if char == "#":
            newline = normalized.find("\n", index)
            if newline == -1:
                break
            index = newline
            continue

        if char == "@" and next_char in {"'", '"'} and (
            index + 2 >= len(normalized) or normalized[index + 2] == "\n"
        ):
            here_string_end = next_char + "@"
            index += 2
            column += 1
            at_line_start = False
            continue

        if char in {"'", '"'}:
            quote = char
            index += 1
            at_line_start = False
            continue

        if char in pairs:
            stack.append((char, line, column))
        elif char in closers:
            if not stack or stack[-1][0] != closers[char]:
                errors.append(f"line {line}, column {column}: unmatched {char!r}")
            else:
                stack.pop()
        index += 1
        at_line_start = False

    if quote:
        errors.append(f"unterminated {quote!r} string")
    if block_comment:
        errors.append("unterminated block comment")
    if here_string_end:
        errors.append(f"unterminated here-string ending with {here_string_end!r}")
    for opener, opener_line, opener_column in reversed(stack):
        errors.append(f"line {opener_line}, column {opener_column}: unclosed {opener!r}")

    return {
        "method": "static_balance_check",
        "native_parser_available": False,
        "success": not errors,
        "errors": errors,
        "line_count": len(lines),
    }


def parse_powershell_text(text: str) -> dict[str, Any]:
    pwsh = shutil.which("pwsh")
    if pwsh:
        temp_path: Path | None = None
        parser_script_path: Path | None = None
        cleanup_errors: list[str] = []
        result: dict[str, Any] | None = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".ps1", encoding="utf-8", delete=False) as handle:
                handle.write(text)
                temp_path = Path(handle.name)
            with tempfile.NamedTemporaryFile("w", suffix=".ps1", encoding="utf-8", delete=False) as handle:
                handle.write(POWERSHELL_PARSE_SCRIPT)
                parser_script_path = Path(handle.name)
            command = [
                pwsh,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(parser_script_path),
                str(temp_path),
            ]
            completed = subprocess.run(command, text=True, capture_output=True, timeout=30, check=False)
            errors = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
            if completed.returncode != 0 and completed.stderr.strip():
                errors.extend(line.strip() for line in completed.stderr.splitlines() if line.strip())
            result = {
                "method": "powershell_language_parser",
                "native_parser_available": True,
                "success": completed.returncode == 0,
                "errors": errors,
                "line_count": source_line_count(text),
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            static = static_powershell_parse(text)
            static["method"] = "static_balance_check_after_native_parser_error"
            static["native_parser_available"] = True
            static["native_parser_error"] = str(exc)
            result = static
        finally:
            for label, path in (("target", temp_path), ("parser", parser_script_path)):
                if path is None:
                    continue
                try:
                    path.unlink()
                except OSError as exc:
                    cleanup_errors.append(f"failed to remove temporary PowerShell {label} script: {exc}")
        if result is None:
            result = static_powershell_parse(text)
            result["method"] = "static_balance_check_after_native_parser_error"
            result["native_parser_available"] = True
            result["native_parser_error"] = "native parser did not produce a result"
        if cleanup_errors:
            result["success"] = False
            result["errors"] = list(result.get("errors", [])) + cleanup_errors
        return result
    return static_powershell_parse(text)


def source_line_count(text: str) -> int:
    normalized = normalize_text(text)
    return normalized.count("\n") + (1 if normalized and not normalized.endswith("\n") else 0)


def read_part_text(path: Path) -> str:
    text = normalize_text(path.read_text(encoding="utf-8"))
    if not text.endswith("\n"):
        text += "\n"
    return text


def build_collector_output(
    repo_root: Path,
    manifest: dict[str, Any],
    errors: list[str],
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    wrapper_rel = require_non_empty_string(manifest, "collector_wrapper_source", "collector manifest", errors)
    part_rels = require_non_empty_string_list(manifest, "collector_part_files", "collector manifest", errors)
    compiled_name = manifest.get("compiled_runtime_name", "DCOIR_Collector.ps1")
    if not isinstance(compiled_name, str) or not compiled_name.strip():
        errors.append("collector manifest: compiled_runtime_name must be a non-empty string")
        compiled_name = "DCOIR_Collector.ps1"

    source_entries: list[dict[str, Any]] = []
    wrapper_path = repo_root / wrapper_rel
    wrapper_entry = part_entry(wrapper_path, repo_root)
    wrapper_entry["role"] = "collector_runtime_wrapper"
    source_entries.append(wrapper_entry)
    if not wrapper_entry["exists"]:
        errors.append(f"{wrapper_rel}: collector wrapper is missing")
        return "", source_entries, {}
    wrapper_text = wrapper_path.read_text(encoding="utf-8")
    if not COLLECTOR_IMPORT_BLOCK.search(wrapper_text):
        errors.append(f"{wrapper_rel}: collector wrapper import block is missing or no longer matches the compiler contract")

    blocks: list[str] = ["# BEGIN COMPILED COLLECTOR PARTS"]
    line_map: list[dict[str, Any]] = []
    generated_line = 2
    for part_rel in part_rels:
        part_path = repo_root / part_rel
        entry = part_entry(part_path, repo_root)
        entry["role"] = "collector_runtime_source_part"
        source_entries.append(entry)
        if not entry["exists"]:
            errors.append(f"{part_rel}: collector source part is missing")
            continue
        if entry["empty"]:
            errors.append(f"{part_rel}: collector source part is empty")
            continue
        text = read_part_text(part_path)
        part_lines = source_line_count(text)
        blocks.append(f"# BEGIN {part_path.name}")
        blocks.append(text.rstrip("\n"))
        blocks.append(f"# END {part_path.name}")
        blocks.append("")
        line_map.append(
            {
                "source_path": part_rel,
                "source_line_start": 1,
                "source_line_end": part_lines,
                "generated_line_start": generated_line + 1,
                "generated_line_end": generated_line + part_lines,
                "mapping_basis": "compiler_begin_end_markers",
            }
        )
        generated_line += part_lines + 3
    blocks.append("# END COMPILED COLLECTOR PARTS")
    inline_block = "\n".join(blocks) + "\n"
    generated_text = COLLECTOR_IMPORT_BLOCK.sub(lambda _m: inline_block, wrapper_text, count=1)
    if not generated_text.endswith("\n"):
        generated_text += "\n"
    output = {
        "id": "collector_compiled_runtime",
        "path": f"compiled_runtime/{compiled_name}",
        "repo_committed_path": None,
        "assembly_model": manifest.get("source_strategy"),
        "source_input_count": len(part_rels),
        "line_mapping_status": "available",
        "line_mapping": line_map,
        "sha256": sha256_text(generated_text),
        "line_count": source_line_count(generated_text),
        "parse": parse_powershell_text(generated_text),
        "parity": {
            "status": "pass",
            "comparison": "deterministic_in_memory_regeneration",
            "checked_in_output_compared": False,
        },
    }
    return generated_text, source_entries, output


def harness_part_paths(repo_root: Path) -> list[Path]:
    root = repo_root / HARNESS_PARTS_ROOT
    return sorted(root.glob("run_DCOIR_Tests.part-*.ps1.txt"))


def build_harness_output(repo_root: Path, errors: list[str]) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    parts = harness_part_paths(repo_root)
    source_entries: list[dict[str, Any]] = []
    if not parts:
        errors.append(f"{HARNESS_PARTS_ROOT.as_posix()}: no harness source parts found")

    assembled: list[str] = []
    line_map: list[dict[str, Any]] = []
    generated_line = 1
    for part_path in parts:
        part_rel = safe_relpath(part_path, repo_root)
        entry = part_entry(part_path, repo_root)
        entry["role"] = "collector_harness_source_part"
        source_entries.append(entry)
        if entry["empty"]:
            errors.append(f"{part_rel}: harness source part is empty")
            continue
        text = read_part_text(part_path)
        assembled.append(text)
        part_lines = source_line_count(text)
        line_map.append(
            {
                "source_path": part_rel,
                "source_line_start": 1,
                "source_line_end": part_lines,
                "generated_line_start": generated_line,
                "generated_line_end": generated_line + part_lines - 1,
                "mapping_basis": "deterministic_sorted_concatenation",
            }
        )
        generated_line += part_lines
    generated_text = "".join(assembled)
    if generated_text and not generated_text.endswith("\n"):
        generated_text += "\n"

    expected_path = repo_root / HARNESS_GENERATED_OUTPUT
    parity: dict[str, Any] = {
        "status": "pass",
        "comparison": "deterministic_in_memory_regeneration",
        "checked_in_output_compared": False,
        "expected_presence": "optional_when_generated",
    }
    if expected_path.exists():
        expected_text = normalize_text(expected_path.read_text(encoding="utf-8"))
        if not expected_text.endswith("\n"):
            expected_text += "\n"
        parity.update(
            {
                "checked_in_output_compared": True,
                "checked_in_path": HARNESS_GENERATED_OUTPUT.as_posix(),
                "checked_in_sha256_normalized": sha256_text(expected_text),
                "generated_sha256": sha256_text(generated_text),
            }
        )
        if sha256_text(expected_text) != sha256_text(generated_text):
            parity["status"] = "fail"
            parity["comparison"] = "checked_in_generated_output_is_stale"
            errors.append(f"{HARNESS_GENERATED_OUTPUT.as_posix()}: checked-in generated harness is stale")
    else:
        parity["comparison"] = "deterministic_regeneration_only_checked_in_output_absent"
        parity["checked_in_path"] = HARNESS_GENERATED_OUTPUT.as_posix()

    output = {
        "id": "harness_generated_tests",
        "path": HARNESS_GENERATED_OUTPUT.as_posix(),
        "repo_committed_path": HARNESS_GENERATED_OUTPUT.as_posix() if expected_path.exists() else None,
        "assembly_model": "sorted_harness_source_part_concatenation",
        "source_input_count": len(parts),
        "line_mapping_status": "available",
        "line_mapping": line_map,
        "sha256": sha256_text(generated_text),
        "line_count": source_line_count(generated_text),
        "parse": parse_powershell_text(generated_text),
        "parity": parity,
    }
    return generated_text, source_entries, output


def inventory_counts(inventory: dict[str, Any]) -> dict[str, int]:
    controls = inventory.get("controls") if isinstance(inventory, dict) else {}
    if not isinstance(controls, dict):
        return {}
    collector = controls.get("collector_manifest", {})
    harness = controls.get("harness_source_parts", {})
    generated = controls.get("generated_outputs", [])
    collector_expected = collector.get("expected_path_count", 0) if isinstance(collector, dict) else 0
    harness_expected = harness.get("part_count", 0) if isinstance(harness, dict) else 0
    return {
        "collector_manifest_path_count": int(collector_expected or 0),
        "collector_source_part_count": max(0, int(collector_expected or 0) - 1),
        "harness_source_part_count": int(harness_expected or 0),
        "generated_output_mapping_count": len(generated) if isinstance(generated, list) else 0,
    }


def compare_inventory_controls(
    observed: dict[str, int],
    inventory: dict[str, Any],
    errors: list[str],
) -> None:
    counts = inventory_counts(inventory)
    if not counts:
        errors.append("PowerShell surface inventory controls are missing collector/harness source-part counts")
        return
    if observed["collector_source_part_count"] < counts["collector_source_part_count"]:
        errors.append(
            "collector source-part map unexpectedly shrank below inventory controls: "
            f"{observed['collector_source_part_count']} < {counts['collector_source_part_count']}"
        )
    if observed["harness_source_part_count"] < counts["harness_source_part_count"]:
        errors.append(
            "harness source-part map unexpectedly shrank below inventory controls: "
            f"{observed['harness_source_part_count']} < {counts['harness_source_part_count']}"
        )
    if observed["generated_output_count"] < 1 + counts["generated_output_mapping_count"]:
        errors.append(
            "generated-output map unexpectedly shrank below collector plus inventory-generated controls: "
            f"{observed['generated_output_count']} < {1 + counts['generated_output_mapping_count']}"
        )


def compare_baseline_report(
    repo_root: Path,
    baseline_report: Path | None,
    summary: dict[str, int],
    shrink_exceptions: list[str],
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any] | None:
    if baseline_report is None:
        warnings.append("no baseline parity report supplied; shrink checks used current inventory controls only")
        return None
    baseline_path = repo_root / baseline_report
    baseline = read_json(baseline_path, "baseline assembly parity report")
    baseline_summary = baseline.get("summary", {}) if isinstance(baseline, dict) else {}
    checked: dict[str, Any] = {"path": baseline_report.as_posix(), "comparisons": []}
    for key in (
        "collector_source_part_count",
        "harness_source_part_count",
        "source_part_count",
        "generated_output_count",
    ):
        before = int(baseline_summary.get(key, 0) or 0)
        after = int(summary.get(key, 0) or 0)
        comparison = {"key": key, "baseline": before, "current": after, "status": "pass"}
        if after < before and not shrink_exceptions:
            comparison["status"] = "fail"
            errors.append(f"{key} unexpectedly shrank without approved exception: {after} < {before}")
        elif after < before:
            comparison["status"] = "approved_exception"
            comparison["exception_records"] = shrink_exceptions
        checked["comparisons"].append(comparison)
    return checked


def coverage_statement() -> list[dict[str, str]]:
    return [
        {
            "surface": "collector runtime source parts",
            "psscriptanalyzer_wrapper_reporting": "source-part paths when #262 analyzer targets #261 inventory entries",
            "dcoir_custom_checks_reporting": "source-part paths when #264 checks target source-part risk classes",
            "assembly_parity_reporting": "source input map, source hash, generated runtime hash, parse status, and line mapping",
        },
        {
            "surface": "collector compiled runtime generated output",
            "psscriptanalyzer_wrapper_reporting": "not invoked by this #265 runner; future workflow integration can pass generated output explicitly",
            "dcoir_custom_checks_reporting": "not invoked by this #265 runner; parity and parse proof are reported here",
            "assembly_parity_reporting": "generated output hash, parse status, deterministic regeneration status, and source line map",
        },
        {
            "surface": "harness source parts and generated harness",
            "psscriptanalyzer_wrapper_reporting": "source-part paths when #262 analyzer targets .ps1.txt surfaces; generated output when materialized and explicitly targeted",
            "dcoir_custom_checks_reporting": "source-part drift risks through #264 fixtures plus #265 parity proof",
            "assembly_parity_reporting": "ordered source input map, generated harness hash, optional checked-in comparison, parse status, and line map",
        },
    ]


def controlled_bad_cases() -> list[dict[str, str]]:
    return [
        {
            "case": "stale_checked_in_generated_output",
            "evidence": "test_stale_checked_in_generated_output_fails",
            "expected_result": "fails when a committed generated harness differs from deterministic assembly",
        },
        {
            "case": "missing_source_part",
            "evidence": "test_missing_source_part_fails",
            "expected_result": "fails when the collector manifest references a missing source part",
        },
        {
            "case": "missing_source_output_mapping",
            "evidence": "test_missing_source_output_mapping_fails",
            "expected_result": "fails when collector part mapping is absent and generated output cannot be mapped",
        },
        {
            "case": "generated_output_parse_failure",
            "evidence": "test_generated_output_parse_failure_fails",
            "expected_result": "fails when regenerated runnable output has an unbalanced PowerShell structure",
        },
        {
            "case": "unexpected_inventory_shrink",
            "evidence": "test_baseline_shrink_without_exception_fails",
            "expected_result": "fails when source/generated counts shrink below baseline without an exception record",
        },
        {
            "case": "clean_control",
            "evidence": "test_clean_control_passes_and_maps_counts and test_real_repo_contract_passes",
            "expected_result": "passes when source parts, generated outputs, parse status, parity status, and mappings are fresh",
        },
    ]


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    validation = report["validation"]
    lines = [
        "# PowerShell Assembly Parity Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Issue: `#{report['issue']}`",
        f"- Success: `{validation['success']}`",
        f"- Source parts: `{summary['source_part_count']}`",
        f"- Collector source parts: `{summary['collector_source_part_count']}`",
        f"- Harness source parts: `{summary['harness_source_part_count']}`",
        f"- Generated outputs mapped: `{summary['generated_output_count']}`",
        f"- Parse status: `{summary['parse_status']}`",
        f"- Parity status: `{summary['parity_status']}`",
        "",
        "## Generated Outputs",
        "",
        "| Output | Inputs | Parse | Parity | Line Mapping |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for output in report["generated_outputs"]:
        lines.append(
            "| `{path}` | `{inputs}` | `{parse}` | `{parity}` | `{mapping}` |".format(
                path=output["path"],
                inputs=output["source_input_count"],
                parse="pass" if output["parse"]["success"] else "fail",
                parity=output["parity"]["status"],
                mapping=output["line_mapping_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Coverage Statement",
            "",
            "| Surface | Analyzer wrapper reporting | Custom check reporting | Assembly parity reporting |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in report["coverage_statement"]:
        lines.append(
            "| `{surface}` | {analyzer} | {custom} | {parity} |".format(
                surface=item["surface"],
                analyzer=item["psscriptanalyzer_wrapper_reporting"],
                custom=item["dcoir_custom_checks_reporting"],
                parity=item["assembly_parity_reporting"],
            )
        )
    lines.extend(["", "## Controlled Cases", ""])
    for item in report["controlled_bad_cases"]:
        lines.append(f"- `{item['case']}`: {item['expected_result']} (`{item['evidence']}`)")
    if validation["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in validation["errors"])
    if validation["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in validation["warnings"])
    return "\n".join(lines) + "\n"


def write_outputs(repo_root: Path, report: dict[str, Any], json_output: Path, markdown_output: Path) -> list[str]:
    errors: list[str] = []
    for path, content in (
        (repo_root / json_output, json.dumps(report, indent=2) + "\n"),
        (repo_root / markdown_output, render_markdown(report)),
    ):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            errors.append(f"failed to write {safe_relpath(path, repo_root)}: {exc}")
    return errors


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str]]:
    repo_root = Path(args.repo_root).resolve()
    manifest_path = repo_root / Path(args.manifest)
    inventory_path = repo_root / Path(args.inventory)
    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    baseline_report = Path(args.baseline_report) if args.baseline_report else None
    shrink_exceptions = list(args.shrink_exception or [])
    errors: list[str] = []
    warnings: list[str] = []

    manifest: dict[str, Any] = {}
    inventory: dict[str, Any] = {}
    try:
        manifest = read_json(manifest_path, "collector runtime manifest")
    except AssemblyParityError as exc:
        errors.append(str(exc))
    try:
        inventory = read_json(inventory_path, "PowerShell surface inventory")
    except AssemblyParityError as exc:
        errors.append(str(exc))
    if manifest and not isinstance(manifest, dict):
        errors.append(f"collector runtime manifest must be a JSON object: {Path(args.manifest).as_posix()}")
        manifest = {}
    if inventory and not isinstance(inventory, dict):
        errors.append(f"PowerShell surface inventory must be a JSON object: {Path(args.inventory).as_posix()}")
        inventory = {}

    collector_text = ""
    harness_text = ""
    collector_sources: list[dict[str, Any]] = []
    harness_sources: list[dict[str, Any]] = []
    generated_outputs: list[dict[str, Any]] = []
    if manifest:
        collector_text, collector_sources, collector_output = build_collector_output(repo_root, manifest, errors)
        if collector_output:
            generated_outputs.append(collector_output)
    harness_text, harness_sources, harness_output = build_harness_output(repo_root, errors)
    generated_outputs.append(harness_output)

    for output in generated_outputs:
        if not output["line_mapping"]:
            errors.append(f"{output['id']}: source/output mapping is missing")
        if not output["parse"]["success"]:
            errors.append(f"{output['id']}: generated output parse check failed")
        if output["parity"]["status"] != "pass":
            errors.append(f"{output['id']}: parity status is {output['parity']['status']}")

    collector_part_count = len([entry for entry in collector_sources if entry.get("role") == "collector_runtime_source_part" and entry.get("exists")])
    harness_part_count = len([entry for entry in harness_sources if entry.get("role") == "collector_harness_source_part" and entry.get("exists")])
    summary = {
        "collector_source_part_count": collector_part_count,
        "harness_source_part_count": harness_part_count,
        "source_part_count": collector_part_count + harness_part_count,
        "source_input_count": len([entry for entry in collector_sources + harness_sources if entry.get("exists")]),
        "generated_output_count": len(generated_outputs),
        "parse_success_count": len([output for output in generated_outputs if output["parse"]["success"]]),
        "parity_success_count": len([output for output in generated_outputs if output["parity"]["status"] == "pass"]),
    }
    summary["parse_status"] = "pass" if summary["parse_success_count"] == len(generated_outputs) else "fail"
    summary["parity_status"] = "pass" if summary["parity_success_count"] == len(generated_outputs) else "fail"

    compare_inventory_controls(summary, inventory, errors)
    baseline = None
    if baseline_report is not None:
        try:
            baseline = compare_baseline_report(repo_root, baseline_report, summary, shrink_exceptions, errors, warnings)
        except AssemblyParityError as exc:
            errors.append(str(exc))
    else:
        warnings.append("no baseline parity report supplied; shrink checks used current inventory controls only")

    report = {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "parent_issue": PARENT_ISSUE_NUMBER,
        "depends_on": [261, 262, 263, 264],
        "source_of_truth": "#265 assembly-aware validation for PowerShell source parts and generated outputs",
        "manifest": {
            "path": Path(args.manifest).as_posix(),
            "exists": manifest_path.is_file(),
            "sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
            "source_strategy": manifest.get("source_strategy") if isinstance(manifest, dict) else None,
        },
        "inventory": {
            "path": Path(args.inventory).as_posix(),
            "exists": inventory_path.is_file(),
            "sha256": sha256_file(inventory_path) if inventory_path.is_file() else None,
            "schema_version": inventory.get("schema_version") if isinstance(inventory, dict) else None,
            "control_counts": inventory_counts(inventory),
        },
        "summary": summary,
        "source_maps": {
            "collector_runtime": collector_sources,
            "harness": harness_sources,
        },
        "generated_outputs": generated_outputs,
        "coverage_statement": coverage_statement(),
        "controlled_bad_cases": controlled_bad_cases(),
        "baseline_comparison": baseline,
        "validation": {
            "success": not errors,
            "errors": errors,
            "warnings": warnings,
        },
        "outputs": {
            "json": json_output.as_posix(),
            "markdown": markdown_output.as_posix(),
        },
    }
    if not args.no_write:
        output_errors = write_outputs(repo_root, report, json_output, markdown_output)
        if output_errors:
            errors.extend(output_errors)
            report["validation"]["success"] = False
            report["validation"]["errors"] = errors
            write_outputs(repo_root, report, json_output, markdown_output)
    return report, errors, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DCOIR PowerShell assembly parity validation")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST.as_posix(), help="Collector runtime manifest JSON")
    parser.add_argument("--inventory", default=DEFAULT_INVENTORY.as_posix(), help="#261 PowerShell inventory JSON")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="Assembly parity JSON report path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Assembly parity Markdown report path")
    parser.add_argument("--baseline-report", default="", help="Previous assembly parity report for shrink checks")
    parser.add_argument("--shrink-exception", action="append", default=[], help="Approved exception record for expected shrink")
    parser.add_argument("--no-write", action="store_true", help="Do not write report outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, errors, _warnings = build_report(args)
    print(json.dumps(report["summary"], indent=2))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
