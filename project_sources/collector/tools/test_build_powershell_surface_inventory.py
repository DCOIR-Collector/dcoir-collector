#!/usr/bin/env python3
"""Unittest entry point for PowerShell surface inventory coverage."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from powershell_surface_inventory_test_cases.basic_and_shape_failures import BasicAndShapeFailureTests
from powershell_surface_inventory_test_cases.defaults_and_profiles import DefaultsAndProfileTests
from powershell_surface_inventory_test_cases.inventory_cli_manifest import InventoryCliManifestTests
from powershell_surface_inventory_test_cases.workflow_shape_collections import WorkflowShapeCollectionTests
from powershell_surface_inventory_test_cases.workflow_snippet_blocks import WorkflowSnippetBlockScalarTests
from powershell_surface_inventory_test_cases.workflow_snippet_detection import WorkflowSnippetDetectionTests


__all__ = [
    "BasicAndShapeFailureTests",
    "DefaultsAndProfileTests",
    "InventoryCliManifestTests",
    "WorkflowShapeCollectionTests",
    "WorkflowSnippetBlockScalarTests",
    "WorkflowSnippetDetectionTests",
]


if __name__ == "__main__":
    unittest.main()
