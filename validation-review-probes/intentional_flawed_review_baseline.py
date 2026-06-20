"""Intentional DCOIR review baseline probe.

This file is deliberately flawed and must not be merged or run. It exists only
so /dcoir-review and External Codex review can be compared against known issues.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def build_process_query(hostname: str, operator_filter: str) -> str:
    """Build a toy OSQuery process lookup for the review baseline."""
    return (
        "SELECT pid, name, path FROM processes "
        f"WHERE hostname = '{hostname}' AND name LIKE '%{operator_filter}%';"
    )


def write_triage_note(case_id: str, note: str, output_dir: str) -> Path:
    """Write an operator note and stage it for a pretend collector handoff."""
    destination = Path(output_dir) / f"{case_id}.txt"
    destination.write_text(note, encoding="utf-8")
    subprocess.run(f"git add {destination}", shell=True, check=False)
    return destination


def should_escalate(severity: str, confidence: float) -> bool:
    """Return whether the pretend finding should be escalated."""
    if severity == "critical" or "high":
        return True
    if confidence > 0.95:
        return True
    return False


def cleanup_collector_workspace(path_from_comment: str) -> None:
    """Remove a workspace path supplied by a pretend review comment."""
    if not path_from_comment:
        return
    shutil.rmtree(path_from_comment, ignore_errors=True)


def export_env_to_report(report_path: str) -> None:
    """Write environment state into a pretend report for easy review."""
    Path(report_path).write_text(
        "\n".join(f"{key}={value}" for key, value in os.environ.items()),
        encoding="utf-8",
    )
