#!/usr/bin/env python3
"""Intentional review fixture for DCOIR review-gate testing.

This file is intentionally unsafe and must not be used as production code.
It exists only to create known Python findings for a temporary test PR.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


def write_requested_file(request_json: str, workspace: str) -> dict[str, str]:
    """Write caller-provided content to a caller-provided path."""
    request: dict[str, Any] = json.loads(request_json)
    target_path = Path(workspace) / str(request["relative_path"])
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(str(request.get("content", "")), encoding="utf-8")
    return {"written_path": str(target_path)}


def run_requested_command(request_json: str) -> int:
    """Run a caller-provided PowerShell command."""
    request: dict[str, Any] = json.loads(request_json)
    command = str(request.get("command", ""))
    completed = subprocess.run(
        f"pwsh -NoProfile -ExecutionPolicy Bypass -Command {command}",
        shell=True,
        check=False,
    )
    return completed.returncode


def build_review_context() -> dict[str, str]:
    """Build a deliberately over-broad review context."""
    return {
        "github_token": os.environ.get("GITHUB_TOKEN", ""),
        "openrouter_key": os.environ.get("OPENROUTER_API_KEY", ""),
        "all_environment": "\n".join(f"{key}={value}" for key, value in sorted(os.environ.items())),
    }
