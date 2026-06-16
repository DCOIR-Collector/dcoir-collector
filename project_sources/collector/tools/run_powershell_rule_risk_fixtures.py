#!/usr/bin/env python3
"""Validate #263 PowerShell rule-to-risk fixture evidence.

The harness reads the committed rule-to-risk matrix and fixture manifest, then
routes the fixtures through the #262 analyzer wrapper by supplying a deterministic
local analyzer command. That keeps this child issue scoped to matrix and fixture
evidence while preserving the fail-closed wrapper contract future workflow work
will reuse.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_powershell_analyzer as analyzer
from powershell_analyzer_contract import AnalyzerContractError, repo_relative_input_path

SCHEMA_VERSION = "dcoir_powershell_rule_risk_fixture_report_v1"
MATRIX_SCHEMA_VERSION = "dcoir_powershell_rule_risk_matrix_v1"
MANIFEST_SCHEMA_VERSION = "dcoir_powershell_rule_risk_fixture_manifest_v1"
ISSUE_NUMBER = 263
DEFAULT_MATRIX = Path("project_sources/collector/powershell_rule_risk_matrix.json")
DEFAULT_MANIFEST = Path("project_sources/collector/fixtures/powershell_analysis/rule_fixture_manifest.json")
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_rule_risk_fixture_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_rule_risk_fixture_report.md")
DEFAULT_MATRIX_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_rule_risk_matrix.md")
FIXTURE_ROOT = Path("project_sources/collector/fixtures/powershell_analysis")
MINIMUM_RISK_CLASSES = {
    "analyzer_policy_inventory_skip_or_tool_failure_reported_success",
    "stale_or_unchecked_last_exit_code_or_success_status",
    "external_command_nonzero_exit_treated_success",
    "fail_rows_reports_or_fixture_outputs_not_causing_failure",
    "source_part_assembly_drift_or_stale_generated_output",
    "unsafe_or_wildcard_deletion_outside_controlled_roots",
    "unbounded_or_materializing_event_query_patterns",
    "broad_suppression_or_baseline_growth_hiding_risk",
    "swallowed_exception_or_write_only_catch",
}


class RuleRiskFixtureError(Exception):
    """Raised for invalid #263 matrix or fixture contract state."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuleRiskFixtureError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuleRiskFixtureError(f"{label} is invalid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise RuleRiskFixtureError(f"{label} could not be read: {path}: {exc}") from exc


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def safe_relpath(path: Path, repo_root: Path) -> str:
    try:
        return relpath(path, repo_root)
    except (OSError, RuntimeError, ValueError):
        return path.as_posix()


def repo_relative_path_or_error(repo_root: Path, value: str | Path, label: str, errors: list[str]) -> Path | None:
    try:
        return repo_relative_input_path(repo_root, value, label)
    except AnalyzerContractError as exc:
        errors.append(str(exc))
        return None


def scalar(value: Any) -> str:
    return "" if value is None else str(value)


def require_string(mapping: dict[str, Any], key: str, label: str, errors: list[str]) -> str:
    value = scalar(mapping.get(key)).strip()
    if not value:
        errors.append(f"{label} missing {key}")
    return value


def require_string_list(mapping: dict[str, Any], key: str, label: str, errors: list[str]) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{label} must declare non-empty string list {key}")
        return []
    return [item.strip() for item in value]


