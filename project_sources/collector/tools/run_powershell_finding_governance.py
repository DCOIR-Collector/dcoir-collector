#!/usr/bin/env python3
"""Validate PowerShell finding baseline, remediation, and suppression governance.

This #266 layer consumes the analyzer/custom-check finding reports produced by
earlier child issues and proves that every current finding is classified before a
future workflow check can become blocking. It intentionally does not edit
workflow YAML, upload SARIF, or change required checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "dcoir_powershell_finding_governance_report_v1"
GOVERNANCE_SCHEMA_VERSION = "dcoir_powershell_finding_governance_v1"
ISSUE_NUMBER = 266
DEFAULT_GOVERNANCE = Path("project_sources/collector/powershell_finding_governance.json")
DEFAULT_CUSTOM_REPORT = Path("project_sources/collector/powershell_custom_check_report.json")
DEFAULT_RULE_RISK_REPORT = Path("project_sources/collector/powershell_rule_risk_fixture_report.json")
DEFAULT_ANALYZER_REPORT = Path("project_sources/collector/powershell_analyzer_report.json")
DEFAULT_ASSEMBLY_PARITY_REPORT = Path("project_sources/collector/powershell_assembly_parity_report.json")
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_finding_governance_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_finding_governance_report.md")
ASSEMBLY_PARITY_SCHEMA_VERSION = "dcoir_powershell_assembly_parity_report_v1"

REPORT_SCHEMAS = {
    DEFAULT_CUSTOM_REPORT.as_posix(): "dcoir_powershell_custom_check_report_v1",
    DEFAULT_RULE_RISK_REPORT.as_posix(): "dcoir_powershell_rule_risk_fixture_report_v1",
    DEFAULT_ANALYZER_REPORT.as_posix(): "dcoir_powershell_analyzer_report_v1",
}

ALLOWED_DECISIONS = {
    "remediate-now",
    "baseline-temporary",
    "advisory",
    "false positive",
    "accepted risk",
}
SEVERITY_ORDER = {
    "information": 0,
    "info": 0,
    "warning": 1,
    "warn": 1,
    "error": 2,
    "critical": 3,
}
REVIEW_FIELDS = ("rationale", "owner", "reviewer", "review_date")
LINE_OR_LOCATOR_FIELDS = ("line", "stable_locator")
EXPIRY_OR_REVISIT_FIELDS = ("expires_on", "revisit_condition")


@dataclass(frozen=True)
class Finding:
    source_report: str
    source_schema_version: str
    path: str
    line: int | None
    column: int | None
    rule_name: str
    check_id: str
    severity: str
    fingerprint: str
    observed_problem: str
    recommended_fix: str
    raw: dict[str, Any]

    def as_report_item(self) -> dict[str, Any]:
        return {
            "source_report": self.source_report,
            "source_schema_version": self.source_schema_version,
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "rule_name": self.rule_name,
            "check_id": self.check_id,
            "severity": self.severity,
            "fingerprint": self.fingerprint,
            "observed_problem": self.observed_problem,
            "recommended_fix": self.recommended_fix,
        }


class GovernanceError(Exception):
    """Raised for fail-closed governance validation errors."""


def scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_repo_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def slash_path(value: str) -> str:
    return value.strip().replace("\\", "/")


def is_windows_drive_path(value: str) -> bool:
    return len(value) >= 2 and value[0].isalpha() and value[1] == ":"


def resolve_repo_input_path(value: str, repo_root: Path, label: str) -> tuple[Path | None, str, str | None]:
    normalized = slash_path(value)
    parts = tuple(part for part in normalized.split("/") if part)
    if not normalized or normalized.startswith("/") or is_windows_drive_path(normalized) or ".." in parts:
        return None, normalized, f"{label} path must be a repo-relative path without traversal"
    candidate = repo_root.joinpath(*parts)
    try:
        candidate.resolve().relative_to(repo_root.resolve())
    except (OSError, ValueError):
        return None, normalized, f"{label} path must resolve inside the repository root"
    return candidate, normalized, None


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GovernanceError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GovernanceError(f"{label} is invalid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise GovernanceError(f"{label} could not be read: {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mark_report_write_failure(report: dict[str, Any], message: str) -> None:
    validation = report.setdefault("validation", {})
    validation["success"] = False
    errors = validation.setdefault("errors", [])
    if isinstance(errors, list):
        errors.append(message)
    else:
        validation["errors"] = [message]


def write_outputs(repo_root: Path, report: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_path = repo_root / json_output
    markdown_path = repo_root / markdown_output
    try:
        write_json(json_path, report)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown(report), encoding="utf-8")
    except OSError as exc:
        message = f"report write failure: {exc}"
        mark_report_write_failure(report, message)
        try:
            write_json(json_path, report)
        except OSError as rewrite_exc:
            rewrite_message = f"report write failure: failed to persist failed JSON status: {rewrite_exc}"
            mark_report_write_failure(report, rewrite_message)
            raise GovernanceError(f"{message}; {rewrite_message}") from rewrite_exc
        raise GovernanceError(message) from exc


def normalize_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def severity_rank(severity: str) -> int:
    return SEVERITY_ORDER.get(severity.casefold(), 99)


def is_blanket_selector(value: str) -> bool:
    stripped = value.strip().casefold()
    return (
        not stripped
        or stripped in {".", "./", "*", "**", "**/*", "all", "repo", "repository", "<repo>"}
        or "*" in stripped
    )


def has_any_text(item: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(scalar(item.get(key)).strip() for key in keys)


def load_doc(repo_root: Path, relative_path: Path, label: str) -> tuple[dict[str, Any], str]:
    absolute_path, repo_path, path_error = resolve_repo_input_path(relative_path.as_posix(), repo_root, label)
    if path_error:
        raise GovernanceError(f"{label} {path_error}: {relative_path.as_posix()}")
    if absolute_path is None:
        raise GovernanceError(f"{label} path could not be resolved: {relative_path.as_posix()}")
    doc = read_json(absolute_path, label)
    if not isinstance(doc, dict):
        raise GovernanceError(f"{label} must be a JSON object: {repo_path}")
    return doc, repo_path


def load_optional_doc(
    repo_root: Path,
    relative_path: Path,
    label: str,
    warnings: list[str],
) -> tuple[dict[str, Any] | None, str]:
    absolute_path, repo_path, path_error = resolve_repo_input_path(relative_path.as_posix(), repo_root, label)
    if path_error:
        raise GovernanceError(f"{label} {path_error}: {relative_path.as_posix()}")
    if absolute_path is None:
        raise GovernanceError(f"{label} path could not be resolved: {relative_path.as_posix()}")
    if not absolute_path.exists():
        warnings.append(f"optional {label} not present: {repo_path}")
        return None, repo_path
    doc = read_json(absolute_path, label)
    if not isinstance(doc, dict):
        raise GovernanceError(f"{label} must be a JSON object: {repo_path}")
    return doc, repo_path


def report_validation_success_state(report: dict[str, Any]) -> tuple[bool, str]:
    validation = report.get("validation")
    if not isinstance(validation, dict):
        return False, "validation must be an object with success=true"
    if "success" not in validation:
        return False, "validation.success is missing"
    success = validation.get("success")
    if success is True:
        return True, "validation.success is true"
    if success is False:
        return False, "validation.success is false"
    return False, "validation.success must be boolean true"


def validate_assembly_parity_report(repo_path: str, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    schema = scalar(report.get("schema_version")).strip()
    if schema != ASSEMBLY_PARITY_SCHEMA_VERSION:
        errors.append(f"{repo_path} schema mismatch: expected {ASSEMBLY_PARITY_SCHEMA_VERSION}, got {schema!r}")
    success, success_reason = report_validation_success_state(report)
    if not success:
        errors.append(f"{repo_path} does not report successful validation: {success_reason}")
    generated_outputs = report.get("generated_outputs", [])
    if generated_outputs is not None and not isinstance(generated_outputs, list):
        errors.append(f"{repo_path} generated_outputs must be a list when present")
    return errors


def stable_fingerprint(source_report: str, raw: dict[str, Any]) -> str:
    basis = {
        "source_report": source_report,
        "path": scalar(raw.get("path") or raw.get("target_path")),
        "rule_name": scalar(raw.get("rule_name")),
        "check_id": scalar(raw.get("check_id") or raw.get("matrix_check_id")),
        "line": raw.get("line"),
        "severity": scalar(raw.get("severity")),
        "observed_problem": scalar(raw.get("observed_problem") or raw.get("message")),
    }
    return sha256_text(json.dumps(basis, sort_keys=True, separators=(",", ":")))


def normalize_finding(raw: dict[str, Any], source_report: str, source_schema: str) -> Finding:
    if not isinstance(raw, dict):
        raise GovernanceError(f"{source_report} finding must be an object")
    path = scalar(raw.get("path") or raw.get("target_path")).strip()
    rule_name = scalar(raw.get("rule_name") or raw.get("rule")).strip()
    check_id = scalar(raw.get("check_id") or raw.get("matrix_check_id")).strip()
    severity = scalar(raw.get("severity") or "Warning").strip()
    if not path:
        raise GovernanceError(f"{source_report} finding missing path")
    if not rule_name and not check_id:
        raise GovernanceError(f"{source_report} finding missing rule_name/check_id for {path}")
    if not severity:
        raise GovernanceError(f"{source_report} finding missing severity for {path}")
    line_value = raw.get("line")
    column_value = raw.get("column")
    line = int(line_value) if isinstance(line_value, int) or str(line_value).isdigit() else None
    column = int(column_value) if isinstance(column_value, int) or str(column_value).isdigit() else None
    return Finding(
        source_report=source_report,
        source_schema_version=source_schema,
        path=path,
        line=line,
        column=column,
        rule_name=rule_name,
        check_id=check_id,
        severity=severity,
        fingerprint=scalar(raw.get("fingerprint")).strip() or stable_fingerprint(source_report, raw),
        observed_problem=scalar(raw.get("observed_problem") or raw.get("message")).strip(),
        recommended_fix=scalar(raw.get("recommended_fix") or raw.get("fix")).strip(),
        raw=raw,
    )


def collect_findings(
    repo_root: Path,
    required_reports: list[Path],
    optional_reports: list[Path],
    errors: list[str],
    warnings: list[str],
) -> tuple[list[Finding], list[dict[str, Any]]]:
    findings: list[Finding] = []
    input_reports: list[dict[str, Any]] = []

    def process_report(report_path: Path, required: bool, missing_is_warning: bool) -> None:
        label = "PowerShell finding report"
        try:
            if missing_is_warning:
                doc, repo_path = load_optional_doc(repo_root, report_path, label, warnings)
            else:
                doc, repo_path = load_doc(repo_root, report_path, label)
        except GovernanceError as exc:
            errors.append(str(exc))
            return
        if doc is None:
            input_reports.append(
                {
                    "path": repo_path,
                    "schema_version": None,
                    "finding_count": 0,
                    "required": required,
                    "present": False,
                    "validation_success": None,
                }
            )
            return
        report_findings = doc.get("findings")
        if not isinstance(report_findings, list):
            qualifier = "optional " if missing_is_warning else ""
            errors.append(f"{qualifier}PowerShell finding report has no findings list: {repo_path}")
            return
        schema = scalar(doc.get("schema_version")).strip()
        success, success_reason = report_validation_success_state(doc)
        input_reports.append(
            {
                "path": repo_path,
                "schema_version": schema,
                "finding_count": len(report_findings),
                "required": required,
                "present": True,
                "validation_success": success,
            }
        )
        expected_schema = REPORT_SCHEMAS.get(repo_path)
        schema_valid = True
        if expected_schema and schema != expected_schema:
            errors.append(f"{repo_path} schema mismatch: expected {expected_schema}, got {schema!r}")
            schema_valid = False
        if not success:
            errors.append(f"{repo_path} does not report successful validation: {success_reason}")
        if not schema_valid or not success:
            return
        for raw in report_findings:
            try:
                findings.append(normalize_finding(raw, repo_path, schema))
            except GovernanceError as exc:
                errors.append(str(exc))

    for report_path in required_reports:
        process_report(report_path, required=True, missing_is_warning=False)
    for report_path in optional_reports:
        process_report(report_path, required=False, missing_is_warning=True)
    return findings, input_reports


def generated_output_paths(assembly_report: dict[str, Any] | None) -> set[str]:
    if not isinstance(assembly_report, dict):
        return set()
    return {
        scalar(output.get("path")).strip()
        for output in assembly_report.get("generated_outputs", [])
        if isinstance(output, dict) and scalar(output.get("path")).strip()
    }


def validate_review_fields(prefix: str, item: dict[str, Any], errors: list[str]) -> None:
    for key in REVIEW_FIELDS:
        if not scalar(item.get(key)).strip():
            errors.append(f"{prefix} missing {key}")
    if not has_any_text(item, EXPIRY_OR_REVISIT_FIELDS):
        errors.append(f"{prefix} missing expiry_or_revisit")


def validate_baseline_record(
    record: dict[str, Any],
    allowed_decisions: set[str],
    today: date,
    errors: list[str],
) -> None:
    record_id = scalar(record.get("id")).strip() or "<missing-id>"
    prefix = f"baseline record {record_id}"
    if not scalar(record.get("id")).strip():
        errors.append("baseline record missing id")
    decision = scalar(record.get("decision")).strip()
    if decision not in allowed_decisions:
        errors.append(f"{prefix} decision {decision!r} is not allowed")
    if not scalar(record.get("path")).strip():
        errors.append(f"{prefix} missing path")
    if not has_any_text(record, ("rule_name", "check_id")):
        errors.append(f"{prefix} missing rule_name_or_check_id")
    if not has_any_text(record, LINE_OR_LOCATOR_FIELDS):
        errors.append(f"{prefix} missing line_or_stable_locator")
    for key in ("severity", "fingerprint"):
        if not scalar(record.get(key)).strip():
            errors.append(f"{prefix} missing {key}")
    validate_review_fields(prefix, record, errors)
    expected = record.get("expected_match_count", 1)
    if not isinstance(expected, int) or expected < 1:
        errors.append(f"{prefix} expected_match_count must be a positive integer")
    expires_on = scalar(record.get("expires_on")).strip()
    if expires_on:
        parsed = normalize_date(expires_on)
        if parsed is None:
            errors.append(f"{prefix} expires_on is not ISO-8601 date")
        elif parsed < today:
            errors.append(f"{prefix} is stale: expires_on {expires_on} is before {today.isoformat()}")


def validate_suppression(
    suppression: dict[str, Any],
    allowed_decisions: set[str],
    generated_paths: set[str],
    today: date,
    errors: list[str],
) -> None:
    suppression_id = scalar(suppression.get("id")).strip() or "<missing-id>"
    prefix = f"suppression {suppression_id}"
    if not scalar(suppression.get("id")).strip():
        errors.append("suppression missing id")
    decision = scalar(suppression.get("decision") or "accepted risk").strip()
    if decision not in allowed_decisions:
        errors.append(f"{prefix} decision {decision!r} is not allowed")
    path = scalar(suppression.get("path")).strip()
    rule_name = scalar(suppression.get("rule_name") or suppression.get("check_id")).strip()
    if is_blanket_selector(path):
        errors.append(f"{prefix} uses a blanket or wildcard path")
    if is_blanket_selector(rule_name):
        errors.append(f"{prefix} uses a blanket or wildcard rule")
    if not scalar(suppression.get("fingerprint")).strip():
        errors.append(f"{prefix} missing fingerprint")
    if scalar(suppression.get("scope")).strip() not in {"line", "fingerprint", "file"}:
        errors.append(f"{prefix} scope must be line, fingerprint, or file")
    validate_review_fields(prefix, suppression, errors)
    expected = suppression.get("expected_match_count", 1)
    if not isinstance(expected, int) or expected < 1:
        errors.append(f"{prefix} expected_match_count must be a positive integer")
    expires_on = scalar(suppression.get("expires_on")).strip()
    if expires_on:
        parsed = normalize_date(expires_on)
        if parsed is None:
            errors.append(f"{prefix} expires_on is not ISO-8601 date")
        elif parsed < today:
            errors.append(f"{prefix} is stale: expires_on {expires_on} is before {today.isoformat()}")
    target_kind = scalar(suppression.get("target_kind")).strip()
    if path in generated_paths or target_kind == "generated_output":
        coverage = scalar(suppression.get("assembly_source_coverage_report")).strip()
        reason = scalar(suppression.get("reviewed_generated_reason")).strip()
        if coverage != "#265" or not reason:
            errors.append(
                f"{prefix} targets generated output without #265 assembly coverage and reviewed generated reason"
            )


def validate_governance_doc(
    governance: dict[str, Any],
    assembly_report: dict[str, Any] | None,
    today: date,
) -> list[str]:
    errors: list[str] = []
    if governance.get("schema_version") != GOVERNANCE_SCHEMA_VERSION:
        errors.append(
            "PowerShell finding governance schema mismatch: "
            f"expected {GOVERNANCE_SCHEMA_VERSION}, got {governance.get('schema_version')!r}"
        )
    policy = governance.get("policy")
    if not isinstance(policy, dict):
        errors.append("PowerShell finding governance policy must be an object")
        policy = {}
    allowed_decisions = set(policy.get("allowed_decisions") or [])
    missing_decisions = sorted(ALLOWED_DECISIONS - allowed_decisions)
    if missing_decisions:
        errors.append(f"PowerShell finding governance policy missing decisions: {', '.join(missing_decisions)}")
    baseline_records = governance.get("baseline_records", [])
    suppressions = governance.get("suppressions", [])
    classification_rules = governance.get("classification_rules", [])
    approved_exceptions = governance.get("approved_delta_exceptions", [])
    if not isinstance(baseline_records, list):
        errors.append("PowerShell finding governance baseline_records must be a list")
        baseline_records = []
    if not isinstance(suppressions, list):
        errors.append("PowerShell finding governance suppressions must be a list")
        suppressions = []
    if not isinstance(classification_rules, list):
        errors.append("PowerShell finding governance classification_rules must be a list")
        classification_rules = []
    if not isinstance(approved_exceptions, list):
        errors.append("PowerShell finding governance approved_delta_exceptions must be a list")
    max_baseline_records = policy.get("max_baseline_records")
    if isinstance(max_baseline_records, int) and len(baseline_records) > max_baseline_records:
        errors.append(
            "PowerShell finding governance stale baseline growth: "
            f"{len(baseline_records)} baseline records exceeds max_baseline_records {max_baseline_records}"
        )
    generated_paths = generated_output_paths(assembly_report)
    seen_baseline_keys: set[tuple[str, str, str]] = set()
    for record in baseline_records:
        if not isinstance(record, dict):
            errors.append("baseline record must be an object")
            continue
        validate_baseline_record(record, allowed_decisions, today, errors)
        key = (
            scalar(record.get("path")).strip(),
            scalar(record.get("rule_name") or record.get("check_id")).strip(),
            scalar(record.get("fingerprint")).strip(),
        )
        if key in seen_baseline_keys:
            errors.append(f"duplicate baseline record for {key[0]} {key[1]} {key[2]}")
        seen_baseline_keys.add(key)
    seen_suppression_keys: set[tuple[str, str, str]] = set()
    for suppression in suppressions:
        if not isinstance(suppression, dict):
            errors.append("suppression must be an object")
            continue
        validate_suppression(suppression, allowed_decisions, generated_paths, today, errors)
        key = (
            scalar(suppression.get("path")).strip(),
            scalar(suppression.get("rule_name") or suppression.get("check_id")).strip(),
            scalar(suppression.get("fingerprint")).strip(),
        )
        if key in seen_suppression_keys:
            errors.append(f"duplicate suppression for {key[0]} {key[1]} {key[2]}")
        seen_suppression_keys.add(key)
    for rule in classification_rules:
        if not isinstance(rule, dict):
            errors.append("classification rule must be an object")
            continue
        rule_id = scalar(rule.get("id")).strip() or "<missing-id>"
        decision = scalar(rule.get("decision")).strip()
        if decision not in allowed_decisions:
            errors.append(f"classification rule {rule_id} decision {decision!r} is not allowed")
        if not scalar(rule.get("id")).strip():
            errors.append("classification rule missing id")
        if not any(isinstance(rule.get(key), list) and rule.get(key) for key in ("path_prefixes", "paths", "rule_names", "check_ids")):
            errors.append(f"classification rule {rule_id} has no bounded selector")
        validate_review_fields(f"classification rule {rule_id}", rule, errors)
    return errors


def finding_matches_baseline(finding: Finding, record: dict[str, Any]) -> bool:
    if scalar(record.get("fingerprint")).strip() != finding.fingerprint:
        return False
    if scalar(record.get("path")).strip() != finding.path:
        return False
    record_rule = scalar(record.get("rule_name")).strip()
    record_check = scalar(record.get("check_id")).strip()
    return (record_rule and record_rule == finding.rule_name) or (record_check and record_check == finding.check_id)


def finding_matches_suppression(finding: Finding, suppression: dict[str, Any]) -> bool:
    if scalar(suppression.get("fingerprint")).strip() != finding.fingerprint:
        return False
    if scalar(suppression.get("path")).strip() != finding.path:
        return False
    suppression_rule = scalar(suppression.get("rule_name")).strip()
    suppression_check = scalar(suppression.get("check_id")).strip()
    return (suppression_rule and suppression_rule == finding.rule_name) or (
        suppression_check and suppression_check == finding.check_id
    )


def finding_matches_rule(finding: Finding, rule: dict[str, Any]) -> bool:
    prefixes = [scalar(prefix).strip() for prefix in rule.get("path_prefixes", []) if scalar(prefix).strip()]
    paths = [scalar(path).strip() for path in rule.get("paths", []) if scalar(path).strip()]
    rule_names = [scalar(name).strip() for name in rule.get("rule_names", []) if scalar(name).strip()]
    check_ids = [scalar(check_id).strip() for check_id in rule.get("check_ids", []) if scalar(check_id).strip()]
    source_schemas = [scalar(schema).strip() for schema in rule.get("source_schema_versions", []) if scalar(schema).strip()]
    severities = [scalar(severity).strip().casefold() for severity in rule.get("severities", []) if scalar(severity).strip()]
    if prefixes and not any(finding.path.startswith(prefix) for prefix in prefixes):
        return False
    if paths and finding.path not in paths:
        return False
    if rule_names and finding.rule_name not in rule_names:
        return False
    if check_ids and finding.check_id not in check_ids:
        return False
    if source_schemas and finding.source_schema_version not in source_schemas:
        return False
    if severities and finding.severity.casefold() not in severities:
        return False
    return bool(prefixes or paths or rule_names or check_ids or source_schemas or severities)


def exception_approves_missing(record: dict[str, Any], exceptions: list[dict[str, Any]]) -> bool:
    record_id = scalar(record.get("id")).strip()
    fingerprint = scalar(record.get("fingerprint")).strip()
    for exception in exceptions:
        if not isinstance(exception, dict):
            continue
        if scalar(exception.get("kind")).strip() != "unexpected_disappearance":
            continue
        if scalar(exception.get("baseline_record_id")).strip() == record_id:
            return True
        if scalar(exception.get("fingerprint")).strip() == fingerprint:
            return True
    return False


def classify_findings(governance: dict[str, Any], findings: list[Finding], today: date) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    errors: list[str] = []
    baseline_records = [record for record in governance.get("baseline_records", []) if isinstance(record, dict)]
    suppressions = [suppression for suppression in governance.get("suppressions", []) if isinstance(suppression, dict)]
    classification_rules = [rule for rule in governance.get("classification_rules", []) if isinstance(rule, dict)]
    approved_exceptions = [item for item in governance.get("approved_delta_exceptions", []) if isinstance(item, dict)]
    classifications: list[dict[str, Any]] = []
    matched_baseline_ids: Counter[str] = Counter()
    matched_suppression_ids: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    for finding in findings:
        item = finding.as_report_item()
        matched_record = next((record for record in baseline_records if finding_matches_baseline(finding, record)), None)
        if matched_record:
            baseline_id = scalar(matched_record.get("id")).strip()
            matched_baseline_ids[baseline_id] += 1
            baseline_severity = scalar(matched_record.get("severity")).strip()
            if severity_rank(finding.severity) > severity_rank(baseline_severity):
                errors.append(
                    "severity increase for baseline "
                    f"{baseline_id}: current {finding.severity} exceeds baseline {baseline_severity}"
                )
            decision = scalar(matched_record.get("decision")).strip()
            item["governance"] = {
                "decision": decision,
                "matched_by": "baseline_record",
                "record_id": baseline_id,
                "rationale": scalar(matched_record.get("rationale")).strip(),
                "owner": scalar(matched_record.get("owner")).strip(),
                "reviewer": scalar(matched_record.get("reviewer")).strip(),
                "review_date": scalar(matched_record.get("review_date")).strip(),
            }
            decision_counts[decision] += 1
            classifications.append(item)
            continue
        matched_suppression = next(
            (suppression for suppression in suppressions if finding_matches_suppression(finding, suppression)),
            None,
        )
        if matched_suppression:
            suppression_id = scalar(matched_suppression.get("id")).strip()
            matched_suppression_ids[suppression_id] += 1
            decision = scalar(matched_suppression.get("decision") or "accepted risk").strip()
            item["governance"] = {
                "decision": decision,
                "matched_by": "suppression",
                "record_id": suppression_id,
                "rationale": scalar(matched_suppression.get("rationale")).strip(),
                "owner": scalar(matched_suppression.get("owner")).strip(),
                "reviewer": scalar(matched_suppression.get("reviewer")).strip(),
                "review_date": scalar(matched_suppression.get("review_date")).strip(),
            }
            decision_counts[decision] += 1
            classifications.append(item)
            continue
        matched_rule = next((rule for rule in classification_rules if finding_matches_rule(finding, rule)), None)
        if matched_rule:
            decision = scalar(matched_rule.get("decision")).strip()
            item["governance"] = {
                "decision": decision,
                "matched_by": "classification_rule",
                "record_id": scalar(matched_rule.get("id")).strip(),
                "rationale": scalar(matched_rule.get("rationale")).strip(),
                "owner": scalar(matched_rule.get("owner")).strip(),
                "reviewer": scalar(matched_rule.get("reviewer")).strip(),
                "review_date": scalar(matched_rule.get("review_date")).strip(),
            }
            decision_counts[decision] += 1
            classifications.append(item)
            continue
        item["governance"] = {
            "decision": "unclassified",
            "matched_by": "none",
            "record_id": None,
        }
        decision_counts["unclassified"] += 1
        errors.append(
            "new unclassified PowerShell finding: "
            f"{finding.path} {finding.rule_name or finding.check_id} {finding.fingerprint}"
        )
        classifications.append(item)
    for record in baseline_records:
        record_id = scalar(record.get("id")).strip()
        expected = record.get("expected_match_count", 1)
        actual = matched_baseline_ids.get(record_id, 0)
        if actual == 0 and exception_approves_missing(record, approved_exceptions):
            continue
        if actual != expected:
            errors.append(
                f"baseline record {record_id} matched {actual} findings, expected {expected}; "
                "unexpected disappearance or count regression"
            )
    for suppression in suppressions:
        suppression_id = scalar(suppression.get("id")).strip()
        expected = suppression.get("expected_match_count", 1)
        actual = matched_suppression_ids.get(suppression_id, 0)
        if actual != expected:
            errors.append(f"suppression {suppression_id} matched {actual} findings, expected {expected}")
    delta = {
        "baseline_record_count": len(baseline_records),
        "matched_baseline_record_count": sum(matched_baseline_ids.values()),
        "suppression_count": len(suppressions),
        "matched_suppression_count": sum(matched_suppression_ids.values()),
        "unclassified_finding_count": decision_counts.get("unclassified", 0),
        "decision_counts": dict(sorted(decision_counts.items())),
        "baseline_match_counts": dict(sorted(matched_baseline_ids.items())),
        "suppression_match_counts": dict(sorted(matched_suppression_ids.items())),
        "as_of": today.isoformat(),
    }
    return classifications, delta, errors


def governance_summary(findings: list[Finding], classifications: list[dict[str, Any]], delta: dict[str, Any]) -> dict[str, Any]:
    severity_counts = Counter(finding.severity for finding in findings)
    source_counts = Counter(finding.source_schema_version or finding.source_report for finding in findings)
    return {
        "finding_count": len(findings),
        "classified_finding_count": len([item for item in classifications if item["governance"]["decision"] != "unclassified"]),
        "unclassified_finding_count": delta["unclassified_finding_count"],
        "baseline_record_count": delta["baseline_record_count"],
        "matched_baseline_record_count": delta["matched_baseline_record_count"],
        "suppression_count": delta["suppression_count"],
        "matched_suppression_count": delta["matched_suppression_count"],
        "decision_counts": delta["decision_counts"],
        "severity_counts": dict(sorted(severity_counts.items())),
        "source_schema_counts": dict(sorted(source_counts.items())),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    validation = report["validation"]
    delta = report["baseline_delta"]
    lines = [
        "# PowerShell Finding Governance Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Issue: #{report['issue']}",
        f"- Validation: `{'pass' if validation['success'] else 'fail'}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Current findings | {summary['finding_count']} |",
        f"| Classified findings | {summary['classified_finding_count']} |",
        f"| Unclassified findings | {summary['unclassified_finding_count']} |",
        f"| Baseline records | {summary['baseline_record_count']} |",
        f"| Matched baseline records | {summary['matched_baseline_record_count']} |",
        f"| Suppressions | {summary['suppression_count']} |",
        f"| Matched suppressions | {summary['matched_suppression_count']} |",
        "",
        "## Decisions",
        "",
        "| Decision | Count |",
        "| --- | ---: |",
    ]
    for decision, count in sorted(summary["decision_counts"].items()):
        lines.append(f"| `{decision}` | {count} |")
    if not summary["decision_counts"]:
        lines.append("| none | 0 |")
    lines.extend(
        [
            "",
            "## Baseline Delta Proof",
            "",
            f"- New unclassified findings: `{delta['unclassified_finding_count']}`",
            f"- Matched baseline records: `{delta['matched_baseline_record_count']}` / `{delta['baseline_record_count']}`",
            f"- Matched suppressions: `{delta['matched_suppression_count']}` / `{delta['suppression_count']}`",
            f"- As of: `{delta['as_of']}`",
            "",
            "## Inputs",
            "",
            "| Report | Required | Schema | Findings |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for item in report["input_reports"]:
        schema = item.get("schema_version") or "not present"
        lines.append(f"| `{item['path']}` | `{item.get('required', False)}` | `{schema}` | {item['finding_count']} |")
    lines.extend(
        [
            "",
            "## Controlled Fail-Closed Proof",
            "",
            "| Control | Expected Result | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for control in report["controlled_fail_closed_proof"]:
        lines.append(f"| `{control['id']}` | {control['expected_result']} | `{control['evidence']}` |")
    if validation["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in validation["errors"])
    if validation["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in validation["warnings"])
    return "\n".join(lines) + "\n"


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str]]:
    repo_root = Path(args.repo_root).resolve()
    today = normalize_date(args.as_of_date) if getattr(args, "as_of_date", "") else date.today()
    if today is None:
        today = date.today()
    errors: list[str] = []
    warnings: list[str] = []
    governance: dict[str, Any] = {}
    assembly_report: dict[str, Any] | None = None
    assembly_report_for_coverage: dict[str, Any] | None = None
    try:
        governance, governance_path = load_doc(repo_root, Path(args.governance), "PowerShell finding governance")
    except GovernanceError as exc:
        errors.append(str(exc))
        governance_path = str(args.governance)
    try:
        assembly_report, assembly_path = load_optional_doc(
            repo_root,
            Path(args.assembly_parity_report),
            "PowerShell assembly parity report",
            warnings,
        )
    except GovernanceError as exc:
        errors.append(str(exc))
        assembly_path = str(args.assembly_parity_report)
    if assembly_report is not None:
        assembly_errors = validate_assembly_parity_report(assembly_path, assembly_report)
        errors.extend(assembly_errors)
        if not assembly_errors:
            assembly_report_for_coverage = assembly_report
    if governance:
        errors.extend(validate_governance_doc(governance, assembly_report_for_coverage, today))
    required_reports = [Path(path) for path in (args.finding_report or [])]
    if not required_reports:
        required_reports = [DEFAULT_CUSTOM_REPORT, DEFAULT_RULE_RISK_REPORT]
    if not getattr(args, "allow_missing_analyzer_report", False) and DEFAULT_ANALYZER_REPORT not in required_reports:
        required_reports.append(DEFAULT_ANALYZER_REPORT)
    optional_reports = [Path(path) for path in (args.optional_finding_report or [])]
    if getattr(args, "allow_missing_analyzer_report", False):
        analyzer_path = DEFAULT_ANALYZER_REPORT.as_posix()
        optional_report_paths = {path.as_posix() for path in optional_reports}
        required_report_paths = {path.as_posix() for path in required_reports}
        if analyzer_path not in optional_report_paths and analyzer_path not in required_report_paths:
            optional_reports.append(DEFAULT_ANALYZER_REPORT)
    required_report_paths = {path.as_posix() for path in required_reports}
    optional_reports = [path for path in optional_reports if path.as_posix() not in required_report_paths]
    findings, input_reports = collect_findings(repo_root, required_reports, optional_reports, errors, warnings)
    classifications, delta, classification_errors = classify_findings(governance, findings, today) if governance else ([], {}, [])
    errors.extend(classification_errors)
    assembly_success: bool | None = None
    if isinstance(assembly_report, dict):
        assembly_success = report_validation_success_state(assembly_report)[0]
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "parent_issue": 260,
        "depends_on": [262, 263, 264, 265],
        "governance": {
            "path": governance_path,
            "schema_version": governance.get("schema_version") if governance else None,
            "policy": governance.get("policy", {}) if governance else {},
            "classification_rule_count": len(governance.get("classification_rules", [])) if governance else 0,
        },
        "assembly_parity_report": {
            "path": assembly_path,
            "present": assembly_report is not None,
            "schema_version": assembly_report.get("schema_version") if isinstance(assembly_report, dict) else None,
            "validation_success": assembly_success,
            "generated_output_paths": sorted(generated_output_paths(assembly_report_for_coverage)),
        },
        "input_reports": input_reports,
        "summary": {},
        "baseline_delta": delta
        or {
            "baseline_record_count": 0,
            "matched_baseline_record_count": 0,
            "suppression_count": 0,
            "matched_suppression_count": 0,
            "unclassified_finding_count": 0,
            "decision_counts": {},
            "baseline_match_counts": {},
            "suppression_match_counts": {},
            "as_of": today.isoformat(),
        },
        "classifications": classifications,
        "controlled_fail_closed_proof": governance.get("control_proofs", []) if governance else [],
        "validation": {
            "success": not errors,
            "errors": errors,
            "warnings": warnings,
        },
    }
    report["summary"] = governance_summary(findings, classifications, report["baseline_delta"])
    return report, errors, warnings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--governance", default=DEFAULT_GOVERNANCE.as_posix(), help="Governance JSON policy")
    parser.add_argument(
        "--finding-report",
        action="append",
        default=[],
        help="Required analyzer/custom finding report JSON. Defaults to #263/#264 reports.",
    )
    parser.add_argument(
        "--optional-finding-report",
        action="append",
        default=[],
        help="Optional finding report JSON. Missing optional reports are warnings.",
    )
    parser.add_argument(
        "--assembly-parity-report",
        default=DEFAULT_ASSEMBLY_PARITY_REPORT.as_posix(),
        help="#265 assembly parity report JSON.",
    )
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="Output JSON report path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Output Markdown report path")
    parser.add_argument("--as-of-date", default="", help="ISO date for stale baseline checks")
    parser.add_argument(
        "--allow-missing-analyzer-report",
        action="store_true",
        help="Explicitly permit a missing #262 analyzer report as optional local evidence.",
    )
    parser.add_argument("--no-write", action="store_true", help="Build the report without writing output files")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    report, _errors, _warnings = build_report(args)
    repo_root = Path(args.repo_root).resolve()
    if not args.no_write:
        try:
            write_outputs(repo_root, report, Path(args.json_output), Path(args.markdown_output))
        except GovernanceError as exc:
            if report["validation"]["success"]:
                mark_report_write_failure(report, str(exc))
    if report["validation"]["success"]:
        return 0
    for error in report["validation"]["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
