#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import textwrap
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_powershell_analyzer as analyzer


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def update_inventory_sha256(root: Path, rel: str, text: str) -> None:
    inventory_path = root / analyzer.DEFAULT_INVENTORY
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    for surface_record in inventory["surfaces"]:
        if surface_record["path"] == rel:
            surface_record["sha256"] = analyzer.sha256_text(text)
            break
    else:
        raise AssertionError(f"inventory test surface not found: {rel}")
    write(inventory_path, json.dumps(inventory, indent=2) + "\n")


def surface(
    path: str,
    category: str,
    source_type: str,
    decision: str = "include",
    sha256: str = "",
) -> dict[str, object]:
    return {
        "path": path,
        "category": category,
        "source_type": source_type,
        "status": "source" if decision == "include" else "workflow_embedded",
        "inclusion_decision": decision,
        "decision_reason": "test target" if decision == "include" else "reference surface",
        "exists": True,
        "marker_lines": [],
        "embedded_snippets": [],
        "size_bytes": 20,
        "line_count": 1,
        "sha256": sha256,
    }


class PowerShellAnalyzerWrapperTests(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        source_text = "Write-Output 'collector ok'\n"
        harness_text = "Write-Output 'harness ok'\n"
        workflow_text = (
            "jobs:\n"
            "  validate:\n"
            "    steps:\n"
            "      - shell: pwsh\n"
            "        run: Write-Host ok\n"
        )
        write(root / "project_sources/collector/source/DCOIR_Collector.ps1", source_text)
        write(root / "project_sources/collector/harness/run_DCOIR_Tests.ps1", harness_text)
        write(root / ".github/workflows/validate-on-pr.yml", workflow_text)
        write(
            root / "project_sources/collector/PSScriptAnalyzerSettings.psd1",
            textwrap.dedent(
                """\
                # DCOIR_POLICY_ID: dcoir-powershell-analyzer-policy-v1
                # DCOIR_EXCLUSIONS: none
                @{
                    Severity = @('Error', 'Warning')
                    IncludeRules = @(
                        'PSAvoidUsingPlainTextForPassword'
                        'PSAvoidUsingConvertToSecureStringWithPlainText'
                        'PSAvoidUsingInvokeExpression'
                        'PSAvoidUsingWriteHost'
                        'PSUseDeclaredVarsMoreThanAssignments'
                        'PSUseShouldProcessForStateChangingFunctions'
                    )
                    Rules = @{
                        PSAvoidUsingPlainTextForPassword = @{}
                        PSAvoidUsingConvertToSecureStringWithPlainText = @{}
                        PSAvoidUsingInvokeExpression = @{}
                        PSAvoidUsingWriteHost = @{}
                        PSUseDeclaredVarsMoreThanAssignments = @{}
                        PSUseShouldProcessForStateChangingFunctions = @{}
                    }
                }
                """
            ),
        )
        inventory = {
            "schema_version": analyzer.INVENTORY_SCHEMA_VERSION,
            "issue": 261,
            "summary": {"total_surfaces": 3},
            "validation": {"success": True, "errors": [], "warnings": []},
            "surfaces": [
                surface(
                    "project_sources/collector/source/DCOIR_Collector.ps1",
                    "collector_runtime_wrapper",
                    ".ps1",
                    sha256=analyzer.sha256_text(source_text),
                ),
                surface(
                    "project_sources/collector/harness/run_DCOIR_Tests.ps1",
                    "collector_harness_script",
                    ".ps1",
                    sha256=analyzer.sha256_text(harness_text),
                ),
                surface(
                    ".github/workflows/validate-on-pr.yml",
                    "workflow_embedded_powershell",
                    "workflow_yaml",
                    "reference",
                    sha256=analyzer.sha256_text(workflow_text),
                ),
            ],
        }
        write(root / "project_sources/collector/powershell_surface_inventory.json", json.dumps(inventory, indent=2) + "\n")
        write(
            root / "fake_analyzer.py",
            textwrap.dedent(
                """\
                import json
                import sys
                import time
                from pathlib import Path

                mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
                request = json.loads(sys.stdin.read())
                target = request["target"]
                if mode == "crash":
                    print("simulated crash", file=sys.stderr)
                    raise SystemExit(23)
                if mode == "invalid_json":
                    print("{not-json")
                    raise SystemExit(0)
                if mode == "timeout":
                    time.sleep(3)
                if mode == "skip":
                    print(json.dumps({
                        "analyzer_name": "FakePSScriptAnalyzer",
                        "analyzer_version": "1.0.0",
                        "powershell_engine": "Core",
                        "powershell_version": "7.4.1",
                        "target_path": target["path"],
                        "analyzed": False,
                        "skipped_reason": "simulated skip",
                        "findings": [],
                    }))
                    raise SystemExit(0)
                version = "2.0" if mode == "old_version" else "7.4.1"
                text = Path(target["analysis_path"]).read_text(encoding="utf-8")
                findings = []
                if mode != "no_findings" and "Write-Host" in text:
                    findings.append({
                        "path": target["analysis_path"],
                        "line": 1,
                        "column": 1,
                        "symbol": "",
                        "rule_name": "PSAvoidUsingWriteHost",
                        "severity": "Warning",
                        "observed_problem": "Write-Host makes analyzer output noisy and reviewer-hostile.",
                        "recommended_fix": "Use Write-Output or structured logging.",
                    })
                response = {
                    "analyzer_name": "FakePSScriptAnalyzer",
                    "analyzer_version": "1.0.0",
                    "powershell_engine": "Core",
                    "powershell_version": version,
                    "target_path": target["path"],
                    "analyzed": True,
                    "findings": findings,
                }
                if mode == "missing_analyzed":
                    response.pop("analyzed")
                if mode == "null_analyzed":
                    response["analyzed"] = None
                if mode == "string_analyzed":
                    response["analyzed"] = "true"
                if mode == "missing_target_path":
                    response.pop("target_path")
                print(json.dumps(response))
                """
            ),
        )
        return temp

    def make_args(self, root: Path, mode: str = "auto", **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "repo_root": str(root),
            "inventory": analyzer.DEFAULT_INVENTORY.as_posix(),
            "settings": analyzer.DEFAULT_SETTINGS.as_posix(),
            "json_output": analyzer.DEFAULT_JSON_OUTPUT.as_posix(),
            "markdown_output": analyzer.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
            "analyzer_command": [sys.executable, str(root / "fake_analyzer.py"), mode],
            "target_path": [],
            "baseline_json": None,
            "timeout_seconds": 10,
            "minimum_powershell_version": "5.1",
            "fail_on_severity": "Warning",
            "allow_findings": False,
            "expect_finding_rule": None,
            "expect_finding_path": None,
            "expect_no_findings": False,
            "no_write": False,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def required_include_rules_block(self, indent: str = "        ") -> str:
        return "\n".join(f"{indent}'{rule}'" for rule in sorted(analyzer.REQUIRED_POLICY_RULES))

    def required_rule_keys_block(self, indent: str = "        ") -> str:
        return "\n".join(f"{indent}{rule} = @{{}}" for rule in sorted(analyzer.REQUIRED_POLICY_RULES))

    def test_control_report_passes_and_records_counts(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = analyzer.build_report(self.make_args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertIsNotNone(report)
        assert report is not None
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["target_count"], 2)
        self.assertEqual(report["summary"]["analyzed_count"], 2)
        self.assertEqual(report["summary"]["skipped_target_count"], 0)
        self.assertEqual(report["summary"]["reference_or_excluded_surface_count"], 1)
        self.assertEqual(report["analyzer"]["name"], "FakePSScriptAnalyzer")
        self.assertEqual(report["powershell"]["version"], "7.4.1")

    def test_ps1_txt_target_is_staged_and_finding_path_maps_back(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-000.ps1.txt"
            source_part_text = "Write-Host 'bad source part'\n"
            write(root / rel, source_part_text)
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"].append(
                surface(
                    rel,
                    "collector_harness_source_part",
                    ".ps1.txt",
                    sha256=analyzer.sha256_text(source_part_text),
                )
            )
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            args = self.make_args(root, target_path=[rel], allow_findings=True)
            report, errors, _warnings = analyzer.build_report(args)

        self.assertEqual(errors, [])
        assert report is not None
        self.assertEqual(report["findings"][0]["path"], rel)
        self.assertEqual(report["findings"][0]["rule_name"], "PSAvoidUsingWriteHost")
        self.assertEqual(report["targets"][0]["path"], rel)
        self.assertTrue(report["targets"][0]["staged_for_analysis"])
        self.assertNotIn("absolute_path", report["targets"][0])
        self.assertNotIn("analysis_path", report["targets"][0])

    def test_missing_analyzer_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            args = self.make_args(root, analyzer_command=[str(root / "missing_analyzer")])
            report, errors, _warnings = analyzer.build_report(args)

        self.assertIsNotNone(report)
        self.assertTrue(any("analyzer tool missing" in error for error in errors))

    def test_analyzer_crash_fails_closed(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = analyzer.build_report(self.make_args(Path(temp), "crash"))

        self.assertIsNotNone(report)
        self.assertTrue(any("analyzer crash" in error for error in errors))

    def test_analyzer_timeout_fails_closed(self) -> None:
        with self.make_repo() as temp:
            args = self.make_args(Path(temp), "timeout", timeout_seconds=1)
            report, errors, _warnings = analyzer.build_report(args)

        self.assertIsNotNone(report)
        self.assertTrue(any("analyzer timeout" in error for error in errors))

    def test_skipped_target_fails_closed(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = analyzer.build_report(self.make_args(Path(temp), "skip"))

        self.assertIsNotNone(report)
        self.assertTrue(any("intended analyzer target was skipped" in error for error in errors))

    def test_missing_analyzed_field_fails_closed(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = analyzer.build_report(self.make_args(Path(temp), "missing_analyzed"))

        self.assertIsNotNone(report)
        self.assertTrue(any("intended analyzer target was skipped" in error for error in errors))

    def test_null_analyzed_field_fails_closed(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = analyzer.build_report(self.make_args(Path(temp), "null_analyzed"))

        self.assertIsNotNone(report)
        self.assertTrue(any("intended analyzer target was skipped" in error for error in errors))

    def test_string_analyzed_field_fails_closed(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = analyzer.build_report(self.make_args(Path(temp), "string_analyzed"))

        self.assertIsNotNone(report)
        self.assertTrue(any("intended analyzer target was skipped" in error for error in errors))

    def test_missing_target_path_fails_closed(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = analyzer.build_report(self.make_args(Path(temp), "missing_target_path"))

        self.assertIsNotNone(report)
        self.assertTrue(any("missing target_path" in error for error in errors))

    def test_unsupported_powershell_version_fails_closed(self) -> None:
        with self.make_repo() as temp:
            report, errors, _warnings = analyzer.build_report(self.make_args(Path(temp), "old_version"))

        self.assertIsNotNone(report)
        self.assertTrue(any("unsupported PowerShell version" in error for error in errors))

    def test_missing_policy_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            (root / analyzer.DEFAULT_SETTINGS).unlink()
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("analyzer settings file is missing" in error for error in errors))

    def test_invalid_policy_fails_on_broad_exclusion(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / analyzer.DEFAULT_SETTINGS, "# DCOIR_POLICY_ID: test\n@{ Severity=@('Information'); ExcludeRules=@('*'); Rules=@{} }\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("wildcard ExcludeRules" in error for error in errors))

    def test_policy_requires_error_and_warning_severities(self) -> None:
        for severity_value in ("@('Error')", "@('Information')", "@('Information', 'Error')"):
            with self.subTest(severity_value=severity_value):
                with self.make_repo() as temp:
                    root = Path(temp)
                    settings = (root / analyzer.DEFAULT_SETTINGS).read_text(encoding="utf-8")
                    settings = settings.replace("Severity = @('Error', 'Warning')", f"Severity = {severity_value}")
                    write(root / analyzer.DEFAULT_SETTINGS, settings)
                    report, errors, _warnings = analyzer.build_report(self.make_args(root))

                self.assertIsNotNone(report)
                self.assertTrue(any("missing active Severity entries" in error for error in errors))

    def test_scalar_wildcard_exclude_rules_fail_closed(self) -> None:
        for excluded in ("'*'", "'PS*'"):
            with self.subTest(excluded=excluded):
                with self.make_repo() as temp:
                    root = Path(temp)
                    settings = (root / analyzer.DEFAULT_SETTINGS).read_text(encoding="utf-8")
                    settings = settings.replace("    Rules = @{", f"    ExcludeRules = {excluded}\n    Rules = @{{")
                    write(root / analyzer.DEFAULT_SETTINGS, settings)
                    report, errors, _warnings = analyzer.build_report(self.make_args(root))

                self.assertIsNotNone(report)
                self.assertTrue(any("ExcludeRules are not allowed" in error for error in errors))

    def test_case_variant_exclude_rules_fail_closed(self) -> None:
        for key, excluded in (("excluderules", "'*'"), ("EXCLUDERULES", "'PS*'")):
            with self.subTest(key=key, excluded=excluded):
                with self.make_repo() as temp:
                    root = Path(temp)
                    settings = (root / analyzer.DEFAULT_SETTINGS).read_text(encoding="utf-8")
                    settings = settings.replace("    Rules = @{", f"    {key} = {excluded}\n    Rules = @{{")
                    write(root / analyzer.DEFAULT_SETTINGS, settings)
                    report, errors, _warnings = analyzer.build_report(self.make_args(root))

                self.assertIsNotNone(report)
                self.assertTrue(any("ExcludeRules are not allowed" in error for error in errors))

    def test_multiline_wildcard_exclude_rules_fail_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            settings = (root / analyzer.DEFAULT_SETTINGS).read_text(encoding="utf-8")
            settings = settings.replace(
                "    Rules = @{",
                "    ExcludeRules = @(\n"
                "        'PS*'\n"
                "    )\n"
                "    Rules = @{",
            )
            write(root / analyzer.DEFAULT_SETTINGS, settings)
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("broad PS* ExcludeRules" in error for error in errors))

    def test_comment_only_required_rules_do_not_satisfy_policy(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            comments = "\n".join(f"# {rule}" for rule in sorted(analyzer.REQUIRED_POLICY_RULES))
            write(
                root / analyzer.DEFAULT_SETTINGS,
                "# DCOIR_POLICY_ID: dcoir-powershell-analyzer-policy-v1\n"
                f"{comments}\n"
                "@{ Severity=@('Error','Warning'); IncludeRules=@(); Rules=@{} }\n",
            )
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("missing active IncludeRules entries" in error for error in errors))
        self.assertTrue(any("missing active Rules keys" in error for error in errors))

    def test_nested_decoy_policy_does_not_satisfy_top_level_policy(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(
                root / analyzer.DEFAULT_SETTINGS,
                textwrap.dedent(
                    f"""\
                    # DCOIR_POLICY_ID: dcoir-powershell-analyzer-policy-v1
                    @{{
                        Metadata = @{{
                            Severity = @('Error', 'Warning')
                            IncludeRules = @(
                    {self.required_include_rules_block("            ")}
                            )
                            Rules = @{{
                    {self.required_rule_keys_block("            ")}
                            }}
                            ExcludeRules = @()
                        }}
                        Severity = @('Information')
                        IncludeRules = @()
                        Rules = @{{}}
                        ExcludeRules = @('*')
                    }}
                    """
                ),
            )
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("missing active Severity entries" in error for error in errors))
        self.assertTrue(any("missing active IncludeRules entries" in error for error in errors))
        self.assertTrue(any("missing active Rules keys" in error for error in errors))
        self.assertTrue(any("wildcard ExcludeRules" in error for error in errors))

    def test_duplicate_top_level_policy_assignments_fail_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            settings = (root / analyzer.DEFAULT_SETTINGS).read_text(encoding="utf-8")
            settings = settings.replace(
                "    IncludeRules = @(",
                "    Severity = @('Error', 'Warning')\n    IncludeRules = @(",
            )
            write(root / analyzer.DEFAULT_SETTINGS, settings)
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("duplicate top-level Severity" in error for error in errors))

    def test_case_variant_duplicate_top_level_policy_assignments_fail_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            settings = (root / analyzer.DEFAULT_SETTINGS).read_text(encoding="utf-8")
            settings = settings.replace(
                "    IncludeRules = @(",
                "    severity = @('Error', 'Warning')\n    IncludeRules = @(",
            )
            write(root / analyzer.DEFAULT_SETTINGS, settings)
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("duplicate top-level Severity" in error for error in errors))

    def test_nested_required_rule_names_do_not_satisfy_rules_keys(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            nested_rules = "\n".join(f"            {rule} = @{{}}" for rule in sorted(analyzer.REQUIRED_POLICY_RULES))
            settings = (root / analyzer.DEFAULT_SETTINGS).read_text(encoding="utf-8")
            settings = settings.replace(
                "    Rules = @{\n"
                "        PSAvoidUsingPlainTextForPassword = @{}\n"
                "        PSAvoidUsingConvertToSecureStringWithPlainText = @{}\n"
                "        PSAvoidUsingInvokeExpression = @{}\n"
                "        PSAvoidUsingWriteHost = @{}\n"
                "        PSUseDeclaredVarsMoreThanAssignments = @{}\n"
                "        PSUseShouldProcessForStateChangingFunctions = @{}\n"
                "    }",
                "    Rules = @{\n"
                "        SomeOtherRule = @{\n"
                f"{nested_rules}\n"
                "        }\n"
                "    }",
            )
            write(root / analyzer.DEFAULT_SETTINGS, settings)
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("missing active Rules keys" in error for error in errors))

    def test_policy_requires_rules_assignment_not_only_include_rules(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(
                root / analyzer.DEFAULT_SETTINGS,
                textwrap.dedent(
                    """\
                    # DCOIR_POLICY_ID: dcoir-powershell-analyzer-policy-v1
                    @{
                        Severity = @('Error', 'Warning')
                        IncludeRules = @(
                            'PSAvoidUsingPlainTextForPassword'
                            'PSAvoidUsingConvertToSecureStringWithPlainText'
                            'PSAvoidUsingInvokeExpression'
                            'PSAvoidUsingWriteHost'
                            'PSUseDeclaredVarsMoreThanAssignments'
                            'PSUseShouldProcessForStateChangingFunctions'
                        )
                    }
                    """
                ),
            )
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("missing Rules declaration" in error for error in errors))

    def test_invalid_inventory_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / analyzer.DEFAULT_INVENTORY, "{not-json")
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("invalid JSON" in error for error in errors))

    def test_missing_inventory_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            (root / analyzer.DEFAULT_INVENTORY).unlink()
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("PowerShell surface inventory is missing" in error for error in errors))

    def test_absolute_inventory_path_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "/tmp/dcoir-outside.ps1"
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"].append(surface(rel, "collector_runtime_wrapper", ".ps1"))
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root, target_path=[rel]))

        self.assertIsNotNone(report)
        self.assertTrue(any("inventory path must be repo-relative" in error for error in errors))

    def test_parent_traversal_inventory_path_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "../outside.ps1"
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"].append(surface(rel, "collector_runtime_wrapper", ".ps1"))
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root, target_path=[rel]))

        self.assertIsNotNone(report)
        self.assertTrue(any("inventory path must not contain parent traversal" in error for error in errors))

    def test_ps1_txt_parent_traversal_staging_path_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/harness/source/parts/../../outside.ps1.txt"
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"].append(surface(rel, "collector_harness_source_part", ".ps1.txt"))
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root, target_path=[rel]))

        self.assertIsNotNone(report)
        self.assertTrue(any("inventory path must not contain parent traversal" in error for error in errors))

    def test_stale_inventory_hash_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/source/DCOIR_Collector.ps1"
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"][0]["sha256"] = "0" * 64
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root, target_path=[rel]))

        self.assertIsNotNone(report)
        self.assertTrue(any("inventory sha256 does not match current file content" in error for error in errors))

    def test_missing_inventory_hash_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/source/DCOIR_Collector.ps1"
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"][0]["sha256"] = ""
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root, target_path=[rel]))

        self.assertIsNotNone(report)
        self.assertTrue(any("inventory sha256 is missing or invalid" in error for error in errors))

    def test_stale_reference_workflow_inventory_hash_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"][2]["sha256"] = "0" * 64
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("inventory sha256 does not match current file content" in error for error in errors))

    def test_missing_reference_workflow_inventory_hash_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"][2]["sha256"] = ""
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("inventory sha256 is missing or invalid" in error for error in errors))

    def test_stale_reference_workflow_hash_fails_with_target_filter(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/source/DCOIR_Collector.ps1"
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"][2]["sha256"] = "0" * 64
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root, target_path=[rel]))

        self.assertIsNotNone(report)
        self.assertTrue(any("inventory sha256 does not match current file content" in error for error in errors))

    def test_inventory_hash_accepts_line_ending_normalized_match(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/source/DCOIR_Collector.ps1"
            (root / rel).write_bytes(b"Write-Output 'collector ok'\r\n")
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"][0]["sha256"] = analyzer.sha256_text("Write-Output 'collector ok'\n")
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root, target_path=[rel]))

        self.assertIsNotNone(report)
        self.assertEqual(errors, [])

    def test_empty_intended_target_set_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            workflow_text = (root / ".github/workflows/validate-on-pr.yml").read_text(encoding="utf-8")
            inventory = json.loads((root / analyzer.DEFAULT_INVENTORY).read_text(encoding="utf-8"))
            inventory["surfaces"] = [
                surface(
                    ".github/workflows/validate-on-pr.yml",
                    "workflow_embedded_powershell",
                    "workflow_yaml",
                    "reference",
                    sha256=analyzer.sha256_text(workflow_text),
                )
            ]
            write(root / analyzer.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
            report, errors, _warnings = analyzer.build_report(self.make_args(root))

        self.assertIsNotNone(report)
        self.assertTrue(any("intended target set is empty" in error for error in errors))

    def test_expected_bad_fixture_without_findings_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            bad = root / "project_sources/collector/source/DCOIR_Collector.ps1"
            bad_text = "Write-Host 'should be caught'\n"
            bad.write_text(bad_text, encoding="utf-8")
            update_inventory_sha256(root, "project_sources/collector/source/DCOIR_Collector.ps1", bad_text)
            args = self.make_args(
                root,
                "no_findings",
                target_path=["project_sources/collector/source/DCOIR_Collector.ps1"],
                allow_findings=True,
                expect_finding_rule="PSAvoidUsingWriteHost",
                expect_finding_path="project_sources/collector/source/DCOIR_Collector.ps1",
            )
            report, errors, _warnings = analyzer.build_report(args)

        self.assertIsNotNone(report)
        self.assertTrue(any("expected analyzer finding PSAvoidUsingWriteHost" in error for error in errors))

    def test_bad_fixture_finding_fails_and_normalizes(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/source/DCOIR_Collector.ps1"
            bad_text = "Write-Host 'bad'\n"
            write(root / rel, bad_text)
            update_inventory_sha256(root, rel, bad_text)
            args = self.make_args(root, target_path=[rel])
            report, errors, _warnings = analyzer.build_report(args)

        self.assertIsNotNone(report)
        assert report is not None
        self.assertTrue(any("unsuppressed analyzer findings" in error for error in errors))
        self.assertEqual(report["findings"][0]["path"], rel)
        self.assertEqual(report["findings"][0]["rule_name"], "PSAvoidUsingWriteHost")
        self.assertEqual(report["findings"][0]["severity"], "Warning")

    def test_baseline_parse_failure_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            baseline = root / "bad-baseline.json"
            write(baseline, "{not-json")
            report, errors, _warnings = analyzer.build_report(self.make_args(root, baseline_json=str(baseline)))

        self.assertIsNotNone(report)
        self.assertTrue(any("baseline" in error and "invalid JSON" in error for error in errors))

    def test_suppressed_rule_mismatch_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            baseline = root / "baseline.json"
            write(
                baseline,
                json.dumps(
                    {
                        "schema_version": analyzer.BASELINE_SCHEMA_VERSION,
                        "suppressions": [
                            {
                                "path": "project_sources/collector/source/DCOIR_Collector.ps1",
                                "rule_name": "PSAvoidUsingWriteHost",
                                "fingerprint": "0" * 64,
                                "reason": "test",
                            }
                        ],
                    }
                ),
            )
            report, errors, _warnings = analyzer.build_report(self.make_args(root, baseline_json=str(baseline)))

        self.assertIsNotNone(report)
        self.assertTrue(any("suppressed-rule mismatch" in error for error in errors))

    def test_baseline_suppression_requires_fingerprint(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            baseline = root / "baseline.json"
            write(
                baseline,
                json.dumps(
                    {
                        "schema_version": analyzer.BASELINE_SCHEMA_VERSION,
                        "suppressions": [
                            {
                                "path": "project_sources/collector/source/DCOIR_Collector.ps1",
                                "rule_name": "PSAvoidUsingWriteHost",
                                "reason": "test",
                            }
                        ],
                    }
                ),
            )
            report, errors, _warnings = analyzer.build_report(self.make_args(root, baseline_json=str(baseline)))

        self.assertIsNotNone(report)
        self.assertTrue(any("baseline suppression missing fingerprint" in error for error in errors))

    def test_baseline_suppression_must_match_one_finding(self) -> None:
        finding = {
            "path": "project_sources/collector/source/DCOIR_Collector.ps1",
            "rule_name": "PSAvoidUsingWriteHost",
            "fingerprint": "abc",
            "suppressed_by_baseline": False,
        }
        errors = analyzer.apply_baseline(
            [finding.copy(), finding.copy()],
            {
                "schema_version": analyzer.BASELINE_SCHEMA_VERSION,
                "suppressions": [
                    {
                        "path": finding["path"],
                        "rule_name": finding["rule_name"],
                        "fingerprint": finding["fingerprint"],
                        "reason": "duplicate fixture",
                    }
                ],
            },
        )

        self.assertTrue(any("matched 2 analyzer findings, expected 1" in error for error in errors))

    def test_duplicate_baseline_suppressions_fail_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            baseline = root / "baseline.json"
            suppression = {
                "path": "project_sources/collector/source/DCOIR_Collector.ps1",
                "rule_name": "PSAvoidUsingWriteHost",
                "fingerprint": "abc",
                "reason": "duplicate fixture",
            }
            write(
                baseline,
                json.dumps(
                    {
                        "schema_version": analyzer.BASELINE_SCHEMA_VERSION,
                        "suppressions": [suppression, suppression],
                    }
                ),
            )
            report, errors, _warnings = analyzer.build_report(self.make_args(root, baseline_json=str(baseline)))

        self.assertIsNotNone(report)
        self.assertTrue(any("baseline duplicate suppression" in error for error in errors))

    def test_matching_baseline_suppresses_finding(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/source/DCOIR_Collector.ps1"
            bad_text = "Write-Host 'baseline accepted for now'\n"
            write(root / rel, bad_text)
            update_inventory_sha256(root, rel, bad_text)
            initial_report, initial_errors, _warnings = analyzer.build_report(
                self.make_args(root, target_path=[rel], allow_findings=True)
            )
            self.assertEqual(initial_errors, [])
            assert initial_report is not None
            fingerprint = initial_report["findings"][0]["fingerprint"]
            baseline = root / "baseline.json"
            write(
                baseline,
                json.dumps(
                    {
                        "schema_version": analyzer.BASELINE_SCHEMA_VERSION,
                        "suppressions": [
                            {
                                "path": rel,
                                "rule_name": "PSAvoidUsingWriteHost",
                                "fingerprint": fingerprint,
                                "reason": "temporary reviewed baseline in test",
                            }
                        ],
                    }
                ),
            )
            report, errors, _warnings = analyzer.build_report(
                self.make_args(root, target_path=[rel], baseline_json=str(baseline))
            )

        self.assertEqual(errors, [])
        assert report is not None
        self.assertEqual(report["summary"]["suppressed_finding_count"], 1)
        self.assertEqual(report["summary"]["unsuppressed_finding_count"], 0)
        self.assertEqual(report["baseline"]["matched_suppression_count"], 1)
        self.assertEqual(report["baseline"]["suppression_keys"][0]["fingerprint"], fingerprint)

    def test_report_write_failure_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report, errors, _warnings = analyzer.build_report(self.make_args(root))
            self.assertEqual(errors, [])
            assert report is not None
            (root / "output-as-directory").mkdir()
            with self.assertRaises(analyzer.AnalyzerContractError) as caught:
                analyzer.write_outputs(root, report, Path("output-as-directory"), Path("report.md"))

        self.assertIn("report write failure", str(caught.exception))

    def test_markdown_report_write_failure_fails_closed(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report, errors, _warnings = analyzer.build_report(self.make_args(root))
            self.assertEqual(errors, [])
            assert report is not None
            (root / "markdown-output-as-directory").mkdir()
            with self.assertRaises(analyzer.AnalyzerContractError) as caught:
                analyzer.write_outputs(root, report, Path("report.json"), Path("markdown-output-as-directory"))

        self.assertIn("report write failure", str(caught.exception))

    def test_cli_rewrites_json_as_failed_when_markdown_write_fails(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            (root / "markdown-output-as-directory").mkdir()
            argv = [
                "run_powershell_analyzer.py",
                "--repo-root",
                str(root),
                "--analyzer-command",
                sys.executable,
                "--analyzer-command",
                str(root / "fake_analyzer.py"),
                "--analyzer-command",
                "auto",
                "--json-output",
                "report.json",
                "--markdown-output",
                "markdown-output-as-directory",
            ]
            with unittest.mock.patch.object(sys, "argv", argv):
                rc = analyzer.main()
            written = json.loads((root / "report.json").read_text(encoding="utf-8"))

        self.assertEqual(rc, 1)
        self.assertFalse(written["validation"]["success"])
        self.assertTrue(any("report write failure" in error for error in written["validation"]["errors"]))

    def test_setup_failure_report_can_be_written(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            args = self.make_args(root, analyzer_command=[])
            with unittest.mock.patch.object(analyzer.shutil, "which", return_value=None):
                report, errors, _warnings = analyzer.build_report(args)
            self.assertIsNotNone(report)
            self.assertTrue(any("analyzer tool missing" in error for error in errors))
            assert report is not None
            analyzer.write_outputs(root, report, Path("failure-report.json"), Path("failure-report.md"))
            written = json.loads((root / "failure-report.json").read_text(encoding="utf-8"))

        self.assertFalse(written["validation"]["success"])
        self.assertEqual(written["analyzer"]["name"], "not_run")
        self.assertTrue(any("analyzer tool missing" in error for error in written["validation"]["errors"]))


if __name__ == "__main__":
    unittest.main()
