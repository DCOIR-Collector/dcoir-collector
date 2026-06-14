#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
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


class PowerShellCustomCheckReviewThreadTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        check_id: str,
        rule_name: str,
        risk_class: str,
        bad_text: str,
        good_text: str,
        expected_line: int = 1,
    ) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        bad_path = "project_sources/collector/fixtures/powershell_analysis/bad/review_thread_bad.ps1"
        good_path = "project_sources/collector/fixtures/powershell_analysis/good/review_thread_good.ps1"
        write(root / bad_path, bad_text)
        write(root / good_path, good_text)
        matrix = {
            "schema_version": custom.MATRIX_SCHEMA_VERSION,
            "issue": 263,
            "checks": [
                {
                    "id": check_id,
                    "rule_name": rule_name,
                    "blocking": True,
                    "expected_severity": "Error",
                    "risk_classes": [risk_class],
                }
            ],
        }
        checks = {
            "schema_version": custom.CHECKS_SCHEMA_VERSION,
            "issue": custom.ISSUE_NUMBER,
            "checks": [
                {
                    "id": check_id,
                    "rule_name": rule_name,
                    "matrix_check_id": check_id,
                    "expected_severity": "Error",
                    "risk_classes": [risk_class],
                    "target_surfaces": ["validation tooling"],
                    "intent": "Review regression fixture.",
                    "target": "Validation report scripts.",
                    "detection": "Review regression fixture detection.",
                    "limitations": "Fixture-level static detection only.",
                    "false_positive_controls": ["Allows explicit fail-closed handling."],
                    "failure_impact": "Review regression can pass validation incorrectly.",
                    "recommended_fix": "Fail closed on the reviewed pattern.",
                }
            ],
        }
        manifest = {
            "schema_version": custom.FIXTURE_MANIFEST_SCHEMA_VERSION,
            "issue": custom.ISSUE_NUMBER,
            "fixtures": [
                {
                    "id": "review-thread-bad",
                    "kind": "negative",
                    "check_id": check_id,
                    "path": bad_path,
                    "description": "Negative review regression fixture.",
                    "expected_findings": [
                        {
                            "check_id": check_id,
                            "rule_name": rule_name,
                            "severity": "Error",
                            "line": expected_line,
                            "risk_class": risk_class,
                        }
                    ],
                },
                {
                    "id": "review-thread-good",
                    "kind": "control",
                    "check_id": check_id,
                    "path": good_path,
                    "description": "Control review regression fixture.",
                    "expected_findings": [],
                },
            ],
        }
        inventory = {
            "schema_version": custom.INVENTORY_SCHEMA_VERSION,
            "issue": 261,
            "summary": {"total_surfaces": 2},
            "validation": {"success": True, "errors": [], "warnings": []},
            "surfaces": [surface(bad_path), surface(good_path)],
        }
        write(root / custom.DEFAULT_MATRIX, json.dumps(matrix, indent=2) + "\n")
        write(root / custom.DEFAULT_CHECKS, json.dumps(checks, indent=2) + "\n")
        write(root / custom.DEFAULT_FIXTURE_MANIFEST, json.dumps(manifest, indent=2) + "\n")
        write(root / custom.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
        return temp

    def args(self, root: Path) -> argparse.Namespace:
        return argparse.Namespace(
            repo_root=str(root),
            checks=custom.DEFAULT_CHECKS.as_posix(),
            matrix=custom.DEFAULT_MATRIX.as_posix(),
            inventory=custom.DEFAULT_INVENTORY.as_posix(),
            fixture_manifest=custom.DEFAULT_FIXTURE_MANIFEST.as_posix(),
            json_output=custom.DEFAULT_JSON_OUTPUT.as_posix(),
            markdown_output=custom.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
            target_scope="fixtures",
            target_path=[],
            fail_on_severity="Warning",
            allow_findings=False,
            no_write=True,
        )

    def test_absolute_custom_fixture_path_fails_before_normalization(self) -> None:
        with self.make_repo(
            check_id="dcoir-fail-output-must-fail",
            rule_name="DCOIR.FailOutputMustFailValidation",
            risk_class="fail_rows_reports_or_fixture_outputs_not_causing_failure",
            bad_text='$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }\n',
            good_text='$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }\nthrow "failed"\n',
        ) as temp:
            root = Path(temp)
            manifest_path = root / custom.DEFAULT_FIXTURE_MANIFEST
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["fixtures"][0]["path"] = "/" + manifest["fixtures"][0]["path"]
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")

            report, errors, _warnings = custom.build_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertEqual(report["summary"]["target_count"], 0)
        self.assertTrue(any("path must be a repo-relative path without traversal" in error for error in errors))

    def test_quoted_call_operator_without_exit_check_is_reported(self) -> None:
        with self.make_repo(
            check_id="dcoir-check-external-exit",
            rule_name="DCOIR.ExternalProcessExitChecked",
            risk_class="external_command_nonzero_exit_treated_success",
            bad_text='& "C:\\Program Files\\tool.exe"\n',
            good_text='& "C:\\Program Files\\tool.exe"\nif ($LASTEXITCODE -ne 0) { throw "failed" }\n',
        ) as temp:
            report, errors, _warnings = custom.build_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["observed_fixture_finding_count"], 1)
        self.assertEqual(report["findings"][0]["path"], "project_sources/collector/fixtures/powershell_analysis/bad/review_thread_bad.ps1")
        self.assertEqual(report["findings"][0]["line"], 1)
        self.assertEqual(report["findings"][0]["risk_class"], "external_command_nonzero_exit_treated_success")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
