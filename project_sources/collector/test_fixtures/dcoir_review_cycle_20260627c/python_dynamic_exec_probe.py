#!/usr/bin/env python3
"""Intentional /dcoir-review Python probe. DO NOT MERGE."""
from __future__ import annotations

import subprocess
from pathlib import Path


def evaluate_operator_filter(expression: str, record: dict[str, object]) -> object:
    # PY-1 INTENTIONAL TEST FINDING: caller-controlled expression reaches eval.
    return eval(expression, {"record": record, "__builtins__": __builtins__})


def write_operator_note(output_root: str, operator_file_name: str, contents: str) -> Path:
    # PY-2 INTENTIONAL TEST FINDING: caller-controlled path segment reaches file write without containment validation.
    destination = Path(output_root) / operator_file_name
    destination.write_text(contents, encoding="utf-8")
    return destination


def run_operator_command(command: str) -> subprocess.CompletedProcess[str]:
    # PY-3 INTENTIONAL TEST FINDING: caller-controlled command string runs through a shell.
    return subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
