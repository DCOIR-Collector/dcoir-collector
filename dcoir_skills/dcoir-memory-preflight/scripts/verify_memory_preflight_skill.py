#!/usr/bin/env python3
"""Validate the folded dcoir-memory-preflight skill package contents."""
from __future__ import annotations
import argparse
import pathlib
import sys

REQUIRED_FILES = [
    "SKILL.md",
    "references/airtable_cache_contract.md",
    "references/task_time_skill_routing.md",
    "references/session_checkpoint_and_closeout_workflow.md",
    "scripts/build_checkpoint_payload.py",
    "scripts/validate_cache_contract.py",
]
REQUIRED_MARKERS = [
    "updated-skill|20260507T183500Z|full-continuity-takeover",
    "updated-skill|20260507T000000Z|session-continuity-owner-fold-in",
    "updated-skill|20260505T073000Z|task-time-routing-strengthening",
]
REQUIRED_TEXT = [
    "primary and active continuity, checkpoint, startup, resume, re-anchor, handoff, and closeout owner",
    "Session Checkpoints",
    "active continuity, checkpoint, startup, resume, re-anchor, handoff, and closeout owner",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=pathlib.Path)
    args = parser.parse_args()
    root = args.skill_dir
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.is_file():
            errors.append(f"missing required file: {rel}")
    skill_md = root / "SKILL.md"
    if skill_md.is_file():
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        for marker in REQUIRED_MARKERS:
            if marker not in text:
                errors.append(f"missing marker text: {marker}")
        for snippet in REQUIRED_TEXT:
            if snippet not in text:
                errors.append(f"missing required text: {snippet}")
        if not text.startswith("---\nname: dcoir-memory-preflight"):
            errors.append("SKILL.md frontmatter missing or wrong")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: folded dcoir-memory-preflight skill checks passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
