#!/usr/bin/env python3
"""Update a local plan-state cache and refresh markdown mirrors.

This script is intended for deterministic local rendering before GitHub updates. It supports
simple status transitions and active-task updates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from plan_templates import ALLOWED_PLAN_STATUSES, ALLOWED_TASK_STATUSES, find_task, flatten_tasks, task_lookup, utc_now, write_plan_folder


def set_if_blank(mapping: dict, key: str, value: str) -> None:
    if value and not str(mapping.get(key, '')).strip():
        mapping[key] = value


def first_next_eligible_task(plan: dict) -> dict | None:
    for row in flatten_tasks(plan.get('tasks', [])):
        if row.get('status') == 'todo':
            return row
    return None


def set_next_step_from_task(plan: dict, resume: dict, task: dict) -> None:
    next_action = task.get('next_action', '').strip() or f"start {task.get('id', '')} {task.get('title', '').strip()}".strip()
    why = task.get('why_it_matters', '').strip()
    if next_action:
        plan['next_recommended_action'] = next_action
        resume['exact_resume_goal'] = next_action
    if why:
        resume['why_current_task_matters'] = why


def set_no_remaining_next_step(plan: dict, resume: dict) -> None:
    next_action = 'review plan completion or close the plan'
    plan['next_recommended_action'] = next_action
    resume['exact_resume_goal'] = next_action
    resume['why_current_task_matters'] = 'all current tasks are complete, skipped, or otherwise non-actionable from the current local plan state'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan_dir")
    parser.add_argument("--task-id")
    parser.add_argument("--task-status", choices=ALLOWED_TASK_STATUSES)
    parser.add_argument("--plan-status", choices=ALLOWED_PLAN_STATUSES)
    parser.add_argument("--next-action")
    parser.add_argument("--blocker-signature")
    parser.add_argument("--blocker-mitigation", default="")
    parser.add_argument("--touch-path", action="append", default=[])
    parser.add_argument("--resume-detail")
    parser.add_argument("--why-current-task-matters")
    parser.add_argument("--carry-forward-note")
    parser.add_argument("--flush-trigger")
    parser.add_argument("--pending-flush-item", action="append", default=[])
    parser.add_argument("--promotion-candidate", action="append", default=[])
    parser.add_argument("--remain-local-note", action="append", default=[])
    parser.add_argument("--countdown-label")
    parser.add_argument("--countdown-remaining", type=int)
    parser.add_argument("--countdown-trigger-action")
    parser.add_argument("--countdown-note", default="")
    args = parser.parse_args()

    plan_dir = Path(args.plan_dir)
    plan_path = plan_dir / "plan_state.json"
    if not plan_path.exists():
        raise SystemExit('no pre-existing local plan-state cache was present for this plan folder; run scripts/ensure_plan_state.py first and do not treat the missing interval as local-cache continuity')
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    now = utc_now()
    plan["updated_at"] = now

    if args.plan_status:
        plan["status"] = args.plan_status

    if args.next_action:
        plan["next_recommended_action"] = args.next_action

    resume = plan.setdefault("resume_state", {})

    if args.task_id and args.task_status == "in_progress":
        set_if_blank(resume, "exact_resume_goal", plan.get("next_recommended_action", ""))
    if args.next_action:
        set_if_blank(resume, "exact_resume_goal", args.next_action)
    if args.resume_detail:
        resume["resume_detail"] = args.resume_detail
    if args.why_current_task_matters:
        resume["why_current_task_matters"] = args.why_current_task_matters
    if args.carry_forward_note:
        resume["carry_forward_note"] = args.carry_forward_note
    if args.flush_trigger:
        resume["flush_trigger"] = args.flush_trigger
    if args.pending_flush_item:
        existing = resume.setdefault("pending_flush_items", [])
        existing.extend(item for item in args.pending_flush_item if item not in existing)
    if args.promotion_candidate:
        existing = resume.setdefault("promotion_candidates", [])
        existing.extend(item for item in args.promotion_candidate if item not in existing)
    if args.remain_local_note:
        existing = resume.setdefault("remain_local_notes", [])
        existing.extend(item for item in args.remain_local_note if item not in existing)
    if args.countdown_label:
        counters = [c for c in resume.setdefault("validation_counters", []) if c.get("label") != args.countdown_label]
        counters.append({
            "label": args.countdown_label,
            "remaining": args.countdown_remaining if args.countdown_remaining is not None else "",
            "trigger_action": args.countdown_trigger_action or "",
            "note": args.countdown_note or "",
        })
        resume["validation_counters"] = counters

    if args.task_id:
        task = find_task(plan.get("tasks", []), args.task_id)
        if task is None:
            raise SystemExit(f"task not found: {args.task_id}")
        if args.task_status:
            task["status"] = args.task_status
            task["last_update"] = now
            if args.task_status == "in_progress":
                for other in task_lookup(plan.get("tasks", [])).values():
                    if other["id"] != args.task_id and other.get("status") == "in_progress":
                        other["status"] = "todo"
                plan["status"] = "active"
                plan["active_task_id"] = task["id"]
                plan["active_task_title"] = task.get("title", "")
                plan["next_recommended_action"] = task.get("next_action", "") or plan.get("next_recommended_action", "")
                set_if_blank(resume, "exact_resume_goal", task.get("next_action", "") or plan.get("next_recommended_action", ""))
                set_if_blank(resume, "why_current_task_matters", task.get("why_it_matters", ""))
            elif plan.get("active_task_id") == args.task_id and args.task_status in {"done", "blocked", "skipped"}:
                plan["active_task_id"] = ""
                plan["active_task_title"] = ""
                if args.task_status in {"done", "skipped"}:
                    next_task = first_next_eligible_task(plan)
                    if next_task is not None:
                        set_next_step_from_task(plan, resume, next_task)
                    else:
                        set_no_remaining_next_step(plan, resume)
                elif args.task_status == "blocked":
                    plan["status"] = "blocked"
                    blocker_step = (args.blocker_mitigation or "").strip() or f"resolve blocker for {task.get('id', '')} {task.get('title', '').strip()}".strip()
                    plan["next_recommended_action"] = blocker_step
                    resume["exact_resume_goal"] = blocker_step
                    resume["why_current_task_matters"] = task.get("why_it_matters", "") or resume.get("why_current_task_matters", "")
        if args.touch_path:
            existing = set(task.get("touched_paths", []))
            existing.update(args.touch_path)
            task["touched_paths"] = sorted(existing)

    if args.blocker_signature:
        plan.setdefault("blockers", []).append(
            {
                "recorded_at": now,
                "signature": args.blocker_signature,
                "status": "open",
                "mitigation": args.blocker_mitigation,
            }
        )

    write_plan_folder(plan_dir, plan)
    print(plan_dir)
    print(plan.get("active_task_id", ""))


if __name__ == "__main__":
    main()
