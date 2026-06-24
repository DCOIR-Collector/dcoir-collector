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
import run_powershell_function_reachability_report as reach

REPO_ROOT = Path(__file__).resolve().parents[3]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PowerShellFunctionReachabilityReportTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        wrapper_text: str,
        part_texts: dict[str, str],
    ) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        wrapper_path = "project_sources/collector/source/DCOIR_Collector.ps1"
        part_paths = [f"project_sources/collector/source/parts/{name}" for name in part_texts]
        write(root / wrapper_path, textwrap.dedent(wrapper_text))
        for name, text in part_texts.items():
            write(root / "project_sources/collector/source/parts" / name, textwrap.dedent(text))
        write(
            root / reach.DEFAULT_MANIFEST,
            json.dumps(
                {
                    "collector_wrapper_source": wrapper_path,
                    "collector_part_files": part_paths,
                },
                indent=2,
            )
            + "\n",
        )
        return temp

    def args(self, root: Path, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "repo_root": str(root),
            "manifest": reach.DEFAULT_MANIFEST.as_posix(),
            "json_output": reach.DEFAULT_JSON_OUTPUT.as_posix(),
            "markdown_output": reach.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
            "parser_mode": "python_lexical_fallback",
            "entrypoint": [],
            "no_write": True,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def build(self, root: Path, **overrides: object) -> dict[str, object]:
        return reach.build_report(self.args(root, **overrides))

    def test_real_collector_scope_counts_match_report_only_contract(self) -> None:
        report = self.build(REPO_ROOT)

        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["source_file_count"], 19)
        self.assertEqual(report["summary"]["function_count"], 159)
        self.assertEqual(report["summary"]["classification_counts"]["literal_referenced"], 155)
        self.assertEqual(report["summary"]["classification_counts"]["dynamic_invocation_uncertain"], 4)
        self.assertEqual(report["summary"]["classification_counts"].get("static_unreferenced", 0), 0)
        self.assertEqual(report["summary"]["coverage_state"], "not_collected")
        self.assertEqual(report["summary"]["dynamic_invocation_site_count"], 1)
        self.assertTrue(any("safe to delete" in claim for claim in report["non_claims"]))

    def test_markdown_parity_carries_scope_counts_dynamic_sites_and_non_claims(self) -> None:
        report = self.build(REPO_ROOT)
        markdown = reach.render_markdown(report)

        self.assertEqual([], reach.validate_report(report))
        for fragment in (
            "PowerShell Function Reachability Report",
            "Runtime-lane coverage: `not_collected`",
            "`dynamic_invocation_uncertain` | 4",
            "This report does not claim any function is safe to delete.",
            "project_sources/collector/source/DCOIR_Collector.ps1",
        ):
            self.assertIn(fragment, markdown)

    def test_python_fallback_tracks_cross_file_literal_references_before_dynamic_uncertainty(self) -> None:
        with self.make_repo(
            wrapper_text="""
            function Invoke-Wrapper { Invoke-PartOne }
            . $partPath
            """,
            part_texts={
                "PartA.ps1": """
                function Invoke-PartOne { Invoke-PartTwo }
                function Invoke-Uncalled { 'not directly called' }
                """,
                "PartB.ps1": """
                function Invoke-PartTwo { Invoke-Wrapper }
                """,
            },
        ) as temp:
            report = self.build(Path(temp))

        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["function_count"], 4)
        self.assertEqual(report["summary"]["classification_counts"]["literal_referenced"], 3)
        self.assertEqual(report["summary"]["classification_counts"]["dynamic_invocation_uncertain"], 1)
        self.assertEqual(report["summary"]["dynamic_invocation_site_count"], 1)
        by_name = {item["name"]: item for item in report["functions"]}
        self.assertEqual(by_name["Invoke-Uncalled"]["classification"], "dynamic_invocation_uncertain")
        self.assertEqual(by_name["Invoke-PartTwo"]["reference_count"], 1)

    def test_static_unreferenced_is_bounded_when_no_dynamic_sites_exist(self) -> None:
        with self.make_repo(
            wrapper_text="""
            function Invoke-Wrapper { Invoke-PartOne }
            """,
            part_texts={
                "PartA.ps1": """
                function Invoke-PartOne { 'called' }
                function Invoke-Uncalled { 'not called' }
                """,
            },
        ) as temp:
            report = self.build(Path(temp), entrypoint=["Invoke-Wrapper"])

        self.assertTrue(report["validation"]["success"])
        self.assertEqual(report["summary"]["classification_counts"]["entrypoint"], 1)
        self.assertEqual(report["summary"]["classification_counts"]["literal_referenced"], 1)
        self.assertEqual(report["summary"]["classification_counts"]["static_unreferenced"], 1)
        by_name = {item["name"]: item for item in report["functions"]}
        self.assertEqual(by_name["Invoke-Uncalled"]["classification"], "static_unreferenced")
        self.assertIn("not deletion proof", by_name["Invoke-Uncalled"]["claim"])

    def test_comments_and_strings_do_not_create_literal_references(self) -> None:
        with self.make_repo(
            wrapper_text="""
            function Invoke-Wrapper { 'Invoke-CommentOnly in string' }
            # Invoke-CommentOnly in comment
            """,
            part_texts={
                "PartA.ps1": """
                function Invoke-CommentOnly { 'not called' }
                """,
            },
        ) as temp:
            report = self.build(Path(temp), entrypoint=["Invoke-Wrapper"])

        self.assertTrue(report["validation"]["success"])
        by_name = {item["name"]: item for item in report["functions"]}
        self.assertEqual(by_name["Invoke-CommentOnly"]["reference_count"], 0)
        self.assertEqual(by_name["Invoke-CommentOnly"]["classification"], "static_unreferenced")

    def test_missing_manifest_source_fails_closed(self) -> None:
        with self.make_repo(
            wrapper_text="function Invoke-Wrapper { }\n",
            part_texts={"PartA.ps1": "function Invoke-PartOne { }\n"},
        ) as temp:
            root = Path(temp)
            manifest = json.loads((root / reach.DEFAULT_MANIFEST).read_text(encoding="utf-8"))
            manifest["collector_part_files"].append("project_sources/collector/source/parts/Missing.ps1")
            write(root / reach.DEFAULT_MANIFEST, json.dumps(manifest, indent=2) + "\n")
            report = self.build(root)

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(any("collector runtime source is missing" in error for error in report["validation"]["errors"]))

    def test_unsafe_output_and_output_alias_are_rejected_before_write(self) -> None:
        with self.make_repo(
            wrapper_text="function Invoke-Wrapper { }\n",
            part_texts={"PartA.ps1": "function Invoke-PartOne { }\n"},
        ) as temp:
            root = Path(temp)
            report = self.build(root)

            with self.assertRaises(reach.ReachabilityError):
                reach.write_outputs(root, report, Path("../out.json"), reach.DEFAULT_MARKDOWN_OUTPUT)
            with self.assertRaises(reach.ReachabilityError):
                reach.write_outputs(root, report, reach.DEFAULT_JSON_OUTPUT, reach.DEFAULT_JSON_OUTPUT)
            with self.assertRaises(reach.ReachabilityError):
                reach.write_outputs(root, report, Path(".github/workflows/probe.json"), reach.DEFAULT_MARKDOWN_OUTPUT)

    def test_write_outputs_records_requested_artifact_paths(self) -> None:
        with self.make_repo(
            wrapper_text="function Invoke-Wrapper { Invoke-PartOne }\n",
            part_texts={"PartA.ps1": "function Invoke-PartOne { }\n"},
        ) as temp:
            root = Path(temp)
            report = self.build(root)
            json_output = Path("project_sources/collector/reachability_test.json")
            markdown_output = Path("project_sources/collector/reachability_test.md")

            reach.write_outputs(root, report, json_output, markdown_output)
            written = json.loads((root / json_output).read_text(encoding="utf-8"))

        self.assertEqual(written["outputs"]["json"], json_output.as_posix())
        self.assertEqual(written["outputs"]["markdown"], markdown_output.as_posix())

    def test_ast_definition_kind_defaults_empty_values_explicitly(self) -> None:
        self.assertEqual(reach.ast_definition_kind("nested"), "nested")
        self.assertEqual(reach.ast_definition_kind(" top_level "), "top_level")
        self.assertEqual(reach.ast_definition_kind(""), "top_level")
        self.assertEqual(reach.ast_definition_kind("  "), "top_level")
        self.assertEqual(reach.ast_definition_kind(None), "top_level")

    def test_ast_invocation_kind_defaults_empty_values_to_not_extracted(self) -> None:
        self.assertEqual(reach.ast_invocation_kind("Dot"), "Dot")
        self.assertEqual(reach.ast_invocation_kind("  Ampersand  "), "Ampersand")
        for value in ("", "  ", None):
            with self.subTest(value=value):
                self.assertEqual(reach.ast_invocation_kind(value), "not_extracted")
                self.assertNotEqual(reach.ast_invocation_kind(value), "Unknown")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
