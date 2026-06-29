from __future__ import annotations

from .common import InventoryTestCase, Path, write
import build_powershell_surface_inventory as inventory


class WorkflowSnippetBlockScalarTests(InventoryTestCase):
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

    def test_yaml_node_prefix_block_scalar_run_preserves_body(self) -> None:
        cases = [
            (
                "anchored-literal-block",
                "run: &cmd |\n"
                "          $env:Path\n"
                "          Write-Host ok\n",
                "$env:Path\nWrite-Host ok",
            ),
            (
                "tagged-literal-block",
                "run: !dcoir |\n"
                "          $env:Path\n"
                "          Write-Host ok\n",
                "$env:Path\nWrite-Host ok",
            ),
            (
                "anchored-folded-block",
                "run: &cmd >-\n"
                "          Write-Host one\n"
                "          Write-Host two\n",
                "Write-Host one Write-Host two",
            ),
            (
                "tagged-folded-block",
                "run: !dcoir >+\n"
                "          Write-Host one\n"
                "          Write-Host two\n",
                "Write-Host one Write-Host two",
            ),
        ]
        for name, run_block, expected in cases:
            with self.subTest(name=name):
                with self.make_minimal_repo() as temp:
                    root = Path(temp)
                    rel = f".github/workflows/{name}.yml"
                    write(
                        root / rel,
                        "jobs:\n"
                        "  test:\n"
                        "    steps:\n"
                        "      - name: Uses prefixed block scalar\n"
                        "        shell: pwsh\n"
                        f"        {run_block}",
                    )
                    result = inventory.build_inventory(root, changed_files=[rel])

                self.assertTrue(result["validation"]["success"], result["validation"]["errors"])
                snippets = result["surfaces"][0]["embedded_snippets"]
                self.assertEqual(len(snippets), 1)
                self.assertEqual(snippets[0]["command_preview"], expected)
                self.assertEqual(
                    snippets[0]["command_sha256"],
                    inventory.hashlib.sha256(expected.encode("utf-8")).hexdigest(),
                )
                self.assertGreater(snippets[0]["line_end"], snippets[0]["line_start"])

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


