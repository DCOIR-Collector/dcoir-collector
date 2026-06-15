#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parent / "build_powershell_surface_inventory.py"
_SPEC = importlib.util.spec_from_file_location("build_powershell_surface_inventory", _MODULE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Unable to load inventory module from {_MODULE_PATH}")
inventory = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(inventory)


class PowerShellSurfaceInventoryPathSafetyTests(unittest.TestCase):
    def test_changed_file_paths_preserve_valid_repo_relative_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = inventory.normalize_changed_files([
                "project_sources\\collector\\source\\DCOIR_Collector.ps1",
                "./project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1",
                ".github/workflows/validate.yml",
            ], root)
        self.assertEqual(paths, [
            ".github/workflows/validate.yml",
            "project_sources/collector/source/DCOIR_Collector.ps1",
            "project_sources/collector/source/parts/DCOIR_Collector.01_Core.ps1",
        ])

    def test_changed_file_absolute_path_under_repo_becomes_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            absolute = root / "project_sources/collector/source/DCOIR_Collector.ps1"
            paths = inventory.normalize_changed_files([absolute.as_posix()], root)
        self.assertEqual(paths, ["project_sources/collector/source/DCOIR_Collector.ps1"])

    def test_changed_file_inputs_must_not_escape_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            cases = [
                "../outside.ps1",
                "project_sources/../outside.ps1",
                "/project_sources/collector/source/DCOIR_Collector.ps1",
                (root.parent / "outside.ps1").as_posix(),
                "C:\\outside\\collector.ps1",
                "C:outside\\collector.ps1",
                "\\\\server\\share\\collector.ps1",
                "",
            ]
            for value in cases:
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        inventory.normalize_changed_files([value], root)

    def test_changed_file_normalized_outputs_are_not_rooted_or_drive_qualified(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            paths = inventory.normalize_changed_files([
                ".github/workflows/validate.yml",
                (root / "project_sources/collector/source/DCOIR_Collector.ps1").as_posix(),
            ], root)
        for path in paths:
            with self.subTest(path=path):
                self.assertFalse(Path(path).is_absolute())
                self.assertIsNone(re.match(r"^[A-Za-z]:", path.replace("\\", "/")))


if __name__ == "__main__":
    raise SystemExit(unittest.main())
