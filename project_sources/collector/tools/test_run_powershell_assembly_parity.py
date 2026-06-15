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
import run_powershell_assembly_parity as parity


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PowerShellAssemblyParityTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        collector_part_text: str = 'function Invoke-CollectorPart { Write-Output "ok" }\n',
        harness_part_text: str = 'function Invoke-HarnessPart { Write-Output "ok" }\n',
        checked_in_harness_text: str | None = None,
        manifest_wrapper: str | None = None,
        manifest_parts: list[str] | None = None,
    ) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        wrapper = "project_sources/collector/source/DCOIR_Collector.ps1"
        collector_part = "project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1"
        harness_part = "project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-000.ps1.txt"
        write(
            root / wrapper,
            textwrap.dedent(
                """\
                [CmdletBinding()]
                param()
                $collectorPartsRoot = Join-Path $PSScriptRoot 'parts'
                $collectorPartFiles = @()
                foreach ($partFile in $collectorPartFiles) {
                  . $partFile
                }
                function Invoke-DCOIRWrapper { Write-Output "wrapper" }
                """
            ),
        )
        write(root / collector_part, collector_part_text)
        write(root / harness_part, harness_part_text)
        if checked_in_harness_text is not None:
            write(root / parity.HARNESS_GENERATED_OUTPUT, checked_in_harness_text)
        part_list = [collector_part] if manifest_parts is None else manifest_parts
        manifest = {
            "source_strategy": "compile_single_runtime_then_package",
            "collector_wrapper_source": wrapper if manifest_wrapper is None else manifest_wrapper,
            "collector_part_files": part_list,
            "compiled_runtime_name": "DCOIR_Collector.ps1",
        }
        inventory = {
            "schema_version": "dcoir_powershell_surface_inventory_v1",
            "controls": {
                "collector_manifest": {
                    "expected_path_count": 1 + len(part_list),
                    "present_path_count": 1 + len(part_list),
                    "paths": [],
                },
                "harness_source_parts": {
                    "part_count": 1,
                    "parts": [],
                },
                "generated_outputs": [
                    {
                        "path": parity.HARNESS_GENERATED_OUTPUT.as_posix(),
                        "expected_presence": "optional_when_generated",
                        "exists": checked_in_harness_text is not None,
                    }
                ],
            },
            "summary": {"total_surfaces": 3},
            "validation": {"success": True, "errors": [], "warnings": []},
            "surfaces": [],
        }
        write(root / parity.DEFAULT_MANIFEST, json.dumps(manifest, indent=2) + "\n")
        write(root / parity.DEFAULT_INVENTORY, json.dumps(inventory, indent=2) + "\n")
        return temp

    def args(self, root: Path, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "repo_root": str(root),
            "manifest": parity.DEFAULT_MANIFEST.as_posix(),
            "inventory": parity.DEFAULT_INVENTORY.as_posix(),
            "json_output": parity.DEFAULT_JSON_OUTPUT.as_posix(),
            "markdown_output": parity.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
            "baseline_report": "",
            "shrink_exception": [],
            "no_write": True,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_clean_control_passes_and_maps_counts(self) -> None:
        with self.make_repo(checked_in_harness_text='function Invoke-HarnessPart { Write-Output "ok" }\n') as temp:
            report, errors, warnings = parity.build_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertTrue(warnings)
        self.assertEqual(report["summary"]["collector_source_part_count"], 1)
        self.assertEqual(report["summary"]["harness_source_part_count"], 1)
        self.assertEqual(report["summary"]["generated_output_count"], 2)
        self.assertEqual(report["summary"]["parse_status"], "pass")
        self.assertEqual(report["summary"]["parity_status"], "pass")
        self.assertTrue(all(output["line_mapping"] for output in report["generated_outputs"]))

    def test_stale_checked_in_generated_output_fails(self) -> None:
        with self.make_repo(checked_in_harness_text='Write-Output "stale"\n') as temp:
            report, errors, _warnings = parity.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("checked-in generated harness is stale" in error for error in errors))

    def test_missing_source_part_fails(self) -> None:
        missing = "project_sources/collector/source/parts/DCOIR_Collector.99_Missing.ps1"
        with self.make_repo(manifest_parts=[missing]) as temp:
            report, errors, _warnings = parity.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("collector source part is missing" in error for error in errors))

    def assert_manifest_path_rejected(
        self,
        *,
        expected_error_fragment: str,
        manifest_wrapper: str | None = None,
        manifest_parts: list[str] | None = None,
    ) -> None:
        with self.make_repo(manifest_wrapper=manifest_wrapper, manifest_parts=manifest_parts) as temp:
            report, errors, _warnings = parity.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any(expected_error_fragment in error for error in errors), errors)

    def test_literal_dot_slash_manifest_paths_pass(self) -> None:
        wrapper = "project_sources/collector/source/DCOIR_Collector.ps1"
        collector_part = "project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1"
        with self.make_repo(
            manifest_wrapper="./" + wrapper,
            manifest_parts=["./" + collector_part],
            checked_in_harness_text='function Invoke-HarnessPart { Write-Output "ok" }\n',
        ) as temp:
            report, errors, _warnings = parity.build_report(self.args(Path(temp)))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["collector_source_part_count"], 1)

    def test_absolute_collector_wrapper_path_fails_before_normalization(self) -> None:
        self.assert_manifest_path_rejected(
            manifest_wrapper="/project_sources/collector/source/DCOIR_Collector.ps1",
            expected_error_fragment="collector manifest: collector_wrapper_source must be a repo-relative path without traversal",
        )

    def test_parent_traversal_collector_wrapper_path_fails_before_normalization(self) -> None:
        self.assert_manifest_path_rejected(
            manifest_wrapper="../project_sources/collector/source/DCOIR_Collector.ps1",
            expected_error_fragment="collector manifest: collector_wrapper_source must be a repo-relative path without traversal",
        )

    def test_absolute_collector_part_path_fails_before_normalization(self) -> None:
        self.assert_manifest_path_rejected(
            manifest_parts=["/project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1"],
            expected_error_fragment="collector manifest: collector_part_files[1] must be a repo-relative path without traversal",
        )

    def test_windows_parent_traversal_collector_part_path_fails_before_normalization(self) -> None:
        unsafe_part = "..\\project_sources\\collector\\source\\parts\\DCOIR_Collector.01_Core.ps1"
        self.assert_manifest_path_rejected(
            manifest_parts=[unsafe_part],
            expected_error_fragment="collector manifest: collector_part_files[1] must be a repo-relative path without traversal",
        )

    def test_missing_source_output_mapping_fails(self) -> None:
        with self.make_repo(manifest_parts=[]) as temp:
            report, errors, _warnings = parity.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("collector_part_files must be a non-empty list" in error for error in errors))
        self.assertTrue(any("source/output mapping is missing" in error for error in errors))

    def test_generated_output_parse_failure_fails(self) -> None:
        with self.make_repo(collector_part_text="function Broken {\n") as temp:
            report, errors, _warnings = parity.build_report(self.args(Path(temp)))

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("generated output parse check failed" in error for error in errors))

    def test_native_parser_uses_file_argument_for_temp_path(self) -> None:
        captured: dict[str, list[str]] = {}

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        def fake_run(command: list[str], **_kwargs: object) -> Completed:
            captured["command"] = command
            parser_path = Path(command[-2])
            target_path = Path(command[-1])
            self.assertTrue(parser_path.is_file())
            self.assertTrue(target_path.is_file())
            self.assertIn("Parser]::ParseFile", parser_path.read_text(encoding="utf-8"))
            self.assertEqual(target_path.read_text(encoding="utf-8"), 'Write-Output "ok"\n')
            return Completed()

        original_which = parity.shutil.which
        original_run = parity.subprocess.run
        try:
            parity.shutil.which = lambda _name: "pwsh"
            parity.subprocess.run = fake_run
            report = parity.parse_powershell_text('Write-Output "ok"\n')
        finally:
            parity.shutil.which = original_which
            parity.subprocess.run = original_run

        command = captured["command"]
        self.assertEqual(report["method"], "powershell_language_parser")
        self.assertTrue(report["success"])
        self.assertIn("-File", command)
        self.assertNotIn("-Command", command)
        self.assertFalse(Path(command[-2]).exists())
        self.assertFalse(Path(command[-1]).exists())

    def test_native_parser_reports_temp_cleanup_failure(self) -> None:
        captured_paths: list[Path] = []

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        def fake_run(command: list[str], **_kwargs: object) -> Completed:
            captured_paths.extend([Path(command[-2]), Path(command[-1])])
            return Completed()

        original_which = parity.shutil.which
        original_run = parity.subprocess.run
        original_unlink = parity.Path.unlink

        def fail_unlink(path: Path, *args: object, **kwargs: object) -> None:
            if path in captured_paths:
                raise OSError("locked")
            original_unlink(path, *args, **kwargs)

        try:
            parity.shutil.which = lambda _name: "pwsh"
            parity.subprocess.run = fake_run
            parity.Path.unlink = fail_unlink
            report = parity.parse_powershell_text('Write-Output "ok"\n')
        finally:
            parity.shutil.which = original_which
            parity.subprocess.run = original_run
            parity.Path.unlink = original_unlink
            for path in captured_paths:
                if path.exists():
                    path.unlink()

        self.assertFalse(report["success"])
        self.assertTrue(
            any("failed to remove temporary PowerShell" in error for error in report["errors"])
        )

    def test_baseline_shrink_without_exception_fails(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            baseline = {
                "schema_version": parity.SCHEMA_VERSION,
                "summary": {
                    "collector_source_part_count": 2,
                    "harness_source_part_count": 1,
                    "source_part_count": 3,
                    "generated_output_count": 2,
                },
            }
            baseline_path = root / "baseline.json"
            write(baseline_path, json.dumps(baseline, indent=2) + "\n")
            report, errors, _warnings = parity.build_report(
                self.args(root, baseline_report="baseline.json")
            )

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("unexpectedly shrank without approved exception" in error for error in errors))

    def test_real_repo_contract_passes(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        report, errors, _warnings = parity.build_report(self.args(repo_root))

        self.assertEqual(errors, [])
        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["collector_source_part_count"], 18)
        self.assertEqual(report["summary"]["harness_source_part_count"], 12)
        self.assertEqual(report["summary"]["generated_output_count"], 2)
        self.assertEqual(report["summary"]["parse_status"], "pass")
        self.assertEqual(report["summary"]["parity_status"], "pass")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
