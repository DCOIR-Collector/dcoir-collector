#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_powershell_engine_pester_boundary as boundary


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def matrix_row(check_category: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "id": check_category,
        "check_category": check_category,
        "required_engine": "python-3.12",
        "runner_os": "any",
        "module_or_tool_dependency": "standard-library",
        "evidence_type": "json-report",
        "output_artifact": f"artifact/{check_category}.json",
        "blocking": True,
        "owner": "#267-test",
        "boundary": "test boundary",
    }
    row.update(overrides)
    return row


def good_boundary_doc() -> dict[str, object]:
    rows = [matrix_row(category) for category in sorted(boundary.REQUIRED_CHECK_CATEGORIES)]
    for row in rows:
        if row["check_category"] == "windows_powershell_51_parser_runtime_compatibility":
            row["required_engine"] = "Windows PowerShell 5.1 Desktop"
            row["runner_os"] = "windows-latest"
        if row["check_category"] == "powershell_7_static_analyzer":
            row["required_engine"] = "PowerShell 7 Core"
            row["module_or_tool_dependency"] = "PSScriptAnalyzer"
        if row["check_category"] == "pester_supporting_tests":
            row["required_engine"] = "PowerShell 7 Core or Windows PowerShell 5.1 Desktop as declared by the owning test"
            row["runner_os"] = "windows-latest when Windows PowerShell 5.1 behavior is asserted; otherwise any runner with declared engine"
            row["module_or_tool_dependency"] = "Pester"
            row["blocking"] = False
    return {
        "schema_version": boundary.BOUNDARY_SCHEMA_VERSION,
        "issue": boundary.ISSUE_NUMBER,
        "parent_issue": boundary.PARENT_ISSUE_NUMBER,
        "policy": {
            "workflow_readiness_claimed": False,
            "pester_may_replace_analyzer_or_custom_checks": False,
            "engine_evidence_must_be_separate": True,
            "independent_analyzer_enforcement_required": True,
        },
        "engine_matrix": rows,
        "pester_boundary": {
            "scope_decision": "supporting-in-scope-not-analyzer-substitute",
            "blocking_for_static_security_validation": False,
            "must_not_replace": [
                "#262 analyzer wrapper enforcement",
                "#264 DCOIR custom checks",
            ],
            "required_evidence_when_used": sorted(boundary.PESTER_EVIDENCE_FIELDS),
            "owned_responsibilities": [
                {
                    "surface": "wrapper tests",
                    "owner": "future gate",
                    "blocking": False,
                    "notes": "test responsibility",
                }
            ],
        },
        "independent_analyzer_enforcement_proof": {
            "requires_pester": False,
            "source_reports": [
                boundary.DEFAULT_RULE_RISK_REPORT.as_posix(),
                boundary.DEFAULT_CUSTOM_REPORT.as_posix(),
                boundary.DEFAULT_GOVERNANCE_REPORT.as_posix(),
            ],
            "required_conditions": ["proof exists"],
        },
    }


def write_reports(root: Path, *, custom_findings: int = 1, rule_findings: int = 1, unclassified: int = 0) -> None:
    write(
        root / boundary.DEFAULT_RULE_RISK_REPORT,
        json.dumps(
            {
                "schema_version": "dcoir_powershell_rule_risk_fixture_report_v1",
                "validation": {"success": True, "errors": [], "warnings": []},
                "summary": {"observed_finding_count": rule_findings, "finding_count": rule_findings},
            },
            indent=2,
        )
        + "\n",
    )
    write(
        root / boundary.DEFAULT_CUSTOM_REPORT,
        json.dumps(
            {
                "schema_version": "dcoir_powershell_custom_check_report_v1",
                "validation": {"success": True, "errors": [], "warnings": []},
                "summary": {"finding_count": custom_findings},
            },
            indent=2,
        )
        + "\n",
    )
    write(
        root / boundary.DEFAULT_GOVERNANCE_REPORT,
        json.dumps(
            {
                "schema_version": "dcoir_powershell_finding_governance_report_v1",
                "validation": {"success": True, "errors": [], "warnings": []},
                "summary": {
                    "classified_finding_count": custom_findings + rule_findings,
                    "unclassified_finding_count": unclassified,
                    "finding_count": custom_findings + rule_findings,
                },
            },
            indent=2,
        )
        + "\n",
    )
    write(
        root / boundary.DEFAULT_ASSEMBLY_REPORT,
        json.dumps(
            {
                "schema_version": "dcoir_powershell_assembly_parity_report_v1",
                "validation": {"success": True, "errors": [], "warnings": []},
                "summary": {"finding_count": 0},
            },
            indent=2,
        )
        + "\n",
    )


