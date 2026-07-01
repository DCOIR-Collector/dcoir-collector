from __future__ import annotations

from .common import InventoryTestCase, Path, write
import build_powershell_surface_inventory as inventory


class WorkflowShapeCollectionTests(InventoryTestCase):
    def test_workflow_collection_run_and_shell_values_fail_closed(self) -> None:
        cases = [
            ("direct-run-list", "      - shell: pwsh\n        run: [Write-Host ok]\n", "run"),
            ("direct-run-map", "      - shell: pwsh\n        run: { command: Write-Host ok }\n", "run"),
            ("direct-run-alias", "      - shell: pwsh\n        run: *cmd\n", "run"),
            ("direct-run-block-list", "      - shell: pwsh\n        run:\n          - Write-Host ok\n", "run"),
            ("direct-run-block-map", "      - shell: pwsh\n        run:\n          command: Write-Host ok\n", "run"),
            ("direct-shell-list", "      - shell: [pwsh]\n        run: Write-Host ok\n", "shell"),
            ("direct-shell-expression", "      - shell: ${{ matrix.shell }}\n        run: Write-Host ok\n", "shell"),
            ("direct-shell-alias", "      - shell: *ps\n        run: Write-Host ok\n", "shell"),
            ("direct-shell-block-list", "      - shell:\n          - pwsh\n        run: Write-Host ok\n", "shell"),
            ("direct-shell-block-map", "      - shell:\n          executable: pwsh\n        run: Write-Host ok\n", "shell"),
            ("flow-step-run-list", "      - { name: Flow, shell: pwsh, run: [Write-Host ok] }\n", "run"),
            ("flow-step-run-map", "      - { name: Flow, shell: pwsh, run: { command: Write-Host ok } }\n", "run"),
            ("flow-step-run-alias", "      - { name: Flow, shell: pwsh, run: *cmd }\n", "run"),
            ("flow-step-shell-list", "      - { name: Flow, shell: [pwsh], run: Write-Host ok }\n", "shell"),
            ("flow-step-shell-expression", "      - { name: Flow, shell: ${{ matrix.shell }}, run: Write-Host ok }\n", "shell"),
            ("flow-step-shell-alias", "      - { name: Flow, shell: *ps, run: Write-Host ok }\n", "shell"),
            ("commented-flow-step-run-list", "      - { name: Flow, shell: pwsh, run: [Write-Host ok] } # comment\n", "run"),
            ("commented-flow-step-shell-list", "      - { name: Flow, shell: [pwsh], run: Write-Host ok } # comment\n", "shell"),
            (
                "block-default-shell-alias",
                "    defaults:\n"
                "      run:\n"
                "        shell: *ps\n"
                "    steps:\n"
                "      - name: Uses invalid default shell alias\n"
                "        run: Write-Host ok\n",
                "defaults.run.shell",
            ),
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
                "inline-default-shell-alias",
                "    steps:\n"
                "      - name: Uses invalid inline default shell alias\n"
                "        run: Write-Host ok\n"
                "defaults: { run: { shell: *ps } }\n",
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
                "workflow-anchored-job-value",
                ".github/workflows/inline-flow-anchored-job.yml",
                "jobs:\n"
                "  test: &j { steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] }\n",
                "unsupported inline workflow jobs.steps value",
            ),
            (
                "workflow-tagged-job-value",
                ".github/workflows/inline-flow-tagged-job.yml",
                "jobs:\n"
                "  test: !dcoir { steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] }\n",
                "unsupported inline workflow jobs.steps value",
            ),
            (
                "workflow-jobs-value",
                ".github/workflows/inline-flow-jobs.yml",
                "jobs: { test: { steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] } }\n",
                "unsupported inline workflow jobs.steps value",
            ),
            (
                "workflow-anchored-jobs-value",
                ".github/workflows/inline-flow-anchored-jobs.yml",
                "jobs: &j { test: { steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] } }\n",
                "unsupported inline workflow jobs.steps value",
            ),
            (
                "workflow-tagged-jobs-value",
                ".github/workflows/inline-flow-tagged-jobs.yml",
                "jobs: !dcoir { test: { steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] } }\n",
                "unsupported inline workflow jobs.steps value",
            ),
            (
                "composite-runs-value",
                ".github/actions/inline-flow/action.yml",
                "name: Inline composite\n"
                "runs: { using: composite, steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] }\n",
                "unsupported inline workflow runs.steps value",
            ),
            (
                "composite-anchored-runs-value",
                ".github/actions/inline-flow-anchored/action.yml",
                "name: Inline composite\n"
                "runs: &r { using: composite, steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] }\n",
                "unsupported inline workflow runs.steps value",
            ),
            (
                "composite-tagged-runs-value",
                ".github/actions/inline-flow-tagged/action.yml",
                "name: Inline composite\n"
                "runs: !dcoir { using: composite, steps: [{ name: Inline, shell: pwsh, run: Write-Host ok }] }\n",
                "unsupported inline workflow runs.steps value",
            ),
            (
                "workflow-step-sequence-item",
                ".github/workflows/inline-flow-step-sequence-item.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - [shell: pwsh, run: Write-Host ok]\n",
                "unsupported inline workflow step value",
            ),
            (
                "workflow-step-overindented-sequence-item",
                ".github/workflows/inline-flow-overindented-step-sequence-item.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "        - [shell: pwsh, run: Write-Host ok]\n",
                "unsupported inline workflow step value",
            ),
            (
                "workflow-step-anchored-sequence-item",
                ".github/workflows/inline-flow-anchored-step-sequence-item.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - &ps [shell: pwsh, run: Write-Host ok]\n",
                "unsupported inline workflow step value",
            ),
            (
                "workflow-step-tagged-sequence-item",
                ".github/workflows/inline-flow-tagged-step-sequence-item.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - !dcoir [shell: pwsh, run: Write-Host ok]\n",
                "unsupported inline workflow step value",
            ),
            (
                "workflow-step-alias-item",
                ".github/workflows/inline-flow-alias-step-item.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - *ps\n",
                "unsupported alias workflow step value",
            ),
            (
                "workflow-step-overindented-non-list-item",
                ".github/workflows/overindented-non-list-step-item.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "        run: Write-Host ok\n",
                "non-list entry directly under steps",
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


