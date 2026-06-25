#!/usr/bin/env python3
"""Build the #268 PowerShell review-assist report.

This layer consumes the committed #261 and #263 through #267 PowerShell report
family, preserves the optional #262 analyzer gap honestly, and renders a
machine-readable review contract plus a Markdown summary from the same report
object. It intentionally does not mutate workflow YAML, upload SARIF, promote
Pester, or claim required-check readiness.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "dcoir_powershell_review_assist_report_v1"
ISSUE_NUMBER = 268
PARENT_ISSUE_NUMBER = 260
DEFAULT_SCHEMA_PATH = Path("project_sources/collector/powershell_review_assist_report.schema.json")
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_review_assist_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_review_assist_report.md")
DEFAULT_SURFACE_INVENTORY = Path("project_sources/collector/powershell_surface_inventory.json")
DEFAULT_RULE_RISK_REPORT = Path("project_sources/collector/powershell_rule_risk_fixture_report.json")
DEFAULT_RULE_RISK_MATRIX = Path("project_sources/collector/powershell_rule_risk_matrix.json")
DEFAULT_CUSTOM_REPORT = Path("project_sources/collector/powershell_custom_check_report.json")
DEFAULT_ASSEMBLY_PARITY_REPORT = Path("project_sources/collector/powershell_assembly_parity_report.json")
DEFAULT_GOVERNANCE_REPORT = Path("project_sources/collector/powershell_finding_governance_report.json")
DEFAULT_ENGINE_BOUNDARY_REPORT = Path("project_sources/collector/powershell_engine_pester_boundary_report.json")
DEFAULT_ANALYZER_REPORT = Path("project_sources/collector/powershell_analyzer_report.json")
DEFAULT_FUNCTION_REACHABILITY_REPORT = Path("project_sources/collector/powershell_function_reachability_report.json")

SCHEMA_VERSIONS = {
    "surface_inventory": "dcoir_powershell_surface_inventory_v1",
    "rule_risk_report": "dcoir_powershell_rule_risk_fixture_report_v1",
    "rule_risk_matrix": "dcoir_powershell_rule_risk_matrix_v1",
    "custom_report": "dcoir_powershell_custom_check_report_v1",
    "assembly_parity_report": "dcoir_powershell_assembly_parity_report_v1",
    "governance_report": "dcoir_powershell_finding_governance_report_v1",
    "engine_boundary_report": "dcoir_powershell_engine_pester_boundary_report_v1",
    "analyzer_report": "dcoir_powershell_analyzer_report_v1",
    "function_reachability_report": "dcoir_powershell_function_reachability_report_v1",
}

SOURCE_ISSUES = {
    "surface_inventory": 261,
    "analyzer_report": 262,
    "rule_risk_report": 263,
    "rule_risk_matrix": 263,
    "custom_report": 264,
    "assembly_parity_report": 265,
    "governance_report": 266,
    "engine_boundary_report": 267,
    "function_reachability_report": 306,
}

SOURCE_LABELS = {
    "surface_inventory": "#261 surface inventory",
    "rule_risk_report": "#263 rule-risk fixture report",
    "rule_risk_matrix": "#263 rule-risk matrix companion",
    "custom_report": "#264 DCOIR custom-check report",
    "assembly_parity_report": "#265 assembly parity report",
    "governance_report": "#266 finding governance report",
    "engine_boundary_report": "#267 engine/Pester boundary report",
    "analyzer_report": "#262 optional PowerShell analyzer report",
    "function_reachability_report": "#306 function reachability report",
}

REQUIRED_SOURCE_KEYS = (
    "surface_inventory",
    "rule_risk_report",
    "rule_risk_matrix",
    "custom_report",
    "assembly_parity_report",
    "governance_report",
    "engine_boundary_report",
    "function_reachability_report",
)

SOURCE_PATH_PREFIXES = (
    ".github/",
    "chatgpt_staging/",
    "compiled_runtime/",
    "knowledge/",
    "operator_tools/",
    "project_sources/",
    "scripts/",
    "tools/",
)

NON_CLAIMS = [
    "No workflow YAML was changed by #268.",
    "No SARIF file is generated or uploaded by #268.",
    "No GitHub code-scanning alert or required-check behavior is enabled by #268.",
    "No workflow artifact retention behavior is configured by #268.",
    "No Pester result is promoted to blocking static-validation evidence by #268.",
    "No changed-file execution, path-filter behavior, PR-diff coverage, or changed-file gating is claimed by #268.",
    "No live PSScriptAnalyzer evidence is claimed when the #262 analyzer report is absent.",
    "No Windows PowerShell 5.1 runtime validation is claimed by #268.",
    "No #269, #270, PR/workflow readiness, or parent #260 closeability claim is made by #268.",
    "No function deletion readiness or dead-code removal claim is made by #306 reachability reporting.",
]

FUTURE_HANDOFF_CONSUMERS = [
    {
        "issue": 269,
        "consumer": "SARIF decision gate",
        "may_consume": [
            "normalized findings",
            "evidence channel states",
            "missing analyzer evidence",
            "explicit non-claims",
        ],
        "not_claimed_by_268": "SARIF generation, SARIF upload, code scanning, or required-check readiness.",
    },
    {
        "issue": 270,
        "consumer": "workflow/local integration planning",
        "may_consume": [
            "local report artifact names",
            "source report contract",
            "warning carry-forward behavior",
            "handoff metadata",
        ],
        "not_claimed_by_268": "workflow mutation, artifact retention, or changed-file gating.",
    },
]


class ReviewAssistError(RuntimeError):
    """Raised for fail-closed review-assist validation errors."""


@dataclass(frozen=True)
class SourceContract:
    key: str
    path: Path
    required: bool
    expected_schema: str
    require_validation_success: bool
    finding_count_keys: tuple[str, ...] = ("finding_count", "observed_finding_count")


SOURCE_CONTRACTS = {
    "surface_inventory": SourceContract(
        "surface_inventory",
        DEFAULT_SURFACE_INVENTORY,
        True,
        SCHEMA_VERSIONS["surface_inventory"],
        True,
        (),
    ),
    "rule_risk_report": SourceContract(
        "rule_risk_report",
        DEFAULT_RULE_RISK_REPORT,
        True,
        SCHEMA_VERSIONS["rule_risk_report"],
        True,
    ),
    "rule_risk_matrix": SourceContract(
        "rule_risk_matrix",
        DEFAULT_RULE_RISK_MATRIX,
        True,
        SCHEMA_VERSIONS["rule_risk_matrix"],
        False,
        (),
    ),
    "custom_report": SourceContract(
        "custom_report",
        DEFAULT_CUSTOM_REPORT,
        True,
        SCHEMA_VERSIONS["custom_report"],
        True,
    ),
    "assembly_parity_report": SourceContract(
        "assembly_parity_report",
        DEFAULT_ASSEMBLY_PARITY_REPORT,
        True,
        SCHEMA_VERSIONS["assembly_parity_report"],
        True,
        (),
    ),
    "governance_report": SourceContract(
        "governance_report",
        DEFAULT_GOVERNANCE_REPORT,
        True,
        SCHEMA_VERSIONS["governance_report"],
        True,
    ),
    "engine_boundary_report": SourceContract(
        "engine_boundary_report",
        DEFAULT_ENGINE_BOUNDARY_REPORT,
        True,
        SCHEMA_VERSIONS["engine_boundary_report"],
        True,
        (),
    ),
    "analyzer_report": SourceContract(
        "analyzer_report",
        DEFAULT_ANALYZER_REPORT,
        False,
        SCHEMA_VERSIONS["analyzer_report"],
        True,
    ),
    "function_reachability_report": SourceContract(
        "function_reachability_report",
        DEFAULT_FUNCTION_REACHABILITY_REPORT,
        True,
        SCHEMA_VERSIONS["function_reachability_report"],
        True,
        ("function_count",),
    ),
}


def scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def slash_path(value: str) -> str:
    return value.strip().replace("\\", "/")


def is_windows_drive_path(value: str) -> bool:
    return len(value) >= 2 and value[0].isalpha() and value[1] == ":"


def path_has_traversal(value: str) -> bool:
    return any(part == ".." for part in value.split("/"))


def resolve_repo_path(value: str | Path, repo_root: Path, label: str) -> tuple[Path, str]:
    normalized = slash_path(value.as_posix() if isinstance(value, Path) else scalar(value))
    if not normalized:
        raise ReviewAssistError(f"{label} path must not be blank")
    if normalized.startswith("/") or is_windows_drive_path(normalized) or path_has_traversal(normalized):
        raise ReviewAssistError(f"{label} path must be repo-relative without traversal: {normalized}")
    parts = tuple(part for part in normalized.split("/") if part)
    candidate = repo_root.joinpath(*parts)
    try:
        candidate.resolve().relative_to(repo_root.resolve())
    except (OSError, RuntimeError, ValueError) as exc:
        raise ReviewAssistError(f"{label} path must resolve inside the repository root: {normalized}") from exc
    return candidate, normalized


def resolve_existing_input_path(value: str | Path, repo_root: Path, label: str) -> tuple[Path, str]:
    path, repo_path = resolve_repo_path(value, repo_root, label)
    if not path.exists():
        raise ReviewAssistError(f"{label} is missing: {repo_path}")
    return path, repo_path


def repo_path_if_safe(value: str, repo_root: Path, label: str) -> str:
    _path, repo_path = resolve_repo_path(value, repo_root, label)
    return repo_path


def resolve_report_output_path(repo_root: Path, output_path: Path, label: str, suffix: str) -> tuple[Path, str]:
    path, repo_path = resolve_repo_path(output_path, repo_root, label)
    if not repo_path.startswith("project_sources/collector/"):
        raise ReviewAssistError(f"{label} must stay under project_sources/collector/: {repo_path}")
    if path.suffix != suffix:
        raise ReviewAssistError(f"{label} must use {suffix} suffix: {repo_path}")
    return path, repo_path


def looks_like_repo_path(value: str) -> bool:
    normalized = slash_path(value)
    return normalized.startswith(SOURCE_PATH_PREFIXES)


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReviewAssistError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewAssistError(f"{label} is invalid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise ReviewAssistError(f"{label} could not be read: {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_source_path_aliases(repo_root: Path, source_paths: dict[str, Path]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, str] = {}
    for key, path in source_paths.items():
        try:
            absolute, repo_path = resolve_repo_path(path, repo_root, SOURCE_LABELS[key])
            resolved = absolute.resolve().as_posix()
        except ReviewAssistError as exc:
            errors.append(str(exc))
            continue
        prior = seen.get(resolved)
        if prior:
            errors.append(
                f"duplicate or aliased source report path: {SOURCE_LABELS[prior]} and {SOURCE_LABELS[key]} both use {repo_path}"
            )
        else:
            seen[resolved] = key
    return errors


def validation_state(report: dict[str, Any], repo_path: str) -> tuple[bool, list[str], list[str]]:
    validation = report.get("validation")
    if not isinstance(validation, dict):
        return False, [f"{repo_path} validation must be an object"], []
    errors = validation.get("errors", [])
    warnings = validation.get("warnings", [])
    if not isinstance(errors, list):
        return False, [f"{repo_path} validation.errors must be a list"], []
    if not isinstance(warnings, list):
        return False, [f"{repo_path} validation.warnings must be a list"], []
    success = validation.get("success")
    if success is not True:
        reason = "validation.success is false" if success is False else "validation.success must be boolean true"
        return False, [f"{repo_path} does not report successful validation: {reason}"], [scalar(item) for item in warnings]
    return True, [], [scalar(item) for item in warnings]


def require_object(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    errors.append(f"{label} must be an object")
    return {}


def require_list(value: Any, label: str, errors: list[str]) -> list[Any]:
    if isinstance(value, list):
        return value
    errors.append(f"{label} must be a list")
    return []


def require_field(doc: dict[str, Any], key: str, label: str, errors: list[str]) -> Any:
    if key not in doc:
        errors.append(f"{label} missing {key}")
        return None
    return doc[key]


def summary_finding_count(report: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return None
    for key in keys:
        value = summary.get(key)
        if isinstance(value, int):
            return value
    findings = report.get("findings")
    if isinstance(findings, list):
        return len(findings)
    return None


def source_entry(
    contract: SourceContract,
    repo_path: str,
    present: bool,
    schema_version: str | None,
    validation_status: str,
    finding_count: int | None,
    warnings: list[str],
    errors: list[str],
    absent_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "source_key": contract.key,
        "source_issue": SOURCE_ISSUES[contract.key],
        "label": SOURCE_LABELS[contract.key],
        "path": repo_path,
        "expected_schema_version": contract.expected_schema,
        "schema_version": schema_version,
        "required": contract.required,
        "present": present,
        "validation_status": validation_status,
        "finding_count": finding_count,
        "warnings": warnings,
        "errors": errors,
        "absent_reason": absent_reason,
    }


def load_source(
    repo_root: Path,
    contract: SourceContract,
    relative_path: Path,
    errors: list[str],
    carried_forward_warnings: list[dict[str, Any]],
    missing_artifacts: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    label = SOURCE_LABELS[contract.key]
    try:
        absolute, repo_path = resolve_repo_path(relative_path, repo_root, label)
    except ReviewAssistError as exc:
        errors.append(str(exc))
        return None, source_entry(contract, relative_path.as_posix(), False, None, "path_error", None, [], [str(exc)])
    if not absolute.exists():
        reason = (
            "optional analyzer evidence is absent; #268 does not claim live PSScriptAnalyzer evidence"
            if not contract.required
            else "required source report is missing"
        )
        entry = source_entry(
            contract,
            repo_path,
            False,
            None,
            "optional_missing" if not contract.required else "missing",
            0,
            [],
            [],
            reason,
        )
        missing_artifacts.append(
            {
                "source_issue": SOURCE_ISSUES[contract.key],
                "path": repo_path,
                "required": contract.required,
                "reason": reason,
            }
        )
        if contract.required:
            errors.append(f"{label} is missing: {repo_path}")
        else:
            carried_forward_warnings.append(
                {
                    "source_issue": SOURCE_ISSUES[contract.key],
                    "source_report": repo_path,
                    "warning": reason,
                }
            )
        return None, entry
    try:
        doc = read_json(absolute, label)
    except ReviewAssistError as exc:
        errors.append(str(exc))
        return None, source_entry(contract, repo_path, True, None, "read_error", None, [], [str(exc)])
    if not isinstance(doc, dict):
        message = f"{repo_path} must be a JSON object"
        errors.append(message)
        return None, source_entry(contract, repo_path, True, None, "malformed", None, [], [message])
    schema = scalar(doc.get("schema_version")).strip()
    local_errors: list[str] = []
    local_warnings: list[str] = []
    if schema != contract.expected_schema:
        local_errors.append(f"{repo_path} schema mismatch: expected {contract.expected_schema}, got {schema!r}")
    if contract.require_validation_success:
        success, validation_errors, validation_warnings = validation_state(doc, repo_path)
        local_warnings.extend(validation_warnings)
        if not success:
            local_errors.extend(validation_errors)
    else:
        if "validation" in doc:
            success, validation_errors, validation_warnings = validation_state(doc, repo_path)
            local_warnings.extend(validation_warnings)
            if not success:
                local_errors.extend(validation_errors)
    for warning in local_warnings:
        carried_forward_warnings.append(
            {
                "source_issue": SOURCE_ISSUES[contract.key],
                "source_report": repo_path,
                "warning": warning,
            }
        )
    errors.extend(local_errors)
    if contract.key == "analyzer_report" and doc:
        carried_forward_warnings.append(
            {
                "source_issue": 262,
                "source_report": repo_path,
                "warning": "Optional analyzer report is present and was validated as explicit analyzer evidence.",
            }
        )
    validation_status = "success" if not local_errors else "failed"
    if not contract.require_validation_success and not local_errors:
        validation_status = "schema_only_success"
    return doc, source_entry(
        contract,
        repo_path,
        True,
        schema,
        validation_status,
        summary_finding_count(doc, contract.finding_count_keys),
        local_warnings,
        local_errors,
    )


def validate_inventory(repo_root: Path, report: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    summary = require_object(require_field(report, "summary", repo_path, errors), f"{repo_path} summary", errors)
    surfaces = require_list(require_field(report, "surfaces", repo_path, errors), f"{repo_path} surfaces", errors)
    require_field(report, "mode", repo_path, errors)
    require_field(report, "outputs", repo_path, errors)
    if "total_surfaces" not in summary or not isinstance(summary.get("total_surfaces"), int):
        errors.append(f"{repo_path} summary.total_surfaces must be an integer")
    for index, surface in enumerate(surfaces, start=1):
        if not isinstance(surface, dict):
            errors.append(f"{repo_path} surfaces[{index}] must be an object")
            continue
        path = scalar(surface.get("path")).strip()
        if not path:
            errors.append(f"{repo_path} surfaces[{index}] missing path")
            continue
        try:
            repo_path_if_safe(path, repo_root, f"{repo_path} surfaces[{index}]")
        except ReviewAssistError as exc:
            errors.append(str(exc))
        for field in ("category", "source_type", "status", "inclusion_decision", "decision_reason"):
            if field not in surface:
                errors.append(f"{repo_path} surfaces[{index}] missing {field}")


def validate_rule_risk_report(repo_root: Path, report: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    require_object(require_field(report, "summary", repo_path, errors), f"{repo_path} summary", errors)
    fixtures = require_list(require_field(report, "fixtures", repo_path, errors), f"{repo_path} fixtures", errors)
    findings = require_list(require_field(report, "findings", repo_path, errors), f"{repo_path} findings", errors)
    require_field(report, "environment_gap", repo_path, errors)
    require_field(report, "outputs", repo_path, errors)
    for index, fixture in enumerate(fixtures, start=1):
        if not isinstance(fixture, dict):
            errors.append(f"{repo_path} fixtures[{index}] must be an object")
            continue
        for field in ("id", "kind", "path", "expected_finding_count", "observed_finding_count"):
            if field not in fixture:
                errors.append(f"{repo_path} fixtures[{index}] missing {field}")
        if fixture.get("path"):
            try:
                repo_path_if_safe(scalar(fixture["path"]), repo_root, f"{repo_path} fixtures[{index}]")
            except ReviewAssistError as exc:
                errors.append(str(exc))
    for index, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            errors.append(f"{repo_path} findings[{index}] must be an object")
            continue
        for field in ("path", "line", "column", "rule_name", "severity", "observed_problem", "recommended_fix"):
            if field not in finding:
                errors.append(f"{repo_path} findings[{index}] missing {field}")
        for field in ("path", "target_path"):
            if finding.get(field):
                try:
                    repo_path_if_safe(scalar(finding[field]), repo_root, f"{repo_path} findings[{index}].{field}")
                except ReviewAssistError as exc:
                    errors.append(str(exc))


def validate_rule_risk_matrix(repo_root: Path, matrix: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    checks = require_list(require_field(matrix, "checks", repo_path, errors), f"{repo_path} checks", errors)
    for index, check in enumerate(checks, start=1):
        if not isinstance(check, dict):
            errors.append(f"{repo_path} checks[{index}] must be an object")
            continue
        for field in (
            "id",
            "rule_name",
            "risk_classes",
            "target_surfaces",
            "failure_impact",
            "recommended_fix",
        ):
            if field not in check:
                errors.append(f"{repo_path} checks[{index}] missing {field}")
        if not isinstance(check.get("risk_classes"), list):
            errors.append(f"{repo_path} checks[{index}] risk_classes must be a list")
        if not isinstance(check.get("target_surfaces"), list):
            errors.append(f"{repo_path} checks[{index}] target_surfaces must be a list")
        check_source = scalar(check.get("check_source")).strip()
        if check_source:
            try:
                repo_path_if_safe(check_source, repo_root, f"{repo_path} checks[{index}].check_source")
            except ReviewAssistError as exc:
                errors.append(str(exc))


def validate_custom_report(repo_root: Path, report: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    require_object(require_field(report, "summary", repo_path, errors), f"{repo_path} summary", errors)
    findings = require_list(require_field(report, "findings", repo_path, errors), f"{repo_path} findings", errors)
    fixtures = require_list(require_field(report, "fixtures", repo_path, errors), f"{repo_path} fixtures", errors)
    targets = require_list(require_field(report, "targets", repo_path, errors), f"{repo_path} targets", errors)
    require_field(report, "checks", repo_path, errors)
    require_field(report, "outputs", repo_path, errors)
    for index, target in enumerate(targets, start=1):
        try:
            repo_path_if_safe(scalar(target), repo_root, f"{repo_path} targets[{index}]")
        except ReviewAssistError as exc:
            errors.append(str(exc))
    for index, fixture in enumerate(fixtures, start=1):
        if not isinstance(fixture, dict):
            errors.append(f"{repo_path} fixtures[{index}] must be an object")
            continue
        for field in ("id", "kind", "check_id", "path", "expected_finding_count", "observed_finding_count"):
            if field not in fixture:
                errors.append(f"{repo_path} fixtures[{index}] missing {field}")
        if fixture.get("path"):
            try:
                repo_path_if_safe(scalar(fixture["path"]), repo_root, f"{repo_path} fixtures[{index}]")
            except ReviewAssistError as exc:
                errors.append(str(exc))
    for index, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            errors.append(f"{repo_path} findings[{index}] must be an object")
            continue
        for field in (
            "path",
            "line",
            "column",
            "check_id",
            "rule_name",
            "severity",
            "risk_classes",
            "observed_problem",
            "impact",
            "recommended_fix",
            "target_surfaces",
        ):
            if field not in finding:
                errors.append(f"{repo_path} findings[{index}] missing {field}")
        if finding.get("path"):
            try:
                repo_path_if_safe(scalar(finding["path"]), repo_root, f"{repo_path} findings[{index}].path")
            except ReviewAssistError as exc:
                errors.append(str(exc))


def validate_assembly_parity(repo_root: Path, report: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    require_object(require_field(report, "summary", repo_path, errors), f"{repo_path} summary", errors)
    outputs = require_list(
        require_field(report, "generated_outputs", repo_path, errors),
        f"{repo_path} generated_outputs",
        errors,
    )
    require_field(report, "coverage_statement", repo_path, errors)
    require_field(report, "controlled_bad_cases", repo_path, errors)
    if "baseline_comparison" not in report:
        errors.append(f"{repo_path} missing baseline_comparison")
    require_field(report, "outputs", repo_path, errors)
    for index, output in enumerate(outputs, start=1):
        if not isinstance(output, dict):
            errors.append(f"{repo_path} generated_outputs[{index}] must be an object")
            continue
        for field in ("id", "path", "line_mapping_status", "parse", "parity"):
            if field not in output:
                errors.append(f"{repo_path} generated_outputs[{index}] missing {field}")
        if output.get("path"):
            try:
                repo_path_if_safe(scalar(output["path"]), repo_root, f"{repo_path} generated_outputs[{index}].path")
            except ReviewAssistError as exc:
                errors.append(str(exc))
        line_mapping = output.get("line_mapping", [])
        if isinstance(line_mapping, list):
            for map_index, mapping in enumerate(line_mapping, start=1):
                if isinstance(mapping, dict) and mapping.get("source_path"):
                    try:
                        repo_path_if_safe(
                            scalar(mapping["source_path"]),
                            repo_root,
                            f"{repo_path} generated_outputs[{index}].line_mapping[{map_index}]",
                        )
                    except ReviewAssistError as exc:
                        errors.append(str(exc))


def validate_governance_report(repo_root: Path, report: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    require_object(require_field(report, "summary", repo_path, errors), f"{repo_path} summary", errors)
    require_list(require_field(report, "input_reports", repo_path, errors), f"{repo_path} input_reports", errors)
    classifications = require_list(
        require_field(report, "classifications", repo_path, errors),
        f"{repo_path} classifications",
        errors,
    )
    require_field(report, "baseline_delta", repo_path, errors)
    require_field(report, "controlled_fail_closed_proof", repo_path, errors)
    require_field(report, "assembly_parity_report", repo_path, errors)
    require_field(report, "governance", repo_path, errors)
    for index, item in enumerate(classifications, start=1):
        if not isinstance(item, dict):
            errors.append(f"{repo_path} classifications[{index}] must be an object")
            continue
        for field in ("source_report", "source_schema_version", "path", "rule_name", "severity", "governance"):
            if field not in item:
                errors.append(f"{repo_path} classifications[{index}] missing {field}")
        if item.get("path"):
            try:
                repo_path_if_safe(scalar(item["path"]), repo_root, f"{repo_path} classifications[{index}].path")
            except ReviewAssistError as exc:
                errors.append(str(exc))


def validate_engine_boundary(repo_root: Path, report: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    require_object(require_field(report, "summary", repo_path, errors), f"{repo_path} summary", errors)
    require_list(require_field(report, "dependency_reports", repo_path, errors), f"{repo_path} dependency_reports", errors)
    declared = require_list(
        require_field(report, "declared_output_artifacts", repo_path, errors),
        f"{repo_path} declared_output_artifacts",
        errors,
    )
    require_list(require_field(report, "engine_matrix", repo_path, errors), f"{repo_path} engine_matrix", errors)
    require_field(report, "pester_boundary", repo_path, errors)
    require_field(report, "independent_analyzer_enforcement_proof", repo_path, errors)
    for index, artifact in enumerate(declared, start=1):
        if not isinstance(artifact, dict):
            errors.append(f"{repo_path} declared_output_artifacts[{index}] must be an object")
            continue
        for field in ("id", "path", "artifact_status", "blocking", "evidence_claimed_by_boundary"):
            if field not in artifact:
                errors.append(f"{repo_path} declared_output_artifacts[{index}] missing {field}")
        artifact_path = scalar(artifact.get("path")).strip()
        if artifact.get("repo_path") is True and artifact_path:
            try:
                repo_path_if_safe(artifact_path, repo_root, f"{repo_path} declared_output_artifacts[{index}].path")
            except ReviewAssistError as exc:
                errors.append(str(exc))


def validate_analyzer_report(repo_root: Path, report: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    require_object(require_field(report, "summary", repo_path, errors), f"{repo_path} summary", errors)
    findings = require_list(require_field(report, "findings", repo_path, errors), f"{repo_path} findings", errors)
    require_field(report, "targets", repo_path, errors)
    require_field(report, "skipped_surfaces", repo_path, errors)
    require_field(report, "analyzer", repo_path, errors)
    require_field(report, "powershell", repo_path, errors)
    require_field(report, "settings", repo_path, errors)
    require_field(report, "inventory", repo_path, errors)
    require_field(report, "baseline", repo_path, errors)
    require_field(report, "outputs", repo_path, errors)
    for index, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            errors.append(f"{repo_path} findings[{index}] must be an object")
            continue
        if finding.get("path"):
            try:
                repo_path_if_safe(scalar(finding["path"]), repo_root, f"{repo_path} findings[{index}].path")
            except ReviewAssistError as exc:
                errors.append(str(exc))


def validate_function_reachability_report(repo_root: Path, report: dict[str, Any], repo_path: str, errors: list[str]) -> None:
    summary = require_object(require_field(report, "summary", repo_path, errors), f"{repo_path} summary", errors)
    analysis_scope = require_object(
        require_field(report, "analysis_scope", repo_path, errors),
        f"{repo_path} analysis_scope",
        errors,
    )
    functions = require_list(require_field(report, "functions", repo_path, errors), f"{repo_path} functions", errors)
    dynamic_sites = require_list(
        require_field(report, "dynamic_invocation_sites", repo_path, errors),
        f"{repo_path} dynamic_invocation_sites",
        errors,
    )
    runtime_coverage = require_object(
        require_field(report, "runtime_lane_coverage", repo_path, errors),
        f"{repo_path} runtime_lane_coverage",
        errors,
    )
    non_claims = require_list(require_field(report, "non_claims", repo_path, errors), f"{repo_path} non_claims", errors)
    outputs = require_object(require_field(report, "outputs", repo_path, errors), f"{repo_path} outputs", errors)
    source_files = require_list(
        require_field(analysis_scope, "source_files", f"{repo_path} analysis_scope", errors),
        f"{repo_path} analysis_scope.source_files",
        errors,
    )
    classification_counts = require_object(
        require_field(summary, "classification_counts", f"{repo_path} summary", errors),
        f"{repo_path} summary.classification_counts",
        errors,
    )
    allowed_classifications = {
        "entrypoint",
        "literal_referenced",
        "dynamic_invocation_uncertain",
        "static_unreferenced",
    }
    if summary.get("function_count") != len(functions):
        errors.append(f"{repo_path} summary.function_count must match functions length")
    if sum(value for value in classification_counts.values() if isinstance(value, int)) != len(functions):
        errors.append(f"{repo_path} summary.classification_counts must sum to functions length")
    if summary.get("coverage_state") != "not_collected":
        errors.append(f"{repo_path} summary.coverage_state must remain not_collected")
    if runtime_coverage.get("state") != "not_collected":
        errors.append(f"{repo_path} runtime_lane_coverage.state must remain not_collected")
    non_claim_text = "\n".join(scalar(item) for item in non_claims)
    if "safe to delete" not in non_claim_text:
        errors.append(f"{repo_path} non_claims must explicitly reject function deletion readiness")
    for field in ("json", "markdown"):
        output_path = scalar(outputs.get(field)).strip()
        if output_path:
            try:
                repo_path_if_safe(output_path, repo_root, f"{repo_path} outputs.{field}")
            except ReviewAssistError as exc:
                errors.append(str(exc))
    for index, source in enumerate(source_files, start=1):
        if isinstance(source, dict) and source.get("path"):
            try:
                repo_path_if_safe(scalar(source["path"]), repo_root, f"{repo_path} analysis_scope.source_files[{index}].path")
            except ReviewAssistError as exc:
                errors.append(str(exc))
    for index, item in enumerate(functions, start=1):
        if not isinstance(item, dict):
            errors.append(f"{repo_path} functions[{index}] must be an object")
            continue
        for field in (
            "name",
            "classification",
            "source_path",
            "line",
            "static_reference_status",
            "dynamic_uncertainty_status",
            "reference_count",
            "coverage_status",
            "claim",
        ):
            if field not in item:
                errors.append(f"{repo_path} functions[{index}] missing {field}")
        classification = scalar(item.get("classification"))
        if classification not in allowed_classifications:
            errors.append(f"{repo_path} functions[{index}] unknown classification: {classification}")
        if item.get("coverage_status") != "not_observed_in_suite":
            errors.append(f"{repo_path} functions[{index}] coverage_status must remain not_observed_in_suite")
        if item.get("source_path"):
            try:
                repo_path_if_safe(scalar(item["source_path"]), repo_root, f"{repo_path} functions[{index}].source_path")
            except ReviewAssistError as exc:
                errors.append(str(exc))
        references = item.get("references", [])
        if isinstance(references, list):
            for reference_index, reference in enumerate(references, start=1):
                if isinstance(reference, dict) and reference.get("source_path"):
                    try:
                        repo_path_if_safe(
                            scalar(reference["source_path"]),
                            repo_root,
                            f"{repo_path} functions[{index}].references[{reference_index}].source_path",
                        )
                    except ReviewAssistError as exc:
                        errors.append(str(exc))
    for index, site in enumerate(dynamic_sites, start=1):
        if isinstance(site, dict) and site.get("source_path"):
            try:
                repo_path_if_safe(scalar(site["source_path"]), repo_root, f"{repo_path} dynamic_invocation_sites[{index}].source_path")
            except ReviewAssistError as exc:
                errors.append(str(exc))


def validate_loaded_sources(repo_root: Path, docs: dict[str, dict[str, Any]], source_reports: list[dict[str, Any]], errors: list[str]) -> None:
    repo_paths = {entry["source_key"]: entry["path"] for entry in source_reports}
    validators = {
        "surface_inventory": validate_inventory,
        "rule_risk_report": validate_rule_risk_report,
        "rule_risk_matrix": validate_rule_risk_matrix,
        "custom_report": validate_custom_report,
        "assembly_parity_report": validate_assembly_parity,
        "governance_report": validate_governance_report,
        "engine_boundary_report": validate_engine_boundary,
        "analyzer_report": validate_analyzer_report,
        "function_reachability_report": validate_function_reachability_report,
    }
    for key, validator in validators.items():
        doc = docs.get(key)
        if doc is None:
            continue
        validator(repo_root, doc, repo_paths.get(key, SOURCE_CONTRACTS[key].path.as_posix()), errors)


def matrix_by_rule(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for check in matrix.get("checks", []):
        if isinstance(check, dict):
            rule_name = scalar(check.get("rule_name")).strip()
            check_id = scalar(check.get("id")).strip()
            if rule_name:
                result[rule_name] = check
            if check_id:
                result[check_id] = check
    return result


def governance_index(governance_report: dict[str, Any]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    index: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for item in governance_report.get("classifications", []):
        if not isinstance(item, dict):
            continue
        source_report = slash_path(scalar(item.get("source_report")))
        path = slash_path(scalar(item.get("path")))
        rule_name = scalar(item.get("rule_name")).strip()
        check_id = scalar(item.get("check_id")).strip()
        fingerprint = scalar(item.get("fingerprint")).strip()
        keys = [
            (source_report, path, rule_name, check_id),
            (source_report, path, rule_name, ""),
        ]
        if fingerprint:
            keys.append((source_report, path, rule_name, fingerprint))
        for key in keys:
            if key not in index:
                index[key] = item
    return index


def find_governance(
    index: dict[tuple[str, str, str, str], dict[str, Any]],
    source_report: str,
    path: str,
    rule_name: str,
    check_id: str,
    fingerprint: str,
) -> dict[str, Any] | None:
    keys = [
        (source_report, path, rule_name, check_id),
        (source_report, path, rule_name, ""),
        (source_report, path, rule_name, fingerprint),
    ]
    return next((index[key] for key in keys if key in index), None)


def target_kind(path: str, generated_paths: set[str]) -> str:
    if path in generated_paths:
        return "generated_output"
    if "/fixtures/" in path:
        return "fixture"
    if path.endswith(".ps1.txt"):
        return "source_part"
    if "/source/parts/" in path:
        return "source_part"
    if "/harness/source/parts/" in path:
        return "source_part"
    if path.startswith(".github/"):
        return "workflow_reference"
    return "source_or_tooling"


def normalize_line(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    text = scalar(value).strip()
    if text.isdigit():
        return int(text)
    return None


def governance_states(governance_item: dict[str, Any] | None) -> tuple[str, str, str, dict[str, Any]]:
    if not isinstance(governance_item, dict):
        return "unclassified", "not_baselined", "not_suppressed", {}
    governance = governance_item.get("governance")
    if not isinstance(governance, dict):
        return "unclassified", "not_baselined", "not_suppressed", {}
    decision = scalar(governance.get("decision")).strip() or "unclassified"
    matched_by = scalar(governance.get("matched_by")).strip()
    baseline_state = "baseline_record" if matched_by == "baseline_record" else "not_baselined"
    suppression_state = "suppression" if matched_by == "suppression" else "not_suppressed"
    return decision, baseline_state, suppression_state, governance


def normalized_finding(
    *,
    raw: dict[str, Any],
    source_report: str,
    source_schema: str,
    evidence_kind: str,
    matrix_context: dict[str, Any] | None,
    governance_item: dict[str, Any] | None,
    generated_paths: set[str],
) -> dict[str, Any]:
    path = slash_path(scalar(raw.get("path") or raw.get("target_path")))
    rule_name = scalar(raw.get("rule_name") or raw.get("rule")).strip()
    check_id = scalar(raw.get("check_id") or raw.get("matrix_check_id") or raw.get("id")).strip()
    fingerprint = scalar(raw.get("fingerprint")).strip()
    risk_classes = raw.get("risk_classes")
    if not isinstance(risk_classes, list):
        risk_classes = []
    if not risk_classes and matrix_context:
        risk_classes = matrix_context.get("risk_classes", [])
    target_surfaces = raw.get("target_surfaces")
    if not isinstance(target_surfaces, list):
        target_surfaces = []
    if not target_surfaces and matrix_context:
        target_surfaces = matrix_context.get("target_surfaces", [])
    impact = scalar(raw.get("impact") or raw.get("failure_impact")).strip()
    if not impact and matrix_context:
        impact = scalar(matrix_context.get("failure_impact")).strip()
    recommended = scalar(raw.get("recommended_fix") or raw.get("fix")).strip()
    if not recommended and matrix_context:
        recommended = scalar(matrix_context.get("recommended_fix")).strip()
    decision, baseline_state, suppression_state, governance = governance_states(governance_item)
    return {
        "source_report_path": source_report,
        "source_schema_version": source_schema,
        "evidence_kind": evidence_kind,
        "path": path,
        "line": normalize_line(raw.get("line")),
        "column": normalize_line(raw.get("column")),
        "severity": scalar(raw.get("severity") or "Warning").strip(),
        "rule_name": rule_name,
        "check_id": check_id,
        "risk_classes": list(risk_classes),
        "target_surfaces": list(target_surfaces),
        "fingerprint": fingerprint,
        "observed_behavior": scalar(raw.get("observed_problem") or raw.get("message")).strip(),
        "impact": impact,
        "recommended_fix_direction": recommended,
        "governance_classification": decision,
        "baseline_state": baseline_state,
        "suppression_state": suppression_state,
        "governance": governance,
        "source_generated_target_kind": target_kind(path, generated_paths),
    }


def collect_normalized_findings(docs: dict[str, dict[str, Any]], source_report_paths: dict[str, str]) -> list[dict[str, Any]]:
    matrix = matrix_by_rule(docs.get("rule_risk_matrix", {}))
    governance = governance_index(docs.get("governance_report", {}))
    assembly_outputs = docs.get("assembly_parity_report", {}).get("generated_outputs", [])
    generated_paths = {
        slash_path(scalar(output.get("path")))
        for output in assembly_outputs
        if isinstance(output, dict) and scalar(output.get("path")).strip()
    }
    findings: list[dict[str, Any]] = []
    for raw in docs.get("rule_risk_report", {}).get("findings", []):
        if not isinstance(raw, dict):
            continue
        path = slash_path(scalar(raw.get("path") or raw.get("target_path")))
        rule_name = scalar(raw.get("rule_name")).strip()
        check_id = scalar(raw.get("check_id") or raw.get("matrix_check_id")).strip()
        source_report = source_report_paths["rule_risk_report"]
        governance_item = find_governance(
            governance,
            source_report,
            path,
            rule_name,
            check_id,
            scalar(raw.get("fingerprint")).strip(),
        )
        findings.append(
            normalized_finding(
                raw=raw,
                source_report=source_report,
                source_schema=SCHEMA_VERSIONS["rule_risk_report"],
                evidence_kind="deterministic_fixture_analyzer",
                matrix_context=matrix.get(rule_name) or matrix.get(check_id),
                governance_item=governance_item,
                generated_paths=generated_paths,
            )
        )
    for raw in docs.get("custom_report", {}).get("findings", []):
        if not isinstance(raw, dict):
            continue
        path = slash_path(scalar(raw.get("path")))
        rule_name = scalar(raw.get("rule_name")).strip()
        check_id = scalar(raw.get("check_id") or raw.get("matrix_check_id")).strip()
        source_report = source_report_paths["custom_report"]
        governance_item = find_governance(
            governance,
            source_report,
            path,
            rule_name,
            check_id,
            scalar(raw.get("fingerprint")).strip(),
        )
        findings.append(
            normalized_finding(
                raw=raw,
                source_report=source_report,
                source_schema=SCHEMA_VERSIONS["custom_report"],
                evidence_kind="dcoir_custom_static_check",
                matrix_context=None,
                governance_item=governance_item,
                generated_paths=generated_paths,
            )
        )
    analyzer = docs.get("analyzer_report")
    if isinstance(analyzer, dict):
        for raw in analyzer.get("findings", []):
            if not isinstance(raw, dict):
                continue
            findings.append(
                normalized_finding(
                    raw=raw,
                    source_report=source_report_paths["analyzer_report"],
                    source_schema=SCHEMA_VERSIONS["analyzer_report"],
                    evidence_kind="psscriptanalyzer",
                    matrix_context=None,
                    governance_item=None,
                    generated_paths=generated_paths,
                )
            )
    return findings


def validate_normalized_findings(findings: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, finding in enumerate(findings, start=1):
        prefix = f"normalized finding {index} {finding.get('path')} {finding.get('rule_name') or finding.get('check_id')}"
        if finding.get("evidence_kind") == "deterministic_fixture_analyzer":
            if not finding.get("risk_classes"):
                errors.append(f"{prefix} missing #263 matrix risk_classes")
            if not scalar(finding.get("impact")).strip():
                errors.append(f"{prefix} missing #263 matrix impact")
            if not finding.get("target_surfaces"):
                errors.append(f"{prefix} missing #263 matrix target_surfaces")
            if not scalar(finding.get("recommended_fix_direction")).strip():
                errors.append(f"{prefix} missing #263 matrix recommended_fix_direction")
    return errors


def path_decision(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": scalar(item.get("path")).strip(),
        "category": scalar(item.get("category")).strip(),
        "source_type": scalar(item.get("source_type")).strip(),
        "status": scalar(item.get("status")).strip(),
        "reason": scalar(item.get("decision_reason")).strip(),
    }


def surface_inventory_section(report: dict[str, Any]) -> dict[str, Any]:
    surfaces = [item for item in report.get("surfaces", []) if isinstance(item, dict)]
    by_decision: dict[str, list[dict[str, Any]]] = {"include": [], "exclude": [], "reference": [], "skip": []}
    for surface in surfaces:
        decision = scalar(surface.get("inclusion_decision")).strip() or "unknown"
        by_decision.setdefault(decision, []).append(path_decision(surface))
    skipped_paths = report.get("skipped_paths")
    if isinstance(skipped_paths, list):
        by_decision["skip"].extend(
            {
                "path": slash_path(scalar(path)),
                "category": "",
                "source_type": "",
                "status": "skipped",
                "reason": "reported by source inventory skipped_paths",
            }
            for path in skipped_paths
        )
    return {
        "mode": report.get("mode"),
        "summary": report.get("summary", {}),
        "outputs": report.get("outputs", {}),
        "path_decision_counts": {key: len(value) for key, value in sorted(by_decision.items())},
        "included_paths": by_decision.get("include", []),
        "excluded_paths": by_decision.get("exclude", []),
        "reference_paths": by_decision.get("reference", []),
        "skipped_paths": by_decision.get("skip", []),
    }


def fixture_outcomes(report: dict[str, Any]) -> dict[str, Any]:
    fixtures = [item for item in report.get("fixtures", []) if isinstance(item, dict)]
    counter = Counter(scalar(item.get("kind")).strip() or "unknown" for item in fixtures)
    return {
        "counts": dict(sorted(counter.items())),
        "fixtures": [
            {
                "id": item.get("id"),
                "kind": item.get("kind"),
                "path": item.get("path"),
                "expected_finding_count": item.get("expected_finding_count"),
                "observed_finding_count": item.get("observed_finding_count"),
                "observed_rules": item.get("observed_rules", []),
            }
            for item in fixtures
        ],
    }


def collect_unclaimed_artifacts(engine_report: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for item in engine_report.get("declared_output_artifacts", []):
        if not isinstance(item, dict):
            continue
        claimed = item.get("evidence_claimed_by_boundary")
        status = scalar(item.get("artifact_status")).strip()
        exists = item.get("exists")
        if claimed is False or status in {"not_committed_in_267_boundary", "external_or_future"} or exists in {False, None}:
            artifacts.append(
                {
                    "source_issue": 267,
                    "id": item.get("id"),
                    "path": item.get("path"),
                    "artifact_status": status,
                    "blocking": item.get("blocking"),
                    "evidence_claimed_by_boundary": claimed,
                    "reason": "Declared by #267 boundary but not committed, not claimed, external, or future evidence.",
                }
            )
    return artifacts


def evidence_channels(
    docs: dict[str, dict[str, Any]],
    source_entries: dict[str, dict[str, Any]],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    kind_counts = Counter(item["evidence_kind"] for item in findings)
    boundary = docs.get("engine_boundary_report", {})
    governance = docs.get("governance_report", {})
    assembly = docs.get("assembly_parity_report", {})
    rule_risk = docs.get("rule_risk_report", {})
    custom = docs.get("custom_report", {})
    function_reachability = docs.get("function_reachability_report", {})
    function_summary = function_reachability.get("summary", {}) if isinstance(function_reachability.get("summary"), dict) else {}
    analyzer_entry = source_entries["analyzer_report"]
    analyzer_status = analyzer_entry["validation_status"]
    if not analyzer_entry["present"]:
        analyzer_state = "optional_missing"
    elif analyzer_status == "success":
        analyzer_state = "present_validated"
    else:
        analyzer_state = "present_failed"
    return {
        "analyzer": {
            "source_issue": 262,
            "state": analyzer_state,
            "path": analyzer_entry["path"],
            "finding_count": kind_counts.get("psscriptanalyzer", 0),
            "claim": "live PSScriptAnalyzer evidence is not claimed unless this report is present and valid",
        },
        "deterministic_fixture_analyzer": {
            "source_issue": 263,
            "state": source_entries["rule_risk_report"]["validation_status"],
            "finding_count": kind_counts.get("deterministic_fixture_analyzer", 0),
            "environment_gap": rule_risk.get("environment_gap"),
            "fixture_outcomes": fixture_outcomes(rule_risk),
        },
        "custom_checks": {
            "source_issue": 264,
            "state": source_entries["custom_report"]["validation_status"],
            "finding_count": kind_counts.get("dcoir_custom_static_check", 0),
            "fixture_outcomes": fixture_outcomes(custom),
        },
        "assembly_parity": {
            "source_issue": 265,
            "state": source_entries["assembly_parity_report"]["validation_status"],
            "summary": assembly.get("summary", {}),
            "generated_outputs": [
                {
                    "id": item.get("id"),
                    "path": item.get("path"),
                    "line_mapping_status": item.get("line_mapping_status"),
                    "parse": item.get("parse"),
                    "parity": item.get("parity"),
                }
                for item in assembly.get("generated_outputs", [])
                if isinstance(item, dict)
            ],
            "baseline_comparison": assembly.get("baseline_comparison"),
        },
        "finding_governance": {
            "source_issue": 266,
            "state": source_entries["governance_report"]["validation_status"],
            "summary": governance.get("summary", {}),
            "baseline_delta": governance.get("baseline_delta", {}),
            "governance": governance.get("governance", {}),
        },
        "engine_boundary": {
            "source_issue": 267,
            "state": source_entries["engine_boundary_report"]["validation_status"],
            "summary": boundary.get("summary", {}),
            "declared_output_artifacts": boundary.get("declared_output_artifacts", []),
            "independent_analyzer_enforcement_proof": boundary.get("independent_analyzer_enforcement_proof", {}),
        },
        "function_reachability": {
            "source_issue": 306,
            "state": source_entries["function_reachability_report"]["validation_status"],
            "path": source_entries["function_reachability_report"]["path"],
            "parser_mode": function_summary.get("parser_mode"),
            "function_count": function_summary.get("function_count", 0),
            "classification_counts": function_summary.get("classification_counts", {}),
            "dynamic_invocation_site_count": function_summary.get("dynamic_invocation_site_count", 0),
            "coverage_state": function_summary.get("coverage_state"),
            "claim": "report-only reachability evidence; no function deletion readiness or runtime absence is claimed",
        },
        "pester_boundary": {
            "source_issue": 267,
            "state": "supporting_non_blocking",
            "pester_boundary": boundary.get("pester_boundary", {}),
            "claim": "Pester may support later runtime or wrapper evidence but is not blocking static-validation evidence in #268.",
        },
    }


def artifact_contract() -> dict[str, Any]:
    return {
        "issue": ISSUE_NUMBER,
        "local_artifacts": {
            "schema": DEFAULT_SCHEMA_PATH.as_posix(),
            "json": DEFAULT_JSON_OUTPUT.as_posix(),
            "markdown": DEFAULT_MARKDOWN_OUTPUT.as_posix(),
        },
        "future_handoff_consumers": deepcopy(FUTURE_HANDOFF_CONSUMERS),
        "retention_scope": "local committed report artifacts only; workflow artifact retention remains a later explicit gate",
        "workflow_behavior": "none",
    }


def markdown_table_row(values: list[Any]) -> str:
    return "| " + " | ".join(scalar(value).replace("\n", " ").replace("|", "\\|") for value in values) + " |"


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    validation = report["validation"]
    lines = [
        "# PowerShell Review-Assist Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Issue: #{report['issue']}",
        f"- Parent issue: #{report['parent_issue']}",
        f"- Validation: `{'pass' if validation['success'] else 'fail'}`",
        f"- Normalized findings: `{summary['normalized_finding_count']}`",
        f"- Optional analyzer state: `{report['evidence_channels']['analyzer']['state']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key in (
        "required_source_report_count",
        "required_source_reports_present",
        "optional_source_reports_missing",
        "normalized_finding_count",
        "carried_forward_warning_count",
        "missing_artifact_count",
        "unclaimed_artifact_count",
        "non_claim_count",
    ):
        lines.append(markdown_table_row([key, summary.get(key, 0)]))
    lines.extend(["", "## Source Reports", "", "| Report | Required | Status | Schema | Findings |", "| --- | --- | --- | --- | ---: |"])
    for entry in report["source_reports"]:
        lines.append(
            markdown_table_row(
                [
                    f"#{entry['source_issue']} {entry['path']}",
                    entry["required"],
                    entry["validation_status"],
                    entry.get("schema_version") or "not present",
                    entry.get("finding_count") if entry.get("finding_count") is not None else "",
                ]
            )
        )
    lines.extend(["", "## Evidence Channels", "", "| Channel | State | Key Evidence |", "| --- | --- | --- |"])
    channels = report["evidence_channels"]
    lines.append(markdown_table_row(["analyzer", channels["analyzer"]["state"], channels["analyzer"]["claim"]]))
    lines.append(
        markdown_table_row(
            [
                "deterministic_fixture_analyzer",
                channels["deterministic_fixture_analyzer"]["state"],
                f"{channels['deterministic_fixture_analyzer']['finding_count']} findings; {channels['deterministic_fixture_analyzer'].get('environment_gap')}",
            ]
        )
    )
    lines.append(markdown_table_row(["custom_checks", channels["custom_checks"]["state"], f"{channels['custom_checks']['finding_count']} findings"]))
    lines.append(
        markdown_table_row(
            [
                "assembly_parity",
                channels["assembly_parity"]["state"],
                f"{channels['assembly_parity']['summary'].get('generated_output_count', 0)} generated outputs; {channels['assembly_parity']['summary'].get('parity_status')}",
            ]
        )
    )
    delta = channels["finding_governance"].get("baseline_delta", {})
    lines.append(
        markdown_table_row(
            [
                "finding_governance",
                channels["finding_governance"]["state"],
                f"{delta.get('baseline_record_count', 0)} baseline records; {delta.get('suppression_count', 0)} suppressions",
            ]
        )
    )
    lines.append(
        markdown_table_row(
            [
                "engine_boundary",
                channels["engine_boundary"]["state"],
                f"{channels['engine_boundary']['summary'].get('unclaimed_blocking_output_artifact_count', 0)} unclaimed blocking artifacts",
            ]
        )
    )
    function_counts = channels["function_reachability"].get("classification_counts", {})
    lines.append(
        markdown_table_row(
            [
                "function_reachability",
                channels["function_reachability"]["state"],
                (
                    f"{channels['function_reachability'].get('function_count', 0)} functions; "
                    f"{function_counts.get('literal_referenced', 0)} literal referenced; "
                    f"{function_counts.get('dynamic_invocation_uncertain', 0)} dynamic uncertain; "
                    f"coverage {channels['function_reachability'].get('coverage_state')}"
                ),
            ]
        )
    )
    lines.append(markdown_table_row(["pester_boundary", channels["pester_boundary"]["state"], channels["pester_boundary"]["claim"]]))
    lines.extend(["", "## Findings", "", "| Evidence | Severity | Rule/check | Path | Line | Governance |", "| --- | --- | --- | --- | ---: | --- |"])
    for finding in report["findings"]:
        lines.append(
            markdown_table_row(
                [
                    finding["evidence_kind"],
                    finding["severity"],
                    finding["rule_name"] or finding["check_id"],
                    finding["path"],
                    finding["line"] if finding["line"] is not None else "",
                    finding["governance_classification"],
                ]
            )
        )
    lines.extend(["", "## Inventory Decisions", ""])
    inventory = report["surface_inventory"]
    lines.append(f"- Full-scope inventory mode: `{inventory.get('mode')}`")
    lines.append(f"- Total PowerShell surfaces: `{inventory.get('summary', {}).get('total_surfaces')}`")
    for title, key in (
        ("Excluded Paths", "excluded_paths"),
        ("Reference Paths", "reference_paths"),
        ("Skipped Paths", "skipped_paths"),
    ):
        lines.extend(["", f"### {title}", "", "| Path | Reason |", "| --- | --- |"])
        for item in inventory.get(key, []):
            lines.append(markdown_table_row([item.get("path"), item.get("reason")]))
        if not inventory.get(key):
            lines.append(markdown_table_row(["none", "none reported"]))
    lines.extend(["", "## Baseline And Suppression", ""])
    governance_delta = report["evidence_channels"]["finding_governance"].get("baseline_delta", {})
    lines.append(f"- Baseline records: `{governance_delta.get('baseline_record_count', 0)}`")
    lines.append(f"- Matched baseline records: `{governance_delta.get('matched_baseline_record_count', 0)}`")
    lines.append(f"- Suppressions: `{governance_delta.get('suppression_count', 0)}`")
    lines.append(f"- Matched suppressions: `{governance_delta.get('matched_suppression_count', 0)}`")
    lines.extend(["", "## Source And Generated Parity", ""])
    for item in report["evidence_channels"]["assembly_parity"].get("generated_outputs", []):
        parse = item.get("parse") if isinstance(item.get("parse"), dict) else {}
        parity = item.get("parity") if isinstance(item.get("parity"), dict) else {}
        lines.append(
            f"- `{item.get('path')}`: mapping `{item.get('line_mapping_status')}`, parse `{parse.get('success')}`, parity `{parity.get('status')}`"
        )
    lines.extend(["", "## Warnings, Missing Artifacts, And Non-Claims", ""])
    if report["carried_forward_warnings"]:
        lines.extend(["### Carried Forward Warnings", ""])
        for warning in report["carried_forward_warnings"]:
            lines.append(f"- #{warning['source_issue']} `{warning.get('source_report')}`: {warning['warning']}")
    if report["missing_artifacts"]:
        lines.extend(["", "### Missing Artifacts", ""])
        for item in report["missing_artifacts"]:
            lines.append(f"- #{item['source_issue']} `{item.get('path')}`: {item['reason']}")
    if report["unclaimed_artifacts"]:
        lines.extend(["", "### Unclaimed Artifacts", ""])
        for item in report["unclaimed_artifacts"]:
            lines.append(f"- #{item['source_issue']} `{item.get('path')}`: {item['reason']}")
    lines.extend(["", "### Non-Claims", ""])
    lines.extend(f"- {claim}" for claim in report["non_claims"])
    lines.extend(["", "## Artifact Contract", ""])
    lines.append(f"- JSON: `{report['artifact_contract']['local_artifacts']['json']}`")
    lines.append(f"- Markdown: `{report['artifact_contract']['local_artifacts']['markdown']}`")
    lines.append(f"- Retention scope: {report['artifact_contract']['retention_scope']}")
    lines.extend(["", "## Validation", ""])
    if validation["errors"]:
        lines.extend(["### Errors", ""])
        lines.extend(f"- {error}" for error in validation["errors"])
    if validation["warnings"]:
        lines.extend(["### Warnings", ""])
        lines.extend(f"- {warning}" for warning in validation["warnings"])
    return "\n".join(lines) + "\n"


def validate_markdown_parity(report: dict[str, Any], markdown: str) -> list[str]:
    errors: list[str] = []
    required_fragments = [
        str(report["summary"]["normalized_finding_count"]),
        report["evidence_channels"]["analyzer"]["state"],
        report["artifact_contract"]["local_artifacts"]["json"],
        "No workflow YAML was changed by #268.",
    ]
    required_fragments.extend(entry["path"] for entry in report["source_reports"])
    for finding in report["findings"]:
        required_fragments.append(finding["path"])
        required_fragments.append(finding["governance_classification"])
    for item in report["surface_inventory"].get("excluded_paths", []):
        required_fragments.append(item["path"])
    for item in report["surface_inventory"].get("reference_paths", []):
        required_fragments.append(item["path"])
    for warning in report["carried_forward_warnings"]:
        required_fragments.append(warning["warning"])
    for item in report["missing_artifacts"] + report["unclaimed_artifacts"]:
        required_fragments.append(scalar(item.get("path")))
    for item in report["evidence_channels"]["assembly_parity"].get("generated_outputs", []):
        required_fragments.append(scalar(item.get("path")))
    for fragment in required_fragments:
        text = scalar(fragment)
        if text and text not in markdown:
            errors.append(f"Markdown parity missing fragment: {text}")
    return errors


def schema_type_matches(value: Any, schema_type: Any) -> bool:
    allowed = schema_type if isinstance(schema_type, list) else [schema_type]
    for item in allowed:
        if item == "object" and isinstance(value, dict):
            return True
        if item == "array" and isinstance(value, list):
            return True
        if item == "string" and isinstance(value, str):
            return True
        if item == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if item == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if item == "boolean" and isinstance(value, bool):
            return True
        if item == "null" and value is None:
            return True
    return False


def validate_against_schema_contract(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if path == "$" and isinstance(value, dict):
        summary = value.get("summary")
        validation = value.get("validation")
        if isinstance(summary, dict) and isinstance(validation, dict):
            summary_success = summary.get("validation_success")
            validation_success = validation.get("success")
            if isinstance(summary_success, bool) and isinstance(validation_success, bool) and summary_success != validation_success:
                errors.append("$.summary.validation_success must match $.validation.success")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path} must be one of {schema['enum']!r}")
    if "type" in schema and not schema_type_matches(value, schema["type"]):
        errors.append(f"{path} type mismatch: expected {schema['type']!r}")
        return errors
    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{path}.{key} is required")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, subschema in properties.items():
                if key in value and isinstance(subschema, dict):
                    errors.extend(validate_against_schema_contract(value[key], subschema, f"{path}.{key}"))
    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path} must contain at least {min_items} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_against_schema_contract(item, item_schema, f"{path}[{index}]"))
    return errors


def count_required_present(source_reports: list[dict[str, Any]]) -> int:
    return len([entry for entry in source_reports if entry["required"] and entry["present"]])


def summarize(source_reports: list[dict[str, Any]], findings: list[dict[str, Any]], warnings: list[dict[str, Any]], missing: list[dict[str, Any]], unclaimed: list[dict[str, Any]]) -> dict[str, Any]:
    severity_counts = Counter(finding["severity"] for finding in findings)
    evidence_counts = Counter(finding["evidence_kind"] for finding in findings)
    governance_counts = Counter(finding["governance_classification"] for finding in findings)
    return {
        "required_source_report_count": len([entry for entry in source_reports if entry["required"]]),
        "required_source_reports_present": count_required_present(source_reports),
        "optional_source_reports_missing": len([entry for entry in source_reports if not entry["required"] and not entry["present"]]),
        "source_report_count": len(source_reports),
        "normalized_finding_count": len(findings),
        "finding_count_by_evidence_kind": dict(sorted(evidence_counts.items())),
        "finding_count_by_severity": dict(sorted(severity_counts.items())),
        "finding_count_by_governance_classification": dict(sorted(governance_counts.items())),
        "carried_forward_warning_count": len(warnings),
        "missing_artifact_count": len(missing),
        "unclaimed_artifact_count": len(unclaimed),
        "non_claim_count": len(NON_CLAIMS),
        "validation_success": True,
    }


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str]]:
    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    carried_forward_warnings: list[dict[str, Any]] = []
    missing_artifacts: list[dict[str, Any]] = []
    source_paths = {
        "surface_inventory": Path(args.surface_inventory),
        "rule_risk_report": Path(args.rule_risk_report),
        "rule_risk_matrix": Path(args.rule_risk_matrix),
        "custom_report": Path(args.custom_report),
        "assembly_parity_report": Path(args.assembly_parity_report),
        "governance_report": Path(args.governance_report),
        "engine_boundary_report": Path(args.engine_boundary_report),
        "function_reachability_report": Path(args.function_reachability_report),
        "analyzer_report": Path(args.analyzer_report),
    }
    errors.extend(validate_source_path_aliases(repo_root, source_paths))
    docs: dict[str, dict[str, Any]] = {}
    source_reports: list[dict[str, Any]] = []
    for key in (*REQUIRED_SOURCE_KEYS, "analyzer_report"):
        doc, entry = load_source(
            repo_root,
            SOURCE_CONTRACTS[key],
            source_paths[key],
            errors,
            carried_forward_warnings,
            missing_artifacts,
        )
        if doc is not None:
            docs[key] = doc
        source_reports.append(entry)
    validate_loaded_sources(repo_root, docs, source_reports, errors)
    source_report_paths = {entry["source_key"]: entry["path"] for entry in source_reports}
    findings = collect_normalized_findings(docs, source_report_paths) if not errors else []
    errors.extend(validate_normalized_findings(findings))
    engine_report = docs.get("engine_boundary_report", {})
    unclaimed_artifacts = collect_unclaimed_artifacts(engine_report)
    for item in unclaimed_artifacts:
        carried_forward_warnings.append(
            {
                "source_issue": item["source_issue"],
                "source_report": source_report_paths.get("engine_boundary_report"),
                "warning": f"{item.get('path')}: {item.get('artifact_status')} is not claimed by #267/#268",
            }
        )
    rule_risk = docs.get("rule_risk_report", {})
    if scalar(rule_risk.get("environment_gap")).strip():
        carried_forward_warnings.append(
            {
                "source_issue": 263,
                "source_report": source_report_paths.get("rule_risk_report"),
                "warning": scalar(rule_risk.get("environment_gap")).strip(),
            }
        )
    source_entry_by_key = {entry["source_key"]: entry for entry in source_reports}
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "parent_issue": PARENT_ISSUE_NUMBER,
        "depends_on": [261, 263, 264, 265, 266, 267, 306],
        "generated_from": {
            "tool": "project_sources/collector/tools/run_powershell_review_assist_report.py",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "source_reports": [entry["path"] for entry in source_reports],
            "schema_contract": DEFAULT_SCHEMA_PATH.as_posix(),
        },
        "source_reports": source_reports,
        "summary": {},
        "changed_file_context": {
            "changed_file_count": None,
            "changed_file_surface_count": None,
            "unavailable_reason": "No validated changed-file inventory or base/head changed-file source was supplied to #268.",
            "claim": "Full-scope inventory counts are present; changed-file execution or gating is not claimed.",
        },
        "surface_inventory": surface_inventory_section(docs.get("surface_inventory", {})),
        "findings": findings,
        "evidence_channels": evidence_channels(docs, source_entry_by_key, findings),
        "carried_forward_warnings": carried_forward_warnings,
        "missing_artifacts": missing_artifacts,
        "unclaimed_artifacts": unclaimed_artifacts,
        "non_claims": list(NON_CLAIMS),
        "artifact_contract": artifact_contract(),
        "validation": {
            "success": False,
            "errors": errors,
            "warnings": warnings,
        },
    }
    report["summary"] = summarize(source_reports, findings, carried_forward_warnings, missing_artifacts, unclaimed_artifacts)
    if errors:
        report["summary"]["validation_success"] = False
        report["validation"]["success"] = False
        return report, errors, warnings
    report["validation"]["success"] = True
    report["summary"]["validation_success"] = True
    markdown = render_markdown(report)
    parity_errors = validate_markdown_parity(report, markdown)
    try:
        schema_path, _schema_repo_path = resolve_repo_path(Path(args.schema), repo_root, "PowerShell review-assist schema")
    except ReviewAssistError as exc:
        parity_errors.append(str(exc))
        schema_path = None
    if schema_path is not None and schema_path.exists():
        try:
            schema = read_json(schema_path, "PowerShell review-assist schema")
            if isinstance(schema, dict):
                schema_errors = validate_against_schema_contract(report, schema)
                parity_errors.extend(schema_errors)
            else:
                parity_errors.append("PowerShell review-assist schema must be a JSON object")
        except ReviewAssistError as exc:
            parity_errors.append(str(exc))
    elif schema_path is not None:
        parity_errors.append(f"PowerShell review-assist schema is missing: {args.schema}")
    report["validation"]["errors"].extend(parity_errors)
    report["validation"]["success"] = not report["validation"]["errors"]
    report["summary"]["validation_success"] = report["validation"]["success"]
    return report, report["validation"]["errors"], warnings


def mark_report_write_failure(report: dict[str, Any], message: str) -> None:
    report.setdefault("validation", {})["success"] = False
    report.setdefault("summary", {})["validation_success"] = False
    errors = report["validation"].setdefault("errors", [])
    if isinstance(errors, list):
        errors.append(message)
    else:
        report["validation"]["errors"] = [message]


def write_outputs(repo_root: Path, report: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_path, json_repo_path = resolve_report_output_path(
        repo_root,
        json_output,
        "PowerShell review-assist JSON report output",
        ".json",
    )
    markdown_path, markdown_repo_path = resolve_report_output_path(
        repo_root,
        markdown_output,
        "PowerShell review-assist Markdown report output",
        ".md",
    )
    try:
        if json_path.resolve() == markdown_path.resolve():
            raise ReviewAssistError("PowerShell review-assist JSON and Markdown report output paths must be different")
    except OSError as exc:
        raise ReviewAssistError("PowerShell review-assist output paths must resolve inside the repository root") from exc
    markdown = render_markdown(report)
    try:
        write_json(json_path, report)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        message = f"PowerShell review-assist report write failure: {exc}"
        mark_report_write_failure(report, message)
        try:
            write_json(json_path, report)
        except OSError as rewrite_exc:
            mark_report_write_failure(report, f"failed to persist failed JSON status: {rewrite_exc}")
            raise ReviewAssistError(f"{message}; failed to persist failed JSON status: {rewrite_exc}") from rewrite_exc
        raise ReviewAssistError(f"{message}; failed report persisted to {json_repo_path}") from exc
    if json_repo_path == markdown_repo_path:
        raise ReviewAssistError("PowerShell review-assist JSON and Markdown report output paths must be different")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA_PATH.as_posix(), help="JSON Schema contract path")
    parser.add_argument("--surface-inventory", default=DEFAULT_SURFACE_INVENTORY.as_posix(), help="#261 surface inventory JSON")
    parser.add_argument("--rule-risk-report", default=DEFAULT_RULE_RISK_REPORT.as_posix(), help="#263 rule-risk fixture report JSON")
    parser.add_argument("--rule-risk-matrix", default=DEFAULT_RULE_RISK_MATRIX.as_posix(), help="#263 rule-risk matrix JSON")
    parser.add_argument("--custom-report", default=DEFAULT_CUSTOM_REPORT.as_posix(), help="#264 custom-check report JSON")
    parser.add_argument("--assembly-parity-report", default=DEFAULT_ASSEMBLY_PARITY_REPORT.as_posix(), help="#265 assembly parity report JSON")
    parser.add_argument("--governance-report", default=DEFAULT_GOVERNANCE_REPORT.as_posix(), help="#266 finding governance report JSON")
    parser.add_argument("--engine-boundary-report", default=DEFAULT_ENGINE_BOUNDARY_REPORT.as_posix(), help="#267 engine/Pester boundary report JSON")
    parser.add_argument(
        "--function-reachability-report",
        default=DEFAULT_FUNCTION_REACHABILITY_REPORT.as_posix(),
        help="#306 function reachability report JSON",
    )
    parser.add_argument("--analyzer-report", default=DEFAULT_ANALYZER_REPORT.as_posix(), help="Optional #262 analyzer report JSON")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="Output JSON report path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Output Markdown report path")
    parser.add_argument("--no-write", action="store_true", help="Build the report without writing output files")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    report, _errors, _warnings = build_report(args)
    repo_root = Path(args.repo_root).resolve()
    if not args.no_write:
        try:
            write_outputs(repo_root, report, Path(args.json_output), Path(args.markdown_output))
        except ReviewAssistError as exc:
            mark_report_write_failure(report, str(exc))
    if report["validation"]["success"]:
        return 0
    for error in report["validation"]["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
