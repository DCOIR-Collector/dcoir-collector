#!/usr/bin/env python3
"""Validate duplicate-function JSON and Markdown report artifacts."""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


DEFAULT_JSON = Path("project_sources/collector/powershell_duplicate_function_report.json")
DEFAULT_MARKDOWN = Path("project_sources/collector/powershell_duplicate_function_report.md")
SCHEMA_VERSION = "dcoir_powershell_duplicate_function_report_v1"
REPORT_ROOT = PurePosixPath("project_sources/collector")
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class ValidationError(RuntimeError):
    """Raised when a duplicate-function report does not match the contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_int_mapping(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key)
    require(isinstance(value, int), f"summary.{key} must be an integer")
    require(value >= 0, f"summary.{key} must not be negative")
    return value


def resolve_report_path(path: Path, expected_suffix: Path, label: str, root: Path | None = None) -> Path:
    raw = str(path)
    require(raw, f"{label} path is required")
    require(CONTROL_CHARS.search(raw) is None, f"{label} path contains control characters")

    normalized = raw.replace("\\", "/").strip()
    require(normalized, f"{label} path is required")
    candidate = PurePosixPath(normalized)

    require(not candidate.is_absolute(), f"{label} path must be repository-relative")
    require(".." not in candidate.parts, f"{label} path must not contain traversal segments")
    require(candidate.parts[: len(REPORT_ROOT.parts)] == REPORT_ROOT.parts, f"{label} path must be under {REPORT_ROOT}")
    require(candidate.name == expected_suffix.name, f"{label} path must end with {expected_suffix.name}")

    repo_root = (root or Path.cwd()).resolve()
    allowed_root = (repo_root / Path(REPORT_ROOT.as_posix())).resolve()
    resolved = (repo_root / Path(candidate.as_posix())).resolve()
    try:
        resolved.relative_to(allowed_root)
    except ValueError as exc:
        raise ValidationError(f"{label} path escapes {REPORT_ROOT}") from exc

    return Path(candidate.as_posix())


def scoped_report_path(root: Path, path: Path, expected_suffix: Path, label: str) -> Path:
    relative_path = resolve_report_path(path, expected_suffix, label, root=root)
    return root / relative_path


def load_report(path: Path) -> dict[str, Any]:
    require(path.is_file(), f"JSON report missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"JSON report is invalid: {exc}") from exc
    require(isinstance(data, dict), "JSON report root must be an object")
    return data


def validate_json_report(data: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    require(data.get("schema_version") == SCHEMA_VERSION, "unexpected schema_version")

    validation = data.get("validation")
    require(isinstance(validation, dict), "validation must be an object")
    require(isinstance(validation.get("success"), bool), "validation.success must be boolean")
    require(isinstance(validation.get("errors"), list), "validation.errors must be a list")
    require(isinstance(validation.get("warnings"), list), "validation.warnings must be a list")

    summary = data.get("summary")
    require(isinstance(summary, dict), "summary must be an object")
    file_count = require_int_mapping(summary, "file_count")
    function_count = require_int_mapping(summary, "function_name_count")
    duplicate_count = require_int_mapping(summary, "duplicate_function_count")
    parse_failure_count = require_int_mapping(summary, "parse_failure_count")
    require(file_count > 0, "summary.file_count must be positive")

    for key in ("duplicates", "parse_failures", "targets"):
        require(isinstance(data.get(key), list), f"{key} must be a list")

    require(len(data["duplicates"]) == duplicate_count, "duplicate count does not match duplicates list")
    require(len(data["parse_failures"]) == parse_failure_count, "parse failure count does not match list")
    require(len(data["targets"]) == file_count, "file count does not match targets list")
    require(function_count >= duplicate_count, "function_name_count must be at least duplicate_function_count")

    for index, duplicate in enumerate(data["duplicates"], start=1):
        require(isinstance(duplicate, dict), f"duplicates[{index}] must be an object")
        require(isinstance(duplicate.get("function_name"), str) and duplicate["function_name"], f"duplicates[{index}].function_name is required")
        require(isinstance(duplicate.get("normalized_name"), str) and duplicate["normalized_name"], f"duplicates[{index}].normalized_name is required")
        occurrence_count = duplicate.get("occurrence_count")
        occurrences = duplicate.get("occurrences")
        require(isinstance(occurrence_count, int) and occurrence_count >= 2, f"duplicates[{index}].occurrence_count must be >= 2")
        require(isinstance(occurrences, list), f"duplicates[{index}].occurrences must be a list")
        require(len(occurrences) == occurrence_count, f"duplicates[{index}] occurrence count mismatch")
        for occurrence_index, occurrence in enumerate(occurrences, start=1):
            require(isinstance(occurrence, dict), f"duplicates[{index}].occurrences[{occurrence_index}] must be an object")
            require(isinstance(occurrence.get("path"), str) and occurrence["path"], "duplicate occurrence path is required")
            require(isinstance(occurrence.get("line"), int) and occurrence["line"] > 0, "duplicate occurrence line must be positive")

    for index, failure in enumerate(data["parse_failures"], start=1):
        require(isinstance(failure, dict), f"parse_failures[{index}] must be an object")
        for field in ("path", "message"):
            require(isinstance(failure.get(field), str) and failure[field], f"parse_failures[{index}].{field} is required")
        for field in ("line", "column"):
            require(isinstance(failure.get(field), int) and failure[field] > 0, f"parse_failures[{index}].{field} must be positive")

    artifact_contract = data.get("artifact_contract")
    require(isinstance(artifact_contract, dict), "artifact_contract must be an object")
    local_artifacts = artifact_contract.get("local_artifacts")
    require(isinstance(local_artifacts, dict), "artifact_contract.local_artifacts must be an object")
    require(local_artifacts.get("json") == json_path.as_posix(), "artifact_contract JSON path mismatch")
    require(local_artifacts.get("markdown") == markdown_path.as_posix(), "artifact_contract Markdown path mismatch")
    require(artifact_contract.get("workflow_behavior") == "caller_uploaded_artifact", "workflow_behavior mismatch")


def validate_markdown_report(text: str, data: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    require(text.startswith("# PowerShell Duplicate Function Report\n"), "Markdown report heading missing")
    for marker in (
        "## Summary",
        f"- JSON: `{json_path.as_posix()}`",
        f"- Markdown: `{markdown_path.as_posix()}`",
        "- Workflow behavior: `caller_uploaded_artifact`",
        "## Duplicate Function Definitions",
    ):
        require(marker in text, f"Markdown marker missing: {marker}")

    summary = data["summary"]
    require(f"- Files scanned: {summary['file_count']}" in text, "Markdown file count mismatch")
    require(f"- Duplicate function names: {summary['duplicate_function_count']}" in text, "Markdown duplicate count mismatch")
    require(f"- Parse failures: {summary['parse_failure_count']}" in text, "Markdown parse failure count mismatch")

    if summary["parse_failure_count"]:
        require("## Parse Failures" in text, "Markdown parse failure section missing")
        require("| Path | Line | Column | Message |" in text, "Markdown parse failure table missing")

    if summary["duplicate_function_count"]:
        require("| Path | Line |" in text, "Markdown duplicate location table missing")
        for duplicate in data["duplicates"]:
            require(f"### `{duplicate['function_name']}`" in text, f"Markdown missing duplicate function {duplicate['function_name']}")
    else:
        require("No duplicate function definitions found." in text, "Markdown no-duplicates message missing")


def validate_reports(json_path: Path, markdown_path: Path) -> None:
    json_path = resolve_report_path(json_path, DEFAULT_JSON, "JSON report")
    markdown_path = resolve_report_path(markdown_path, DEFAULT_MARKDOWN, "Markdown report")
    data = load_report(json_path)
    require(markdown_path.is_file(), f"Markdown report missing: {markdown_path}")
    markdown = markdown_path.read_text(encoding="utf-8-sig")
    validate_json_report(data, json_path, markdown_path)
    validate_markdown_report(markdown, data, json_path, markdown_path)


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        json_path = scoped_report_path(root, DEFAULT_JSON, DEFAULT_JSON, "JSON report")
        markdown_path = scoped_report_path(root, DEFAULT_MARKDOWN, DEFAULT_MARKDOWN, "Markdown report")
        json_path.parent.mkdir(parents=True)
        report = {
            "schema_version": SCHEMA_VERSION,
            "validation": {"success": True, "errors": [], "warnings": []},
            "summary": {
                "file_count": 1,
                "function_name_count": 2,
                "duplicate_function_count": 0,
                "parse_failure_count": 0,
            },
            "duplicates": [],
            "parse_failures": [],
            "targets": ["project_sources/collector/source/DCOIR_Collector.ps1"],
            "artifact_contract": {
                "local_artifacts": {"json": DEFAULT_JSON.as_posix(), "markdown": DEFAULT_MARKDOWN.as_posix()},
                "workflow_behavior": "caller_uploaded_artifact",
                "retention_scope": "workflow-generated report artifacts uploaded by the caller workflow",
            },
        }
        json_path.write_text(json.dumps(report), encoding="utf-8")
        markdown_path.write_text(
            "\n".join(
                [
                    "# PowerShell Duplicate Function Report",
                    "",
                    "## Summary",
                    "",
                    "- Files scanned: 1",
                    "- Unique function names: 2",
                    "- Duplicate function names: 0",
                    "- Parse failures: 0",
                    "- Workflow behavior: `caller_uploaded_artifact`",
                    f"- JSON: `{DEFAULT_JSON.as_posix()}`",
                    f"- Markdown: `{DEFAULT_MARKDOWN.as_posix()}`",
                    "",
                    "## Duplicate Function Definitions",
                    "",
                    "No duplicate function definitions found.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        previous_cwd = Path.cwd()
        os.chdir(root)
        try:
            validate_reports(DEFAULT_JSON, DEFAULT_MARKDOWN)

            bad = dict(report)
            bad["schema_version"] = "wrong"
            json_path.write_text(json.dumps(bad), encoding="utf-8")
            try:
                validate_reports(DEFAULT_JSON, DEFAULT_MARKDOWN)
            except ValidationError:
                pass
            else:
                raise AssertionError("invalid schema self-test should fail")

            rejected_paths = (
                Path("../etc/passwd"),
                Path("../../../../tmp/evil.md"),
                Path("/tmp/evil.md"),
                Path("project_sources/collector/../validation/powershell_duplicate_function_report.json"),
                Path("project_sources/collector/not_the_report.json"),
                Path("project_sources/validation/powershell_duplicate_function_report.json"),
                Path("project_sources/collector/powershell_duplicate_function_report.json\nextra"),
            )
            for rejected_path in rejected_paths:
                try:
                    resolve_report_path(rejected_path, DEFAULT_JSON, "JSON report", root=root)
                except ValidationError:
                    pass
                else:
                    raise AssertionError(f"unsafe path self-test should fail: {rejected_path!s}")
        finally:
            os.chdir(previous_cwd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=DEFAULT_JSON.as_posix(), type=Path)
    parser.add_argument("--markdown", default=DEFAULT_MARKDOWN.as_posix(), type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            run_self_test()
        else:
            validate_reports(args.json, args.markdown)
    except ValidationError as exc:
        print(f"Duplicate-function report validation failed: {exc}")
        return 1

    print("Duplicate-function report validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
