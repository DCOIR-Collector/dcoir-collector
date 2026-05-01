#!/usr/bin/env python3
"""Regression check for dcoir-plan-tracker parent-plan sync rules."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "SKILL.md": [
        "Mandatory parent-plan sync gate",
        "canonical_parent_plan_id",
        "parent Airtable `Plans` row",
        "Do not rely on checkpoints alone as a substitute",
        "do not close a Work Item while its parent Plan still points at the closed task",
    ],
    "references/airtable_plan_sync_workflow.md": [
        "Parent-plan sync gate",
        "Never let a Session Checkpoint become the only source of truth",
        "Drift repair rule",
    ],
}

def main() -> int:
    missing = []
    for rel, needles in CHECKS.items():
        path = ROOT / rel
        if not path.exists():
            missing.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                missing.append(f"{rel}: missing {needle!r}")
    if missing:
        print("FAIL: parent-plan sync regression checks failed")
        for item in missing:
            print(f"- {item}")
        return 1
    print("PASS: parent-plan sync regression checks passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
