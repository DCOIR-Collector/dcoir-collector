#!/usr/bin/env python3
"""Add a task, subtask, or subsubtask to a local plan-state cache and refresh markdown mirrors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from plan_templates import find_task, utc_now, write_plan_folder


def next_top_level_id(tasks: List[Dict[str, Any]]) -> str:
    top = [t for t in tasks if t.get("level") == "task"]
    return f"T{len(top) + 1}"


def next_child_id(parent: Dict[str, Any]) -> str:
    children = parent.setdefault("children", [])
    return f"{parent['id']}.{len(children) + 1}"


def child_level(parent_level: str) -> str:
    return {
        "task": "subtask",
        "subtask": "subsubtask",
    }.get(parent_level, "subsubtask")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan_dir")
    parser.add_argument("--title", required=True)
    parser.add_argument("--why", required=True)
    parser.add_argument("--next-action", required=True)
    parser.add_argument("--expected-output", required=True)
    parser.add_argument("--validation-gate", required=True)
    parser.add_argument("--owner", default="assistant")
    parser.add_argument("--parent-id")
    args = parser.parse_args()

    plan_dir = Path(args.plan_dir)
    plan_path = plan_dir / "plan_state.json"
    if not plan_path.exists():
        raise SystemExit('no pre-existing local plan-state cache was present for this plan folder; run scripts/ensure_plan_state.py first and do not treat the missing interval as local-cache continuity')
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    now = utc_now()

    task = {
        "id": "",
        "parent_id": args.parent_id or "",
        "level": "task",
        "title": args.title,
        "status": "todo",
        "owner": args.owner,
        "why_it_matters": args.why,
        "next_action": args.next_action,
        "expected_output": args.expected_output,
        "validation_gate": args.validation_gate,
        "touched_paths": [],
        "blocking_dependency": "",
        "last_update": now,
        "children": [],
    }

    if args.parent_id:
        parent = find_task(plan.get("tasks", []), args.parent_id)
        if parent is None:
            raise SystemExit(f"parent task not found: {args.parent_id}")
        task["id"] = next_child_id(parent)
        task["level"] = child_level(parent.get("level", "task"))
        parent.setdefault("children", []).append(task)
    else:
        task["id"] = next_top_level_id(plan.get("tasks", []))
        plan.setdefault("tasks", []).append(task)

    plan["updated_at"] = now
    write_plan_folder(plan_dir, plan)
    print(task["id"])
    print(plan_dir)


if __name__ == "__main__":
    main()
