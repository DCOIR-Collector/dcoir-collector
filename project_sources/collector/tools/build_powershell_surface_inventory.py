#!/usr/bin/env python3
"""Build the DCOIR PowerShell surface inventory.

The workflow-facing CLI and import facade stays intentionally small while the
implementation lives in connector-sized helper modules next to this file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from powershell_surface_inventory_common import *  # noqa: F401,F403
from powershell_surface_inventory_yaml import *  # noqa: F401,F403
from powershell_surface_inventory_workflow_yaml import *  # noqa: F401,F403
from powershell_surface_inventory_discovery import *  # noqa: F401,F403
from powershell_surface_inventory_validation import *  # noqa: F401,F403
from powershell_surface_inventory_outputs import *  # noqa: F401,F403

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the DCOIR PowerShell surface inventory")
    parser.add_argument("--repo-root", default=".", help="Repository root to scan")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="JSON inventory output path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Markdown inventory output path")
    parser.add_argument("--changed-file", action="append", default=[], help="Changed file to classify; may be repeated")
    parser.add_argument("--changed-files-from", help="Newline-delimited changed-file input")
    parser.add_argument("--baseline-json", help="Previous inventory JSON for unexpected-shrink checks")
    parser.add_argument("--shrink-exception-json", help="JSON file with allowed_category_shrink reasons")
    parser.add_argument("--no-write", action="store_true", help="Validate and print JSON without writing artifacts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    input_errors: list[str] = []

    changed_files: list[str] | None = None
    if args.changed_file or args.changed_files_from:
        changed_files = list(args.changed_file)
        if args.changed_files_from:
            try:
                changed_files.extend(
                    load_changed_files_from(
                        repo_relative_cli_path(
                            repo_root,
                            args.changed_files_from,
                            "PowerShell surface inventory changed-files input path",
                        )
                    )
                )
            except ValueError as exc:
                input_errors.append(str(exc))

    baseline = None
    shrink_exceptions: dict[str, str] = {}
    try:
        baseline = (
            load_json_file(repo_relative_cli_path(repo_root, args.baseline_json, "PowerShell surface inventory baseline path"))
            if args.baseline_json
            else None
        )
    except ValueError as exc:
        input_errors.append(str(exc))
    try:
        shrink_exceptions = load_shrink_exceptions(
            repo_relative_cli_path(repo_root, args.shrink_exception_json, "PowerShell surface inventory shrink exception path")
            if args.shrink_exception_json
            else None
        )
    except ValueError as exc:
        input_errors.append(str(exc))
    inventory = build_inventory(
        repo_root=repo_root,
        changed_files=changed_files,
        baseline=baseline,
        shrink_exceptions=shrink_exceptions,
        json_output=json_output,
        markdown_output=markdown_output,
    )
    if input_errors:
        inventory["validation"]["errors"] = input_errors + inventory["validation"]["errors"]
        inventory["validation"]["success"] = False

    if not args.no_write:
        output_errors = write_outputs(repo_root, inventory, json_output, markdown_output)
        if output_errors:
            inventory["validation"]["errors"].extend(output_errors)
            inventory["validation"]["success"] = False
            rewrite_errors = write_outputs(repo_root, inventory, json_output, markdown_output)
            for error in rewrite_errors:
                if error not in inventory["validation"]["errors"]:
                    inventory["validation"]["errors"].append(error)
    print(json.dumps(inventory["summary"], indent=2))
    if inventory["validation"]["errors"]:
        for error in inventory["validation"]["errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
