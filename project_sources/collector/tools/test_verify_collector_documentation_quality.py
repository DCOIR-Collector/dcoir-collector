#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("verify_collector_documentation_quality.py")
SPEC = importlib.util.spec_from_file_location("verify_collector_documentation_quality", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load validator module from {MODULE_PATH}")

validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class DocumentationQualityValidatorTests(unittest.TestCase):
    def _function_help_map(self, text: str) -> dict[str, bool]:
        lines = text.splitlines()
        result: dict[str, bool] = {}
        for lineno, raw in validator.function_lines(text):
            result[validator.function_name(raw)] = validator.has_help_near_function(lines, lineno)
        return result

    def test_detects_file_help_in_header_block(self) -> None:
        text = """<#
.SYNOPSIS
Core collector helpers.
.DESCRIPTION
Durable file header.
#>

function Invoke-Test {
}
"""
        self.assertTrue(validator.detect_file_help(text))

    def test_detects_long_adjacent_help_block(self) -> None:
        text = """<#
.SYNOPSIS
Long helper block.
.DESCRIPTION
This help block intentionally exceeds the old 14-line window.
Line 01
Line 02
Line 03
Line 04
Line 05
Line 06
Line 07
Line 08
Line 09
Line 10
Line 11
Line 12
Line 13
Line 14
Line 15
Line 16
FUNCTION NAME:
Invoke-LongHelp
INPUT:
None
OUTPUT:
None
#>
function Invoke-LongHelp {
}
"""
        help_map = self._function_help_map(text)
        self.assertTrue(help_map["Invoke-LongHelp"])

    def test_detects_nested_helper_with_adjacent_help(self) -> None:
        text = """<#
.SYNOPSIS
Outer function help.
.DESCRIPTION
Top-level helper.
#>
function Invoke-Outer {
    $worker = {
        <#
        .SYNOPSIS
        Nested worker helper.
        .DESCRIPTION
        Nested helper help should count.
        FUNCTION NAME:
        Invoke-WorkerCommandCapture
        INPUT:
        StepDefinition
        OUTPUT:
        Step result object
        #>
        function Invoke-WorkerCommandCapture {
            param($StepDefinition)
        }
    }
}
"""
        help_map = self._function_help_map(text)
        self.assertTrue(help_map["Invoke-Outer"])
        self.assertTrue(help_map["Invoke-WorkerCommandCapture"])

    def test_detects_help_when_blank_lines_exist_between_block_and_function(self) -> None:
        text = """<#
.SYNOPSIS
Blank line tolerant help.
.DESCRIPTION
The validator should skip blank lines between help and function.
#>


function Invoke-BlankLineTolerant {
}
"""
        help_map = self._function_help_map(text)
        self.assertTrue(help_map["Invoke-BlankLineTolerant"])

    def test_rejects_non_adjacent_help_block_when_code_intervenes(self) -> None:
        text = """<#
.SYNOPSIS
Detached help block.
.DESCRIPTION
This help should not count because code intervenes.
#>
$x = 1
function Invoke-MissingAdjacentHelp {
}
"""
        help_map = self._function_help_map(text)
        self.assertFalse(help_map["Invoke-MissingAdjacentHelp"])


if __name__ == "__main__":
    unittest.main()
