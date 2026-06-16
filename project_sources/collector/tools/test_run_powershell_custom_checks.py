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


def check_def(check_id: str, rule_name: str, risk_class: str) -> dict[str, object]:
    return {
        "id": check_id,
        "rule_name": rule_name,
        "matrix_check_id": check_id,
        "expected_severity": "Error",
        "risk_classes": [risk_class],
        "target_surfaces": ["validation tooling"],
        "intent": "Local fail-closed evidence must be tied to the risky row.",
        "failure_impact": "Unrelated failure handling can hide unsafe validation output.",
        "recommended_fix": "Fail the same local path that emits unsafe validation evidence.",
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

    def test_fail_output_ignores_unrelated_throw_elsewhere(self) -> None:
        text = 'throw "unrelated guard"\n\n$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }\n'
        findings = custom.check_fail_output(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
            check_def(
                "dcoir-fail-output-must-fail",
                "DCOIR.FailOutputMustFailValidation",
                "fail_rows_reports_or_fixture_outputs_not_causing_failure",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 3)

    def test_fail_output_ignores_unrelated_validation_fail_elsewhere(self) -> None:
        text = '$validation = "FAIL"\n\n$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }\n'
        findings = custom.check_fail_output(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
            check_def(
                "dcoir-fail-output-must-fail",
                "DCOIR.FailOutputMustFailValidation",
                "fail_rows_reports_or_fixture_outputs_not_causing_failure",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 3)

    def test_fail_output_flags_only_unsafe_mixed_rows(self) -> None:
        text = "\n".join(
            [
                '$Rows += [pscustomobject]@{ Check = "Safe"; Status = "FAIL" }',
                'throw "safe row failed closed"',
                "",
                '$Rows += [pscustomobject]@{ Check = "Unsafe"; Status = "FAIL" }',
                "",
                'exit 1',
                "",
            ]
        )
        findings = custom.check_fail_output(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
            check_def(
                "dcoir-fail-output-must-fail",
                "DCOIR.FailOutputMustFailValidation",
                "fail_rows_reports_or_fixture_outputs_not_causing_failure",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 4)

    def test_fail_output_ignores_commented_local_failure_action(self) -> None:
        text = "\n".join(
            [
                '$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }',
                "# TODO throw when wired",
                "",
            ]
        )
        findings = custom.check_fail_output(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
            check_def(
                "dcoir-fail-output-must-fail",
                "DCOIR.FailOutputMustFailValidation",
                "fail_rows_reports_or_fixture_outputs_not_causing_failure",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 1)

    def test_fail_output_ignores_quoted_local_failure_action(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Fixture"',
                '    Status = "FAIL"',
                '    RecommendedFix = "throw when this fails"',
                "}",
                "",
            ]
        )
        findings = custom.check_fail_output(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
            check_def(
                "dcoir-fail-output-must-fail",
                "DCOIR.FailOutputMustFailValidation",
                "fail_rows_reports_or_fixture_outputs_not_causing_failure",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 3)

    def test_fail_output_accepts_indented_local_failure_actions(self) -> None:
        actions = ['throw "failed"', "exit 1", "return $false"]
        for action in actions:
            with self.subTest(action=action):
                text = "\n".join(
                    [
                        '$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }',
                        f"    {action}",
                        "",
                    ]
                )
                findings = custom.check_fail_output(
                    text,
                    "project_sources/collector/fixtures/powershell_analysis/good/custom_fail_row_fails_command.ps1",
                    check_def(
                        "dcoir-fail-output-must-fail",
                        "DCOIR.FailOutputMustFailValidation",
                        "fail_rows_reports_or_fixture_outputs_not_causing_failure",
                    ),
                )

                self.assertEqual(findings, [])

    def test_fail_output_ignores_block_comment_failure_action(self) -> None:
        text = "\n".join(
            [
                '$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }',
                "<#",
                "throw later",
                "#>",
                "",
            ]
        )
        findings = custom.check_fail_output(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
            check_def(
                "dcoir-fail-output-must-fail",
                "DCOIR.FailOutputMustFailValidation",
                "fail_rows_reports_or_fixture_outputs_not_causing_failure",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 1)

    def test_fail_output_ignores_here_string_failure_action(self) -> None:
        text = "\n".join(
            [
                '$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }',
                '$message = @"',
                "throw later",
                '"@',
                "",
            ]
        )
        findings = custom.check_fail_output(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
            check_def(
                "dcoir-fail-output-must-fail",
                "DCOIR.FailOutputMustFailValidation",
                "fail_rows_reports_or_fixture_outputs_not_causing_failure",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 1)

    def test_fail_output_ignores_non_code_fail_mentions(self) -> None:
        cases = {
            "comment": "# $Rows += [pscustomobject]@{ Check = 'Fixture'; Status = 'FAIL' }",
            "quoted": '$message = "$Rows += [pscustomobject]@{ Check = \'Fixture\'; Status = \'FAIL\' }"',
            "here_string": "\n".join(
                [
                    '$message = @"',
                    "$Rows += [pscustomobject]@{ Check = 'Fixture'; Status = 'FAIL' }",
                    '"@',
                ]
            ),
        }
        for name, text in cases.items():
            with self.subTest(name=name):
                findings = custom.check_fail_output(
                    text,
                    "project_sources/collector/fixtures/powershell_analysis/good/custom_fail_row_fails_command.ps1",
                    check_def(
                        "dcoir-fail-output-must-fail",
                        "DCOIR.FailOutputMustFailValidation",
                        "fail_rows_reports_or_fixture_outputs_not_causing_failure",
                    ),
                )

                self.assertEqual(findings, [])

    def test_analyzer_skip_success_ignores_unrelated_throw_elsewhere(self) -> None:
        text = "\n".join(
            [
                'throw "unrelated guard"',
                "",
                "$Rows += [pscustomobject]@{",
                '    Check = "Analyzer"',
                "    Analyzed = $false",
                "    Skipped = $true",
                '    Status = "PASS"',
                "}",
                "",
            ]
        )
        findings = custom.check_analyzer_skip_success(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
            check_def(
                "dcoir-analyzer-skip-success",
                "DCOIR.AnalyzerSkipMustFailClosed",
                "analyzer_or_validation_skip_treated_success",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 5)

    def test_analyzer_skip_success_accepts_local_throw(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Analyzer"',
                "    Analyzed = $false",
                "    Skipped = $true",
                '    Status = "PASS"',
                "}",
                'throw "skip is not allowed"',
                "",
            ]
        )
        findings = custom.check_analyzer_skip_success(
            text,
            "project_sources/collector/fixtures/powershell_analysis/good/custom_analyzer_skip_fails_closed.ps1",
            check_def(
                "dcoir-analyzer-skip-success",
                "DCOIR.AnalyzerSkipMustFailClosed",
                "analyzer_or_validation_skip_treated_success",
            ),
        )

        self.assertEqual(findings, [])

    def test_analyzer_skip_success_ignores_commented_local_failure_action(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Analyzer"',
                "    Analyzed = $false",
                "    Skipped = $true",
                '    Status = "PASS"',
                "}",
                "# TODO exit 1 after wiring",
                "",
            ]
        )
        findings = custom.check_analyzer_skip_success(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
            check_def(
                "dcoir-analyzer-skip-success",
                "DCOIR.AnalyzerSkipMustFailClosed",
                "analyzer_or_validation_skip_treated_success",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 3)

    def test_analyzer_skip_success_accepts_indented_local_failure_actions(self) -> None:
        actions = ['throw "skip is not allowed"', "exit 1", "return $false"]
        for action in actions:
            with self.subTest(action=action):
                text = "\n".join(
                    [
                        "$Rows += [pscustomobject]@{",
                        '    Check = "Analyzer"',
                        "    Analyzed = $false",
                        "    Skipped = $true",
                        '    Status = "PASS"',
                        "}",
                        f"    {action}",
                        "",
                    ]
                )
                findings = custom.check_analyzer_skip_success(
                    text,
                    "project_sources/collector/fixtures/powershell_analysis/good/custom_analyzer_skip_fails_closed.ps1",
                    check_def(
                        "dcoir-analyzer-skip-success",
                        "DCOIR.AnalyzerSkipMustFailClosed",
                        "analyzer_or_validation_skip_treated_success",
                    ),
                )

                self.assertEqual(findings, [])

    def test_analyzer_skip_success_ignores_block_comment_failure_action(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Analyzer"',
                "    Analyzed = $false",
                "    Skipped = $true",
                '    Status = "PASS"',
                "}",
                "<#",
                "throw later",
                "#>",
                "",
            ]
        )
        findings = custom.check_analyzer_skip_success(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
            check_def(
                "dcoir-analyzer-skip-success",
                "DCOIR.AnalyzerSkipMustFailClosed",
                "analyzer_or_validation_skip_treated_success",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 3)

    def test_analyzer_skip_success_ignores_here_string_failure_action(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Analyzer"',
                "    Analyzed = $false",
                "    Skipped = $true",
                '    Status = "PASS"',
                "}",
                '$message = @"',
                "throw later",
                '"@',
                "",
            ]
        )
        findings = custom.check_analyzer_skip_success(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
            check_def(
                "dcoir-analyzer-skip-success",
                "DCOIR.AnalyzerSkipMustFailClosed",
                "analyzer_or_validation_skip_treated_success",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 3)

    def test_analyzer_skip_success_ignores_quoted_local_failure_action(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Analyzer"',
                "    Analyzed = $false",
                "    Skipped = $true",
                '    Status = "PASS"',
                '    Message = "throw if skipped"',
                "}",
                "",
            ]
        )
        findings = custom.check_analyzer_skip_success(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
            check_def(
                "dcoir-analyzer-skip-success",
                "DCOIR.AnalyzerSkipMustFailClosed",
                "analyzer_or_validation_skip_treated_success",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 3)

    def test_analyzer_skip_success_ignores_non_code_skip_success_mentions(self) -> None:
        cases = {
            "comment": "# Analyzed = $false; Validation = 'success'",
            "quoted": '$message = "Analyzed = $false; Validation = \'success\'"',
            "here_string": "\n".join(
                [
                    '$message = @"',
                    "Analyzed = $false",
                    "Validation = 'success'",
                    '"@',
                ]
            ),
        }
        for name, text in cases.items():
            with self.subTest(name=name):
                findings = custom.check_analyzer_skip_success(
                    text,
                    "project_sources/collector/fixtures/powershell_analysis/good/custom_analyzer_skip_fails_closed.ps1",
                    check_def(
                        "dcoir-analyzer-skip-success",
                        "DCOIR.AnalyzerSkipMustFailClosed",
                        "analyzer_or_validation_skip_treated_success",
                    ),
                )

                self.assertEqual(findings, [])

    def test_analyzer_skip_success_flags_only_unsafe_mixed_rows(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Safe"',
                "    Analyzed = $false",
                '    Status = "PASS"',
                "}",
                'throw "safe row failed closed"',
                "",
                "$Rows += [pscustomobject]@{",
                '    Check = "Unsafe"',
                "    Skipped = $true",
                '    Status = "PASS"',
                "}",
                "",
                'exit 1',
                "",
            ]
        )
        findings = custom.check_analyzer_skip_success(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
            check_def(
                "dcoir-analyzer-skip-success",
                "DCOIR.AnalyzerSkipMustFailClosed",
                "analyzer_or_validation_skip_treated_success",
            ),
        )

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["line"], 10)

    def test_target_path_limits_fixture_assertions_to_selected_fixture(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            bad_path = "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1"
            report, errors, _warnings = custom.build_report(
                self.args(root, target_path=[bad_path])
            )

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["targets"], [bad_path])
        self.assertEqual([fixture["id"] for fixture in report["fixtures"]], ["bad-fail-row-green-exit"])
        self.assertEqual(report["summary"]["negative_fixture_count"], 1)
        self.assertEqual(report["summary"]["control_fixture_count"], 0)
        self.assertEqual(report["summary"]["expected_fixture_finding_count"], 1)
        self.assertEqual(report["summary"]["observed_fixture_finding_count"], 1)

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

    def test_cli_input_paths_must_stay_inside_repo_before_read(self) -> None:
        scenarios = [
            ("checks", "ABSOLUTE_CHECKS", "custom checks path", "checks"),
            ("matrix", "../outside-matrix.json", "rule-to-risk matrix path", "matrix"),
            ("inventory", "../outside-inventory.json", "PowerShell surface inventory path", "inventory"),
            ("fixture_manifest", "ABSOLUTE_FIXTURE_MANIFEST", "custom fixture manifest path", "fixture_manifest"),
        ]
        for arg_name, unsafe_path, expected_label, report_key in scenarios:
            with self.subTest(arg_name=arg_name):
                with self.make_repo() as temp:
                    root = Path(temp).resolve()
                    outside_name = "outside-custom-check-input.json"
                    if unsafe_path.startswith("../"):
                        outside_name = unsafe_path.removeprefix("../")
                    outside = root.parent / outside_name
                    write(outside, "{not-json")
                    if unsafe_path.startswith("ABSOLUTE_"):
                        unsafe_path = outside.as_posix()
                    report, errors, _warnings = custom.build_report(
                        self.args(root, **{arg_name: unsafe_path})
                    )

                self.assertFalse(report["validation"]["success"])
                self.assertTrue(
                    any(f"{expected_label} must be a repo-relative path without traversal" in error for error in errors),
                    errors,
                )
                self.assertFalse(any("not valid JSON" in error for error in errors), errors)
                self.assertFalse(report[report_key]["accepted"])

    def test_output_paths_must_stay_inside_repo_before_write(self) -> None:
        scenarios = [
            (
                "json traversal",
                {"json_output": "../outside-custom-report.json", "markdown_output": "custom-report.md"},
                "custom checks JSON report output path",
                "outside-custom-report.json",
            ),
            (
                "markdown absolute",
                {"json_output": "custom-report.json", "markdown_output": "ABSOLUTE_MARKDOWN"},
                "custom checks Markdown report output path",
                "outside-custom-report.md",
            ),
            (
                "same path",
                {"json_output": "same-report", "markdown_output": "same-report"},
                "custom checks JSON and Markdown report output paths must be different",
                "same-report",
            ),
        ]
        for name, overrides, expected_label, outside_name in scenarios:
            with self.subTest(name=name):
                with self.make_repo() as temp:
                    root = Path(temp).resolve()
                    outside = root.parent / outside_name
                    outside.unlink(missing_ok=True)
                    if overrides["markdown_output"] == "ABSOLUTE_MARKDOWN":
                        overrides["markdown_output"] = outside.as_posix()
                    report, errors, _warnings = custom.build_report(
                        self.args(root, no_write=False, **overrides)
                    )

                self.assertFalse(report["validation"]["success"])
                self.assertTrue(
                    any(expected_label in error for error in errors),
                    errors,
                )
                if name != "same path":
                    self.assertFalse(outside.exists())

    def test_inventory_targets_must_be_safe_before_reading(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp).resolve()
            outside = root.parent / "outside_custom_check.ps1"
            write(outside, '$Rows += [pscustomobject]@{ Check = "Outside"; Status = "FAIL" }\n')
            inventory_path = root / custom.DEFAULT_INVENTORY
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory["surfaces"].extend([
                surface(outside.as_posix()),
                surface("../outside_custom_check.ps1"),
                surface("C:outside/custom_check.ps1"),
            ])
            inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
            report, errors, _warnings = custom.build_report(self.args(root, target_scope="inventory"))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("path must be a repo-relative path without traversal" in error for error in errors), errors)

    def test_symlinked_inventory_target_fails_before_reading(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp).resolve()
            outside = root.parent / "outside_custom_check_symlink.ps1"
            write(outside, '$Rows += [pscustomobject]@{ Check = "Outside"; Status = "FAIL" }\n')
            rel = "project_sources/collector/fixtures/powershell_analysis/bad/symlink_escape.ps1"
            link = root / rel
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(outside)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")
            inventory_path = root / custom.DEFAULT_INVENTORY
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory["surfaces"].append(surface(rel))
            inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
            report, errors, _warnings = custom.build_report(self.args(root, target_scope="inventory"))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("path must resolve inside the repository root" in error for error in errors), errors)

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
