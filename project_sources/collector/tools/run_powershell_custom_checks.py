#!/usr/bin/env python3
"""Run DCOIR-specific static checks for PowerShell validation risk.

This runner promotes the #263 DCOIR fixture analyzer checks into a local,
documented #264 check surface. It intentionally stays outside workflow YAML and
SARIF concerns; later child issues can decide how to consume its JSON/Markdown
artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_powershell_surface_inventory as inventory_builder

SCHEMA_VERSION = "dcoir_powershell_custom_check_report_v1"
CHECKS_SCHEMA_VERSION = "dcoir_powershell_custom_checks_v1"
FIXTURE_MANIFEST_SCHEMA_VERSION = "dcoir_powershell_custom_check_fixture_manifest_v1"
MATRIX_SCHEMA_VERSION = "dcoir_powershell_rule_risk_matrix_v1"
INVENTORY_SCHEMA_VERSION = inventory_builder.SCHEMA_VERSION
ISSUE_NUMBER = 264
PARENT_ISSUE_NUMBER = 260
DEFAULT_CHECKS = Path("project_sources/collector/powershell_custom_checks.json")
DEFAULT_MATRIX = Path("project_sources/collector/powershell_rule_risk_matrix.json")
DEFAULT_INVENTORY = Path("project_sources/collector/powershell_surface_inventory.json")
DEFAULT_FIXTURE_MANIFEST = Path("project_sources/collector/fixtures/powershell_analysis/custom_check_fixture_manifest.json")
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_custom_check_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_custom_check_report.md")
ANALYZABLE_SOURCE_TYPES = {".ps1", ".psm1", ".psd1", ".ps1xml", ".ps1.txt"}
SEVERITY_ORDER = {"information": 0, "warning": 1, "error": 2}
REQUIRED_CHECK_FIELDS = [
    "id",
    "rule_name",
    "matrix_check_id",
    "expected_severity",
    "risk_classes",
    "target_surfaces",
    "intent",
    "target",
    "detection",
    "limitations",
    "false_positive_controls",
    "failure_impact",
    "recommended_fix",
]


class CustomCheckError(RuntimeError):
    """Raised for invalid #264 custom-check contract state."""


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CustomCheckError(f"{label} missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CustomCheckError(f"{label} is not valid JSON: {path}: {exc}") from exc


def safe_relpath(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def scalar(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def require_string(mapping: dict[str, Any], key: str, label: str, errors: list[str]) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: {key} must be a non-empty string")
        return ""
    return value.strip()


def require_string_list(mapping: dict[str, Any], key: str, label: str, errors: list[str]) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{label}: {key} must be a non-empty list of strings")
        return []
    return [item.strip() for item in value]


def normalize_repo_path(value: str) -> str:
    slash_path = value.replace("\\", "/")
    while slash_path.startswith("./"):
        slash_path = slash_path[2:]
    return Path(slash_path).as_posix()


def is_absolute_repo_input(value: str) -> bool:
    raw = value.strip()
    slash_path = raw.replace("\\", "/")
    return slash_path.startswith("/") or re.match(r"^[A-Za-z]:/", slash_path) is not None or Path(raw).is_absolute()


def safe_fixture_path(value: str, label: str, errors: list[str]) -> str:
    raw = value.strip()
    rel = normalize_repo_path(raw)
    raw_parts = Path(raw.replace("\\", "/")).parts
    parts = Path(rel).parts
    if not raw or is_absolute_repo_input(raw) or ".." in raw_parts or rel.startswith("../") or ".." in parts or Path(rel).is_absolute():
        errors.append(f"{label}: path must be a repo-relative path without traversal")
        return rel
    if not rel.startswith("project_sources/collector/fixtures/powershell_analysis/"):
        errors.append(f"{label}: fixture path must stay under project_sources/collector/fixtures/powershell_analysis")
    return rel


def line_number_for(text: str, pattern: str, flags: int = re.IGNORECASE | re.MULTILINE) -> int | None:
    match = re.search(pattern, text, flags)
    if not match:
        return None
    return text[: match.start()].count("\n") + 1


def line_window(lines: list[str], index: int, before: int = 0, after: int = 4) -> str:
    start = max(0, index - before)
    end = min(len(lines), index + after + 1)
    return "\n".join(lines[start:end])


def code_without_full_line_comments(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            kept.append("")
        else:
            kept.append(line)
    return "\n".join(kept)


def make_finding(
    check: dict[str, Any],
    path: str,
    line: int,
    risk_class: str | None = None,
) -> dict[str, Any]:
    selected_risk = risk_class or check["risk_classes"][0]
    payload = {
        "path": path,
        "line": line,
        "column": 1,
        "symbol": "",
        "check_id": check["id"],
        "rule_name": check["rule_name"],
        "matrix_check_id": check["matrix_check_id"],
        "severity": check["expected_severity"],
        "risk_class": selected_risk,
        "risk_classes": check["risk_classes"],
        "observed_problem": check["intent"],
        "impact": check["failure_impact"],
        "failure_impact": check["failure_impact"],
        "fix": check["recommended_fix"],
        "recommended_fix": check["recommended_fix"],
        "target_surfaces": check["target_surfaces"],
    }
    fingerprint_payload = {
        "path": path,
        "line": line,
        "rule_name": payload["rule_name"],
        "severity": payload["severity"],
        "risk_class": selected_risk,
        "observed_problem": payload["observed_problem"],
    }
    payload["fingerprint"] = sha256_text(json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")))
    return payload


def validate_matrix(matrix: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    if matrix.get("schema_version") != MATRIX_SCHEMA_VERSION:
        errors.append(
            f"rule-to-risk matrix schema mismatch: expected {MATRIX_SCHEMA_VERSION}, got {matrix.get('schema_version')!r}"
        )
    checks = matrix.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("rule-to-risk matrix must contain checks[]")
        return {}, errors
    check_map: dict[str, dict[str, Any]] = {}
    for index, raw_check in enumerate(checks, start=1):
        if not isinstance(raw_check, dict):
            errors.append(f"matrix check #{index}: entry is not an object")
            continue
        check_id = scalar(raw_check.get("id")).strip()
        if not check_id:
            errors.append(f"matrix check #{index}: id must be a non-empty string")
            continue
        if check_id in check_map:
            errors.append(f"matrix check #{index}: duplicate check id {check_id}")
        check_map[check_id] = raw_check
    return check_map, errors


def validate_check_definitions(
    checks_doc: dict[str, Any],
    matrix_checks: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if checks_doc.get("schema_version") != CHECKS_SCHEMA_VERSION:
        errors.append(
            f"custom check schema mismatch: expected {CHECKS_SCHEMA_VERSION}, got {checks_doc.get('schema_version')!r}"
        )
    raw_checks = checks_doc.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        errors.append("custom checks document must contain checks[]")
        return {}, errors, warnings

    check_map: dict[str, dict[str, Any]] = {}
    for index, raw_check in enumerate(raw_checks, start=1):
        label = f"custom check #{index}"
        if not isinstance(raw_check, dict):
            errors.append(f"{label}: entry is not an object")
            continue
        for field in REQUIRED_CHECK_FIELDS:
            if field in {"risk_classes", "target_surfaces", "false_positive_controls"}:
                require_string_list(raw_check, field, label, errors)
            else:
                require_string(raw_check, field, label, errors)
        check_id = scalar(raw_check.get("id")).strip()
        if not check_id:
            continue
        if check_id in check_map:
            errors.append(f"{label}: duplicate check id {check_id}")
        if raw_check.get("expected_severity") not in {"Information", "Warning", "Error"}:
            errors.append(f"{label}: expected_severity must be Information, Warning, or Error")
        matrix_check_id = scalar(raw_check.get("matrix_check_id")).strip()
        matrix_check = matrix_checks.get(matrix_check_id)
        if not matrix_check:
            errors.append(f"{label}: matrix_check_id {matrix_check_id!r} is not present in #263 matrix")
        else:
            if raw_check.get("rule_name") != matrix_check.get("rule_name"):
                errors.append(f"{label}: rule_name does not match #263 matrix check {matrix_check_id}")
            if raw_check.get("expected_severity") != matrix_check.get("expected_severity"):
                errors.append(f"{label}: expected_severity does not match #263 matrix check {matrix_check_id}")
            matrix_risks = set(matrix_check.get("risk_classes", []))
            custom_risks = set(raw_check.get("risk_classes", []))
            if not custom_risks:
                errors.append(f"{label}: risk_classes cannot be empty")
            elif not custom_risks.issubset(matrix_risks):
                errors.append(f"{label}: risk_classes are not all mapped by #263 matrix check {matrix_check_id}")
            if matrix_check.get("blocking") is not True:
                warnings.append(f"{label}: mapped #263 matrix check is not blocking")
        check_map[check_id] = raw_check
    return check_map, errors, warnings


def validate_inventory(inventory: dict[str, Any]) -> tuple[set[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if inventory.get("schema_version") != INVENTORY_SCHEMA_VERSION:
        errors.append(
            f"PowerShell inventory schema mismatch: expected {INVENTORY_SCHEMA_VERSION}, got {inventory.get('schema_version')!r}"
        )
    validation = inventory.get("validation", {})
    if validation.get("errors"):
        errors.extend(f"inventory validation error: {error}" for error in validation.get("errors", []))
    warnings.extend(f"inventory warning: {warning}" for warning in validation.get("warnings", []))
    surfaces = inventory.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        errors.append("PowerShell inventory must contain surfaces[]")
        return set(), errors, warnings
    surface_paths: set[str] = set()
    for surface in surfaces:
        if not isinstance(surface, dict):
            continue
        path = scalar(surface.get("path")).strip()
        if path:
            surface_paths.add(path)
    return surface_paths, errors, warnings


def inventory_targets(inventory: dict[str, Any]) -> list[str]:
    targets: list[str] = []
    for surface in inventory.get("surfaces", []):
        if not isinstance(surface, dict):
            continue
        if surface.get("inclusion_decision") != "include":
            continue
        if surface.get("source_type") not in ANALYZABLE_SOURCE_TYPES:
            continue
        path = scalar(surface.get("path")).strip()
        if path:
            targets.append(path)
    return sorted(dict.fromkeys(targets))


def validate_fixture_manifest(
    manifest: dict[str, Any],
    check_map: dict[str, dict[str, Any]],
    surface_paths: set[str],
    repo_root: Path,
) -> tuple[dict[str, dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if manifest.get("schema_version") != FIXTURE_MANIFEST_SCHEMA_VERSION:
        errors.append(
            "custom fixture manifest schema mismatch: "
            f"expected {FIXTURE_MANIFEST_SCHEMA_VERSION}, got {manifest.get('schema_version')!r}"
        )
    raw_fixtures = manifest.get("fixtures")
    if not isinstance(raw_fixtures, list) or not raw_fixtures:
        errors.append("custom fixture manifest must contain fixtures[]")
        return {}, errors, warnings

    fixture_map: dict[str, dict[str, Any]] = {}
    fixture_kinds_by_check: dict[str, set[str]] = {check_id: set() for check_id in check_map}
    for index, raw_fixture in enumerate(raw_fixtures, start=1):
        label = f"custom fixture #{index}"
        if not isinstance(raw_fixture, dict):
            errors.append(f"{label}: entry is not an object")
            continue
        fixture_id = require_string(raw_fixture, "id", label, errors)
        kind = require_string(raw_fixture, "kind", label, errors)
        check_id = require_string(raw_fixture, "check_id", label, errors)
        path = safe_fixture_path(require_string(raw_fixture, "path", label, errors), label, errors)
        if fixture_id in fixture_map:
            errors.append(f"{label}: duplicate fixture id {fixture_id}")
        if kind not in {"negative", "control"}:
            errors.append(f"{label}: kind must be negative or control")
        if check_id not in check_map:
            errors.append(f"{label}: check_id {check_id!r} is not defined")
        else:
            fixture_kinds_by_check[check_id].add(kind)
        if path and path not in surface_paths:
            errors.append(f"{label}: fixture path {path} is missing from PowerShell surface inventory")
        if path and not (repo_root / path).is_file():
            errors.append(f"{label}: fixture source is missing: {path}")

        expected_findings = raw_fixture.get("expected_findings")
        if not isinstance(expected_findings, list):
            errors.append(f"{label}: expected_findings must be a list")
            expected_findings = []
        if kind == "negative" and not expected_findings:
            errors.append(f"{label}: negative fixtures must declare expected_findings")
        if kind == "control" and expected_findings:
            errors.append(f"{label}: control fixtures must not declare expected_findings")
        for expected_index, raw_expected in enumerate(expected_findings, start=1):
            expected_label = f"{label} expected finding #{expected_index}"
            if not isinstance(raw_expected, dict):
                errors.append(f"{expected_label}: entry is not an object")
                continue
            expected_check_id = require_string(raw_expected, "check_id", expected_label, errors)
            rule_name = require_string(raw_expected, "rule_name", expected_label, errors)
            severity = require_string(raw_expected, "severity", expected_label, errors)
            risk_class = require_string(raw_expected, "risk_class", expected_label, errors)
            line = raw_expected.get("line")
            if not isinstance(line, int) or line <= 0:
                errors.append(f"{expected_label}: line must be a positive integer")
            if expected_check_id != check_id:
                errors.append(f"{expected_label}: check_id must match fixture check_id {check_id}")
            check = check_map.get(expected_check_id)
            if check:
                if rule_name != check.get("rule_name"):
                    errors.append(f"{expected_label}: rule_name does not match custom check {expected_check_id}")
                if severity != check.get("expected_severity"):
                    errors.append(f"{expected_label}: severity does not match custom check {expected_check_id}")
                if risk_class not in check.get("risk_classes", []):
                    errors.append(f"{expected_label}: risk_class is not declared on custom check {expected_check_id}")
        if fixture_id:
            fixture_map[fixture_id] = {
                **raw_fixture,
                "path": path,
                "expected_findings": expected_findings,
            }

    for check_id, kinds in fixture_kinds_by_check.items():
        if "negative" not in kinds:
            errors.append(f"{check_id}: custom check has no negative fixture")
        if "control" not in kinds:
            errors.append(f"{check_id}: custom check has no corrected/control fixture")
    return fixture_map, errors, warnings


def check_analyzer_skip_success(text: str, path: str, check: dict[str, Any]) -> list[dict[str, Any]]:
    line = line_number_for(text, r"\b(?:analyzed|skipped)\s*=\s*\$(?:false|true)\b")
    if not line:
        return []
    success_like = re.search(r"\b(?:validation|status)\s*=\s*['\"](?:success|pass|passed|ok)['\"]|\bexit\s+0\b", text, re.IGNORECASE)
    fail_closed = re.search(r"\bthrow\b|\bexit\s+[1-9]\d*\b|\bFAIL\b", text, re.IGNORECASE)
    if success_like and not fail_closed:
        return [make_finding(check, path, line)]
    return []


def check_external_exit(text: str, path: str, check: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    call_operator_target_re = r"(?:\$?[A-Za-z_][\w.]*|\"[^\"]+\"|'[^']+'|\([^)]+\)|[^\s|;&]+)"
    command_re = re.compile(
        rf"^\s*(?:&\s*{call_operator_target_re}|(?:robocopy|cmd|powershell|pwsh|python|git|dotnet)(?:\.exe)?\b|Start-Process\b)",
        re.IGNORECASE,
    )
    for index, line in enumerate(lines):
        if not command_re.search(line):
            continue
        window = line_window(lines, index, after=4)
        if re.search(r"\$LASTEXITCODE|\$\?|\bExitCode\b", window, re.IGNORECASE):
            continue
        findings.append(
            make_finding(check, path, index + 1, "external_command_nonzero_exit_treated_success")
        )
    return findings


def check_fail_output(text: str, path: str, check: dict[str, Any]) -> list[dict[str, Any]]:
    line = line_number_for(text, r"\bStatus\s*=\s*['\"]FAIL['\"]|\bFAIL\b")
    if not line:
        return []
    fail_closed = re.search(
        r"\bthrow\b|\bexit\s+[1-9]\d*\b|\breturn\s+\$false\b|\bvalidation\s*=\s*['\"]FAIL['\"]",
        text,
        re.IGNORECASE,
    )
    if not fail_closed:
        return [make_finding(check, path, line)]
    return []


def check_source_part_drift(text: str, path: str, check: dict[str, Any]) -> list[dict[str, Any]]:
    line = line_number_for(text, r"\bstale-generated\b|\bGeneratedOutputHash\s*=\s*['\"][^'\"]*stale|source[-_ ]part.*drift")
    if line:
        return [make_finding(check, path, line)]
    return []


def check_unsafe_wildcard_delete(text: str, path: str, check: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not re.search(r"\bRemove-Item\b", line, re.IGNORECASE):
            continue
        if not re.search(r"(?<!\w)-Recurse\b", line, re.IGNORECASE):
            continue
        risky_path = "*" in line or re.search(r"(?<!\w)-(?:Path|LiteralPath)\s+\$|Join-Path", line, re.IGNORECASE)
        if not risky_path:
            continue
        context = "\n".join(lines[max(0, index - 8) : index + 1])
        constrained = re.search(r"\bResolve-Path\b", context, re.IGNORECASE) and re.search(
            r"\bStartsWith\b|\bIsChildPath\b|\bGetFullPath\b",
            context,
            re.IGNORECASE,
        )
        if not constrained:
            findings.append(make_finding(check, path, index + 1))
    return findings


def check_bounded_event_query(text: str, path: str, check: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not re.search(r"\bGet-WinEvent\b", line, re.IGNORECASE):
            continue
        context = line_window(lines, index, after=2)
        bounded = re.search(
            r"(?<!\w)-(?:FilterHashtable|FilterXPath|MaxEvents)\b|Select-Object\s+(?<!\w)-First\b",
            context,
            re.IGNORECASE,
        )
        if not bounded:
            findings.append(make_finding(check, path, index + 1))
    return findings


def check_baseline_suppression(text: str, path: str, check: dict[str, Any]) -> list[dict[str, Any]]:
    suppression_text = code_without_full_line_comments(text)
    if not re.search(r"Suppression|SuppressMessage|PSScriptAnalyzer|baseline", suppression_text, re.IGNORECASE):
        return []
    broad_line = line_number_for(suppression_text, r"\bpath\s*=\s*['\"]\*['\"]|\brule_name\s*=\s*['\"]PS\*['\"]")
    missing_fields = [
        field
        for field in ("path", "rule_name", "fingerprint", "expected_match_count")
        if not re.search(rf"\b{field}\b", suppression_text, re.IGNORECASE)
    ]
    has_reason = re.search(r"\breason\b|\bjustification\b", suppression_text, re.IGNORECASE)
    if broad_line or missing_fields or not has_reason:
        line = broad_line or line_number_for(suppression_text, r"Suppress|baseline|rule_name|path") or 1
        return [make_finding(check, path, line)]
    return []


def check_swallowed_catch(text: str, path: str, check: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for match in re.finditer(r"(?is)\bcatch\b\s*\{(?P<body>.*?)\}", text):
        body = match.group("body")
        fails_closed = re.search(
            r"\bthrow\b|\bexit\s+[1-9]\d*\b|\breturn\s+\$false\b|\bStatus\s*=\s*['\"]FAIL['\"]",
            body,
            re.IGNORECASE,
        )
        if fails_closed:
            continue
        body_start_line = text[: match.start("body")].count("\n") + 1
        write_line = line_number_for(body, r"\bWrite-(?:Warning|Host|Output|Verbose|Information)\b")
        line = body_start_line + write_line - 1 if write_line else text[: match.start()].count("\n") + 1
        findings.append(make_finding(check, path, line))
    return findings


CHECK_FUNCTIONS = {
    "dcoir-analyzer-skip-success": check_analyzer_skip_success,
    "dcoir-check-external-exit": check_external_exit,
    "dcoir-fail-output-must-fail": check_fail_output,
    "dcoir-source-part-drift": check_source_part_drift,
    "dcoir-no-unsafe-wildcard-delete": check_unsafe_wildcard_delete,
    "dcoir-bound-event-query": check_bounded_event_query,
    "dcoir-baseline-fingerprint-bound": check_baseline_suppression,
    "dcoir-no-swallowed-catch": check_swallowed_catch,
}


def run_checks_for_text(text: str, path: str, check_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for check_id, check in check_map.items():
        check_function = CHECK_FUNCTIONS.get(check_id)
        if check_function is None:
            findings.append(
                make_finding(
                    {
                        **check,
                        "intent": f"Custom check {check_id} has no implementation.",
                        "failure_impact": "Missing implementation leaves a documented DCOIR check unenforced.",
                        "recommended_fix": "Add a deterministic local detection function for this check.",
                    },
                    path,
                    1,
                )
            )
            continue
        findings.extend(check_function(text, path, check))
    return findings


def expected_match(expected: dict[str, Any], finding: dict[str, Any], path: str) -> bool:
    return (
        finding.get("path") == path
        and finding.get("check_id") == expected.get("check_id")
        and finding.get("rule_name") == expected.get("rule_name")
        and finding.get("severity") == expected.get("severity")
        and finding.get("risk_class") == expected.get("risk_class")
        and finding.get("line") == expected.get("line")
    )


def validate_fixture_results(
    fixture_map: dict[str, dict[str, Any]],
    findings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    by_path: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        by_path.setdefault(finding["path"], []).append(finding)

    fixture_results: list[dict[str, Any]] = []
    for fixture_id, fixture in sorted(fixture_map.items()):
        path = fixture["path"]
        fixture_findings = by_path.get(path, [])
        expected_findings = fixture.get("expected_findings", [])
        if fixture.get("kind") == "control" and fixture_findings:
            errors.append(
                f"{fixture_id}: control fixture produced unexpected findings: "
                + ", ".join(finding["rule_name"] for finding in fixture_findings)
            )
        for expected in expected_findings:
            if not any(expected_match(expected, finding, path) for finding in fixture_findings):
                errors.append(
                    f"{fixture_id}: expected {expected.get('rule_name')} at {path}:{expected.get('line')} was not produced"
                )
        unexpected = [
            finding
            for finding in fixture_findings
            if not any(expected_match(expected, finding, path) for expected in expected_findings)
        ]
        if unexpected and fixture.get("kind") == "negative":
            warnings.append(
                f"{fixture_id}: produced additional unmapped findings: "
                + ", ".join(finding["rule_name"] for finding in unexpected)
            )
        fixture_results.append(
            {
                "id": fixture_id,
                "kind": fixture.get("kind"),
                "check_id": fixture.get("check_id"),
                "path": path,
                "expected_finding_count": len(expected_findings),
                "observed_finding_count": len(fixture_findings),
                "observed_rules": sorted({finding["rule_name"] for finding in fixture_findings}),
            }
        )
    return fixture_results, errors, warnings


def severity_at_or_above(severity: str, threshold: str) -> bool:
    return SEVERITY_ORDER.get(severity.casefold(), 99) >= SEVERITY_ORDER.get(threshold.casefold(), 1)


def select_targets(
    args: argparse.Namespace,
    inventory: dict[str, Any],
    fixture_map: dict[str, dict[str, Any]],
) -> list[str]:
    fixture_paths = [fixture["path"] for fixture in fixture_map.values()]
    if args.target_scope == "fixtures":
        targets = fixture_paths
    elif args.target_scope == "inventory":
        targets = inventory_targets(inventory)
    else:
        targets = fixture_paths + inventory_targets(inventory)
    if args.target_path:
        requested = {normalize_repo_path(path) for path in args.target_path}
        targets = [target for target in targets if target in requested]
    return sorted(dict.fromkeys(targets))


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    validation = report["validation"]
    lines = [
        "# PowerShell Custom DCOIR Check Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Issue: `#{report['issue']}`",
        f"- Target scope: `{report['target_scope']}`",
        f"- Checks: `{report['checks']['path']}`",
        f"- Fixture manifest: `{report['fixture_manifest']['path']}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Custom checks | {summary['custom_check_count']} |",
        f"| Targets scanned | {summary['target_count']} |",
        f"| Findings | {summary['finding_count']} |",
        f"| Negative fixtures | {summary['negative_fixture_count']} |",
        f"| Control fixtures | {summary['control_fixture_count']} |",
        f"| Expected fixture findings | {summary['expected_fixture_finding_count']} |",
        f"| Observed fixture findings | {summary['observed_fixture_finding_count']} |",
        "",
        "## Findings",
        "",
    ]
    if report["findings"]:
        lines.extend(
            [
                "| Check | Risk | Path | Line | Severity | Observed | Impact | Fix |",
                "| --- | --- | --- | ---: | --- | --- | --- | --- |",
            ]
        )
        for finding in report["findings"]:
            observed = str(finding["observed_problem"]).replace("|", "\\|")
            impact = str(finding["impact"]).replace("|", "\\|")
            fix = str(finding["fix"]).replace("|", "\\|")
            lines.append(
                f"| `{finding['check_id']}` | `{finding['risk_class']}` | `{finding['path']}` | "
                f"{finding['line']} | `{finding['severity']}` | {observed} | {impact} | {fix} |"
            )
    else:
        lines.append("No custom DCOIR findings were reported.")
    lines.extend(["", "## Fixture Results", ""])
    lines.extend(["| Fixture | Kind | Check | Expected | Observed | Rules |", "| --- | --- | --- | ---: | ---: | --- |"])
    for fixture in report["fixtures"]:
        rules = ", ".join(f"`{rule}`" for rule in fixture["observed_rules"]) or "(none)"
        lines.append(
            f"| `{fixture['id']}` | `{fixture['kind']}` | `{fixture['check_id']}` | "
            f"{fixture['expected_finding_count']} | {fixture['observed_finding_count']} | {rules} |"
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
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, report: dict[str, Any], json_output: Path, markdown_output: Path) -> list[str]:
    errors: list[str] = []
    outputs = [
        (repo_root / json_output, json.dumps(report, indent=2) + "\n"),
        (repo_root / markdown_output, render_markdown(report)),
    ]
    for path, content in outputs:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            errors.append(f"could not write expected report output {safe_relpath(path, repo_root)}: {exc}")
            continue
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"expected report output was not written: {safe_relpath(path, repo_root)}")
    return errors


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str]]:
    repo_root = Path(args.repo_root).resolve()
    checks_path = (repo_root / args.checks).resolve()
    matrix_path = (repo_root / args.matrix).resolve()
    inventory_path = (repo_root / args.inventory).resolve()
    fixture_manifest_path = (repo_root / args.fixture_manifest).resolve()
    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    errors: list[str] = []
    warnings: list[str] = []
    checks_doc: dict[str, Any] = {}
    matrix: dict[str, Any] = {}
    inventory: dict[str, Any] = {}
    manifest: dict[str, Any] = {}
    check_map: dict[str, dict[str, Any]] = {}
    fixture_map: dict[str, dict[str, Any]] = {}
    surface_paths: set[str] = set()

    try:
        checks_doc = read_json(checks_path, "custom checks")
        matrix = read_json(matrix_path, "rule-to-risk matrix")
        inventory = read_json(inventory_path, "PowerShell surface inventory")
        manifest = read_json(fixture_manifest_path, "custom fixture manifest")
    except CustomCheckError as exc:
        errors.append(str(exc))

    if not errors:
        matrix_checks, matrix_errors = validate_matrix(matrix)
        errors.extend(matrix_errors)
        check_map, check_errors, check_warnings = validate_check_definitions(checks_doc, matrix_checks)
        errors.extend(check_errors)
        warnings.extend(check_warnings)
        surface_paths, inventory_errors, inventory_warnings = validate_inventory(inventory)
        errors.extend(inventory_errors)
        warnings.extend(inventory_warnings)
        fixture_map, fixture_errors, fixture_warnings = validate_fixture_manifest(manifest, check_map, surface_paths, repo_root)
        errors.extend(fixture_errors)
        warnings.extend(fixture_warnings)

    targets = select_targets(args, inventory, fixture_map) if not errors else []
    if not errors and not targets:
        errors.append("no PowerShell targets selected for custom checks")

    findings: list[dict[str, Any]] = []
    if not errors:
        for target in targets:
            target_path = repo_root / target
            if not target_path.is_file():
                errors.append(f"selected PowerShell source missing: {target}")
                continue
            text = target_path.read_text(encoding="utf-8", errors="ignore")
            findings.extend(run_checks_for_text(text, target, check_map))

    fixture_paths = {fixture["path"] for fixture in fixture_map.values()}
    scanned_fixture_paths = fixture_paths.intersection(targets)
    fixture_results: list[dict[str, Any]] = []
    fixture_errors: list[str] = []
    fixture_warnings: list[str] = []
    evaluated_fixture_map = fixture_map
    if fixture_map and scanned_fixture_paths:
        scanned_fixture_map = {
            fixture_id: fixture
            for fixture_id, fixture in fixture_map.items()
            if fixture["path"] in scanned_fixture_paths
        }
        evaluated_fixture_map = scanned_fixture_map
        fixture_results, fixture_errors, fixture_warnings = validate_fixture_results(scanned_fixture_map, findings)
        errors.extend(fixture_errors)
        warnings.extend(fixture_warnings)
    elif fixture_map:
        warnings.append("fixture expectations were not evaluated because no fixture targets were selected")
        fixture_results = [
            {
                "id": fixture_id,
                "kind": fixture.get("kind"),
                "check_id": fixture.get("check_id"),
                "path": fixture.get("path"),
                "expected_finding_count": len(fixture.get("expected_findings", [])),
                "observed_finding_count": 0,
                "observed_rules": [],
            }
            for fixture_id, fixture in sorted(fixture_map.items())
        ]

    unexpected_non_fixture_findings = [
        finding
        for finding in findings
        if finding["path"] not in fixture_paths and severity_at_or_above(finding["severity"], args.fail_on_severity)
    ]
    if unexpected_non_fixture_findings and not args.allow_findings:
        errors.append(
            f"unsuppressed custom findings at or above {args.fail_on_severity}: {len(unexpected_non_fixture_findings)}"
        )

    evaluated_fixture_paths = {fixture["path"] for fixture in evaluated_fixture_map.values()}
    negative_count = len([fixture for fixture in evaluated_fixture_map.values() if fixture.get("kind") == "negative"])
    control_count = len([fixture for fixture in evaluated_fixture_map.values() if fixture.get("kind") == "control"])
    expected_count = sum(len(fixture.get("expected_findings", [])) for fixture in evaluated_fixture_map.values())
    observed_fixture_count = len([finding for finding in findings if finding["path"] in evaluated_fixture_paths])
    report = {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "parent_issue": PARENT_ISSUE_NUMBER,
        "depends_on": [261, 262, 263],
        "source_of_truth": "#264 custom DCOIR check contract mapped to #263 rule-to-risk matrix",
        "target_scope": args.target_scope,
        "checks": {
            "path": safe_relpath(checks_path, repo_root),
            "schema_version": checks_doc.get("schema_version"),
            "sha256": sha256_file(checks_path) if checks_path.is_file() else None,
        },
        "matrix": {
            "path": safe_relpath(matrix_path, repo_root),
            "schema_version": matrix.get("schema_version"),
            "sha256": sha256_file(matrix_path) if matrix_path.is_file() else None,
        },
        "inventory": {
            "path": safe_relpath(inventory_path, repo_root),
            "schema_version": inventory.get("schema_version"),
            "sha256": sha256_file(inventory_path) if inventory_path.is_file() else None,
            "inventory_total_surfaces": inventory.get("summary", {}).get("total_surfaces") if isinstance(inventory, dict) else None,
        },
        "fixture_manifest": {
            "path": safe_relpath(fixture_manifest_path, repo_root),
            "schema_version": manifest.get("schema_version"),
            "sha256": sha256_file(fixture_manifest_path) if fixture_manifest_path.is_file() else None,
        },
        "summary": {
            "custom_check_count": len(check_map),
            "target_count": len(targets),
            "finding_count": len(findings),
            "negative_fixture_count": negative_count,
            "control_fixture_count": control_count,
            "expected_fixture_finding_count": expected_count,
            "observed_fixture_finding_count": observed_fixture_count,
        },
        "targets": targets,
        "fixtures": fixture_results,
        "findings": findings,
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
    parser = argparse.ArgumentParser(description="Run DCOIR custom PowerShell checks")
    parser.add_argument("--repo-root", default=".", help="Repository root to scan")
    parser.add_argument("--checks", default=DEFAULT_CHECKS.as_posix(), help="Custom check definition JSON")
    parser.add_argument("--matrix", default=DEFAULT_MATRIX.as_posix(), help="#263 rule-to-risk matrix JSON")
    parser.add_argument("--inventory", default=DEFAULT_INVENTORY.as_posix(), help="#261 PowerShell inventory JSON")
    parser.add_argument("--fixture-manifest", default=DEFAULT_FIXTURE_MANIFEST.as_posix(), help="#264 fixture manifest JSON")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="Custom check JSON report path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Custom check Markdown report path")
    parser.add_argument("--target-scope", default="fixtures", choices=["fixtures", "inventory", "all"], help="Targets to scan")
    parser.add_argument("--target-path", action="append", default=[], help="Repo-relative target path to scan; may repeat")
    parser.add_argument("--fail-on-severity", default="Warning", choices=["Information", "Warning", "Error"], help="Finding severity threshold")
    parser.add_argument("--allow-findings", action="store_true", help="Allow non-fixture findings without failing")
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