class PowerShellEnginePesterBoundaryTests(unittest.TestCase):
    def make_repo(self, doc: dict[str, object] | None = None, **report_overrides: int) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / boundary.DEFAULT_BOUNDARY, json.dumps(doc or good_boundary_doc(), indent=2) + "\n")
        write_reports(root, **report_overrides)
        return temp

    def args(self, root: Path, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "repo_root": str(root),
            "boundary": boundary.DEFAULT_BOUNDARY.as_posix(),
            "json_output": boundary.DEFAULT_JSON_OUTPUT.as_posix(),
            "markdown_output": boundary.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
            "extra_report": [boundary.DEFAULT_ASSEMBLY_REPORT.as_posix()],
            "no_write": True,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_control_boundary_passes(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["required_category_count"], len(boundary.REQUIRED_CHECK_CATEGORIES))
        self.assertFalse(report["summary"]["pester_blocking_for_static_validation"])
        self.assertFalse(report["independent_analyzer_enforcement_proof"]["requires_pester"])

    def test_missing_windows_51_category_fails_closed(self) -> None:
        doc = good_boundary_doc()
        doc["engine_matrix"] = [
            row
            for row in doc["engine_matrix"]  # type: ignore[index]
            if row["check_category"] != "windows_powershell_51_parser_runtime_compatibility"
        ]
        with self.make_repo(doc) as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("engine_matrix missing categories" in error for error in errors))

    def test_ambiguous_engine_fails_closed(self) -> None:
        doc = good_boundary_doc()
        rows = doc["engine_matrix"]  # type: ignore[assignment]
        rows[0]["required_engine"] = "pwsh"  # type: ignore[index]
        with self.make_repo(doc) as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("ambiguous engine" in error for error in errors))

    def test_pester_cannot_replace_analyzer_or_custom_checks(self) -> None:
        doc = good_boundary_doc()
        doc["policy"]["pester_may_replace_analyzer_or_custom_checks"] = True  # type: ignore[index]
        with self.make_repo(doc) as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("Pester must not be allowed" in error for error in errors))

    def test_missing_pester_evidence_requirement_fails_closed(self) -> None:
        doc = good_boundary_doc()
        doc["pester_boundary"]["required_evidence_when_used"] = ["Pester version"]  # type: ignore[index]
        with self.make_repo(doc) as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("required_evidence_when_used missing" in error for error in errors))

    def test_independent_proof_cannot_require_pester(self) -> None:
        doc = good_boundary_doc()
        doc["independent_analyzer_enforcement_proof"]["requires_pester"] = True  # type: ignore[index]
        with self.make_repo(doc) as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("must not require Pester" in error for error in errors))

    def test_missing_dependency_report_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            (root / boundary.DEFAULT_CUSTOM_REPORT).unlink()
            report, errors, _warnings = boundary.build_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("dependency report missing" in error for error in errors))

    def test_dependency_report_requires_explicit_validation_success(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report_path = root / boundary.DEFAULT_CUSTOM_REPORT
            dependency = json.loads(report_path.read_text(encoding="utf-8"))
            dependency["validation"] = {"errors": [], "warnings": []}
            write(report_path, json.dumps(dependency, indent=2) + "\n")
            report, errors, _warnings = boundary.build_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("missing explicit validation.success or top-level success" in error for error in errors))

    def test_dependency_report_accepts_documented_top_level_success(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report_path = root / boundary.DEFAULT_CUSTOM_REPORT
            dependency = json.loads(report_path.read_text(encoding="utf-8"))
            dependency.pop("validation", None)
            dependency["success"] = True
            write(report_path, json.dumps(dependency, indent=2) + "\n")
            report, errors, _warnings = boundary.build_report(self.args(root))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        custom_fact = next(
            fact
            for fact in report["dependency_reports"]
            if fact["path"] == boundary.DEFAULT_CUSTOM_REPORT.as_posix()
        )
        self.assertTrue(custom_fact["success"])

    def test_dependency_report_rejects_non_boolean_validation_success(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report_path = root / boundary.DEFAULT_CUSTOM_REPORT
            dependency = json.loads(report_path.read_text(encoding="utf-8"))
            dependency["validation"]["success"] = "true"
            dependency["success"] = True
            write(report_path, json.dumps(dependency, indent=2) + "\n")
            report, errors, _warnings = boundary.build_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("validation.success must be boolean true" in error for error in errors))

    def test_missing_blocking_repo_artifact_fails_without_explicit_status(self) -> None:
        doc = good_boundary_doc()
        rows = doc["engine_matrix"]  # type: ignore[assignment]
        rows[0]["output_artifact"] = "project_sources/collector/missing-report.json"  # type: ignore[index]
        with self.make_repo(doc) as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("blocking engine matrix artifact missing" in error for error in errors))

    def test_explicit_not_committed_artifact_is_not_claimed_boundary_evidence(self) -> None:
        doc = good_boundary_doc()
        rows = doc["engine_matrix"]  # type: ignore[assignment]
        rows[0]["output_artifact"] = "project_sources/collector/missing-report.json"  # type: ignore[index]
        rows[0]["artifact_status"] = "not_committed_in_267_boundary"  # type: ignore[index]
        with self.make_repo(doc) as temp:
            report, errors, warnings = boundary.build_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertTrue(any("not committed or claimed" in warning for warning in warnings))
        artifact = report["declared_output_artifacts"][0]
        self.assertFalse(artifact["exists"])
        self.assertFalse(artifact["evidence_claimed_by_boundary"])
        self.assertEqual(artifact["artifact_status"], "not_committed_in_267_boundary")

    def test_custom_finding_proof_is_required(self) -> None:
        with self.make_repo(custom_findings=0) as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("missing custom check findings" in error for error in errors))

    def test_governance_unclassified_findings_fail_closed(self) -> None:
        with self.make_repo(unclassified=1) as temp:
            report, errors, _warnings = boundary.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("unclassified governance findings" in error for error in errors))


if __name__ == "__main__":
    raise SystemExit(unittest.main())
