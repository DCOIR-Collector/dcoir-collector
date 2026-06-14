#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
import unittest.mock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_powershell_surface_inventory as inventory


def write(path: Path, text: str = "Write-Output 'ok'\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PowerShellSurfaceInventoryTests(unittest.TestCase):
    def make_minimal_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(
            root / "project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json",
            '{\n'
            '  "collector_wrapper_source": "project_sources/collector/source/DCOIR_Collector.ps1",\n'
            '  "collector_part_files": [\n'
            '    "project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1"\n'
            "  ]\n"
            "}\n",
        )
        write(root / "project_sources/collector/source/DCOIR_Collector.ps1")
        write(root / "project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1")
        write(root / "project_sources/collector/harness/run_DCOIR_Tests.ps1")
        write(root / "project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-000.ps1.txt")
        write(root / "operator_tools/sample/Invoke-DcoirSample.ps1")
        write(root / ".github/workflows/sample.yml", "jobs:\n  test:\n    steps:\n      - shell: pwsh\n        run: Write-Host ok\n")
        return temp

    def test_control_inventory_succeeds(self) -> None:
        with self.make_minimal_repo() as temp:
            result = inventory.build_inventory(Path(temp))
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        categories = result["summary"]["by_category"]
        self.assertEqual(categories["collector_runtime_wrapper"], 1)
        self.assertEqual(categories["collector_runtime_source_part"], 1)
        self.assertEqual(categories["collector_harness_script"], 1)
        self.assertEqual(categories["collector_harness_source_part"], 1)
        self.assertEqual(categories["workflow_embedded_powershell"], 1)
        operator_surface = next(
            surface for surface in result["surfaces"] if surface["path"] == "operator_tools/sample/Invoke-DcoirSample.ps1"
        )
        self.assertEqual(operator_surface["marker_lines"], [])

    def test_unclassified_changed_file_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(root / "misc/unknown.ps1")
            result = inventory.build_inventory(root, changed_files=["misc/unknown.ps1"])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("no inventory category" in error for error in result["validation"]["errors"]))

    def test_changed_file_paths_accept_windows_separators(self) -> None:
        with self.make_minimal_repo() as temp:
            result = inventory.build_inventory(
                Path(temp),
                changed_files=["project_sources\\collector\\source\\DCOIR_Collector.ps1"],
            )

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"][0]["path"], "project_sources/collector/source/DCOIR_Collector.ps1")

    def test_missing_changed_file_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            result = inventory.build_inventory(Path(temp), changed_files=["project_sources/collector/source/missing.ps1"])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("missing from the working tree" in error for error in result["validation"]["errors"]))

    def test_missing_changed_workflow_yaml_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            for changed_path in [
                ".github/workflows/deleted.yml",
                ".github/actions/deleted/action.yml",
            ]:
                with self.subTest(changed_path=changed_path):
                    result = inventory.build_inventory(Path(temp), changed_files=[changed_path])
                self.assertFalse(result["validation"]["success"])
                self.assertTrue(any("workflow/action YAML path is missing" in error for error in result["validation"]["errors"]))

    def test_empty_changed_workflow_yaml_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/empty.yml"
            write(root / rel, "")
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("workflow/action YAML is empty" in error for error in result["validation"]["errors"]))

    def test_malformed_workflow_yaml_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/malformed.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - shell: pwsh\n"
                "        run: [Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("unclosed '['" in error for error in result["validation"]["errors"]))

    def test_malformed_flow_mapping_value_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/malformed-flow-map.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - shell: pwsh\n"
                "        run: { command: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("unclosed '{'" in error for error in result["validation"]["errors"]))

    def test_malformed_flow_mapping_fragment_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/malformed-flow-fragment.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - { name: Flow, shell: pwsh, run: Write-Host one, two }\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertFalse(result["validation"]["success"])
        self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")
        self.assertTrue(any("unsupported flow mapping fragment" in error for error in result["validation"]["errors"]))

    def test_malformed_workflow_indentation_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/malformed-indent.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - shell: pwsh\n"
                "       run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("unsupported odd indentation" in error for error in result["validation"]["errors"]))

    def test_workflow_marker_without_extractable_snippet_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/malformed-even-indent.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - shell: pwsh\n"
                "      run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("non-list entry directly under steps" in error for error in result["validation"]["errors"]))

    def test_malformed_step_list_item_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/malformed-step-item.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - shell pwsh\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("non-mapping step entry" in error for error in result["validation"]["errors"]))

    def test_changed_workflow_yaml_without_powershell_markers_can_pass(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/no-powershell.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Bash step\n"
                "        run: echo ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_workflow_collection_run_and_shell_values_fail_closed(self) -> None:
        cases = [
            ("direct-run-list", "      - shell: pwsh\n        run: [Write-Host ok]\n", "run"),
            ("direct-run-map", "      - shell: pwsh\n        run: { command: Write-Host ok }\n", "run"),
            ("direct-run-block-list", "      - shell: pwsh\n        run:\n          - Write-Host ok\n", "run"),
            ("direct-run-block-map", "      - shell: pwsh\n        run:\n          command: Write-Host ok\n", "run"),
            ("direct-shell-list", "      - shell: [pwsh]\n        run: Write-Host ok\n", "shell"),
            ("direct-shell-expression", "      - shell: ${{ matrix.shell }}\n        run: Write-Host ok\n", "shell"),
            ("direct-shell-block-list", "      - shell:\n          - pwsh\n        run: Write-Host ok\n", "shell"),
            ("direct-shell-block-map", "      - shell:\n          executable: pwsh\n        run: Write-Host ok\n", "shell"),
            ("flow-step-run-list", "      - { name: Flow, shell: pwsh, run: [Write-Host ok] }\n", "run"),
            ("flow-step-run-map", "      - { name: Flow, shell: pwsh, run: { command: Write-Host ok } }\n", "run"),
            ("flow-step-shell-list", "      - { name: Flow, shell: [pwsh], run: Write-Host ok }\n", "shell"),
            ("flow-step-shell-expression", "      - { name: Flow, shell: ${{ matrix.shell }}, run: Write-Host ok }\n", "shell"),
            ("commented-flow-step-run-list", "      - { name: Flow, shell: pwsh, run: [Write-Host ok] } # comment\n", "run"),
            ("commented-flow-step-shell-list", "      - { name: Flow, shell: [pwsh], run: Write-Host ok } # comment\n", "shell"),
            (
                "block-default-shell-list",
                "    defaults:\n"
                "      run:\n"
                "        shell: [pwsh]\n"
                "    steps:\n"
                "      - name: Uses invalid default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "block-default-shell-expression",
                "    defaults:\n"
                "      run:\n"
                "        shell: ${{ matrix.shell }}\n"
                "    steps:\n"
                "      - name: Uses invalid default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "block-default-shell-block-list",
                "    defaults:\n"
                "      run:\n"
                "        shell:\n"
                "          - pwsh\n"
                "    steps:\n"
                "      - name: Uses invalid default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "block-default-shell-block-map",
                "    defaults:\n"
                "      run:\n"
                "        shell:\n"
                "          executable: pwsh\n"
                "    steps:\n"
                "      - name: Uses invalid default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "inline-default-shell-list",
                "    steps:\n"
                "      - name: Uses invalid inline default shell\n"
                "        run: Write-Host ok\n"
                "defaults: { run: { shell: [pwsh] } }\n",
                "defaults.run.shell",
            ),
            (
                "inline-default-shell-multi-list",
                "    steps:\n"
                "      - name: Uses invalid multi-item inline default shell\n"
                "        run: Write-Host ok\n"
                "defaults: { run: { shell: [pwsh, -NoProfile] } }\n",
                "defaults.run.shell",
            ),
            (
                "job-inline-default-shell-expression",
                "    defaults: { run: { shell: ${{ matrix.shell }} } }\n"
                "    steps:\n"
                "      - name: Uses invalid job inline default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "nested-inline-default-shell-list",
                "    defaults:\n"
                "      run: { shell: [pwsh] }\n"
                "    steps:\n"
                "      - name: Uses invalid nested inline default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
        ]
        for name, body, key in cases:
            with self.subTest(name=name):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/{name}.yml"
                    steps_header = "" if "    steps:" in body else "    steps:\n"
                    write(root / rel, "jobs:\n  test:\n" + steps_header + body)
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertFalse(result["validation"]["success"])
                self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")
                self.assertTrue(
                    any(f"non-scalar workflow {key} value" in error for error in result["validation"]["errors"])
                )

    def test_workflow_default_shell_expression_fails_closed(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/top-default-shell-expression.yml"
            write(
                root / rel,
                "defaults:\n"
                "  run:\n"
                "    shell: ${{ matrix.shell }}\n"
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses workflow default shell\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertFalse(result["validation"]["success"])
        self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")
        self.assertTrue(
            any("non-scalar workflow defaults.run.shell value" in error for error in result["validation"]["errors"])
        )

    def test_empty_workflow_run_and_shell_values_fail_closed(self) -> None:
        cases = [
            ("direct-run-empty", "      - shell: pwsh\n        run:\n", "run"),
            ("direct-run-quoted-empty", '      - shell: pwsh\n        run: ""\n', "run"),
            ("direct-shell-empty", "      - shell:\n        run: Write-Host ok\n", "shell"),
            ("direct-shell-quoted-empty", '      - shell: ""\n        run: Write-Host ok\n', "shell"),
            ("flow-run-empty", "      - { name: Flow, shell: pwsh, run: }\n", "run"),
            ("flow-run-quoted-empty", '      - { name: Flow, shell: pwsh, run: "" }\n', "run"),
            ("flow-shell-empty", "      - { name: Flow, shell: , run: Write-Host ok }\n", "shell"),
            ("flow-shell-quoted-empty", '      - { name: Flow, shell: "", run: Write-Host ok }\n', "shell"),
            (
                "default-shell-empty",
                "    defaults:\n"
                "      run:\n"
                "        shell:\n"
                "    steps:\n"
                "      - name: Uses invalid empty default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "default-shell-quoted-empty",
                "    defaults:\n"
                "      run:\n"
                '        shell: ""\n'
                "    steps:\n"
                "      - name: Uses invalid quoted-empty default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "inline-default-shell-empty",
                "    steps:\n"
                "      - name: Uses invalid inline default shell\n"
                "        run: Write-Host ok\n"
                "defaults: { run: { shell: } }\n",
                "defaults.run.shell",
            ),
            (
                "inline-default-shell-quoted-empty",
                "    steps:\n"
                "      - name: Uses invalid quoted-empty inline default shell\n"
                "        run: Write-Host ok\n"
                'defaults: { run: { shell: "" } }\n',
                "defaults.run.shell",
            ),
            (
                "job-inline-default-shell-empty",
                "    defaults: { run: { shell: } }\n"
                "    steps:\n"
                "      - name: Uses invalid job inline default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "nested-inline-default-shell-empty",
                "    defaults:\n"
                "      run: { shell: }\n"
                "    steps:\n"
                "      - name: Uses invalid nested inline default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
            (
                "nested-inline-default-shell-quoted-empty",
                "    defaults:\n"
                '      run: { shell: "" }\n'
                "    steps:\n"
                "      - name: Uses invalid nested quoted-empty default shell\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
        ]
        for name, body, key in cases:
            with self.subTest(name=name):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/{name}.yml"
                    steps_header = "" if "    steps:" in body else "    steps:\n"
                    write(root / rel, "jobs:\n  test:\n" + steps_header + body)
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertFalse(result["validation"]["success"])
                self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")
                self.assertTrue(
                    any(f"non-scalar workflow {key} value" in error for error in result["validation"]["errors"])
                )

    def test_empty_block_scalar_run_fails_closed(self) -> None:
        for marker in ["|", ">"]:
            with self.subTest(marker=marker):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/empty-block-run-{marker.replace('|', 'pipe').replace('>', 'fold')}.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Empty block scalar run\n"
                        "        shell: pwsh\n"
                        f"        run: {marker}\n",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertFalse(result["validation"]["success"])
                self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")
                self.assertTrue(any("empty workflow run value" in error for error in result["validation"]["errors"]))

    def test_block_scalar_shell_values_fail_closed(self) -> None:
        cases = [
            (
                "direct-shell-block-scalar",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Direct shell block scalar\n"
                "        shell: |\n"
                "          pwsh\n"
                "        run: Write-Host ok\n",
                "shell",
            ),
            (
                "default-shell-block-scalar",
                "jobs:\n"
                "  test:\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: |\n"
                "          pwsh\n"
                "    steps:\n"
                "      - name: Default shell block scalar\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
        ]
        for name, text, key in cases:
            with self.subTest(name=name):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/{name}.yml"
                    write(root / rel, text)
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertFalse(result["validation"]["success"])
                self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")
                self.assertTrue(
                    any(
                        f"unsupported block-scalar workflow {key} value" in error
                        for error in result["validation"]["errors"]
                    )
                )

    def test_matrix_run_and_shell_data_are_not_validated_as_steps(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/matrix-run-shell-data.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    strategy:\n"
                "      matrix:\n"
                "        include:\n"
                "          - run: [unit, integration]\n"
                "            shell: [pwsh, bash]\n"
                "    steps:\n"
                "      - name: Bash step\n"
                "        run: echo ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_matrix_nested_steps_data_are_not_validated_as_executable_steps(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/matrix-nested-steps-data.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    strategy:\n"
                "      matrix:\n"
                "        include:\n"
                "          - name: data-only\n"
                "            steps:\n"
                "              - shell: pwsh\n"
                "                run: Write-Host fake\n"
                "    steps:\n"
                "      - name: Bash step\n"
                "        run: echo ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_flow_style_inline_steps_fail_closed(self) -> None:
        cases = [
            (
                "workflow-steps-value",
                ".github/workflows/inline-flow-steps.yml",
                "jobs:\n"
                "  test:\n"
                "    steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }]\n",
                "unsupported inline workflow steps value",
            ),
            (
                "workflow-job-value",
                ".github/workflows/inline-flow-job.yml",
                "jobs:\n"
                "  test: { steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] }\n",
                "unsupported inline workflow jobs.steps value",
            ),
            (
                "workflow-jobs-value",
                ".github/workflows/inline-flow-jobs.yml",
                "jobs: { test: { steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] } }\n",
                "unsupported inline workflow jobs.steps value",
            ),
            (
                "composite-runs-value",
                ".github/actions/inline-flow/action.yml",
                "name: Inline composite\n"
                "runs: { using: composite, steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] }\n",
                "unsupported inline workflow runs.steps value",
            ),
        ]
        for name, rel, text, expected_error in cases:
            with self.subTest(name=name):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    write(root / rel, text)
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertFalse(result["validation"]["success"])
                self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")
                self.assertTrue(any(expected_error in error for error in result["validation"]["errors"]))

    def test_flow_style_step_plain_scalar_apostrophe_is_not_a_quote(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/flow-apostrophe.yml"
            expected_name = "Collector's Flow"
            expected_command = "echo Collector's log"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                f"      - {{ name: {expected_name}, shell: pwsh, run: {expected_command} }}\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["step_or_action"], expected_name)
        self.assertEqual(snippets[0]["command_preview"], expected_command)

    def test_plain_scalar_apostrophe_does_not_fail_workflow_shape(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/apostrophe.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Collector's plain shell step\n"
                "        run: echo ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_plain_scalar_unmatched_parenthesis_does_not_fail_workflow_shape(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/parenthesis.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Validate (preview\n"
                "        run: echo ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_plain_scalar_brackets_and_braces_do_not_fail_workflow_shape(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/plain-brackets.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Validate [preview\n"
                "        run: echo {ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_comment_delimiters_do_not_fail_workflow_shape(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/comment-delimiters.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Validate # [not yaml structure\n"
                "        run: echo ok # } also not yaml structure\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_empty_included_powershell_surface_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = "operator_tools/sample/empty.psm1"
            write(root / rel, "")
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("included PowerShell surface is empty" in error for error in result["validation"]["errors"]))

    def test_file_facts_are_line_ending_stable(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = "operator_tools/sample/CrLf.ps1"
            crlf_bytes = b"Write-Output 'ok'\r\n"
            lf_bytes = b"Write-Output 'ok'\n"
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(crlf_bytes)

            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["file_facts_policy"], "text_bytes_with_line_endings_normalized_to_lf")
        self.assertEqual(result["surfaces"][0]["size_bytes"], len(lf_bytes))
        self.assertEqual(result["surfaces"][0]["line_count"], 1)
        self.assertEqual(result["surfaces"][0]["sha256"], inventory.hashlib.sha256(lf_bytes).hexdigest())

    def test_git_discovery_filters_ignored_segments(self) -> None:
        class Completed:
            returncode = 0
            stdout = (
                b"operator_tools/sample/Invoke-DcoirSample.ps1\0"
                b"operator_tools/sample/node_modules/vendor.ps1\0"
                b"project_sources/collector/source/DCOIR_Collector.ps1\0"
            )

        with unittest.mock.patch.object(inventory.subprocess, "run", return_value=Completed()):
            files = inventory.git_tracked_files(Path("/repo"))

        self.assertEqual(
            files,
            [
                "operator_tools/sample/Invoke-DcoirSample.ps1",
                "project_sources/collector/source/DCOIR_Collector.ps1",
            ],
        )

    def test_powershell_analyzer_policy_is_validation_tooling(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/PSScriptAnalyzerSettings.psd1"
            write(root / rel, "@{ Severity = @('Error', 'Warning') }\n")
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(len(result["surfaces"]), 1)
        self.assertEqual(result["surfaces"][0]["category"], "collector_validation_tooling")
        self.assertEqual(result["surfaces"][0]["inclusion_decision"], "include")
        self.assertEqual(result["surfaces"][0]["source_type"], ".psd1")

    def test_empty_generated_output_fails_when_present(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = inventory.HARNESS_GENERATED_OUTPUT.as_posix()
            write(root / rel, "")
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("included PowerShell surface is empty" in error for error in result["validation"]["errors"]))

    def test_baseline_shrink_fails_without_exception(self) -> None:
        with self.make_minimal_repo() as temp:
            baseline = {
                "summary": {
                    "by_category": {
                        "collector_runtime_source_part": 2,
                    }
                }
            }
            result = inventory.build_inventory(Path(temp), baseline=baseline)
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("unexpectedly shrank" in error for error in result["validation"]["errors"]))

    def test_changed_manifest_invalid_json_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            (root / "project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json").write_text(
                "{not-json",
                encoding="utf-8",
            )
            result = inventory.build_inventory(
                root,
                changed_files=["project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json"],
            )
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("Invalid JSON" in error for error in result["validation"]["errors"]))

    def test_changed_manifest_missing_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            (root / "project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json").unlink()
            result = inventory.build_inventory(
                root,
                changed_files=["project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json"],
            )
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("manifest is missing" in error for error in result["validation"]["errors"]))

    def test_changed_collector_file_requires_valid_manifest(self) -> None:
        manifest_rel = "project_sources/collector/manifests/Collector_Runtime_Package_Manifest.json"
        collector_rel = "project_sources/collector/source/DCOIR_Collector.ps1"
        for manifest_content, expected_error in [
            (None, "manifest is missing"),
            ("{not-json", "Invalid JSON"),
            ("{}\n", "did not provide any expected PowerShell source paths"),
        ]:
            with self.subTest(expected_error=expected_error):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    manifest_path = root / manifest_rel
                    if manifest_content is None:
                        manifest_path.unlink()
                    else:
                        manifest_path.write_text(manifest_content, encoding="utf-8")
                    result = inventory.build_inventory(root, changed_files=[collector_rel])
                self.assertFalse(result["validation"]["success"])
                self.assertTrue(any(expected_error in error for error in result["validation"]["errors"]))

    def test_changed_collector_file_passes_with_valid_manifest(self) -> None:
        with self.make_minimal_repo() as temp:
            result = inventory.build_inventory(
                Path(temp),
                changed_files=["project_sources/collector/source/DCOIR_Collector.ps1"],
            )
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["summary"]["by_category"]["collector_runtime_wrapper"], 1)

    def test_workflow_run_before_shell_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/run-before-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Run before shell\n"
                "        run: Write-Host ok\n"
                "        shell: pwsh\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/run-before-shell.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["summary"]["by_category"]["workflow_embedded_powershell"], 1)
        snippet = result["surfaces"][0]["embedded_snippets"][0]
        self.assertEqual(snippet["shell"], "pwsh")
        self.assertEqual(snippet["line_start"], 5)
        self.assertEqual(snippet["line_end"], 6)

    def test_compact_block_scalar_run_before_shell_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/compact-block-run-before-shell.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - run: |\n"
                "          Write-Host ok\n"
                "        shell: pwsh\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")
        self.assertEqual(snippets[0]["line_start"], 4)
        self.assertEqual(snippets[0]["line_end"], 6)

    def test_quoted_custom_shell_template_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/custom-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Custom shell template\n"
                '        shell: "pwsh -NoProfile -File {0}"\n'
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/custom-shell.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh -NoProfile -File {0}")

    def test_custom_shell_template_preserves_inner_quotes(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/custom-shell-inner-quotes.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Custom shell template with inner quotes\n"
                "        shell: \"pwsh -NoProfile -Command '& {0}'\"\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(
                root,
                changed_files=[".github/workflows/custom-shell-inner-quotes.yml"],
            )
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh -NoProfile -Command '& {0}'")

    def test_unquoted_custom_shell_template_is_preserved(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/unquoted-custom-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Unquoted custom shell\n"
                "        shell: pwsh -NoProfile -File {0}\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/unquoted-custom-shell.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh -NoProfile -File {0}")

    def test_unquoted_windows_powershell_shell_path_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/windows-powershell-path.yml"
            shell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -File {0}"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Windows PowerShell path\n"
                f"        shell: {shell}\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], shell)
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_flow_style_step_with_powershell_shell_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/flow-step.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - { name: Flow style, shell: pwsh, run: Write-Host ok }\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/flow-step.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["step_or_action"], "Flow style")
        self.assertEqual(snippets[0]["shell"], "pwsh")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_flow_style_step_with_trailing_comment_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/flow-step-comment.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - { name: Flow style, shell: pwsh, run: Write-Host ok } # normal comment\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["step_or_action"], "Flow style")
        self.assertEqual(snippets[0]["shell"], "pwsh")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_steps_key_with_trailing_comment_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/commented-steps.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps: # test steps\n"
                "      - name: Commented step # display-only comment\n"
                "        shell: pwsh # explicit shell\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["step_or_action"], "Commented step")
        self.assertEqual(snippets[0]["shell"], "pwsh")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_scalar_run_comments_are_not_command_markers(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/run-comment-marker.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Bash step\n"
                "        run: echo ok # powershell note\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_block_scalar_comments_are_not_command_markers(self) -> None:
        for body in [
            "          echo ok\n          # powershell note\n",
            "          echo ok # powershell note\n",
        ]:
            with self.subTest(body=body):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = ".github/workflows/block-comment-marker.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Bash block step\n"
                        "        run: |\n"
                        f"{body}",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
                self.assertEqual(result["surfaces"], [])

    def test_plain_scalar_apostrophe_before_comment_is_not_a_quote(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/run-apostrophe-comment-marker.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Bash step\n"
                "        run: echo Collector's log # powershell note\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_single_quoted_run_with_escaped_apostrophe_and_hash_is_preserved(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/single-quoted-run.yml"
            expected = "Write-Host Bob's # literal hash"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Single quoted command\n"
                "        shell: pwsh\n"
                "        run: 'Write-Host Bob''s # literal hash' # trailing YAML comment\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["command_preview"], expected)
        self.assertEqual(snippets[0]["command_sha256"], inventory.hashlib.sha256(expected.encode("utf-8")).hexdigest())

    def test_unterminated_quoted_workflow_scalars_fail_closed(self) -> None:
        cases = [
            (
                "unterminated-run",
                "      - name: Unterminated run\n"
                "        shell: pwsh\n"
                "        run: \"Write-Host ok\n",
            ),
            (
                "unterminated-shell",
                "      - name: Unterminated shell\n"
                "        shell: \"pwsh\n"
                "        run: Write-Host ok\n",
            ),
        ]
        for name, body in cases:
            with self.subTest(name=name):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/{name}.yml"
                    write(root / rel, "jobs:\n  test:\n    steps:\n" + body)
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertFalse(result["validation"]["success"])
                self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")
                self.assertTrue(
                    any("unterminated quoted scalar" in error for error in result["validation"]["errors"])
                )

    def test_composite_action_runs_steps_are_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/actions/sample/action.yml"
            write(
                root / rel,
                "name: Sample composite\n"
                "runs:\n"
                "  using: composite\n"
                "  steps:\n"
                "    - name: Composite PowerShell step\n"
                "      shell: pwsh\n"
                "      run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["step_or_action"], "Composite PowerShell step")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_inline_run_command_preserves_trailing_quote(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/inline-quoted-command.yml"
            expected = "Write-Host '#ok'"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Inline quoted command\n"
                "        shell: pwsh\n"
                f"        run: {expected}\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["command_preview"], expected)
        self.assertEqual(snippets[0]["command_sha256"], inventory.hashlib.sha256(expected.encode("utf-8")).hexdigest())

    def test_quoted_inline_run_command_strips_yaml_comment(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/inline-quoted-command-comment.yml"
            expected = "Write-Host '#ok'"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Inline quoted command\n"
                "        shell: pwsh\n"
                f"        run: \"{expected}\" # trailing YAML comment\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["command_preview"], expected)
        self.assertEqual(snippets[0]["command_sha256"], inventory.hashlib.sha256(expected.encode("utf-8")).hexdigest())

    def test_block_scalar_chomping_marker_preserves_explicit_shell_body(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/block-chomp.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses block chomping marker\n"
                "        shell: pwsh\n"
                "        run: |-\n"
                "          Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/block-chomp.yml"])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_block_scalar_chomping_marker_preserves_default_shell_body(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/default-block-chomp.yml",
                "jobs:\n"
                "  test:\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: pwsh\n"
                "    steps:\n"
                "      - name: Uses default shell block chomping marker\n"
                "        run: >+\n"
                "          Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/default-block-chomp.yml"])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_folded_block_scalar_run_uses_folded_command_text(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            expected = "Write-Host one Write-Host two"
            write(
                root / ".github/workflows/folded-block-command.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses folded block scalar\n"
                "        shell: pwsh\n"
                "        run: >\n"
                "          Write-Host one\n"
                "          Write-Host two\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/folded-block-command.yml"])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["command_preview"], expected)
        self.assertEqual(snippets[0]["command_sha256"], inventory.hashlib.sha256(expected.encode("utf-8")).hexdigest())

    def test_block_scalar_digit_markers_preserve_body(self) -> None:
        for marker in ["|2", "|2-", "|+2", ">2", ">2-", ">+2"]:
            with self.subTest(marker=marker):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/block-{marker.replace('|', 'pipe').replace('>', 'fold')}.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Uses block digit marker\n"
                        "        shell: pwsh\n"
                        f"        run: {marker}\n"
                        "          Write-Host ok\n",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
                snippets = result["surfaces"][0]["embedded_snippets"]
                self.assertEqual(len(snippets), 1)
                self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_block_scalar_auto_indent_markers_preserve_body(self) -> None:
        for marker in ["|", ">"]:
            with self.subTest(marker=marker):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/block-auto-indent-{marker.replace('|', 'pipe').replace('>', 'fold')}.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Uses auto block indentation marker\n"
                        "        shell: pwsh\n"
                        f"        run: {marker}\n"
                        "         Write-Host ok\n",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
                snippets = result["surfaces"][0]["embedded_snippets"]
                self.assertEqual(len(snippets), 1)
                self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")
                self.assertEqual(
                    snippets[0]["command_sha256"],
                    inventory.hashlib.sha256(b"Write-Host ok").hexdigest(),
                )

    def test_block_scalar_explicit_indent_markers_preserve_body(self) -> None:
        for marker, content_indent in [("|1", 9), ("|3", 11), ("|4", 12), ("|9", 17)]:
            with self.subTest(marker=marker):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/block-explicit-indent-{marker.replace('|', 'pipe')}.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Uses explicit block indentation marker\n"
                        "        shell: pwsh\n"
                        f"        run: {marker}\n"
                        f"{' ' * content_indent}Write-Host ok\n",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
                snippets = result["surfaces"][0]["embedded_snippets"]
                self.assertEqual(len(snippets), 1)
                self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")
                self.assertEqual(
                    snippets[0]["command_sha256"],
                    inventory.hashlib.sha256(b"Write-Host ok").hexdigest(),
                )

    def test_block_scalar_explicit_indent_rejects_too_shallow_body(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/block-explicit-indent-too-shallow.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses too-shallow explicit block indentation\n"
                "        shell: pwsh\n"
                "        run: |4\n"
                "          Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertFalse(result["validation"]["success"])
        self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")

    def test_invalid_block_scalar_markers_fail_closed(self) -> None:
        for marker in ["|++", "|--", "|22", "|0", "|2+3", ">+2-", "'|'", '"|"']:
            with self.subTest(marker=marker):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    marker_slug = marker.replace("|", "pipe").replace(">", "fold").replace("'", "quote").replace('"', "dquote")
                    rel = f".github/workflows/invalid-block-{marker_slug}.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Invalid block marker\n"
                        "        shell: pwsh\n"
                        f"        run: {marker}\n"
                        "          Write-Host ok\n",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertFalse(result["validation"]["success"])
                self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")

    def test_bare_invalid_block_scalar_markers_fail_closed(self) -> None:
        for marker in ["|++", "|--", "|22", "|0", "|2+3", ">+2-", "'|'", '"|"']:
            with self.subTest(marker=marker):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    marker_slug = marker.replace("|", "pipe").replace(">", "fold").replace("'", "quote").replace('"', "dquote")
                    rel = f".github/workflows/bare-invalid-block-{marker_slug}.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Bare invalid block marker\n"
                        "        shell: pwsh\n"
                        f"        run: {marker}\n",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertFalse(result["validation"]["success"])
                self.assertEqual(result["surfaces"][0]["category"], "invalid_workflow_surface")

    def test_block_scalar_marker_with_comment_preserves_body(self) -> None:
        for marker in ["| # keep literal", "|- # strip trailing newline"]:
            with self.subTest(marker=marker):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/block-comment-{marker.split()[0].replace('|', 'pipe')}.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Uses block marker comment\n"
                        "        shell: pwsh\n"
                        f"        run: {marker}\n"
                        "          Write-Host ok\n",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
                snippets = result["surfaces"][0]["embedded_snippets"]
                self.assertEqual(len(snippets), 1)
                self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_defaults_run_shell_is_inherited_without_fake_snippet(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/default-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: powershell\n"
                "    steps:\n"
                "      - name: Uses default shell\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/default-shell.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "powershell")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_job_defaults_after_steps_still_apply(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/default-after-steps.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses later default\n"
                "        run: Write-Host ok\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: pwsh\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/default-after-steps.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh")

    def test_top_level_defaults_after_jobs_still_apply(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/top-default-after-jobs.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses top default\n"
                "        run: Write-Host ok\n"
                "defaults:\n"
                "  run:\n"
                "    shell: pwsh\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/top-default-after-jobs.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh")

    def test_inline_top_level_default_shell_applies(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/inline-top-default.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses inline default\n"
                "        run: Write-Host ok\n"
                "defaults: { run: { shell: pwsh } }\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/inline-top-default.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh")

    def test_inline_job_default_shell_applies(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/inline-job-default.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses inline job default\n"
                "        run: Write-Host ok\n"
                "    defaults: { run: { shell: powershell } }\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/inline-job-default.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "powershell")

    def test_custom_default_shell_template_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/custom-default-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    defaults:\n"
                "      run:\n"
                '        shell: "powershell.exe -NoProfile -File {0}"\n'
                "    steps:\n"
                "      - name: Uses custom default shell\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/custom-default-shell.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "powershell.exe -NoProfile -File {0}")

    def test_unquoted_custom_default_shell_template_is_preserved(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/unquoted-custom-default.yml",
                "jobs:\n"
                "  test:\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: pwsh -NoProfile -File {0}\n"
                "    steps:\n"
                "      - name: Uses unquoted custom default shell\n"
                "        run: Write-Host ok\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/unquoted-custom-default.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh -NoProfile -File {0}")

    def test_inline_custom_default_shell_template_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/inline-custom-default.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Uses inline custom default\n"
                "        run: Write-Host ok\n"
                'defaults: { run: { shell: "pwsh -NoProfile -File {0}" } }\n',
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/inline-custom-default.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh -NoProfile -File {0}")

    def test_nested_shell_key_does_not_override_step_default_shell(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/nested-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: pwsh\n"
                "    steps:\n"
                "      - name: Has nested env shell\n"
                "        run: Write-Host ok\n"
                "        env:\n"
                "          shell: bash\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/nested-shell.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["shell"], "pwsh")

    def test_nested_defaults_do_not_create_workflow_surface(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/nested-defaults.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Plain run with metadata defaults\n"
                "        run: echo not-powershell\n"
                "        metadata:\n"
                "          defaults:\n"
                "            run:\n"
                "              shell: pwsh\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/nested-defaults.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_job_default_shell_does_not_leak_to_sibling_job(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/two-jobs.yml",
                "jobs:\n"
                "  first:\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: pwsh\n"
                "    steps:\n"
                "      - name: First PowerShell job\n"
                "        run: Write-Host ok\n"
                "  second:\n"
                "    steps:\n"
                "      - name: Plain shell job\n"
                "        run: echo not-powershell\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/two-jobs.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["step_or_action"], "First PowerShell job")

    def test_hyphenated_powershell_words_do_not_create_workflow_surface(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / ".github/workflows/hyphenated-mentions.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Prefix hyphen\n"
                "        run: echo not-powershell\n"
                "      - name: Suffix hyphen\n"
                "        run: echo powershell-validation\n",
            )
            result = inventory.build_inventory(root, changed_files=[".github/workflows/hyphenated-mentions.yml"])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["surfaces"], [])

    def test_unmanifested_collector_part_fails_full_inventory(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(root / "project_sources/collector/source/parts/DCOIR_Collector.02_Unmanifested.ps1")
            result = inventory.build_inventory(root)
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("not listed" in error for error in result["validation"]["errors"]))

    def test_unmanifested_collector_part_fails_changed_mode(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/source/parts/DCOIR_Collector.02_Unmanifested.ps1"
            write(root / rel)
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("not listed" in error for error in result["validation"]["errors"]))

    def test_temp_named_collector_part_cannot_hide_from_manifest_enforcement(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = "project_sources/collector/source/parts/temp/DCOIR_Collector.02_TempNamed.ps1"
            write(root / rel)
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertEqual(result["surfaces"][0]["category"], "collector_runtime_source_part")
        self.assertTrue(any("not listed" in error for error in result["validation"]["errors"]))

    def test_profile_required_harness_part_missing_fails_full_inventory(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / "project_sources/github_actions/workflow_required_surface_profiles.json",
                '{\n'
                '  "validate_on_pr": [\n'
                '    "project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-000.ps1.txt",\n'
                '    "project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-001.ps1.txt"\n'
                "  ]\n"
                "}\n",
            )
            result = inventory.build_inventory(root)
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("required by" in error for error in result["validation"]["errors"]))

    def test_required_surface_profile_only_change_expands_harness_parts(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = inventory.REQUIRED_SURFACE_PROFILES_PATH.as_posix()
            write(
                root / rel,
                '{\n'
                '  "validate_on_pr": [\n'
                '    "project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-000.ps1.txt"\n'
                "  ]\n"
                "}\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        self.assertEqual(result["summary"]["by_category"]["collector_harness_source_part"], 1)
        self.assertIn("project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-000.ps1.txt", result["changed_file_dependency_expansion"]["expanded_paths"])

    def test_deleted_required_surface_profile_change_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = inventory.REQUIRED_SURFACE_PROFILES_PATH.as_posix()
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("Required surface profile is missing" in error for error in result["validation"]["errors"]))

    def test_malformed_required_surface_profile_fails(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = inventory.REQUIRED_SURFACE_PROFILES_PATH.as_posix()
            write(root / rel, "{not-json")
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("Invalid JSON in required surface profile" in error for error in result["validation"]["errors"]))

    def test_required_surface_profile_without_harness_parts_fails_when_changed(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = inventory.REQUIRED_SURFACE_PROFILES_PATH.as_posix()
            write(root / rel, '{"validate_on_pr": ["README.md"]}\n')
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("did not provide any harness source parts" in error for error in result["validation"]["errors"]))

    def test_unprofiled_harness_part_fails_when_profile_exists(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            write(
                root / "project_sources/github_actions/workflow_required_surface_profiles.json",
                '{\n'
                '  "validate_on_pr": [\n'
                '    "project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-000.ps1.txt"\n'
                "  ]\n"
                "}\n",
            )
            rel = "project_sources/collector/harness/source/parts/run_DCOIR_Tests.part-001.ps1.txt"
            write(root / rel)
            result = inventory.build_inventory(root, changed_files=[rel])
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("not listed" in error for error in result["validation"]["errors"]))

    def test_baseline_rejected_in_changed_mode(self) -> None:
        with self.make_minimal_repo() as temp:
            result = inventory.build_inventory(
                Path(temp),
                changed_files=["project_sources/collector/source/DCOIR_Collector.ps1"],
                baseline={"summary": {"by_category": {"collector_runtime_source_part": 2}}},
            )
        self.assertFalse(result["validation"]["success"])
        self.assertTrue(any("Baseline shrink checks require full inventory mode" in error for error in result["validation"]["errors"]))


if __name__ == "__main__":
    unittest.main()
