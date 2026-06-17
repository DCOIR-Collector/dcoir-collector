#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import textwrap
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_powershell_rule_risk_fixtures as harness


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PowerShellRuleRiskFixtureTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        bad_text: str = 'Write-Host "bad output"\n',
        control_text: str = 'Write-Output "good output"\n',
        expected_line: int = 1,
        matrix_fixtures: list[str] | None = None,
        duplicate_check: bool = False,
    ) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "project_sources/collector/fixtures/powershell_analysis/bad/write_host.ps1", bad_text)
        write(root / "project_sources/collector/fixtures/powershell_analysis/good/control.ps1", control_text)
        self.write_settings(root)
        fixtures = ["bad-write-host"] if matrix_fixtures is None else matrix_fixtures
        checks = [
            {
                "id": "pssa-avoid-write-host",
                "rule_name": "PSAvoidUsingWriteHost",
                "tool": "PSScriptAnalyzer",
                "check_source": "project_sources/collector/PSScriptAnalyzerSettings.psd1",
                "blocking": True,
                "expected_severity": "Warning",
                "risk_classes": ["review_assist_output_quality"],
                "target_surfaces": ["validation tooling"],
                "failure_impact": "Host-only output can disappear from durable reports.",
                "recommended_fix": "Use Write-Output or structured reporting.",
                "fixtures": fixtures,
                "promotion_criteria": "Already blocking in this test matrix.",
            }
        ]
        if duplicate_check:
            checks.append(dict(checks[0]))
        matrix = {
            "schema_version": harness.MATRIX_SCHEMA_VERSION,
            "issue": harness.ISSUE_NUMBER,
            "minimum_risk_classes": [],
            "checks": checks,
        }
        manifest = {
            "schema_version": harness.MANIFEST_SCHEMA_VERSION,
            "issue": harness.ISSUE_NUMBER,
            "matrix": harness.DEFAULT_MATRIX.as_posix(),
            "fixtures_root": harness.FIXTURE_ROOT.as_posix(),
            "fixtures": [
                {
                    "id": "bad-write-host",
                    "kind": "negative",
                    "path": "project_sources/collector/fixtures/powershell_analysis/bad/write_host.ps1",
                    "description": "Write-Host negative fixture.",
                    "expected_findings": [
                        {
                            "check_id": "pssa-avoid-write-host",
                            "rule_name": "PSAvoidUsingWriteHost",
                            "severity": "Warning",
                            "line": expected_line,
                            "risk_class": "review_assist_output_quality",
                        }
                    ],
                },
                {
                    "id": "good-control",
                    "kind": "control",
                    "path": "project_sources/collector/fixtures/powershell_analysis/good/control.ps1",
                    "description": "Clean control fixture.",
                    "expected_findings": [],
                },
            ],
        }
        write(root / harness.DEFAULT_MATRIX, json.dumps(matrix, indent=2) + "\n")
        write(root / harness.DEFAULT_MANIFEST, json.dumps(manifest, indent=2) + "\n")
        return temp

    def write_settings(self, root: Path) -> None:
        include_rules = "\n".join(f"        '{rule}'" for rule in sorted(harness.analyzer.REQUIRED_POLICY_RULES))
        rules = "\n".join(f"        {rule} = @{{}}" for rule in sorted(harness.analyzer.REQUIRED_POLICY_RULES))
        write(
            root / "project_sources/collector/PSScriptAnalyzerSettings.psd1",
            textwrap.dedent(
                f"""\
                # DCOIR_POLICY_ID: dcoir-powershell-analyzer-policy-v1
                # DCOIR_EXCLUSIONS: none
                @{{
                    Severity = @('Error', 'Warning')
                    IncludeRules = @(
{include_rules}
                    )
                    Rules = @{{
{rules}
                    }}
                }}
                """
            ),
        )

    def args(self, root: Path) -> argparse.Namespace:
        return argparse.Namespace(
            repo_root=str(root),
            matrix=harness.DEFAULT_MATRIX.as_posix(),
            manifest=harness.DEFAULT_MANIFEST.as_posix(),
            json_output=harness.DEFAULT_JSON_OUTPUT.as_posix(),
            markdown_output=harness.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
            matrix_markdown_output=harness.DEFAULT_MATRIX_MARKDOWN_OUTPUT.as_posix(),
            timeout_seconds=10,
            no_write=True,
            skip_minimum_risk_class_check=True,
        )

    def test_fixture_report_passes_for_negative_and_control(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["negative_fixture_count"], 1)
        self.assertEqual(report["summary"]["control_fixture_count"], 1)
        self.assertEqual(report["summary"]["expected_finding_count"], 1)
        self.assertEqual(report["summary"]["observed_finding_count"], 1)

    def test_fixture_report_ignores_status_fail_variable_outside_result_object(self) -> None:
        with self.make_repo(
            bad_text='$Status = "FAIL"\nWrite-Host "bad output"\n',
            expected_line=2,
        ) as temp:
            report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["expected_finding_count"], 1)
        self.assertEqual(report["summary"]["observed_finding_count"], 1)
        self.assertEqual(report["findings"][0]["rule_name"], "PSAvoidUsingWriteHost")

    def test_temp_inventory_path_passed_repo_relative_to_wrapper(self) -> None:
        captured: dict[str, str] = {}

        def fake_build_report(args: argparse.Namespace) -> tuple[dict[str, object], list[str], list[str]]:
            captured["inventory"] = args.inventory
            return (
                {
                    "schema_version": harness.analyzer.SCHEMA_VERSION,
                    "findings": [
                        {
                            "path": "project_sources/collector/fixtures/powershell_analysis/bad/write_host.ps1",
                            "line": 1,
                            "column": 1,
                            "symbol": "",
                            "rule_name": "PSAvoidUsingWriteHost",
                            "severity": "Warning",
                            "observed_problem": "host output",
                            "recommended_fix": "use durable output",
                        }
                    ],
                },
                [],
                [],
            )

        with self.make_repo() as temp:
            root = Path(temp)
            with unittest.mock.patch.object(harness.analyzer, "build_report", side_effect=fake_build_report):
                report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(root))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertIn("inventory", captured)
        self.assertFalse(Path(captured["inventory"]).is_absolute())
        self.assertTrue(captured["inventory"].startswith(".dcoir-rule-risk-fixtures-"))

    def test_fixture_report_accepts_crlf_fixture_inventory_hashes(self) -> None:
        with self.make_repo(
            bad_text='Write-Host "bad output"\r\n',
            control_text='Write-Output "good output"\r\n',
        ) as temp:
            report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["observed_finding_count"], 1)

    def test_missing_negative_expected_finding_fails(self) -> None:
        with self.make_repo(expected_line=2) as temp:
            report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("expected PSAvoidUsingWriteHost" in error for error in errors))

    def test_control_fixture_unexpected_finding_fails(self) -> None:
        with self.make_repo(control_text='Write-Host "unexpected host output"\n') as temp:
            report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("control fixture produced unexpected findings" in error for error in errors))

    def test_blocking_check_without_fixture_fails(self) -> None:
        with self.make_repo(matrix_fixtures=[]) as temp:
            report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("blocking checks must name at least one fixture" in error for error in errors))

    def test_duplicate_check_id_fails(self) -> None:
        with self.make_repo(duplicate_check=True) as temp:
            report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("duplicate check id" in error for error in errors))

    def test_matrix_and_manifest_paths_reject_absolute_and_traversal_before_read(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            outside = root.parent / f"{root.name}-outside-rule-risk-input.json"
            write(outside, "{not-json\n")
            try:
                cases = [
                    ("matrix", outside.as_posix(), "rule-to-risk matrix path"),
                    ("matrix", f"../{outside.name}", "rule-to-risk matrix path"),
                    ("manifest", outside.as_posix(), "fixture manifest path"),
                    ("manifest", f"../{outside.name}", "fixture manifest path"),
                ]
                for attr, value, label in cases:
                    with self.subTest(attr=attr, value=value):
                        args = self.args(root)
                        setattr(args, attr, value)
                        report, errors, _warnings, _matrix = harness.build_fixture_report(args)

                    self.assertFalse(report["validation"]["success"])
                    self.assertTrue(
                        any(f"{label} must be a repo-relative path without traversal" in error for error in errors)
                    )
                    self.assertFalse(any("invalid JSON" in error for error in errors))
            finally:
                outside.unlink(missing_ok=True)

    def test_output_paths_reject_absolute_and_traversal_before_write(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report, errors, _warnings, matrix = harness.build_fixture_report(self.args(root))
            self.assertEqual(errors, [])
            outside = root.parent / f"{root.name}-outside-rule-risk-output.json"
            cases = [
                (
                    Path(f"../{outside.name}"),
                    Path("project_sources/collector/safe-report.md"),
                    Path("project_sources/collector/safe-matrix.md"),
                    "fixture report JSON output path",
                ),
                (
                    Path("project_sources/collector/safe-report.json"),
                    outside,
                    Path("project_sources/collector/safe-matrix.md"),
                    "fixture report Markdown output path",
                ),
                (
                    Path("project_sources/collector/safe-report.json"),
                    Path("project_sources/collector/safe-report.md"),
                    Path(f"../{outside.name}"),
                    "rule-risk matrix Markdown output path",
                ),
            ]
            for json_output, markdown_output, matrix_output, label in cases:
                with self.subTest(label=label):
                    with self.assertRaises(harness.RuleRiskFixtureError) as caught:
                        harness.write_outputs(root, report, matrix, json_output, markdown_output, matrix_output)
                    self.assertIn(label, str(caught.exception))
                    self.assertFalse(outside.exists())

    def test_output_symlink_resolving_outside_repo_is_rejected(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report, errors, _warnings, matrix = harness.build_fixture_report(self.args(root))
            self.assertEqual(errors, [])
            outside_dir = root.parent / f"{root.name}-outside-rule-risk-output-dir"
            outside_dir.mkdir(exist_ok=True)
            link = root / "project_sources/collector/linked-output"
            try:
                link.symlink_to(outside_dir, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")
            try:
                with self.assertRaises(harness.RuleRiskFixtureError) as caught:
                    harness.write_outputs(
                        root,
                        report,
                        matrix,
                        Path("project_sources/collector/linked-output/report.json"),
                        Path("project_sources/collector/safe-report.md"),
                        Path("project_sources/collector/safe-matrix.md"),
                    )
                self.assertIn("must resolve inside the repository root", str(caught.exception))
                self.assertFalse((outside_dir / "report.json").exists())
            finally:
                (outside_dir / "report.json").unlink(missing_ok=True)
                shutil.rmtree(outside_dir, ignore_errors=True)

    def test_output_paths_must_be_distinct(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report, errors, _warnings, matrix = harness.build_fixture_report(self.args(root))
            self.assertEqual(errors, [])
            with self.assertRaises(harness.RuleRiskFixtureError) as caught:
                harness.write_outputs(
                    root,
                    report,
                    matrix,
                    Path("project_sources/collector/same-output.md"),
                    Path("project_sources/collector/same-output.md"),
                    Path("project_sources/collector/safe-matrix.md"),
                )

        self.assertIn("must be different", str(caught.exception))

    def test_main_rewrites_json_report_failed_when_later_output_write_fails(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            blocked_markdown = root / "project_sources/collector/blocked-report.md"
            blocked_markdown.mkdir()
            json_output = Path("project_sources/collector/stale-success-report.json")
            argv = [
                "run_powershell_rule_risk_fixtures.py",
                "--repo-root",
                root.as_posix(),
                "--skip-minimum-risk-class-check",
                "--json-output",
                json_output.as_posix(),
                "--markdown-output",
                "project_sources/collector/blocked-report.md",
                "--matrix-markdown-output",
                "project_sources/collector/stale-success-matrix.md",
            ]
            with unittest.mock.patch.object(sys, "argv", argv):
                exit_code = harness.main()
            written = json.loads((root / json_output).read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertFalse(written["validation"]["success"])
        self.assertTrue(any("report write failure" in error for error in written["validation"]["errors"]))

    def test_main_rewrites_status_reports_failed_when_matrix_output_write_fails(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            blocked_matrix = root / "project_sources/collector/blocked-matrix.md"
            blocked_matrix.mkdir()
            json_output = Path("project_sources/collector/matrix-failure-report.json")
            markdown_output = Path("project_sources/collector/matrix-failure-report.md")
            write(root / json_output, json.dumps({"validation": {"success": True}}) + "\n")
            write(root / markdown_output, "# Old Report\n\n- Validation: `pass`\n")
            argv = [
                "run_powershell_rule_risk_fixtures.py",
                "--repo-root",
                root.as_posix(),
                "--skip-minimum-risk-class-check",
                "--json-output",
                json_output.as_posix(),
                "--markdown-output",
                markdown_output.as_posix(),
                "--matrix-markdown-output",
                "project_sources/collector/blocked-matrix.md",
            ]
            with unittest.mock.patch.object(sys, "argv", argv):
                exit_code = harness.main()
            written_json = json.loads((root / json_output).read_text(encoding="utf-8"))
            written_markdown = (root / markdown_output).read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertFalse(written_json["validation"]["success"])
        self.assertTrue(any("report write failure" in error for error in written_json["validation"]["errors"]))
        self.assertIn("Validation: `fail`", written_markdown)
        self.assertNotIn("Validation: `pass`", written_markdown)

    def test_unsafe_absolute_fixture_path_is_not_hashed(self) -> None:
        with self.make_repo(matrix_fixtures=["bad-write-host", "outside-fixture"]) as temp:
            root = Path(temp)
            outside = root / "outside.ps1"
            write(outside, 'Write-Host "outside"\n')
            manifest_path = root / harness.DEFAULT_MANIFEST
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["fixtures"].append(
                {
                    "id": "outside-fixture",
                    "kind": "negative",
                    "path": outside.as_posix(),
                    "description": "Unsafe absolute fixture path.",
                    "expected_findings": [
                        {
                            "check_id": "pssa-avoid-write-host",
                            "rule_name": "PSAvoidUsingWriteHost",
                            "severity": "Warning",
                            "line": 1,
                            "risk_class": "review_assist_output_quality",
                        }
                    ],
                }
            )
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")
            original_sha256_file = harness.sha256_file

            def guarded_sha256(path: Path) -> str:
                if path.resolve() == outside.resolve():
                    raise AssertionError("unsafe hash attempted")
                return original_sha256_file(path)

            with unittest.mock.patch.object(harness, "sha256_file", side_effect=guarded_sha256):
                report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("fixture path must be repo-relative" in error for error in errors))
        self.assertTrue(any("matrix references missing fixture ids: outside-fixture" in error for error in errors))

    def test_parent_traversal_fixture_path_is_not_hashed(self) -> None:
        with self.make_repo(matrix_fixtures=["bad-write-host", "outside-fixture"]) as temp:
            root = Path(temp)
            write(root / "project_sources/collector/fixtures/powershell_analysis/escape.ps1", 'Write-Host "safe"\n')
            write(root / "project_sources/collector/fixtures/outside.ps1", 'Write-Host "outside"\n')
            manifest_path = root / harness.DEFAULT_MANIFEST
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["fixtures"].append(
                {
                    "id": "outside-fixture",
                    "kind": "negative",
                    "path": "project_sources/collector/fixtures/powershell_analysis/../outside.ps1",
                    "description": "Unsafe traversal fixture path.",
                    "expected_findings": [
                        {
                            "check_id": "pssa-avoid-write-host",
                            "rule_name": "PSAvoidUsingWriteHost",
                            "severity": "Warning",
                            "line": 1,
                            "risk_class": "review_assist_output_quality",
                        }
                    ],
                }
            )
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")
            unsafe = root / "project_sources/collector/fixtures/outside.ps1"
            original_sha256_file = harness.sha256_file

            def guarded_sha256(path: Path) -> str:
                if path.resolve() == unsafe.resolve():
                    raise AssertionError("unsafe hash attempted")
                return original_sha256_file(path)

            with unittest.mock.patch.object(harness, "sha256_file", side_effect=guarded_sha256):
                report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("fixture path must be repo-relative" in error for error in errors))
        self.assertTrue(any("matrix references missing fixture ids: outside-fixture" in error for error in errors))

    def test_fixture_symlink_resolving_outside_root_is_not_hashed(self) -> None:
        with self.make_repo(matrix_fixtures=["bad-write-host", "outside-fixture"]) as temp:
            root = Path(temp)
            outside = root / "outside.ps1"
            write(outside, 'Write-Host "outside"\n')
            link = root / "project_sources/collector/fixtures/powershell_analysis/bad/outside_link.ps1"
            try:
                link.unlink(missing_ok=True)
                link.symlink_to(outside)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")
            manifest_path = root / harness.DEFAULT_MANIFEST
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["fixtures"].append(
                {
                    "id": "outside-fixture",
                    "kind": "negative",
                    "path": "project_sources/collector/fixtures/powershell_analysis/bad/outside_link.ps1",
                    "description": "Unsafe symlink fixture path.",
                    "expected_findings": [
                        {
                            "check_id": "pssa-avoid-write-host",
                            "rule_name": "PSAvoidUsingWriteHost",
                            "severity": "Warning",
                            "line": 1,
                            "risk_class": "review_assist_output_quality",
                        }
                    ],
                }
            )
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")
            original_sha256_file = harness.sha256_file

            def guarded_sha256(path: Path) -> str:
                if path.resolve() == outside.resolve():
                    raise AssertionError("unsafe hash attempted")
                return original_sha256_file(path)

            with unittest.mock.patch.object(harness, "sha256_file", side_effect=guarded_sha256):
                report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("fixture path resolves outside" in error for error in errors))
        self.assertTrue(any("matrix references missing fixture ids: outside-fixture" in error for error in errors))

    def test_symlinked_fixture_root_is_not_hashed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            fixture_root = root / harness.FIXTURE_ROOT
            redirected_root = root / "redirected_fixture_root"
            try:
                fixture_root.rename(redirected_root)
                fixture_root.symlink_to(redirected_root, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"symlink creation is unavailable: {exc}")
            unsafe = redirected_root / "bad/write_host.ps1"
            original_sha256_file = harness.sha256_file

            def guarded_sha256(path: Path) -> str:
                if path.resolve() == unsafe.resolve():
                    raise AssertionError("unsafe hash attempted")
                return original_sha256_file(path)

            with unittest.mock.patch.object(harness, "sha256_file", side_effect=guarded_sha256):
                report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("fixture root must not be a symlink" in error for error in errors))
        self.assertTrue(any("matrix references missing fixture ids: bad-write-host" in error for error in errors))

    def test_directory_shaped_fixture_path_is_not_hashed(self) -> None:
        with self.make_repo(matrix_fixtures=["bad-write-host", "directory-fixture"]) as temp:
            root = Path(temp)
            directory_fixture = root / "project_sources/collector/fixtures/powershell_analysis/bad/directory.ps1"
            directory_fixture.mkdir()
            manifest_path = root / harness.DEFAULT_MANIFEST
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["fixtures"].append(
                {
                    "id": "directory-fixture",
                    "kind": "negative",
                    "path": "project_sources/collector/fixtures/powershell_analysis/bad/directory.ps1",
                    "description": "Directory-shaped fixture path.",
                    "expected_findings": [
                        {
                            "check_id": "pssa-avoid-write-host",
                            "rule_name": "PSAvoidUsingWriteHost",
                            "severity": "Warning",
                            "line": 1,
                            "risk_class": "review_assist_output_quality",
                        }
                    ],
                }
            )
            write(manifest_path, json.dumps(manifest, indent=2) + "\n")
            original_sha256_file = harness.sha256_file

            def guarded_sha256(path: Path) -> str:
                if path.resolve() == directory_fixture.resolve():
                    raise AssertionError("unsafe hash attempted")
                return original_sha256_file(path)

            with unittest.mock.patch.object(harness, "sha256_file", side_effect=guarded_sha256):
                report, errors, _warnings, _matrix = harness.build_fixture_report(self.args(root))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("fixture path must be a file" in error for error in errors))
        self.assertTrue(any("matrix references missing fixture ids: directory-fixture" in error for error in errors))

    def test_fixture_findings_ignore_non_code_skip_success_mentions(self) -> None:
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
                findings = harness.fixture_findings(
                    text,
                    "project_sources/collector/fixtures/powershell_analysis/good/control.ps1",
                )

                self.assertFalse(
                    any(finding["rule_name"] == "DCOIR.NoAnalyzerSkipSuccess" for finding in findings)
                )

    def test_fixture_findings_do_not_treat_comment_or_string_as_here_string_start_for_skip_success(self) -> None:
        cases = {
            "comment_opener": '# docs @"',
            "quoted_opener": '$message = "docs @"',
        }
        for name, opener in cases.items():
            with self.subTest(name=name):
                findings = harness.fixture_findings(
                    "\n".join(
                        [
                            opener,
                            '$Rows += [pscustomobject]@{ Check = "Analyzer"; Analyzed = $false; Validation = "success" }',
                            "",
                        ]
                    ),
                    "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
                )
                matching = [finding for finding in findings if finding["rule_name"] == "DCOIR.NoAnalyzerSkipSuccess"]

                self.assertEqual(len(matching), 1)
                self.assertEqual(matching[0]["line"], 2)

    def test_fixture_findings_do_not_treat_comment_or_string_as_block_comment_start_for_skip_success(self) -> None:
        cases = {
            "comment_opener": "# docs <#",
            "quoted_opener": '$message = "docs <#"',
        }
        for name, opener in cases.items():
            with self.subTest(name=name):
                findings = harness.fixture_findings(
                    "\n".join(
                        [
                            opener,
                            '$Rows += [pscustomobject]@{ Check = "Analyzer"; Analyzed = $false; Validation = "success" }',
                            "",
                        ]
                    ),
                    "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
                )
                matching = [finding for finding in findings if finding["rule_name"] == "DCOIR.NoAnalyzerSkipSuccess"]

                self.assertEqual(len(matching), 1)
                self.assertEqual(matching[0]["line"], 2)

    def test_fixture_findings_track_long_skip_success_object_until_closing_brace(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Analyzer"',
                '    Scope = "Analyzer"',
                '    Rule = "DCOIR.NoAnalyzerSkipSuccess"',
                '    Target = "fixture"',
                '    Category = "validation"',
                '    Surface = "PowerShell"',
                '    Evidence = "row"',
                '    Detail = "skipped"',
                '    Recommendation = "fail closed"',
                "    Analyzed = $false",
                '    Validation = "success"',
                "}",
                'throw "long skip object failed closed"',
                "",
            ]
        )
        findings = harness.fixture_findings(
            text,
            "project_sources/collector/fixtures/powershell_analysis/good/control.ps1",
        )

        self.assertFalse(any(finding["rule_name"] == "DCOIR.NoAnalyzerSkipSuccess" for finding in findings))

    def test_fixture_findings_keep_skip_success_evidence_local(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Safe"',
                "    Analyzed = $false",
                '    Validation = "success"',
                "}",
                'throw "safe row failed closed"',
                "",
                "$Rows += [pscustomobject]@{",
                '    Check = "Unsafe"',
                "    Skipped = $true",
                '    Validation = "success"',
                "}",
                "",
            ]
        )
        findings = harness.fixture_findings(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1",
        )
        matching = [finding for finding in findings if finding["rule_name"] == "DCOIR.NoAnalyzerSkipSuccess"]

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["line"], 10)

    def test_fixture_findings_ignore_non_code_fail_rows(self) -> None:
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
                findings = harness.fixture_findings(
                    text,
                    "project_sources/collector/fixtures/powershell_analysis/good/control.ps1",
                )

                self.assertFalse(
                    any(finding["rule_name"] == "DCOIR.FailOutputMustFailValidation" for finding in findings)
                )

    def test_fixture_findings_ignore_status_fail_variable_outside_result_object(self) -> None:
        findings = harness.fixture_findings(
            '$Status = "FAIL"\nWrite-Host "bad output"\n',
            "project_sources/collector/fixtures/powershell_analysis/bad/write_host.ps1",
        )
        fail_rows = [finding for finding in findings if finding["rule_name"] == "DCOIR.FailOutputMustFailValidation"]
        write_host = [finding for finding in findings if finding["rule_name"] == "PSAvoidUsingWriteHost"]

        self.assertEqual(fail_rows, [])
        self.assertEqual(len(write_host), 1)
        self.assertEqual(write_host[0]["line"], 2)

    def test_fixture_findings_do_not_treat_comment_or_string_as_here_string_start_for_fail_rows(self) -> None:
        cases = {
            "comment_opener": '# docs @"',
            "quoted_opener": '$message = "docs @"',
        }
        for name, opener in cases.items():
            with self.subTest(name=name):
                findings = harness.fixture_findings(
                    "\n".join(
                        [
                            opener,
                            '$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }',
                            "",
                        ]
                    ),
                    "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
                )
                matching = [
                    finding for finding in findings if finding["rule_name"] == "DCOIR.FailOutputMustFailValidation"
                ]

                self.assertEqual(len(matching), 1)
                self.assertEqual(matching[0]["line"], 2)

    def test_fixture_findings_do_not_treat_comment_or_string_as_block_comment_start_for_fail_rows(self) -> None:
        cases = {
            "comment_opener": "# docs <#",
            "quoted_opener": '$message = "docs <#"',
        }
        for name, opener in cases.items():
            with self.subTest(name=name):
                findings = harness.fixture_findings(
                    "\n".join(
                        [
                            opener,
                            '$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL" }',
                            "",
                        ]
                    ),
                    "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
                )
                matching = [
                    finding for finding in findings if finding["rule_name"] == "DCOIR.FailOutputMustFailValidation"
                ]

                self.assertEqual(len(matching), 1)
                self.assertEqual(matching[0]["line"], 2)

    def test_fixture_findings_track_long_fail_object_until_closing_brace(self) -> None:
        text = "\n".join(
            [
                "$Rows += [pscustomobject]@{",
                '    Check = "Fixture"',
                '    Scope = "Analyzer"',
                '    Rule = "DCOIR.FailOutputMustFailValidation"',
                '    Target = "fixture"',
                '    Category = "validation"',
                '    Surface = "PowerShell"',
                '    Evidence = "row"',
                '    Detail = "bad row"',
                '    Recommendation = "fail closed"',
                '    Status = "FAIL"',
                '    Extra = "more object content"',
                "}",
                'throw "long fail object failed closed"',
                "",
            ]
        )
        findings = harness.fixture_findings(
            text,
            "project_sources/collector/fixtures/powershell_analysis/good/control.ps1",
        )

        self.assertFalse(any(finding["rule_name"] == "DCOIR.FailOutputMustFailValidation" for finding in findings))

    def test_fixture_findings_bind_fail_rows_to_local_failure_action(self) -> None:
        text = "\n".join(
            [
                '$Rows += [pscustomobject]@{ Check = "Safe"; Status = "FAIL" }',
                'throw "safe row failed closed"',
                "",
                '$Rows += [pscustomobject]@{ Check = "Unsafe"; Status = "FAIL" }',
                "",
                "exit 1",
                "",
            ]
        )
        findings = harness.fixture_findings(
            text,
            "project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1",
        )
        matching = [finding for finding in findings if finding["rule_name"] == "DCOIR.FailOutputMustFailValidation"]

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["line"], 4)

    def test_plaintext_password_fixture_uses_parameter_default_shape(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "fixtures/powershell_analysis/bad/plaintext_password.ps1"
        text = fixture.read_text(encoding="utf-8")

        self.assertRegex(text, r"param\(\[string\]\$Password\s*=")
        findings = harness.fixture_findings(text, fixture.as_posix())
        matching = [
            finding
            for finding in findings
            if finding["rule_name"] == "PSAvoidUsingPlainTextForPassword" and finding["line"] == 2
        ]
        self.assertEqual(len(matching), 1)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
