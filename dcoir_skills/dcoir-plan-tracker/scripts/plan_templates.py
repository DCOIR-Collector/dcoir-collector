#!/usr/bin/env python3
"""Template helpers for dcoir-plan-tracker."""
from __future__ import annotations

import copy
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_PLAN_FILES = [
    "00_index.md",
    "01_scope_and_constraints.md",
    "02_execution_table.md",
    "03_decisions_and_rationale.md",
    "04_call_log.md",
    "05_resume_state.md",
    "06_artifacts_and_outputs.md",
    "07_closeout.md",
    "plan_state.json",
]

ALLOWED_PLAN_STATUSES = ["draft", "approved_to_execute", "active", "blocked", "paused", "complete", "archived"]
ALLOWED_TASK_STATUSES = ["todo", "in_progress", "blocked", "done", "skipped"]


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "untitled-plan"


def build_plan_id(date_yyyymmdd: str, slug: str) -> str:
    if not re.fullmatch(r"\d{8}", date_yyyymmdd):
        raise ValueError("date must be YYYYMMDD")
    return f"PLAN-{date_yyyymmdd}-{slugify(slug)}"


def today_yyyymmdd() -> str:
    return dt.date.today().strftime("%Y%m%d")


def utc_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def make_empty_plan_state(plan_id: str, title: str, objective: str, owner: str = "assistant") -> Dict[str, Any]:
    return {
        "plan_id": plan_id,
        "title": title,
        "objective": objective,
        "owner": owner,
        "status": "draft",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "active_task_id": "",
        "active_task_title": "",
        "next_recommended_action": "define the first top-level tasks",
        "assumptions": [],
        "constraints": [],
        "stop_conditions": [],
        "decisions": [],
        "blockers": [],
        "artifacts": [],
        "call_log": [],
        "tasks": [],
        "resume_state": {
            "exact_resume_goal": "",
            "resume_detail": "",
            "why_current_task_matters": "",
            "carry_forward_note": "",
            "flush_trigger": "",
            "pending_flush_items": [],
            "promotion_candidates": [],
            "remain_local_notes": [],
            "validation_counters": [],
        },
    }


def flatten_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for task in tasks:
        row = copy.deepcopy(task)
        row.setdefault("children", [])
        children = row.pop("children")
        rows.append(row)
        rows.extend(flatten_tasks(children))
    return rows


