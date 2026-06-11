#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_powershell_custom_checks as custom


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def surface(path: str) -> dict[str, object]:
    return {
        "path": path,
        "category": "fixture_or_example",
        "source_type": ".ps1",
        "status": "fixture",
        "inclusion_decision": "include",
        "decision_reason": "test fixture",
        "exists": True,
        "marker_lines": [],
        "embedded_snippets": [],
        "size_bytes": 20,
        "line_count": 1,
        "sha256": "",
    }


class PowerShellCustomCheckTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        bad_text: str = '$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }\n',
        good_text: str = '$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }\nthrow "failed"\n',
        expected_line: int = 1,
        matrix_rule_name: str = "DCOIR.FailOutputMustFailValidation",
        omit_good_from_inventory: bool = False,
    ) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        bad_path = "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1"
        good_path = "project_sources/collector/fixtures/powershell_analysis/good/custom_fail_row_fails_command.ps1"
        write(root / bad_path, bad_text)
        write(root / good_path, good_text)
        matrix = {
            "schema_version": custom.MATRIX_SCHEMA_VERSION,
            "issue": 263,
            "checks": [
                {
                    "id": "dcoir-fail-output-must-fail",
                    "rule_name": matrix_rule_name,
                    "blocking": True,
                    "expected_severity": "Error",
                    "risk_classes": ["fail_rows_reports_or_fixture_outputs_not_causing_failure"],
                }
            ],
        }
        checks = {
            "schema_version": custom.CHECKS_SCHEMA_VERSION,
            "issue": custom.ISSUE_NUMBER,
            "checks": [
                {
                    "id": "dcoir-fail-output-must-fail",
                    "rule_name": "DCOIR.FailOutputMustFailValidation",
                    "matrix_check_id": "dcoir-fail-output-must-fail",
                    "expected_severity": "Error",
                    "risk_classes": ["fail_rows_reports_or_fixture_outputs_not_causing_failure"],
                    "target_surfaces": ["validation tooling"],
                    "intent": "FAIL rows must fail the command.",
                    "target": "Validation report scripts.",
                    "detection": "Find FAIL rows without a fail-closed path.",
                    "limitations": "Fixture-level static detection only.",
                    "false_positive_controls": ["Allows throw or nonzero exit."],
                    "failure_impact": "A FAIL report can exit green.",
                    "recommended_fix": "Throw or exit nonzero when FAIL rows are emitted.",
                }
            ],
        }
        manifest = {
            "schema_version": custom.FIXTURE_MANIFEST_SCHEMA_VERSION,
            "issue": custom.ISSUE_NUMBER,
            "fixtures": [
                {
                    "id": "bad-fail-row-green-exit",
                    "kind": "negative",
                    "check_id": "dcoir-fail-output-must-fail",
                    "path": bad_path,
                    "description": "Bad fixture.",
                    "expected_findings": [
                        {
                            "check_id": "dcoir-fail-output-must-fail",
                            "rule_name": "DCOIR.FailOutputMustFailValidation",
                            "severity": "Error",
                            "line": expected_line,
                            "risk_class": "fail_rows_reports_or_fixture_outputs_not_causing_failure",
                        }
                    ],
                },
                {
                    "id": "good-fail-row-fails-command",
                    "kind": "control",
                    "check_id": "dcoir-fail-output-must-fail",
                    "path": good_path,
                    "description": "Good fixture.",
                    "expected_findings": [],
                },
            ],
        }
        surfaces = [surface(bad_path)]
        if not omit_good_from_inventory:
            surfaces.append(surface(good_path))
        inventory = {
            "schema_version": custom.INVENTORY_SCHEMA_VERSION,
            "issue": 261,
            "summary": {"total_surfaces": len(surfaces)},
            "validation": {"success": True, "errors": [], "warnings": []},
            "surfaces": surfaces,
        }
        write(root / custom.DEFAULT_MATRIX, json.dumps(matrix, indent=2) + "\n")
        write(root / custom.DEFAULT_CHECKS, json.dumps(checks, indent=2) + "\n")
        write(root / custom.DEFAULT_FIXTURE_MANIFEST, json.dumps(manifest, indent=2) + "\n")
        write(root / custom.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
        return temp

    def args(self, root: Path, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "repo_root": str(root),
            "checks": custom.DEFAULT_CHECKS.as_posix(),
            "matrix": custom.DEFAULT_MATRIX.as_posix(),
            "inventory": custom.DEFAULT_INVENTORY.as_posix(),
            "fixture_manifest": custom.DEFAULT_FIXTURE_MANIFEST.as_posix(),
            "json_output": custom.DEFAULT_JSON_OUTPUT.as_posix(),
            "markdown_output": custom.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
            "target_scope": "fixtures",
            "target_path": [],
            "fail_on_severity": "Warning",
            "allow_findings": False,
            "no_write": True,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_fixture_report_passes_and_has_normalized_fields(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = custom.build_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["custom_check_count"], 1)
        self.assertEqual(report["summary"]["negative_fixture_count"], 1)
        self.assertEqual(report["summary"]["control_fixture_count"], 1)
        self.assertEqual(report["summary"]["expected_fixture_finding_count"], 1)
        self.assertEqual(report["summary"]["observed_fixture_finding_count"], 1)
        finding = report["findings"][0]
        for key in ("check_id", "risk_class", "path", "severity", "observed_problem", "impact", "fix"):
            self.assertIn(key, finding)

    def test_bad_fixture_must_trigger(self) -> None:
        with self.make_repo(bad_text='Write-Output "all clear"\n') as temp:
            report, errors, _warnings = custom.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("was not produced" in error for error in errors))

    def test_control_fixture_must_stay_clean(self) -> None:
        with self.make_repo(good_text='$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }\n') as temp:
            report, errors, _warnings = custom.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("control fixture produced unexpected findings" in error for error in errors))

    def test_missing_fixture_from_inventory_fails_closed(self) -> None:
        with self.make_repo(omit_good_from_inventory=True) as temp:
            report, errors, _warnings = custom.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("missing from PowerShell surface inventory" in error for error in errors))

    def test_matrix_mapping_mismatch_fails_closed(self) -> None:
        with self.make_repo(matrix_rule_name="DCOIR.OtherRule") as temp:
            report, errors, _warnings = custom.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("rule_name does not match #263 matrix" in error for error in errors))

    def test_missing_input_file_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            (root / custom.DEFAULT_CHECKS).unlink()
            report, errors, _warnings = custom.build_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("custom checks missing" in error for error in errors))

    def test_real_custom_contract_has_negative_and_control_for_each_check(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        report, errors, _warnings = custom.build_report(self.args(repo_root))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["custom_check_count"], 8)
        self.assertEqual(report["summary"]["negative_fixture_count"], 8)
        self.assertEqual(report["summary"]["control_fixture_count"], 8)
        self.assertEqual(report["summary"]["expected_fixture_finding_count"], 8)
        self.assertEqual(report["summary"]["observed_fixture_finding_count"], 8)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
