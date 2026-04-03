#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a DCOIR collector repair plan from audit results.")
    parser.add_argument("--audit-json", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--requested-mode", default="repair")
    parser.add_argument("--defect-summary", default="bounded collector or harness defect under test")
    args = parser.parse_args()

    audit = load_json(Path(args.audit_json))
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    repair_candidates = audit.get("repair_candidates", [])
    doc_health = audit.get("documentation_health", {})

    changed_targets: List[str] = []
    for item in repair_candidates:
        target = item.get("target")
        if target and target not in changed_targets:
            changed_targets.append(target)

    if not changed_targets:
        changed_targets = ["no static-repair target identified; use only when an execution-backed defect is present"]

    plan = {
        "generated_at": timestamp,
        "requested_mode": args.requested_mode,
        "defect_summary": args.defect_summary,
        "changed_targets": changed_targets,
        "repair_candidates": repair_candidates,
        "documentation_actions": [],
        "validation_lanes": [
            "rerun motivating failure lane",
            "rerun at least one known-good control lane",
            "regenerate maintenance code blocks",
        ],
        "stop_conditions": [
            "stop if the defect cannot be reproduced or bounded well enough to patch safely",
            "stop if the required changed set would exceed the requested scope without explicit approval",
            "stop if validation evidence is missing after the patch",
        ],
    }

    if not doc_health.get("file_comment_help_present"):
        plan["documentation_actions"].append("add concise file-level comment-based help to the primary collector entry-point if the patch touches that script")
    if int(doc_health.get("undocumented_function_count", 0)) > 0:
        plan["documentation_actions"].append("add or refresh concise maintenance cues for externally-invoked or output-contract-critical functions in the changed area")

    Path(args.json_out).write_text(json.dumps(plan, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
