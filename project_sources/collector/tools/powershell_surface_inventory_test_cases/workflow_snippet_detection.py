from __future__ import annotations

from .common import InventoryTestCase, Path, write
import build_powershell_surface_inventory as inventory


class WorkflowSnippetDetectionTests(InventoryTestCase):
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

    def test_anchored_flow_style_step_with_powershell_shell_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/anchored-flow-step.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - &ps { name: Anchored Flow, shell: pwsh, run: Write-Host ok }\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["step_or_action"], "Anchored Flow")
        self.assertEqual(snippets[0]["shell"], "pwsh")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_tagged_flow_style_step_with_powershell_shell_is_detected(self) -> None:
        with self.make_minimal_repo() as temp:
            root = Path(temp)
            rel = ".github/workflows/tagged-flow-step.yml"
            write(
                root / rel,
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - !dcoir { name: Tagged Flow, shell: pwsh, run: Write-Host ok }\n",
            )
            result = inventory.build_inventory(root, changed_files=[rel])

        self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
        snippets = result["surfaces"][0]["embedded_snippets"]
        self.assertEqual(len(snippets), 1)
        self.assertEqual(snippets[0]["step_or_action"], "Tagged Flow")
        self.assertEqual(snippets[0]["shell"], "pwsh")
        self.assertEqual(snippets[0]["command_preview"], "Write-Host ok")

    def test_yaml_node_prefix_scalar_shell_and_run_values_are_normalized(self) -> None:
        cases = [
            (
                "anchored-shell",
                ".github/workflows/anchored-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Anchored shell\n"
                "        shell: &ps pwsh\n"
                "        run: Write-Host ok\n",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "tagged-shell",
                ".github/workflows/tagged-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Tagged shell\n"
                "        shell: !dcoir pwsh\n"
                "        run: Write-Host ok\n",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "anchored-run",
                ".github/workflows/anchored-run.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Anchored run\n"
                "        shell: pwsh\n"
                "        run: &cmd Write-Host ok\n",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "tagged-run",
                ".github/workflows/tagged-run.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - name: Tagged run\n"
                "        shell: pwsh\n"
                "        run: !dcoir Write-Host ok\n",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "anchored-default-shell",
                ".github/workflows/anchored-default-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: &ps pwsh\n"
                "    steps:\n"
                "      - name: Anchored default shell\n"
                "        run: Write-Host ok\n",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "tagged-default-shell",
                ".github/workflows/tagged-default-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    defaults:\n"
                "      run:\n"
                "        shell: !dcoir pwsh\n"
                "    steps:\n"
                "      - name: Tagged default shell\n"
                "        run: Write-Host ok\n",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "flow-anchored-shell-tagged-run",
                ".github/workflows/flow-anchored-shell-tagged-run.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - { name: Flow prefixes, shell: &ps pwsh, run: !dcoir Write-Host ok }\n",
                "pwsh",
                "Write-Host ok",
            ),
        ]
        for name, rel, text, expected_shell, expected_command in cases:
            with self.subTest(name=name):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    write(root / rel, text)
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
                snippets = result["surfaces"][0]["embedded_snippets"]
                self.assertEqual(len(snippets), 1)
                self.assertEqual(snippets[0]["shell"], expected_shell)
                self.assertEqual(snippets[0]["command_preview"], expected_command)

    def test_yaml_node_prefix_first_step_key_is_normalized(self) -> None:
        cases = [
            (
                "anchored-first-shell",
                ".github/workflows/anchored-first-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - &step shell: pwsh\n"
                "        run: Write-Host ok\n",
                "(unnamed step)",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "tagged-first-shell",
                ".github/workflows/tagged-first-shell.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - !dcoir shell: pwsh\n"
                "        run: Write-Host ok\n",
                "(unnamed step)",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "anchored-first-run",
                ".github/workflows/anchored-first-run.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - &step run: Write-Host ok\n"
                "        shell: pwsh\n",
                "(unnamed step)",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "tagged-first-run",
                ".github/workflows/tagged-first-run.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - !dcoir run: Write-Host ok\n"
                "        shell: pwsh\n",
                "(unnamed step)",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "anchored-first-name",
                ".github/workflows/anchored-first-name.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - &step name: Anchored first name\n"
                "        shell: pwsh\n"
                "        run: Write-Host ok\n",
                "Anchored first name",
                "pwsh",
                "Write-Host ok",
            ),
            (
                "tagged-first-name",
                ".github/workflows/tagged-first-name.yml",
                "jobs:\n"
                "  test:\n"
                "    steps:\n"
                "      - !dcoir name: Tagged first name\n"
                "        shell: pwsh\n"
                "        run: Write-Host ok\n",
                "Tagged first name",
                "pwsh",
                "Write-Host ok",
            ),
        ]
        for name, rel, text, expected_name, expected_shell, expected_command in cases:
            with self.subTest(name=name):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    write(root / rel, text)
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
                snippets = result["surfaces"][0]["embedded_snippets"]
                self.assertEqual(len(snippets), 1)
                self.assertEqual(snippets[0]["step_or_action"], expected_name)
                self.assertEqual(snippets[0]["shell"], expected_shell)
                self.assertEqual(snippets[0]["command_preview"], expected_command)

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