def task_lookup(tasks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {row["id"]: row for row in flatten_tasks(tasks)}


def find_task(tasks: List[Dict[str, Any]], task_id: str) -> Dict[str, Any] | None:
    for task in tasks:
        if task["id"] == task_id:
            return task
        child = find_task(task.get("children", []), task_id)
        if child:
            return child
    return None


def render_index_md(plan: Dict[str, Any]) -> str:
    resume = plan.get("resume_state", {})
    pending_flush = len(resume.get("pending_flush_items", []))
    counters = resume.get("validation_counters", [])
    countdown_line = "none recorded"
    if counters:
        countdown_line = "; ".join(
            f"{item.get('label', 'countdown')}: remaining={item.get('remaining', '')}"
            for item in counters
        )
    return f"""# {plan['plan_id']}

- title: {plan['title']}
- objective: {plan['objective']}
- owner: {plan['owner']}
- status: {plan['status']}
- created_at: {plan['created_at']}
- updated_at: {plan['updated_at']}
- active_task_id: {plan['active_task_id']}
- active_task_title: {plan['active_task_title']}
- next_recommended_action: {plan['next_recommended_action']}
- pending_flush_item_count: {pending_flush}
- validation_counters: {countdown_line}
"""


def render_scope_md(plan: Dict[str, Any]) -> str:
    assumptions = "\n".join(f"- {item}" for item in plan.get("assumptions", []) or ["none recorded yet"])
    constraints = "\n".join(f"- {item}" for item in plan.get("constraints", []) or ["none recorded yet"])
    stops = "\n".join(f"- {item}" for item in plan.get("stop_conditions", []) or ["none recorded yet"])
    return f"""# Scope And Constraints\n\n## Objective\n- {plan['objective']}\n\n## Assumptions\n{assumptions}\n\n## Constraints\n{constraints}\n\n## Stop Conditions\n{stops}\n"""


def render_execution_table_md(plan: Dict[str, Any]) -> str:
    header = "| id | parent_id | level | title | status | owner | why_it_matters | next_action | expected_output | validation_gate | touched_paths | blocking_dependency | last_update |\n"
    separator = "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    lines = [header, separator]
    for row in flatten_tasks(plan.get("tasks", [])):
        lines.append(
            "| {id} | {parent_id} | {level} | {title} | {status} | {owner} | {why_it_matters} | {next_action} | {expected_output} | {validation_gate} | {touched_paths} | {blocking_dependency} | {last_update} |\n".format(
                id=row.get("id", ""),
                parent_id=row.get("parent_id", ""),
                level=row.get("level", ""),
                title=row.get("title", ""),
                status=row.get("status", ""),
                owner=row.get("owner", ""),
                why_it_matters=row.get("why_it_matters", ""),
                next_action=row.get("next_action", ""),
                expected_output=row.get("expected_output", ""),
                validation_gate=row.get("validation_gate", ""),
                touched_paths=", ".join(row.get("touched_paths", [])),
                blocking_dependency=row.get("blocking_dependency", ""),
                last_update=row.get("last_update", ""),
            )
        )
    if len(lines) == 2:
        lines.append("|  |  |  | no tasks yet |  |  |  |  |  |  |  |  |  |\n")
    return "# Execution Table\n\n" + "".join(lines)


def render_decisions_md(plan: Dict[str, Any]) -> str:
    items = plan.get("decisions", [])
    if not items:
        return "# Decisions And Rationale\n\n- none recorded yet\n"
    body = []
    for item in items:
        body.append(f"## {item.get('title', 'decision')}\n- rationale: {item.get('rationale', '')}\n- recorded_at: {item.get('recorded_at', '')}\n")
    return "# Decisions And Rationale\n\n" + "\n".join(body)


def render_call_log_md(plan: Dict[str, Any]) -> str:
    items = plan.get("call_log", [])
    if not items:
        return "# Call Log\n\n- none recorded yet\n"
    body = []
    for item in items:
        body.append(f"- {item.get('timestamp', '')}: {item.get('summary', '')}")
    return "# Call Log\n\n" + "\n".join(body) + "\n"


def render_resume_state_md(plan: Dict[str, Any]) -> str:
    blockers = plan.get("blockers", [])
    blocker_lines = "\n".join(
        f"- {item.get('signature', 'blocker')}: {item.get('status', '')} | mitigation: {item.get('mitigation', '')}"
        for item in blockers
    ) or "- none recorded yet"
    resume = plan.get("resume_state", {})
    pending_flush_items = resume.get("pending_flush_items", [])
    promotion_candidates = resume.get("promotion_candidates", [])
    remain_local_notes = resume.get("remain_local_notes", [])
    counters = resume.get("validation_counters", [])
    pending_flush_lines = "\n".join(f"- {item}" for item in pending_flush_items) or "- none recorded yet"
    promotion_lines = "\n".join(f"- {item}" for item in promotion_candidates) or "- none recorded yet"
    remain_local_lines = "\n".join(f"- {item}" for item in remain_local_notes) or "- none recorded yet"
    counter_lines = "\n".join(
        f"- {item.get('label', 'countdown')}: remaining={item.get('remaining', '')} | trigger_action: {item.get('trigger_action', '')} | note: {item.get('note', '')}"
        for item in counters
    ) or "- none recorded yet"
    return f"""# Resume State

- plan_status: {plan['status']}
- active_task_id: {plan['active_task_id']}
- active_task_title: {plan['active_task_title']}
- next_recommended_action: {plan['next_recommended_action']}
- exact_resume_goal: {resume.get('exact_resume_goal', '') or 'not recorded yet'}
- why_current_task_matters: {resume.get('why_current_task_matters', '') or 'not recorded yet'}
- resume_detail: {resume.get('resume_detail', '') or 'not recorded yet'}
- carry_forward_note: {resume.get('carry_forward_note', '') or 'not recorded yet'}
- flush_trigger: {resume.get('flush_trigger', '') or 'not recorded yet'}

## Blockers
{blocker_lines}

## Pending Flush Items
{pending_flush_lines}

## Promotion Candidates
{promotion_lines}

## Remain Local For Now
{remain_local_lines}

## Validation Counters
{counter_lines}
"""


def render_artifacts_md(plan: Dict[str, Any]) -> str:
    items = plan.get("artifacts", [])
    if not items:
        return "# Artifacts And Outputs\n\n- none recorded yet\n"
    body = []
    for item in items:
        body.append(f"- {item}")
    return "# Artifacts And Outputs\n\n" + "\n".join(body) + "\n"


def render_closeout_md(plan: Dict[str, Any]) -> str:
    return "# Closeout\n\n- status: not closed yet\n"


def write_plan_folder(plan_dir: Path, plan: Dict[str, Any]) -> None:
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "00_index.md").write_text(render_index_md(plan), encoding="utf-8")
    (plan_dir / "01_scope_and_constraints.md").write_text(render_scope_md(plan), encoding="utf-8")
    (plan_dir / "02_execution_table.md").write_text(render_execution_table_md(plan), encoding="utf-8")
    (plan_dir / "03_decisions_and_rationale.md").write_text(render_decisions_md(plan), encoding="utf-8")
    (plan_dir / "04_call_log.md").write_text(render_call_log_md(plan), encoding="utf-8")
    (plan_dir / "05_resume_state.md").write_text(render_resume_state_md(plan), encoding="utf-8")
    (plan_dir / "06_artifacts_and_outputs.md").write_text(render_artifacts_md(plan), encoding="utf-8")
    (plan_dir / "07_closeout.md").write_text(render_closeout_md(plan), encoding="utf-8")
    (plan_dir / "plan_state.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
