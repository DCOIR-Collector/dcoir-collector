#!/usr/bin/env python3
"""Render Airtable-ready payloads from dcoir-plan-tracker local plan folders.

Current model: Plans + Work Items + Session Checkpoints are live operational
surfaces. Retired Plan Tasks / Plan Checkpoints / Tracking Registry surfaces are
not required unless live schema readback proves they exist for a specific task.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from plan_templates import flatten_tasks

BASE_ID = 'appM4KSwnVf3G3OTK'
TABLES = {
    'plans': {'id': 'tblBcp5FyMIfOm7Xe', 'name': 'Plans'},
    'work_items': {'id': 'tblgsQAVWvh8K7gIR', 'name': 'Work Items'},
    'session_checkpoints': {'id': 'tblTe75HKZOJaPDGn', 'name': 'Session Checkpoints'},
    'admin_registry': {'id': 'tblFaJW1V2DPc9css', 'name': 'Admin Registry'},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def short_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')


def load_plan(plan_dir: Path) -> dict[str, Any]:
    path = plan_dir / 'plan_state.json'
    return json.loads(path.read_text(encoding='utf-8'))


def multiline(items: list[str]) -> str:
    return '\n'.join(f'- {item}' for item in items if str(item).strip()) or 'none recorded'


def plan_fields(plan: dict[str, Any]) -> dict[str, Any]:
    resume = plan.get('resume_state', {})
    scope = [f"objective: {plan.get('objective', '')}"]
    for key in ('assumptions', 'constraints', 'stop_conditions'):
        values = plan.get(key, []) or []
        if values:
            scope.append(f"{key}: {'; '.join(values)}")
    return {
        'plan_id': plan.get('plan_id', ''),
        'plan_title': plan.get('title', ''),
        'active_task_id': plan.get('active_task_id', ''),
        'active_task_title': plan.get('active_task_title', ''),
        'scope_constraints': '\n'.join(scope),
        'exact_resume_goal': resume.get('exact_resume_goal', ''),
        'resume_detail': resume.get('resume_detail', ''),
        'why_current_task_matters': resume.get('why_current_task_matters', ''),
        'carry_forward_note': resume.get('carry_forward_note', ''),
        'flush_trigger': resume.get('flush_trigger', ''),
        'pending_flush_items': multiline(resume.get('pending_flush_items', [])),
        'promotion_candidates': multiline(resume.get('promotion_candidates', [])),
        'remain_local_notes': multiline(resume.get('remain_local_notes', [])),
        'next_recommended_action': plan.get('next_recommended_action', ''),
        'last_updated_text': plan.get('updated_at', ''),
        'active_plan_task_id': plan.get('active_task_id', ''),
    }


def admin_registry_hint(object_key: str, object_name: str, owning_table: str, notes: str) -> dict[str, Any]:
    return {
        'registry_key': object_key,
        'object_name': object_name,
        'owning_table': owning_table,
        'notes': notes,
    }


def task_fields(plan_id: str, task: dict[str, Any]) -> dict[str, Any]:
    task_id = task.get('id', '')
    notes = [
        f"plan_id: {plan_id}",
        f"parent_task_id: {task.get('parent_id', '')}",
        f"level: {task.get('level', 'task')}",
        f"owner: {task.get('owner', '')}",
        f"why_it_matters: {task.get('why_it_matters', '')}",
        f"expected_output: {task.get('expected_output', '')}",
        f"validation_gate: {task.get('validation_gate', '')}",
        f"last_update: {task.get('last_update', '')}",
    ]
    touched_paths = task.get('touched_paths', []) or []
    return {
        'Work Item': task.get('title', ''),
        'Item ID': task_id,
        'Repo Path or Skill': '\n'.join(touched_paths),
        'Evidence / Notes': '\n'.join(notes),
        'Blocker': task.get('blocking_dependency', ''),
        'Next Action': task.get('next_action', ''),
        'Active': task.get('status', 'todo') not in {'done', 'skipped', 'archived'},
        'canonical_parent_plan_id': plan_id,
        'source_table': 'local plan_state.json',
        'source_record_id': task_id,
    }


def checkpoint_fields(plan: dict[str, Any], trigger: str, blocker_signature: str, failed_attempt_summary: str, successful_mitigation: str, reusable_lesson_candidate: str, safe_to_flush_now: str, remain_local_for_now: str) -> dict[str, Any]:
    resume = plan.get('resume_state', {})
    checkpoint_id = f"scp-{short_stamp()}-{plan.get('plan_id', '')}"
    return {
        'checkpoint_id': checkpoint_id,
        'session_id': plan.get('plan_id', ''),
        'checkpoint_at': utc_now(),
        'trigger': trigger,
        'state_summary': f"plan_id: {plan.get('plan_id', '')}\nactive_task_id: {plan.get('active_task_id', '')}",
        'current_focus': plan.get('active_task_title', ''),
        'open_threads': f"blocker_signature: {blocker_signature}\nfailed_attempt_summary: {failed_attempt_summary}",
        'decisions_constraints': f"successful_mitigation: {successful_mitigation}\nreusable_lesson_candidate: {reusable_lesson_candidate}\nsafe_to_flush_now: {safe_to_flush_now}\nremain_local_for_now: {remain_local_for_now}",
        'buffered_promotion_candidates': multiline(resume.get('promotion_candidates', [])),
        'next_recommended_move': plan.get('next_recommended_action', ''),
        'resume_prompt': resume.get('resume_detail', ''),
        'checkpoint_status': 'active',
    }


def emit(payload: dict[str, Any], output_json: str | None) -> None:
    text = json.dumps(payload, indent=2)
    if output_json:
        Path(output_json).write_text(text + '\n', encoding='utf-8')
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description='Render Airtable-ready payloads from dcoir-plan-tracker local plan folders.')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('plan')
    p.add_argument('plan_dir')
    p.add_argument('--output-json')

    t = sub.add_parser('tasks')
    t.add_argument('plan_dir')
    t.add_argument('--output-json')

    c = sub.add_parser('checkpoint')
    c.add_argument('plan_dir')
    c.add_argument('--trigger', required=True)
    c.add_argument('--blocker-signature', default='')
    c.add_argument('--failed-attempt-summary', default='')
    c.add_argument('--successful-mitigation', default='')
    c.add_argument('--reusable-lesson-candidate', default='')
    c.add_argument('--safe-to-flush-now', default='')
    c.add_argument('--remain-local-for-now', default='')
    c.add_argument('--output-json')

    args = parser.parse_args()
    plan = load_plan(Path(args.plan_dir))

    if args.cmd == 'plan':
        fields = plan_fields(plan)
        emit({
            'base_id': BASE_ID,
            'table': TABLES['plans'],
            'fields': fields,
            'admin_registry_hint': admin_registry_hint(fields['plan_id'], fields['plan_title'], TABLES['plans']['name'], fields.get('next_recommended_action', '')),
        }, args.output_json)
        return 0

    if args.cmd == 'tasks':
        rows = [task_fields(plan.get('plan_id', ''), row) for row in flatten_tasks(plan.get('tasks', []))]
        emit({'base_id': BASE_ID, 'table': TABLES['work_items'], 'records': rows}, args.output_json)
        return 0

    fields = checkpoint_fields(
        plan,
        args.trigger,
        args.blocker_signature,
        args.failed_attempt_summary,
        args.successful_mitigation,
        args.reusable_lesson_candidate,
        args.safe_to_flush_now,
        args.remain_local_for_now,
    )
    emit({
        'base_id': BASE_ID,
        'table': TABLES['session_checkpoints'],
        'fields': fields,
        'admin_registry_hint': admin_registry_hint(fields['checkpoint_id'], fields['trigger'], TABLES['session_checkpoints']['name'], fields.get('next_recommended_move', '')),
    }, args.output_json)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
