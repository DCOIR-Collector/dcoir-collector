#!/usr/bin/env python3
"""Validate the #267 PowerShell engine and Pester evidence boundary."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "dcoir_powershell_engine_pester_boundary_report_v1"
BOUNDARY_SCHEMA_VERSION = "dcoir_powershell_engine_pester_boundary_v1"
ISSUE_NUMBER = 267
PARENT_ISSUE_NUMBER = 260
DEFAULT_BOUNDARY = Path("project_sources/collector/powershell_engine_pester_boundary.json")
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_engine_pester_boundary_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_engine_pester_boundary_report.md")
DEFAULT_RULE_RISK_REPORT = Path("project_sources/collector/powershell_rule_risk_fixture_report.json")
DEFAULT_CUSTOM_REPORT = Path("project_sources/collector/powershell_custom_check_report.json")
DEFAULT_GOVERNANCE_REPORT = Path("project_sources/collector/powershell_finding_governance_report.json")
DEFAULT_ASSEMBLY_REPORT = Path("project_sources/collector/powershell_assembly_parity_report.json")

REQUIRED_CHECK_CATEGORIES = {
    "surface_inventory",
    "windows_powershell_51_parser_runtime_compatibility",
    "powershell_7_static_analyzer",
    "rule_risk_negative_fixture_proof",
    "dcoir_custom_static_checks",
    "assembly_aware_source_generated_parity",
    "baseline_remediation_suppression_governance",
    "pester_supporting_tests",
}
REQUIRED_MATRIX_FIELDS = (
    "id",
    "check_category",
    "required_engine",
    "runner_os",
    "module_or_tool_dependency",
    "evidence_type",
    "output_artifact",
    "blocking",
    "owner",
    "boundary",
)
PESTER_EVIDENCE_FIELDS = {
    "discovery command",
    "Pester version",
    "PowerShell engine and version",
    "runner OS",
    "test count",
    "pass/fail count",
    "machine-readable test result artifact",
    "human-readable summary",
    "owning issue or workflow gate",
    "failure behavior",
}
REPORT_SCHEMAS = {
    DEFAULT_RULE_RISK_REPORT.as_posix(): "dcoir_powershell_rule_risk_fixture_report_v1",
    DEFAULT_CUSTOM_REPORT.as_posix(): "dcoir_powershell_custom_check_report_v1",
    DEFAULT_GOVERNANCE_REPORT.as_posix(): "dcoir_powershell_finding_governance_report_v1",
    DEFAULT_ASSEMBLY_REPORT.as_posix(): "dcoir_powershell_assembly_parity_report_v1",
}
REPO_ARTIFACT_PREFIXES = (
    ".github/",
    "operator_tools/",
    "project_sources/",
    "scripts/",
    "tools/",
)
EXPLICIT_ARTIFACT_STATUSES = {
    "not_committed_in_267_boundary",
}


class EngineBoundaryError(RuntimeError):
    """Raised for fail-closed #267 validation errors."""


def scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EngineBoundaryError(f"{label} missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EngineBoundaryError(f"{label} invalid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise EngineBoundaryError(f"{label} could not be read: {path}: {exc}") from exc


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_repo_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def has_text(value: Any) -> bool:
    return bool(scalar(value).strip())


def fail_if_missing_fields(prefix: str, item: dict[str, Any], fields: tuple[str, ...], errors: list[str]) -> None:
    for field in fields:
        if field not in item or (field != "blocking" and not has_text(item.get(field))):
            errors.append(f"{prefix} missing {field}")


def validate_boundary_doc(boundary: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    if boundary.get("schema_version") != BOUNDARY_SCHEMA_VERSION:
        errors.append(
            "PowerShell engine/Pester boundary schema mismatch: "
            f"expected {BOUNDARY_SCHEMA_VERSION}, got {boundary.get('schema_version')!r}"
        )
    if boundary.get("issue") != ISSUE_NUMBER:
        errors.append(f"PowerShell engine/Pester boundary issue must be {ISSUE_NUMBER}")
    if boundary.get("parent_issue") != PARENT_ISSUE_NUMBER:
        errors.append(f"PowerShell engine/Pester boundary parent_issue must be {PARENT_ISSUE_NUMBER}")
    policy = boundary.get("policy")
    if not isinstance(policy, dict):
        errors.append("PowerShell engine/Pester boundary policy must be an object")
        policy = {}
    if policy.get("workflow_readiness_claimed") is not False:
        errors.append("workflow readiness must not be claimed by #267 boundary artifacts")
    if policy.get("pester_may_replace_analyzer_or_custom_checks") is not False:
        errors.append("Pester must not be allowed to replace analyzer or custom-check enforcement")
    if policy.get("engine_evidence_must_be_separate") is not True:
        errors.append("engine evidence separation must be required")
    if policy.get("independent_analyzer_enforcement_required") is not True:
        errors.append("independent analyzer enforcement proof must be required")

    matrix = boundary.get("engine_matrix")
    if not isinstance(matrix, list) or not matrix:
        errors.append("engine_matrix must be a non-empty list")
        matrix = []
    seen_categories: set[str] = set()
    matrix_rows: list[dict[str, Any]] = []
    for index, row in enumerate(matrix, start=1):
        if not isinstance(row, dict):
            errors.append(f"engine_matrix[{index}] must be an object")
            continue
        row_id = scalar(row.get("id")).strip() or f"<row-{index}>"
        fail_if_missing_fields(f"engine matrix row {row_id}", row, REQUIRED_MATRIX_FIELDS, errors)
        category = scalar(row.get("check_category")).strip()
        if category:
            if category in seen_categories:
                errors.append(f"duplicate engine matrix category {category}")
            seen_categories.add(category)
        if not isinstance(row.get("blocking"), bool):
            errors.append(f"engine matrix row {row_id} blocking must be boolean")
        engine = scalar(row.get("required_engine")).strip().casefold()
        runner_os = scalar(row.get("runner_os")).strip()
        if engine in {"pwsh", "powershell", "powershell core", "windows powershell"}:
            errors.append(f"engine matrix row {row_id} uses ambiguous engine {row.get('required_engine')!r}")
        if "windows powerShell 5.1".casefold() in engine and "windows" not in runner_os.casefold():
            errors.append(f"engine matrix row {row_id} asserts Windows PowerShell 5.1 without Windows runner")
        matrix_rows.append(row)
    missing_categories = sorted(REQUIRED_CHECK_CATEGORIES - seen_categories)
    if missing_categories:
        errors.append(f"engine_matrix missing categories: {', '.join(missing_categories)}")

    pester = boundary.get("pester_boundary")
    if not isinstance(pester, dict):
        errors.append("pester_boundary must be an object")
        pester = {}
    if scalar(pester.get("scope_decision")).strip() not in {
        "supporting-in-scope-not-analyzer-substitute",
        "out-of-scope-for-260-static-validation",
    }:
        errors.append("pester_boundary scope_decision must explicitly define in-scope or out-of-scope status")
    if pester.get("blocking_for_static_security_validation") is not False:
        errors.append("Pester must not be blocking for static security validation in #267")
    must_not_replace = {
        scalar(item).strip()
        for item in pester.get("must_not_replace", [])
        if scalar(item).strip()
    }
    for required in ("#262 analyzer wrapper enforcement", "#264 DCOIR custom checks"):
        if required not in must_not_replace:
            errors.append(f"pester_boundary must_not_replace missing {required}")
    evidence = {
        scalar(item).strip()
        for item in pester.get("required_evidence_when_used", [])
        if scalar(item).strip()
    }
    missing_evidence = sorted(PESTER_EVIDENCE_FIELDS - evidence)
    if missing_evidence:
        errors.append(f"pester_boundary required_evidence_when_used missing: {', '.join(missing_evidence)}")
    responsibilities = pester.get("owned_responsibilities")
    if not isinstance(responsibilities, list) or not responsibilities:
        errors.append("pester_boundary owned_responsibilities must be a non-empty list")
    else:
        for index, responsibility in enumerate(responsibilities, start=1):
            if not isinstance(responsibility, dict):
                errors.append(f"pester responsibility {index} must be an object")
                continue
            fail_if_missing_fields(
                f"pester responsibility {scalar(responsibility.get('surface')).strip() or index}",
                responsibility,
                ("surface", "owner", "blocking", "notes"),
                errors,
            )
            if not isinstance(responsibility.get("blocking"), bool):
                errors.append(f"pester responsibility {index} blocking must be boolean")

    proof = boundary.get("independent_analyzer_enforcement_proof")
    if not isinstance(proof, dict):
        errors.append("independent_analyzer_enforcement_proof must be an object")
        proof = {}
    if proof.get("requires_pester") is not False:
        errors.append("independent analyzer enforcement proof must not require Pester")
    source_reports = proof.get("source_reports")
    if not isinstance(source_reports, list) or not source_reports:
        errors.append("independent analyzer enforcement proof source_reports must be a non-empty list")
        source_reports = []
    if not isinstance(proof.get("required_conditions"), list) or not proof.get("required_conditions"):
        errors.append("independent analyzer enforcement proof required_conditions must be a non-empty list")

    metadata = {
        "matrix_rows": matrix_rows,
        "category_counts": dict(Counter(scalar(row.get("check_category")).strip() for row in matrix_rows)),
        "pester_scope_decision": scalar(pester.get("scope_decision")).strip(),
        "source_reports": [scalar(report).strip() for report in source_reports if scalar(report).strip()],
    }
    if not errors and len(seen_categories) == len(REQUIRED_CHECK_CATEGORIES):
        warnings.append("workflow readiness remains a later explicit gate; #267 only defines evidence ownership")
    return errors, warnings, metadata


def report_success_state(report: dict[str, Any]) -> tuple[bool, str]:
    validation = report.get("validation")
    if isinstance(validation, dict) and "success" in validation:
        success = validation.get("success")
        if success is True:
            return True, "validation.success is true"
        if success is False:
            return False, "validation.success is false"
        return False, "validation.success must be boolean true"
    if validation is not None and not isinstance(validation, dict):
        return False, "validation must be an object with success=true"
    if "success" in report:
        success = report.get("success")
        if success is True:
            return True, "top-level success is true"
        if success is False:
            return False, "top-level success is false"
        return False, "top-level success must be boolean true"
    return False, "missing explicit validation.success or top-level success"


def report_success(report: dict[str, Any]) -> bool:
    success, _reason = report_success_state(report)
    return success


def summary_count(report: dict[str, Any], key: str) -> int:
    summary = report.get("summary")
    if not isinstance(summary, dict):
        return 0
    value = summary.get(key)
    return value if isinstance(value, int) else 0


def report_finding_count(report: dict[str, Any]) -> int:
    for key in ("finding_count", "observed_finding_count", "classified_finding_count"):
        count = summary_count(report, key)
        if count:
            return count
    return 0


def is_repo_artifact_path(value: str) -> bool:
    return value.startswith(REPO_ARTIFACT_PREFIXES)


def declared_output_artifacts(
    repo_root: Path,
    matrix_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    artifacts: list[dict[str, Any]] = []
    for row in matrix_rows:
        artifact = scalar(row.get("output_artifact")).strip()
        row_id = scalar(row.get("id")).strip()
        status = scalar(row.get("artifact_status")).strip()
        if status and status not in EXPLICIT_ARTIFACT_STATUSES:
            errors.append(f"engine matrix row {row_id} has unsupported artifact_status {status!r}")
        repo_path = is_repo_artifact_path(artifact)
        exists = (repo_root / artifact).is_file() if repo_path else None
        evidence_claimed = bool(repo_path and exists)
        if status == "not_committed_in_267_boundary":
            evidence_claimed = False
            warnings.append(
                f"engine matrix row {row_id} artifact is not committed or claimed by this #267 boundary: {artifact}"
            )
        elif repo_path and row.get("blocking") is True and not exists:
            errors.append(f"blocking engine matrix artifact missing: {artifact} ({row_id})")
        artifacts.append(
            {
                "id": row_id,
                "check_category": scalar(row.get("check_category")).strip(),
                "path": artifact,
                "repo_path": repo_path,
                "exists": exists,
                "blocking": row.get("blocking"),
                "artifact_status": status or ("present" if exists else "external_or_future"),
                "evidence_claimed_by_boundary": evidence_claimed,
            }
        )
    return artifacts, errors, warnings


def validate_source_reports(
    repo_root: Path,
    source_reports: list[str],
    extra_reports: list[Path],
) -> tuple[list[dict[str, Any]], list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    report_facts: list[dict[str, Any]] = []
    loaded: dict[str, dict[str, Any]] = {}
    requested = [Path(path) for path in source_reports]
    for report_path in requested + extra_reports:
        repo_path = report_path.as_posix()
        if repo_path in loaded:
            continue
        try:
            report = read_json(repo_root / report_path, "PowerShell #267 dependency report")
        except EngineBoundaryError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(report, dict):
            errors.append(f"PowerShell #267 dependency report must be an object: {repo_path}")
            continue
        expected_schema = REPORT_SCHEMAS.get(repo_path)
        schema = scalar(report.get("schema_version")).strip()
        if expected_schema and schema != expected_schema:
            errors.append(f"{repo_path} schema mismatch: expected {expected_schema}, got {schema!r}")
        success, success_reason = report_success_state(report)
        if not success:
            errors.append(f"{repo_path} does not report successful validation: {success_reason}")
        loaded[repo_path] = report
        report_facts.append(
            {
                "path": repo_path,
                "schema_version": schema,
                "success": success,
                "finding_count": report_finding_count(report),
                "exists": True,
            }
        )
    proof = {
        "rule_risk_fixture_findings": summary_count(loaded.get(DEFAULT_RULE_RISK_REPORT.as_posix(), {}), "observed_finding_count"),
        "custom_check_findings": summary_count(loaded.get(DEFAULT_CUSTOM_REPORT.as_posix(), {}), "finding_count"),
        "governance_unclassified_findings": 0,
        "governance_classified_findings": 0,
        "assembly_parity_success": report_success(loaded.get(DEFAULT_ASSEMBLY_REPORT.as_posix(), {})),
    }
    governance_report = loaded.get(DEFAULT_GOVERNANCE_REPORT.as_posix(), {})
    governance_summary = governance_report.get("summary") if isinstance(governance_report, dict) else {}
    if isinstance(governance_summary, dict):
        proof["governance_unclassified_findings"] = governance_summary.get("unclassified_finding_count", 0)
        proof["governance_classified_findings"] = governance_summary.get("classified_finding_count", 0)
    if proof["rule_risk_fixture_findings"] < 1:
        errors.append("independent analyzer proof missing rule-risk fixture findings")
    if proof["custom_check_findings"] < 1:
        errors.append("independent analyzer proof missing custom check findings")
    if proof["governance_unclassified_findings"] != 0:
        errors.append("independent analyzer proof has unclassified governance findings")
    if proof["governance_classified_findings"] < 1:
        errors.append("independent analyzer proof missing classified governance findings")
    if not proof["assembly_parity_success"]:
        errors.append("assembly parity report must remain successful for engine-boundary readback")
    if not errors and DEFAULT_ASSEMBLY_REPORT.as_posix() in loaded:
        warnings.append("Windows PowerShell 5.1 runtime evidence remains separate from local static report generation")
    return report_facts, errors, warnings, proof


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# PowerShell Engine and Pester Boundary Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Issue: `#{report['issue']}`",
        f"- Validation: `{'pass' if report['validation']['success'] else 'fail'}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Matrix rows | {summary['matrix_row_count']} |",
        f"| Required categories covered | {summary['required_category_count']} / {summary['expected_required_category_count']} |",
        f"| Dependency reports | {summary['dependency_report_count']} |",
        f"| Declared output artifacts | {summary['declared_output_artifact_count']} |",
        f"| Missing blocking output artifacts | {summary['missing_blocking_output_artifact_count']} |",
        f"| Unclaimed blocking output artifacts | {summary['unclaimed_blocking_output_artifact_count']} |",
        f"| Pester blocking for static validation | `{summary['pester_blocking_for_static_validation']}` |",
        f"| Independent enforcement requires Pester | `{summary['independent_enforcement_requires_pester']}` |",
        "",
        "## Engine Matrix",
        "",
        "| Check | Engine | Runner | Evidence | Blocking | Owner |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["engine_matrix"]:
        lines.append(
            "| `{id}` | {engine} | {runner} | {evidence} | `{blocking}` | {owner} |".format(
                id=row["id"],
                engine=row["required_engine"],
                runner=row["runner_os"],
                evidence=row["evidence_type"],
                blocking=row["blocking"],
                owner=row["owner"],
            )
        )
    lines.extend(
        [
            "",
            "## Declared Output Artifacts",
            "",
            "| Check | Artifact | Repo path | Exists | Claimed by #267 boundary | Status |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for artifact in report["declared_output_artifacts"]:
        lines.append(
            "| `{id}` | `{path}` | `{repo_path}` | `{exists}` | `{claimed}` | `{status}` |".format(
                id=artifact["id"],
                path=artifact["path"],
                repo_path=artifact["repo_path"],
                exists=artifact["exists"],
                claimed=artifact["evidence_claimed_by_boundary"],
                status=artifact["artifact_status"],
            )
        )
    lines.extend(
        [
            "",
            "## Pester Boundary",
            "",
            f"- Decision: `{report['pester_boundary']['scope_decision']}`",
            f"- Static-security blocking: `{report['pester_boundary']['blocking_for_static_security_validation']}`",
            f"- Analyzer/custom-check substitute: `{report['pester_boundary']['pester_may_replace_analyzer_or_custom_checks']}`",
            "",
            "## Independent Analyzer Enforcement Proof",
            "",
            "| Proof | Count/State |",
            "| --- | ---: |",
        ]
    )
    proof = report["independent_analyzer_enforcement_proof"]
    lines.extend(
        [
            f"| Rule-risk fixture findings | {proof['rule_risk_fixture_findings']} |",
            f"| Custom-check findings | {proof['custom_check_findings']} |",
            f"| Governance classified findings | {proof['governance_classified_findings']} |",
            f"| Governance unclassified findings | {proof['governance_unclassified_findings']} |",
            f"| Assembly parity success | `{proof['assembly_parity_success']}` |",
            f"| Requires Pester | `{proof['requires_pester']}` |",
            "",
            "## Dependency Reports",
            "",
            "| Report | Schema | Success | Findings |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for dependency in report["dependency_reports"]:
        lines.append(
            f"| `{dependency['path']}` | `{dependency['schema_version']}` | `{dependency['success']}` | {dependency['finding_count']} |"
        )
    if report["validation"]["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in report["validation"]["warnings"]:
            lines.append(f"- {warning}")
    if report["validation"]["errors"]:
        lines.extend(["", "## Errors", ""])
        for error in report["validation"]["errors"]:
            lines.append(f"- {error}")
    lines.append("")
    return "\n".join(lines)


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any], list[str], list[str]]:
    repo_root = Path(args.repo_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    try:
        boundary = read_json(repo_root / args.boundary, "PowerShell engine/Pester boundary")
    except EngineBoundaryError as exc:
        boundary = {}
        errors.append(str(exc))
    if not isinstance(boundary, dict):
        errors.append("PowerShell engine/Pester boundary must be a JSON object")
        boundary = {}

    boundary_errors, boundary_warnings, metadata = validate_boundary_doc(boundary)
    errors.extend(boundary_errors)
    warnings.extend(boundary_warnings)

    source_reports = metadata.get("source_reports", [])
    dependency_reports, dependency_errors, dependency_warnings, proof_counts = validate_source_reports(
        repo_root,
        [str(path) for path in source_reports],
        [Path(path) for path in args.extra_report],
    )
    errors.extend(dependency_errors)
    warnings.extend(dependency_warnings)

    matrix_rows = metadata.get("matrix_rows", [])
    output_artifacts, artifact_errors, artifact_warnings = declared_output_artifacts(repo_root, matrix_rows)
    errors.extend(artifact_errors)
    warnings.extend(artifact_warnings)
    pester = boundary.get("pester_boundary", {}) if isinstance(boundary.get("pester_boundary"), dict) else {}
    policy = boundary.get("policy", {}) if isinstance(boundary.get("policy"), dict) else {}
    required_categories_covered = {
        scalar(row.get("check_category")).strip()
        for row in matrix_rows
        if scalar(row.get("check_category")).strip() in REQUIRED_CHECK_CATEGORIES
    }
    missing_blocking_artifacts = [
        artifact
        for artifact in output_artifacts
        if artifact["repo_path"] and artifact["blocking"] is True and artifact["exists"] is False
    ]
    unclaimed_blocking_artifacts = [
        artifact
        for artifact in output_artifacts
        if artifact["blocking"] is True and artifact["evidence_claimed_by_boundary"] is False
    ]
    proof = dict(proof_counts)
    proof["requires_pester"] = bool(
        isinstance(boundary.get("independent_analyzer_enforcement_proof"), dict)
        and boundary["independent_analyzer_enforcement_proof"].get("requires_pester") is True
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "parent_issue": PARENT_ISSUE_NUMBER,
        "boundary_policy_path": safe_repo_path(repo_root / args.boundary, repo_root),
        "summary": {
            "matrix_row_count": len(matrix_rows),
            "required_category_count": len(required_categories_covered),
            "expected_required_category_count": len(REQUIRED_CHECK_CATEGORIES),
            "dependency_report_count": len(dependency_reports),
            "pester_blocking_for_static_validation": pester.get("blocking_for_static_security_validation"),
            "independent_enforcement_requires_pester": proof["requires_pester"],
            "workflow_readiness_claimed": policy.get("workflow_readiness_claimed"),
            "declared_output_artifact_count": len(output_artifacts),
            "missing_blocking_output_artifact_count": len(missing_blocking_artifacts),
            "unclaimed_blocking_output_artifact_count": len(unclaimed_blocking_artifacts),
        },
        "engine_matrix": matrix_rows,
        "declared_output_artifacts": output_artifacts,
        "pester_boundary": {
            "scope_decision": scalar(pester.get("scope_decision")).strip(),
            "blocking_for_static_security_validation": pester.get("blocking_for_static_security_validation"),
            "pester_may_replace_analyzer_or_custom_checks": policy.get(
                "pester_may_replace_analyzer_or_custom_checks"
            ),
            "required_evidence_when_used": pester.get("required_evidence_when_used", []),
            "owned_responsibilities": pester.get("owned_responsibilities", []),
        },
        "independent_analyzer_enforcement_proof": proof,
        "dependency_reports": dependency_reports,
        "validation": {
            "success": not errors,
            "errors": errors,
            "warnings": warnings,
        },
    }
    return report, errors, warnings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--boundary", default=DEFAULT_BOUNDARY.as_posix())
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix())
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix())
    parser.add_argument(
        "--extra-report",
        action="append",
        default=[DEFAULT_ASSEMBLY_REPORT.as_posix()],
        help="Additional dependency report to read and summarize.",
    )
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report, errors, _warnings = build_report(args)
    repo_root = Path(args.repo_root).resolve()
    if not args.no_write:
        write_json(repo_root / args.json_output, report)
        markdown = build_markdown(report)
        markdown_path = repo_root / args.markdown_output
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "schema_version": report["schema_version"],
                "matrix_row_count": report["summary"]["matrix_row_count"],
                "required_category_count": report["summary"]["required_category_count"],
                "dependency_report_count": report["summary"]["dependency_report_count"],
                "missing_blocking_output_artifact_count": report["summary"][
                    "missing_blocking_output_artifact_count"
                ],
                "unclaimed_blocking_output_artifact_count": report["summary"][
                    "unclaimed_blocking_output_artifact_count"
                ],
                "rule_risk_fixture_findings": report["independent_analyzer_enforcement_proof"][
                    "rule_risk_fixture_findings"
                ],
                "custom_check_findings": report["independent_analyzer_enforcement_proof"][
                    "custom_check_findings"
                ],
                "governance_classified_findings": report["independent_analyzer_enforcement_proof"][
                    "governance_classified_findings"
                ],
                "pester_blocking_for_static_validation": report["summary"][
                    "pester_blocking_for_static_validation"
                ],
                "success": report["validation"]["success"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
