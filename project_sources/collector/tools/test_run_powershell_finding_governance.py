#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_powershell_finding_governance as governance


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finding(
    *,
    path: str = "project_sources/collector/fixtures/powershell_analysis/bad/example.ps1",
    rule_name: str = "DCOIR.Example",
    check_id: str = "dcoir-example",
    severity: str = "Error",
    fingerprint: str = "finding-fingerprint-1",
) -> dict[str, object]:
    return {
        "path": path,
        "line": 1,
        "column": 1,
        "rule_name": rule_name,
        "check_id": check_id,
        "severity": severity,
        "observed_problem": "Example problem.",
        "recommended_fix": "Fix the example problem.",
        "fingerprint": fingerprint,
    }


def baseline_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": "baseline-example-1",
        "decision": "baseline-temporary",
        "path": "project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1",
        "line": 10,
        "rule_name": "DCOIR.Example",
        "severity": "Error",
        "fingerprint": "finding-fingerprint-1",
        "rationale": "Temporary baseline pending remediation.",
        "owner": "DCOIR Collector maintainers",
        "reviewer": "DCOIR operator",
        "review_date": "2026-06-10",
        "expires_on": "2026-12-31",
        "expected_match_count": 1,
    }
    record.update(overrides)
    return record


def suppression_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": "suppression-example-1",
        "decision": "accepted risk",
        "path": "project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1",
        "line": 10,
        "scope": "line",
        "rule_name": "DCOIR.Example",
        "severity": "Error",
        "fingerprint": "finding-fingerprint-1",
        "rationale": "Reviewed local suppression.",
        "owner": "DCOIR Collector maintainers",
        "reviewer": "DCOIR operator",
        "review_date": "2026-06-10",
        "expires_on": "2026-12-31",
        "expected_match_count": 1,
    }
    record.update(overrides)
    return record


class PowerShellFindingGovernanceTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        report_findings: list[dict[str, object]] | None = None,
        governance_overrides: dict[str, object] | None = None,
        write_analyzer_report: bool = True,
    ) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        finding_report = {
            "schema_version": "dcoir_powershell_custom_check_report_v1",
            "findings": report_findings if report_findings is not None else [finding()],
            "validation": {"success": True, "errors": [], "warnings": []},
            "summary": {"finding_count": len(report_findings if report_findings is not None else [finding()])},
        }
        rule_risk_report = {
            "schema_version": "dcoir_powershell_rule_risk_fixture_report_v1",
            "findings": [],
            "validation": {"success": True, "errors": [], "warnings": []},
            "summary": {"finding_count": 0},
        }
        analyzer_report = {
            "schema_version": "dcoir_powershell_analyzer_report_v1",
            "findings": [],
            "validation": {"success": True, "errors": [], "warnings": []},
            "summary": {"finding_count": 0},
        }
        assembly_report = {
            "schema_version": "dcoir_powershell_assembly_parity_report_v1",
            "validation": {"success": True, "errors": [], "warnings": []},
            "generated_outputs": [
                {"id": "collector_compiled_runtime", "path": "compiled_runtime/DCOIR_Collector.ps1"}
            ],
        }
        governance_doc: dict[str, object] = {
            "schema_version": governance.GOVERNANCE_SCHEMA_VERSION,
            "issue": governance.ISSUE_NUMBER,
            "policy": {
                "allowed_decisions": sorted(governance.ALLOWED_DECISIONS),
                "max_baseline_records": 10,
            },
            "classification_rules": [
                {
                    "id": "fixture-findings",
                    "decision": "advisory",
                    "path_prefixes": ["project_sources/collector/fixtures/powershell_analysis/"],
                    "rationale": "Fixtures are advisory control evidence.",
                    "owner": "DCOIR Collector maintainers",
                    "reviewer": "DCOIR operator",
                    "review_date": "2026-06-10",
                    "revisit_condition": "Before workflow gating.",
                }
            ],
            "baseline_records": [],
            "suppressions": [],
            "approved_delta_exceptions": [],
            "control_proofs": [],
        }
        if governance_overrides:
            governance_doc.update(governance_overrides)
        write(root / governance.DEFAULT_CUSTOM_REPORT, json.dumps(finding_report, indent=2) + "\n")
        write(root / governance.DEFAULT_RULE_RISK_REPORT, json.dumps(rule_risk_report, indent=2) + "\n")
        if write_analyzer_report:
            write(root / governance.DEFAULT_ANALYZER_REPORT, json.dumps(analyzer_report, indent=2) + "\n")
        write(root / governance.DEFAULT_ASSEMBLY_PARITY_REPORT, json.dumps(assembly_report, indent=2) + "\n")
        write(root / governance.DEFAULT_GOVERNANCE, json.dumps(governance_doc, indent=2) + "\n")
        return temp

    def args(self, root: Path, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "repo_root": str(root),
            "governance": governance.DEFAULT_GOVERNANCE.as_posix(),
            "finding_report": [],
            "optional_finding_report": [],
            "assembly_parity_report": governance.DEFAULT_ASSEMBLY_PARITY_REPORT.as_posix(),
            "json_output": governance.DEFAULT_JSON_OUTPUT.as_posix(),
            "markdown_output": governance.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
            "as_of_date": "2026-06-10",
            "allow_missing_analyzer_report": False,
            "no_write": True,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_default_missing_analyzer_report_fails_closed(self) -> None:
        with self.make_repo(write_analyzer_report=False) as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("powershell_analyzer_report.json" in error for error in errors))

    def test_custom_required_reports_still_require_analyzer_without_opt_out(self) -> None:
        with self.make_repo(write_analyzer_report=False) as temp:
            report, errors, _warnings = governance.build_report(
                self.args(
                    Path(temp),
                    finding_report=[governance.DEFAULT_CUSTOM_REPORT.as_posix()],
                )
            )

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("powershell_analyzer_report.json" in error for error in errors))

    def test_missing_analyzer_report_requires_explicit_opt_out(self) -> None:
        with self.make_repo(write_analyzer_report=False) as temp:
            report, errors, warnings = governance.build_report(
                self.args(Path(temp), allow_missing_analyzer_report=True)
            )

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertTrue(any("powershell_analyzer_report.json" in warning for warning in warnings))
        analyzer_input = next(
            item
            for item in report["input_reports"]
            if item["path"] == governance.DEFAULT_ANALYZER_REPORT.as_posix()
        )
        self.assertFalse(analyzer_input["required"])
        self.assertFalse(analyzer_input["present"])

    def test_fixture_classification_passes(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["finding_count"], 1)
        self.assertEqual(report["summary"]["decision_counts"], {"advisory": 1})

    def test_new_finding_without_classification_fails_closed(self) -> None:
        source_finding = finding(path="project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1")
        with self.make_repo(report_findings=[source_finding]) as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("new unclassified PowerShell finding" in error for error in errors))

    def test_baseline_record_classifies_source_finding(self) -> None:
        source_finding = finding(path="project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1")
        with self.make_repo(
            report_findings=[source_finding],
            governance_overrides={"baseline_records": [baseline_record()]},
        ) as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["decision_counts"], {"baseline-temporary": 1})

    def test_malformed_baseline_fails_closed(self) -> None:
        bad_record = baseline_record()
        bad_record.pop("fingerprint")
        with self.make_repo(governance_overrides={"baseline_records": [bad_record]}) as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("missing fingerprint" in error for error in errors))

    def test_severity_increase_fails_closed(self) -> None:
        source_finding = finding(
            path="project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1",
            severity="Error",
        )
        record = baseline_record(severity="Warning")
        with self.make_repo(
            report_findings=[source_finding],
            governance_overrides={"baseline_records": [record]},
        ) as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("severity increase" in error for error in errors))

    def test_unexpected_baseline_disappearance_fails_closed(self) -> None:
        with self.make_repo(report_findings=[], governance_overrides={"baseline_records": [baseline_record()]}) as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("unexpected disappearance" in error for error in errors))

    def test_blanket_suppression_fails_closed(self) -> None:
        suppression = suppression_record(path="*", rule_name="PS*")
        with self.make_repo(governance_overrides={"suppressions": [suppression]}) as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("blanket or wildcard path" in error for error in errors))
        self.assertTrue(any("blanket or wildcard rule" in error for error in errors))

    def test_generated_output_suppression_requires_assembly_coverage(self) -> None:
        suppression = suppression_record(
            path="compiled_runtime/DCOIR_Collector.ps1",
            target_kind="generated_output",
        )
        with self.make_repo(governance_overrides={"suppressions": [suppression]}) as temp:
            report, errors, _warnings = governance.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("#265 assembly coverage" in error for error in errors))

    def test_real_repo_contract_passes(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        report, errors, _warnings = governance.build_report(
            self.args(repo_root, allow_missing_analyzer_report=True)
        )

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["finding_count"], 22)
        self.assertEqual(report["summary"]["unclassified_finding_count"], 0)
        self.assertEqual(report["summary"]["decision_counts"], {"advisory": 22})
        self.assertEqual(report["summary"]["baseline_record_count"], 0)
        self.assertEqual(report["summary"]["suppression_count"], 0)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
