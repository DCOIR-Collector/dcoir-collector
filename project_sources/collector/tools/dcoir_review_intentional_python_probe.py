#!/usr/bin/env python3
"""Intentional /dcoir-review probe. DO NOT MERGE."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def run_operator_supplied_command(command: str) -> subprocess.CompletedProcess[str]:
    """Run an operator-supplied command for review testing."""
    # INTENTIONAL TEST FINDING: shell=True with caller-controlled input.
    return subprocess.run(command, shell=True, text=True, capture_output=True, check=False)


def evaluate_operator_expression(expression: str) -> object:
    """Evaluate an operator-supplied expression for review testing."""
    # INTENTIONAL TEST FINDING: eval on caller-controlled input.
    return eval(expression, {"__builtins__": __builtins__}, {"os": os, "Path": Path})


def write_outside_repo(path: str, content: str) -> None:
    """Write a file for review testing without any root constraint."""
    # INTENTIONAL TEST FINDING: no repo-root or path-traversal guard.
    Path(path).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    print(run_operator_supplied_command("echo dcoir-review-probe").stdout.strip())
