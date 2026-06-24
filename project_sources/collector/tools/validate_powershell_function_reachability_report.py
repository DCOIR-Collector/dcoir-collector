#!/usr/bin/env python3
"""Validate regenerated PowerShell function reachability reports against committed reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CLASSIFICATIONS = (
    "entrypoint",
    "literal_referenced",
    "dynamic_invocation_uncertain",
    "static_unreferenced",
)

SUMMARY_FIELDS = (
    ("source_file_count", "source file count"),
    ("nested_function_count", "nested function count"),
    ("reference_count", "reference count"),
    ("coverage_state", "coverage state"),
    ("validation_success", "validation success summary"),
)

STRUCTURAL_REPORT_FIELDS = (
    ("analysis_scope", "analysis scope"),
    ("entrypoint_names", "entrypoint names"),
    ("functions", "function records"),
    ("dynamic_invocation_sites", "dynamic invocation site records"),
    ("runtime_lane_coverage", "runtime-lane coverage"),
    ("non_claims", "non-claims"),
)

REGENERATE_COMMAND = (
    "python project_sources/collector/tools/run_powershell_function_reachability_report.py "
    "--repo-root . --no-powershell "
    "--json-output project_sources/collector/powershell_function_reachability_report.json "
    "--markdown-output project_sources/collector/powershell_function_reachability_report.md"
)


def read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is invalid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return data


def summary(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("summary")
    return value if isinstance(value, dict) else {}


def classification_counts(report: dict[str, Any]) -> dict[str, Any]:
    value = summary(report).get("classification_counts")
    return value if isinstance(value, dict) else {}


def validation_success(report: dict[str, Any]) -> Any:
    value = report.get("validation")
    if not isinstance(value, dict):
        return None
    return value.get("success")


def stable_generated_from(report: dict[str, Any]) -> Any:
    value = report.get("generated_from")
    if not isinstance(value, dict):
        return value
    return {key: entry for key, entry in value.items() if key != "generated_at_utc"}


def int_value(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def classification_count(report: dict[str, Any], name: str) -> int:
    return int_value(classification_counts(report).get(name))


def mismatch_message(reason: str) -> str:
    return (
        f"{reason} If the collector function surface changed intentionally, regenerate and commit the "
        f"reachability reports with: {REGENERATE_COMMAND}. The review-assist gate compares regenerated "
        "workflow output to the committed reports and does not update committed artifacts."
    )


def append_value_mismatch(errors: list[str], label: str) -> None:
    errors.append(mismatch_message(f"Regenerated PowerShell function reachability {label} did not match the committed report."))


def compare_reports(generated: dict[str, Any], committed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    generated_summary = summary(generated)
    committed_summary = summary(committed)
    if validation_success(generated) is not True:
        errors.append(mismatch_message("Regenerated PowerShell function reachability report did not pass self-validation."))
    if validation_success(committed) is not True:
        errors.append(mismatch_message("Committed PowerShell function reachability report did not pass self-validation."))
    if generated_summary.get("parser_mode") != committed_summary.get("parser_mode"):
        errors.append(mismatch_message("Regenerated PowerShell function reachability parser mode did not match the committed report."))
    if generated_summary.get("function_count") != committed_summary.get("function_count"):
        errors.append(mismatch_message("Regenerated PowerShell function reachability function count did not match the committed report."))
    if generated_summary.get("dynamic_invocation_site_count") != committed_summary.get("dynamic_invocation_site_count"):
        errors.append(
            mismatch_message("Regenerated PowerShell function reachability dynamic invocation site count did not match the committed report.")
        )
    for summary_field, summary_label in SUMMARY_FIELDS:
        if generated_summary.get(summary_field) != committed_summary.get(summary_field):
            append_value_mismatch(errors, summary_label)
    for classification_name in CLASSIFICATIONS:
        generated_count = classification_count(generated, classification_name)
        committed_count = classification_count(committed, classification_name)
        if generated_count != committed_count:
            reason = (
                "Regenerated PowerShell function reachability classification count did not match committed report for "
                f"{classification_name}: generated={generated_count} committed={committed_count}"
            )
            errors.append(mismatch_message(reason))
    if stable_generated_from(generated) != stable_generated_from(committed):
        append_value_mismatch(errors, "generator metadata")
    for field_name, field_label in STRUCTURAL_REPORT_FIELDS:
        if generated.get(field_name) != committed.get(field_name):
            append_value_mismatch(errors, field_label)
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-json", required=True, help="Regenerated workflow reachability JSON report")
    parser.add_argument("--committed-json", required=True, help="Committed reachability JSON report")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        generated = read_json(Path(args.generated_json), "regenerated PowerShell function reachability report")
        committed = read_json(Path(args.committed_json), "committed PowerShell function reachability report")
        errors = compare_reports(generated, committed)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