def safe_fixture_path(value: str, label: str, errors: list[str]) -> str | None:
    invalid = False
    if "\\" in value:
        errors.append(f"{label}: fixture path must use POSIX separators")
        invalid = True
    candidate = Path(value)
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        errors.append(f"{label}: fixture path must be repo-relative and must not traverse parents")
        invalid = True
    normalized = candidate.as_posix()
    if not normalized.startswith(FIXTURE_ROOT.as_posix() + "/"):
        errors.append(f"{label}: fixture path must stay under {FIXTURE_ROOT.as_posix()}")
        invalid = True
    if not normalized.endswith(".ps1"):
        errors.append(f"{label}: fixture path must be a .ps1 file")
        invalid = True
    if invalid:
        return None
    return normalized


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def path_contains_symlink(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return path.is_symlink()
    current = root
    for part in relative_parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def validate_fixture_root(repo_root: Path, errors: list[str]) -> bool:
    fixture_root = repo_root / FIXTURE_ROOT
    if not fixture_root.exists():
        errors.append(f"fixture root is missing: {FIXTURE_ROOT.as_posix()}")
        return False
    if not fixture_root.is_dir():
        errors.append(f"fixture root must be a directory: {FIXTURE_ROOT.as_posix()}")
        return False
    if path_contains_symlink(fixture_root, repo_root):
        errors.append(f"fixture root must not be a symlink: {FIXTURE_ROOT.as_posix()}")
        return False
    if not is_relative_to(fixture_root, repo_root):
        errors.append(f"fixture root resolves outside repository: {FIXTURE_ROOT.as_posix()}")
        return False
    return True


def validate_matrix(matrix: dict[str, Any], enforce_minimum_risks: bool) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if matrix.get("schema_version") != MATRIX_SCHEMA_VERSION:
        errors.append(
            "rule-to-risk matrix schema mismatch: "
            f"expected {MATRIX_SCHEMA_VERSION}, got {matrix.get('schema_version')!r}"
        )
    checks = matrix.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("rule-to-risk matrix must contain checks[]")
        return {}, errors, warnings

    seen_ids: set[str] = set()
    check_map: dict[str, dict[str, Any]] = {}
    covered_risks: set[str] = set()
    advisory_count = 0
    blocking_count = 0
    for index, raw_check in enumerate(checks, start=1):
        label = f"matrix check #{index}"
        if not isinstance(raw_check, dict):
            errors.append(f"{label} is not an object")
            continue
        check_id = require_string(raw_check, "id", label, errors)
        if check_id in seen_ids:
            errors.append(f"{label}: duplicate check id {check_id}")
        seen_ids.add(check_id)
        require_string(raw_check, "rule_name", label, errors)
        require_string(raw_check, "tool", label, errors)
        require_string(raw_check, "check_source", label, errors)
        expected_severity = require_string(raw_check, "expected_severity", label, errors)
        if expected_severity and expected_severity not in {"Information", "Warning", "Error"}:
            errors.append(f"{label}: expected_severity must be Information, Warning, or Error")
        risks = require_string_list(raw_check, "risk_classes", label, errors)
        covered_risks.update(risks)
        require_string_list(raw_check, "target_surfaces", label, errors)
        require_string(raw_check, "failure_impact", label, errors)
        require_string(raw_check, "recommended_fix", label, errors)
        fixtures = raw_check.get("fixtures")
        if not isinstance(fixtures, list) or not all(isinstance(item, str) and item.strip() for item in fixtures):
            errors.append(f"{label}: fixtures must be a list of strings")
            fixtures = []
        if raw_check.get("blocking") is True:
            blocking_count += 1
            if not fixtures:
                errors.append(f"{label}: blocking checks must name at least one fixture")
        elif raw_check.get("blocking") is False:
            advisory_count += 1
            if not scalar(raw_check.get("promotion_criteria")).strip():
                errors.append(f"{label}: advisory checks must state promotion_criteria")
        else:
            errors.append(f"{label}: blocking must be true or false")
        if check_id:
            check_map[check_id] = raw_check

    if blocking_count == 0:
        errors.append("matrix must contain at least one blocking check")
    if advisory_count == 0:
        warnings.append("matrix has no advisory checks; #263 expects advisory/blocking separation")
    if enforce_minimum_risks:
        missing = sorted(MINIMUM_RISK_CLASSES - covered_risks)
        if missing:
            errors.append("matrix is missing minimum #263 risk classes: " + ", ".join(missing))
    return check_map, errors, warnings


def validate_manifest(
    manifest: dict[str, Any],
    repo_root: Path,
    check_map: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append(
            "fixture manifest schema mismatch: "
            f"expected {MANIFEST_SCHEMA_VERSION}, got {manifest.get('schema_version')!r}"
        )
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        errors.append("fixture manifest must contain fixtures[]")
        return {}, errors, warnings

    fixture_root_valid = validate_fixture_root(repo_root, errors)
    fixture_map: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    control_count = 0
    negative_count = 0
    for index, raw_fixture in enumerate(fixtures, start=1):
        label = f"fixture #{index}"
        if not isinstance(raw_fixture, dict):
            errors.append(f"{label} is not an object")
            continue
        fixture_id = require_string(raw_fixture, "id", label, errors)
        if fixture_id in seen_ids:
            errors.append(f"{label}: duplicate fixture id {fixture_id}")
        seen_ids.add(fixture_id)
        kind = require_string(raw_fixture, "kind", label, errors)
        if kind not in {"negative", "control"}:
            errors.append(f"{label}: kind must be negative or control")
        path = safe_fixture_path(require_string(raw_fixture, "path", label, errors), label, errors)
        require_string(raw_fixture, "description", label, errors)
        expected_findings = raw_fixture.get("expected_findings")
        if not isinstance(expected_findings, list):
            errors.append(f"{label}: expected_findings must be a list")
            expected_findings = []
        if kind == "negative":
            negative_count += 1
            if not expected_findings:
                errors.append(f"{label}: negative fixtures must declare expected_findings")
        elif kind == "control":
            control_count += 1
            if expected_findings:
                errors.append(f"{label}: control fixtures must not declare expected findings")
        absolute: Path | None = None
        usable_path = path is not None and fixture_root_valid
        if path is not None:
            absolute = repo_root / path
            if not fixture_root_valid:
                absolute = None
            elif not is_relative_to(absolute, repo_root / FIXTURE_ROOT):
                errors.append(f"{label}: fixture path resolves outside {FIXTURE_ROOT.as_posix()}")
                absolute = None
                usable_path = False
            elif not absolute.exists():
                errors.append(f"{label}: fixture file is missing: {path}")
                usable_path = False
            elif not absolute.is_file():
                errors.append(f"{label}: fixture path must be a file: {path}")
                absolute = None
                usable_path = False
            elif absolute.stat().st_size == 0:
                errors.append(f"{label}: fixture file is empty: {path}")
                usable_path = False

        for expected_index, raw_expected in enumerate(expected_findings, start=1):
            expected_label = f"{label} expected finding #{expected_index}"
            if not isinstance(raw_expected, dict):
                errors.append(f"{expected_label} is not an object")
                continue
            check_id = require_string(raw_expected, "check_id", expected_label, errors)
            if check_id and check_id not in check_map:
                errors.append(f"{expected_label}: unknown check_id {check_id}")
            rule_name = require_string(raw_expected, "rule_name", expected_label, errors)
            severity = require_string(raw_expected, "severity", expected_label, errors)
            risk_class = require_string(raw_expected, "risk_class", expected_label, errors)
            if severity and severity not in {"Information", "Warning", "Error"}:
                errors.append(f"{expected_label}: severity must be Information, Warning, or Error")
            line = raw_expected.get("line")
            if not isinstance(line, int) or line < 1:
                errors.append(f"{expected_label}: line must be a positive integer")
            if check_id in check_map:
                check = check_map[check_id]
                if rule_name and rule_name != check.get("rule_name"):
                    errors.append(f"{expected_label}: rule_name does not match matrix check {check_id}")
                if severity and severity != check.get("expected_severity"):
                    errors.append(f"{expected_label}: severity does not match matrix check {check_id}")
                if risk_class and risk_class not in check.get("risk_classes", []):
                    errors.append(f"{expected_label}: risk_class is not declared on matrix check {check_id}")
        if fixture_id and path is not None and usable_path:
            enriched = dict(raw_fixture)
            enriched["path"] = path
            enriched["sha256"] = sha256_file(absolute) if absolute is not None and absolute.exists() and absolute.is_file() else None
            fixture_map[fixture_id] = enriched

    if control_count == 0:
        errors.append("fixture manifest must contain at least one control fixture")
    if negative_count == 0:
        errors.append("fixture manifest must contain at least one negative fixture")
    matrix_fixture_ids = {
        fixture_id
        for check in check_map.values()
        if check.get("blocking") is True
        for fixture_id in check.get("fixtures", [])
    }
    missing_fixtures = sorted(fixture_id for fixture_id in matrix_fixture_ids if fixture_id not in fixture_map)
    if missing_fixtures:
        errors.append("matrix references missing fixture ids: " + ", ".join(missing_fixtures))
    unreferenced_negatives = sorted(
        fixture_id
        for fixture_id, fixture in fixture_map.items()
        if fixture.get("kind") == "negative" and fixture_id not in matrix_fixture_ids
    )
    if unreferenced_negatives:
        warnings.append("negative fixtures not referenced by a blocking check: " + ", ".join(unreferenced_negatives))
    return fixture_map, errors, warnings


def line_number_for(text: str, pattern: str) -> int | None:
    compiled = re.compile(pattern, re.IGNORECASE)
    for line_number, line in enumerate(text.splitlines(), start=1):
        if compiled.search(line):
            return line_number
    return None


def finding(path: str, line: int, rule_name: str, severity: str, problem: str, fix: str) -> dict[str, Any]:
    return {
        "path": path,
        "line": line,
        "column": 1,
        "symbol": "",
        "rule_name": rule_name,
        "severity": severity,
        "observed_problem": problem,
        "recommended_fix": fix,
    }


def fixture_findings(text: str, path: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    invoke_line = line_number_for(text, r"\bInvoke-Expression\b")
    if invoke_line:
        findings.append(
            finding(
                path,
                invoke_line,
                "PSAvoidUsingInvokeExpression",
                "Warning",
                "Dynamic expression execution hides command intent and can execute untrusted input.",
                "Replace Invoke-Expression with explicit command invocation or structured parsing.",
            )
        )
    secure_line = line_number_for(text, r"\bConvertTo-SecureString\b.*(?<!\w)-AsPlainText\b")
    if secure_line:
        findings.append(
            finding(
                path,
                secure_line,
                "PSAvoidUsingConvertToSecureStringWithPlainText",
                "Warning",
                "Plaintext data is converted to SecureString.",
                "Avoid plaintext secret material and use a protected input path.",
            )
        )
    credential_literal_line = line_number_for(
        text,
        r"\[(?:string|securestring|pscredential)\]\s*\$(?:Password|Credential|Secret)\s*=\s*['\"][^'\"]+['\"]"
        r"|\$(?:Password|Credential|Secret)\s*=\s*['\"][^'\"]+['\"]",
    )
    if credential_literal_line:
        findings.append(
            finding(
                path,
                credential_literal_line,
                "PSAvoidUsingPlainTextForPassword",
                "Warning",
                "Credential-like variable is assigned a literal string.",
                "Use a non-secret placeholder or load secret material from a protected source.",
            )
        )
    write_host_line = line_number_for(text, r"\bWrite-Host\b")
    if write_host_line:
        findings.append(
            finding(
                path,
                write_host_line,
                "PSAvoidUsingWriteHost",
                "Warning",
                "Validation output is written only to the host stream.",
                "Write durable output through Write-Output, structured reports, or repo logging helpers.",
            )
        )
    unused_line = line_number_for(text, r"\$Unused[A-Za-z0-9_]*\s*=")
    if unused_line:
        findings.append(
            finding(
                path,
                unused_line,
                "PSUseDeclaredVarsMoreThanAssignments",
                "Warning",
                "Assigned validation state is never consumed.",
                "Remove the unused state or wire it into the validation/report decision.",
            )
        )
    function_line = line_number_for(text, r"^\s*function\s+(?:Remove|Set|Clear|New)-[A-Za-z0-9_-]+")
    if function_line and "SupportsShouldProcess" not in text:
        findings.append(
            finding(
                path,
                function_line,
                "PSUseShouldProcessForStateChangingFunctions",
                "Warning",
                "State-changing function does not declare SupportsShouldProcess.",
                "Add CmdletBinding(SupportsShouldProcess) and guard mutation with ShouldProcess.",
            )
        )
    analyzer_skip_line = line_number_for(text, r"analyzed\s*=\s*\$false")
    if analyzer_skip_line and re.search(r"validation\s*=\s*['\"]success['\"]", text, re.IGNORECASE):
        findings.append(
            finding(
                path,
                analyzer_skip_line,
                "DCOIR.NoAnalyzerSkipSuccess",
                "Error",
                "Analyzer skip state is represented with a success validation state.",
                "Fail closed when analyzer policy, inventory, target, or command execution is incomplete.",
            )
        )
    external_line = line_number_for(text, r"^\s*&\s*\$?[A-Za-z_][\w.]*|^\s*(?:robocopy\.exe|cmd\.exe|Start-Process)\b")
    if external_line and "$LASTEXITCODE" not in text and "$?" not in text:
        findings.append(
            finding(
                path,
                external_line,
                "DCOIR.CheckExternalCommandExit",
                "Error",
                "External command result is not checked before continuing.",
                "Capture and validate the command exit state immediately.",
            )
        )
    fail_line = line_number_for(text, r"\[pscustomobject\]@\{.*Status\s*=\s*['\"]FAIL['\"]")
    if fail_line and not re.search(r"\bthrow\b|\bexit\s+1\b", text, re.IGNORECASE):
        findings.append(
            finding(
                path,
                fail_line,
                "DCOIR.FailOutputMustFailValidation",
                "Error",
                "A FAIL output row can be emitted without a failing process result.",
                "Tie FAIL rows and reports to a thrown exception, nonzero exit, or failed validation summary.",
            )
        )
    drift_line = line_number_for(text, r"GeneratedOutputHash\s*=\s*['\"][^'\"]*stale|stale-generated")
    if drift_line:
        findings.append(
            finding(
                path,
                drift_line,
                "DCOIR.SourcePartAssemblyDrift",
                "Error",
                "Generated output marker indicates stale source-part assembly.",
                "Regenerate or compare source-part hashes before accepting analyzer evidence.",
            )
        )
    delete_line = line_number_for(text, r"\bRemove-Item\b.*\*.*(?<!\w)-Recurse\b|\bRemove-Item\b.*(?<!\w)-Recurse\b.*\*")
    if delete_line and "Resolve-Path" not in text:
        findings.append(
            finding(
                path,
                delete_line,
                "DCOIR.NoUnsafeWildcardDeletion",
                "Error",
                "Wildcard recursive deletion is not constrained to a resolved controlled root.",
                "Resolve and constrain the cleanup root before deleting, and avoid broad wildcards.",
            )
        )
    event_line = line_number_for(text, r"\bGet-WinEvent\b")
    if event_line:
        event_text = "\n".join(text.splitlines()[event_line - 1 : event_line + 2])
        if not re.search(r"-MaxEvents\b|-FilterHashtable\b|-FilterXPath\b", event_text, re.IGNORECASE):
            findings.append(
                finding(
                    path,
                    event_line,
                    "DCOIR.BoundedEventQueryRequired",
                    "Error",
                    "Event query is not bounded by filter or count cap.",
                    "Use FilterHashtable, explicit windows, MaxEvents, or a bounded Take parameter.",
                )
            )
    baseline_line = line_number_for(text, r"path\s*=\s*['\"]\*['\"]|rule_name\s*=\s*['\"]PS\*['\"]")
    if baseline_line and "fingerprint" not in text.casefold():
        findings.append(
            finding(
                path,
                baseline_line,
                "DCOIR.BaselineSuppressionMustBeFingerprintBound",
                "Error",
                "Baseline suppression is broad and lacks a finding fingerprint.",
                "Bind suppressions to path, rule, fingerprint, expected match count, and reason.",
            )
        )
    catch_match = re.search(r"(?is)\bcatch\b\s*\{(?P<body>.*?)\}", text)
    if catch_match:
        body = catch_match.group("body")
        if not re.search(r"\bthrow\b|\bexit\b", body, re.IGNORECASE):
            prefix = text[: catch_match.start("body")]
            catch_body_start = prefix.count("\n") + 1
            warning_line = line_number_for(body, r"\bWrite-(?:Warning|Host|Output)\b")
            line = catch_body_start + warning_line - 1 if warning_line else text[: catch_match.start()].count("\n") + 1
            findings.append(
                finding(
                    path,
                    line,
                    "DCOIR.NoSwallowedCatch",
                    "Error",
                    "Catch block writes a message but does not fail or rethrow.",
                    "Rethrow, exit nonzero, or return a failed validation state after recording diagnostics.",
                )
            )
    return findings


def run_fixture_analyzer() -> int:
    request = json.loads(sys.stdin.read())
    target = request["target"]
    text = Path(target["analysis_path"]).read_text(encoding="utf-8", errors="ignore")
    target_path = str(target["path"])
    response = {
        "analyzer_name": "DCOIRFixtureAnalyzer",
        "analyzer_version": "1.0.0",
        "powershell_engine": "Core",
        "powershell_version": "7.4.1",
        "target_path": target_path,
        "analyzed": True,
        "findings": fixture_findings(text, target_path),
    }
    sys.stdout.write(json.dumps(response) + "\n")
    return 0


def inventory_surface(repo_root: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    path = fixture["path"]
    absolute = repo_root / path
    text = absolute.read_text(encoding="utf-8", errors="ignore")
    return {
        "path": path,
        "category": "collector_harness_script",
        "source_type": ".ps1",
        "status": "fixture",
        "inclusion_decision": "include",
        "decision_reason": "#263 fixture harness temporary analyzer target.",
        "exists": True,
        "marker_lines": [],
        "embedded_snippets": [],
        "size_bytes": len(absolute.read_bytes()),
        "line_count": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "sha256": analyzer.sha256_text(text),
    }


def write_temp_inventory(repo_root: Path, fixtures: list[dict[str, Any]], temp_root: Path) -> Path:
    inventory = {
        "schema_version": analyzer.INVENTORY_SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "summary": {"total_surfaces": len(fixtures)},
        "validation": {"success": True, "errors": [], "warnings": []},
        "surfaces": [inventory_surface(repo_root, fixture) for fixture in fixtures],
    }
    inventory_path = temp_root / "powershell_rule_risk_fixture_inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    return inventory_path


def wrapper_args(repo_root: Path, inventory_path: Path, fixture_paths: list[str], timeout_seconds: int) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=str(repo_root),
        inventory=safe_relpath(inventory_path, repo_root),
        settings=analyzer.DEFAULT_SETTINGS.as_posix(),
        json_output=(Path("project_sources/collector") / "_fixture_wrapper_report.json").as_posix(),
        markdown_output=(Path("project_sources/collector") / "_fixture_wrapper_report.md").as_posix(),
        analyzer_command=[sys.executable, Path(__file__).resolve().as_posix(), "--fixture-analyzer"],
        target_path=fixture_paths,
        baseline_json=None,
        timeout_seconds=timeout_seconds,
        minimum_powershell_version="5.1",
        fail_on_severity="Warning",
        allow_findings=True,
        expect_finding_rule=None,
        expect_finding_path=None,
        expect_no_findings=False,
        no_write=True,
    )


def expected_match(expected: dict[str, Any], finding_row: dict[str, Any], path: str) -> bool:
    return (
        finding_row.get("path") == path
        and finding_row.get("rule_name") == expected.get("rule_name")
        and finding_row.get("severity") == expected.get("severity")
        and finding_row.get("line") == expected.get("line")
    )


def validate_fixture_results(
    check_map: dict[str, dict[str, Any]],
    fixture_map: dict[str, dict[str, Any]],
    findings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    by_path: dict[str, list[dict[str, Any]]] = {}
    for finding_row in findings:
        by_path.setdefault(str(finding_row.get("path")), []).append(finding_row)

    expected_by_check: dict[str, int] = {}
    observed_by_check: dict[str, int] = {}
    fixture_results: list[dict[str, Any]] = []
    for fixture_id, fixture in sorted(fixture_map.items()):
        fixture_findings_for_path = by_path.get(fixture["path"], [])
        expected_findings = fixture.get("expected_findings", [])
        fixture_errors: list[str] = []
        if fixture.get("kind") == "control" and fixture_findings_for_path:
            fixture_errors.append(
                f"{fixture_id}: control fixture produced unexpected findings: "
                + ", ".join(finding["rule_name"] for finding in fixture_findings_for_path)
            )
        for expected in expected_findings:
            check_id = expected.get("check_id")
            expected_by_check[check_id] = expected_by_check.get(check_id, 0) + 1
            matches = [
                finding_row
                for finding_row in fixture_findings_for_path
                if expected_match(expected, finding_row, fixture["path"])
            ]
            if not matches:
                fixture_errors.append(
                    f"{fixture_id}: expected {expected.get('rule_name')} at "
                    f"{fixture['path']}:{expected.get('line')} was not produced"
                )
            else:
                observed_by_check[check_id] = observed_by_check.get(check_id, 0) + len(matches)
        unexpected = [
            finding_row
            for finding_row in fixture_findings_for_path
            if not any(expected_match(expected, finding_row, fixture["path"]) for expected in expected_findings)
        ]
        if unexpected and fixture.get("kind") == "negative":
            warnings.append(
                f"{fixture_id}: produced additional unmapped findings: "
                + ", ".join(finding["rule_name"] for finding in unexpected)
            )
        errors.extend(fixture_errors)
        fixture_results.append(
            {
                "id": fixture_id,
                "kind": fixture.get("kind"),
                "path": fixture["path"],
                "sha256": fixture.get("sha256"),
                "expected_finding_count": len(expected_findings),
                "observed_finding_count": len(fixture_findings_for_path),
                "observed_rules": sorted({finding["rule_name"] for finding in fixture_findings_for_path}),
                "validation": {
                    "success": not fixture_errors,
                    "errors": fixture_errors,
                },
            }
        )

    negative_fixture_ids = {
        fixture_id for fixture_id, fixture in fixture_map.items() if fixture.get("kind") == "negative"
    }
    for check_id, check in sorted(check_map.items()):
        if check.get("blocking") is not True:
            continue
        fixtures = [fixture_id for fixture_id in check.get("fixtures", []) if fixture_id in fixture_map]
        negative_fixtures = [fixture_id for fixture_id in fixtures if fixture_id in negative_fixture_ids]
        if not negative_fixtures:
            errors.append(f"{check_id}: blocking check has no negative fixture")
        if expected_by_check.get(check_id, 0) == 0:
            errors.append(f"{check_id}: blocking check has no manifest expected finding")
        if observed_by_check.get(check_id, 0) == 0:
            errors.append(f"{check_id}: blocking check has no observed fixture finding")
    return fixture_results, errors, warnings


def render_matrix_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# PowerShell Rule-To-Risk Matrix",
        "",
        f"- Schema: `{matrix.get('schema_version')}`",
        f"- Issue: `#{matrix.get('issue')}`",
        f"- Parent issue: `#{matrix.get('parent_issue')}`",
        "- Scope: rule-to-risk mapping and fixture proof only; no workflow, SARIF, required-check, or PR mutation.",
        "",
        "## Checks",
        "",
        "| Check ID | Rule | Tool | Blocking | Severity | Risk Classes | Fixtures |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for check in matrix.get("checks", []):
        risks = "<br>".join(f"`{risk}`" for risk in check.get("risk_classes", []))
        fixtures = ", ".join(f"`{fixture}`" for fixture in check.get("fixtures", [])) or "(none)"
        lines.append(
            f"| `{check.get('id')}` | `{check.get('rule_name')}` | {check.get('tool')} | "
            f"`{str(check.get('blocking')).lower()}` | `{check.get('expected_severity')}` | {risks} | {fixtures} |"
        )
    lines.extend(["", "## Advisory Promotion", ""])
    advisory = [check for check in matrix.get("checks", []) if check.get("blocking") is False]
    if not advisory:
        lines.append("- No advisory checks declared.")
    for check in advisory:
        lines.append(f"- `{check.get('id')}`: {check.get('promotion_criteria')}")
    lines.append("")
    return "\n".join(lines)


def render_report_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    validation = report["validation"]
    lines = [
        "# PowerShell Rule-Risk Fixture Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Issue: `#{report['issue']}`",
        f"- Matrix: `{report['matrix']['path']}`",
        f"- Manifest: `{report['manifest']['path']}`",
        f"- Analyzer wrapper: `{report['analyzer_wrapper']['path']}`",
        f"- Fixture analyzer: `{report['fixture_analyzer']['name']} {report['fixture_analyzer']['version']}`",
        f"- Validation: `{'pass' if validation['success'] else 'fail'}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Matrix checks | {summary['matrix_check_count']} |",
        f"| Blocking checks | {summary['blocking_check_count']} |",
        f"| Advisory checks | {summary['advisory_check_count']} |",
        f"| Negative fixtures | {summary['negative_fixture_count']} |",
        f"| Control fixtures | {summary['control_fixture_count']} |",
        f"| Expected findings | {summary['expected_finding_count']} |",
        f"| Observed findings | {summary['observed_finding_count']} |",
        "",
        "## Fixtures",
        "",
        "| Fixture | Kind | Expected | Observed | Status | Rules |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for fixture in report["fixtures"]:
        rules = ", ".join(f"`{rule}`" for rule in fixture["observed_rules"]) or "(none)"
        status = "pass" if fixture["validation"]["success"] else "fail"
        lines.append(
            f"| `{fixture['id']}` | `{fixture['kind']}` | {fixture['expected_finding_count']} | "
            f"{fixture['observed_finding_count']} | `{status}` | {rules} |"
        )
    lines.extend(["", "## Validation Findings", ""])
    if validation["errors"]:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in validation["errors"])
    else:
        lines.append("- No validation errors.")
    if validation["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in validation["warnings"])
    if report.get("environment_gap"):
        lines.extend(["", "## Environment Gap", "", f"- {report['environment_gap']}"])
    lines.append("")
    return "\n".join(lines)


def ensure_distinct_output_paths(paths: list[tuple[str, Path]], errors: list[str]) -> None:
    seen: dict[Path, str] = {}
    for label, path in paths:
        prior = seen.get(path)
        if prior is not None:
            errors.append(f"{label} output path must be different from {prior} output path")
        seen[path] = label


def mark_output_failure(report: dict[str, Any], error: str) -> None:
    validation = report.setdefault("validation", {})
    validation["success"] = False
    errors = validation.setdefault("errors", [])
    if error not in errors:
        errors.append(error)


def rewrite_failed_report_outputs(
    json_path: Path | None,
    markdown_path: Path | None,
    report: dict[str, Any],
    error: str,
) -> None:
    mark_output_failure(report, error)
    written_paths: set[Path] = set()
    rewrite_targets = [
        (json_path, json.dumps(report, indent=2) + "\n", "JSON"),
        (markdown_path, render_report_markdown(report), "Markdown"),
    ]
    for path, text, label in rewrite_targets:
        if path is None or path in written_paths:
            continue
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            written_paths.add(path)
        except (TypeError, OSError) as exc:
            mark_output_failure(report, f"failed to rewrite failed {label} report after output error: {exc}")


def write_outputs(
    repo_root: Path,
    report: dict[str, Any],
    matrix: dict[str, Any],
    json_output: Path,
    markdown_output: Path,
    matrix_markdown_output: Path,
) -> None:
    path_errors: list[str] = []
    json_path = repo_relative_path_or_error(repo_root, json_output, "fixture report JSON output path", path_errors)
    markdown_path = repo_relative_path_or_error(repo_root, markdown_output, "fixture report Markdown output path", path_errors)
    matrix_markdown_path = repo_relative_path_or_error(
        repo_root,
        matrix_markdown_output,
        "rule-risk matrix Markdown output path",
        path_errors,
    )
    if json_path is not None and markdown_path is not None and matrix_markdown_path is not None:
        ensure_distinct_output_paths(
            [("JSON", json_path), ("Markdown", markdown_path), ("matrix Markdown", matrix_markdown_path)],
            path_errors,
        )
    if path_errors:
        error = "; ".join(path_errors)
        rewrite_failed_report_outputs(json_path, markdown_path, report, error)
        raise RuleRiskFixtureError(error)

    if json_path is None or markdown_path is None or matrix_markdown_path is None:
        raise RuleRiskFixtureError("output path validation failed unexpectedly")
    output_paths = [("JSON", json_path), ("Markdown", markdown_path), ("matrix Markdown", matrix_markdown_path)]
    outputs = [
        ("matrix Markdown", matrix_markdown_path, render_matrix_markdown(matrix)),
        ("JSON", json_path, json.dumps(report, indent=2) + "\n"),
        ("Markdown", markdown_path, render_report_markdown(report)),
    ]
    try:
        for _label, path, text in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        for label, path in output_paths:
            if not path.exists() or path.stat().st_size == 0:
                raise RuleRiskFixtureError(f"missing output: {label} report was not written to {path}")
    except RuleRiskFixtureError as exc:
        error = str(exc)
    except (TypeError, OSError) as exc:
        error = f"report write failure: {exc}"
    else:
        return

    rewrite_failed_report_outputs(json_path, markdown_path, report, error)
    raise RuleRiskFixtureError(error)


def build_fixture_report(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str], dict[str, Any]]:
    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    matrix_path = repo_relative_path_or_error(repo_root, args.matrix, "rule-to-risk matrix path", errors)
    manifest_path = repo_relative_path_or_error(repo_root, args.manifest, "fixture manifest path", errors)
    matrix: dict[str, Any] = {}
    manifest: dict[str, Any] = {}
    fixture_results: list[dict[str, Any]] = []
    wrapper_report: dict[str, Any] | None = None

    if matrix_path is not None:
        try:
            matrix = read_json(matrix_path, "rule-to-risk matrix")
            if not isinstance(matrix, dict):
                raise RuleRiskFixtureError("rule-to-risk matrix must be a JSON object")
        except RuleRiskFixtureError as exc:
            errors.append(str(exc))
    if manifest_path is not None:
        try:
            manifest = read_json(manifest_path, "fixture manifest")
            if not isinstance(manifest, dict):
                raise RuleRiskFixtureError("fixture manifest must be a JSON object")
        except RuleRiskFixtureError as exc:
            errors.append(str(exc))

    check_map: dict[str, dict[str, Any]] = {}
    fixture_map: dict[str, dict[str, Any]] = {}
    if not errors:
        check_map, matrix_errors, matrix_warnings = validate_matrix(matrix, not args.skip_minimum_risk_class_check)
        fixture_map, manifest_errors, manifest_warnings = validate_manifest(manifest, repo_root, check_map)
        errors.extend(matrix_errors)
        errors.extend(manifest_errors)
        warnings.extend(matrix_warnings)
        warnings.extend(manifest_warnings)

    findings: list[dict[str, Any]] = []
    if not errors:
        fixtures = [fixture_map[fixture_id] for fixture_id in sorted(fixture_map)]
        with tempfile.TemporaryDirectory(prefix=".dcoir-rule-risk-fixtures-", dir=repo_root) as temp:
            inventory_path = write_temp_inventory(repo_root, fixtures, Path(temp))
            args_for_wrapper = wrapper_args(
                repo_root=repo_root,
                inventory_path=inventory_path,
                fixture_paths=[fixture["path"] for fixture in fixtures],
                timeout_seconds=args.timeout_seconds,
            )
            wrapper_report, wrapper_errors, wrapper_warnings = analyzer.build_report(args_for_wrapper)
            warnings.extend(wrapper_warnings)
            if wrapper_errors:
                errors.extend(f"fixture wrapper: {error}" for error in wrapper_errors)
            if wrapper_report is None:
                errors.append("fixture wrapper did not return a report")
            else:
                findings = wrapper_report.get("findings", [])
    if not errors and wrapper_report is not None:
        fixture_results, result_errors, result_warnings = validate_fixture_results(check_map, fixture_map, findings)
        errors.extend(result_errors)
        warnings.extend(result_warnings)
    elif fixture_map:
        fixture_results = [
            {
                "id": fixture_id,
                "kind": fixture.get("kind"),
                "path": fixture.get("path"),
                "sha256": fixture.get("sha256"),
                "expected_finding_count": len(fixture.get("expected_findings", [])),
                "observed_finding_count": 0,
                "observed_rules": [],
                "validation": {"success": False, "errors": ["fixture analysis did not complete"]},
            }
            for fixture_id, fixture in sorted(fixture_map.items())
        ]

    blocking_count = len([check for check in check_map.values() if check.get("blocking") is True])
    advisory_count = len([check for check in check_map.values() if check.get("blocking") is False])
    negative_count = len([fixture for fixture in fixture_map.values() if fixture.get("kind") == "negative"])
    control_count = len([fixture for fixture in fixture_map.values() if fixture.get("kind") == "control"])
    expected_count = sum(len(fixture.get("expected_findings", [])) for fixture in fixture_map.values())

    report = {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "source_of_truth": "#263 rule-to-risk matrix and fixture manifest",
        "scope": "Matrix and fixture harness only. No workflow YAML, SARIF, required-check, PR, or external-agent invocation.",
        "matrix": {
            "path": safe_relpath(matrix_path, repo_root) if matrix_path is not None else Path(args.matrix).as_posix(),
            "schema_version": matrix.get("schema_version"),
            "sha256": sha256_file(matrix_path) if matrix_path is not None and matrix_path.exists() and matrix_path.is_file() else None,
        },
        "manifest": {
            "path": safe_relpath(manifest_path, repo_root) if manifest_path is not None else Path(args.manifest).as_posix(),
            "schema_version": manifest.get("schema_version"),
            "sha256": sha256_file(manifest_path)
            if manifest_path is not None and manifest_path.exists() and manifest_path.is_file()
            else None,
        },
        "analyzer_wrapper": {
            "path": "project_sources/collector/tools/run_powershell_analyzer.py",
            "schema_version": analyzer.SCHEMA_VERSION,
            "wrapped_report_schema_version": wrapper_report.get("schema_version") if wrapper_report else None,
        },
        "fixture_analyzer": {
            "name": "DCOIRFixtureAnalyzer",
            "version": "1.0.0",
            "command_kind": "custom_json_command",
        },
        "summary": {
            "matrix_check_count": len(check_map),
            "blocking_check_count": blocking_count,
            "advisory_check_count": advisory_count,
            "negative_fixture_count": negative_count,
            "control_fixture_count": control_count,
            "expected_finding_count": expected_count,
            "observed_finding_count": len(findings),
        },
        "fixtures": fixture_results,
        "findings": findings,
        "validation": {
            "success": not errors,
            "errors": errors,
            "warnings": warnings,
        },
        "outputs": {
            "json": Path(args.json_output).as_posix(),
            "markdown": Path(args.markdown_output).as_posix(),
            "matrix_markdown": Path(args.matrix_markdown_output).as_posix(),
        },
        "environment_gap": (
            "This #263 harness uses a deterministic local fixture analyzer through the #262 wrapper. "
            "It intentionally does not execute PSScriptAnalyzer, so this fixture report does not claim whether "
            "pwsh or the PSScriptAnalyzer module is installed in the current environment."
        ),
    }
    return report, errors, warnings, matrix


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate DCOIR PowerShell rule-risk fixtures")
    parser.add_argument("--fixture-analyzer", action="store_true", help="Run deterministic fixture analyzer mode")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--matrix", default=DEFAULT_MATRIX.as_posix(), help="Rule-to-risk matrix JSON")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST.as_posix(), help="Fixture manifest JSON")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="Fixture report JSON output path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Fixture report Markdown output path")
    parser.add_argument(
        "--matrix-markdown-output",
        default=DEFAULT_MATRIX_MARKDOWN_OUTPUT.as_posix(),
        help="Generated matrix Markdown output path",
    )
    parser.add_argument("--timeout-seconds", type=int, default=20, help="Analyzer wrapper timeout per fixture")
    parser.add_argument("--no-write", action="store_true", help="Do not write report outputs")
    parser.add_argument(
        "--skip-minimum-risk-class-check",
        action="store_true",
        help="Testing-only escape hatch for small temporary matrices",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fixture_analyzer:
        return run_fixture_analyzer()
    report, errors, _warnings, matrix = build_fixture_report(args)
    if not args.no_write:
        try:
            write_outputs(
                Path(args.repo_root).resolve(),
                report,
                matrix,
                Path(args.json_output),
                Path(args.markdown_output),
                Path(args.matrix_markdown_output),
            )
        except RuleRiskFixtureError as exc:
            error = str(exc)
            if error not in errors:
                errors.append(error)
            report["validation"]["success"] = False
            report["validation"]["errors"] = errors
    print(json.dumps(report["summary"], indent=2))
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
