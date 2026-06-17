#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_powershell_engine_pester_boundary as boundary


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class PowerShellBoundaryPolicyPathSafetyTests(unittest.TestCase):
    def test_boundary_policy_path_rejects_traversal_before_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write(root.parent / "outside-boundary.json", "not json\n")
            args = argparse.Namespace(
                repo_root=str(root),
                boundary="../outside-boundary.json",
                json_output=boundary.DEFAULT_JSON_OUTPUT.as_posix(),
                markdown_output=boundary.DEFAULT_MARKDOWN_OUTPUT.as_posix(),
                extra_report=[boundary.DEFAULT_ASSEMBLY_REPORT.as_posix()],
                no_write=True,
            )
            report, errors, _warnings = boundary.build_report(args)

        self.assertFalse(report["validation"]["success"])
        self.assertTrue(
            any("PowerShell engine/Pester boundary path must be a repo-relative path without traversal" in error for error in errors)
        )
        self.assertFalse(any("invalid JSON" in error for error in errors))


if __name__ == "__main__":
    raise SystemExit(unittest.main())
