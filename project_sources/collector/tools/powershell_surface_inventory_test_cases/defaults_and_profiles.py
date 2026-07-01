from __future__ import annotations

from .common import InventoryTestCase, Path, write
import build_powershell_surface_inventory as inventory


class DefaultsAndProfileTests(InventoryTestCase):
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



