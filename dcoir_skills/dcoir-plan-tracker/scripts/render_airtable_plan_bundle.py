#!/usr/bin/env python3
"""Render Airtable-ready payloads from dcoir-plan-tracker local plan folders."""
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
    'plan_tasks': {'id': 'tblsATLIDeh6gtcoM', 'name': 'Plan Tasks'},
    'plan_checkpoints': {'id': 'tbl6z4Lyai2RABMyw', 'name': 'Plan Checkpoints'},
    'tracking_registry': {'id': 'tblohiMxxVbDUnN77', 'name': 'Tracking Registry'},
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
    scope = []
    scope.append(f"objective: {plan.get('objective', '')}")
    for key in ('assumptions', 'constraints', 'stop_conditions'):
        values = plan.get(key, []) or []
        if values:
            scope.append(f"{key}: {'; '.join(values)}")
    return {
        'plan_id': plan.get('plan_id', ''),
        'plan_title': plan.get('title', ''),
        'plan_state': plan.get('status', 'draft'),
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
    }


def plan_registry(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        'object_id': fields['plan_id'],
        'object_type': 'plan',
        'source_skill': 'dcoir-plan-tracker',
        'primary_title': fields['plan_title'],
        'parent_object_id': '',
        'session_id': '',
        'plan_id': fields['plan_id'],
        'status': fields['plan_state'],
        'created_time_text': fields['last_updated_text'],
        'updated_time_text': fields['last_updated_text'],
        'is_active': fields['plan_state'] not in {'complete', 'archived'},
        'airtable_table_name': TABLES['plans']['name'],
        'airtable_record_id': '',
        'github_promotion_status': 'candidate',
        'importance': 'high',
        'tags': 'plan\ntracker',
        'summary': fields['next_recommended_action'],
    }


def task_fields(plan_id: str, task: dict[str, Any]) -> dict[str, Any]:
    return {
        'task_id': task.get('id', ''),
        'plan_id': plan_id,
        'parent_task_id': task.get('parent_id', ''),
        'level': task.get('level', 'task'),
        'title': task.get('title', ''),
        'status': task.get('status', 'todo'),
        'owner': task.get('owner', ''),
        'why_it_matters': task.get('why_it_matters', ''),
        'next_action': task.get('next_action', ''),
        'expected_output': task.get('expected_output', ''),
        'validation_gate': task.get('validation_gate', ''),
        'touched_paths': '\n'.join(task.get('touched_paths', [])),
        'blocking_dependency': task.get('blocking_dependency', ''),
        'last_update_text': task.get('last_update', ''),
    }


def task_registry(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        'object_id': fields['task_id'],
        'object_type': 'plan_task',
        'source_skill': 'dcoir-plan-tracker',
        'primary_title': fields['title'],
        'parent_object_id': fields['parent_task_id'],
        'session_id': '',
        'plan_id': fields['plan_id'],
        'status': fields['status'],
        'created_time_text': fields['last_update_text'],
        'updated_time_text': fields['last_update_text'],
        'is_active': fields['status'] not in {'done', 'skipped'},
        'airtable_table_name': TABLES['plan_tasks']['name'],
        'airtable_record_id': '',
        'github_promotion_status': 'candidate',
        'importance': 'medium',
        'tags': f"task\n{fields['level']}",
        'summary': fields['next_action'],
    }


def checkpoint_fields(plan: dict[str, Any], trigger: str, blocker_signature: str, failed_attempt_summary: str, successful_mitigation: str, reusable_lesson_candidate: str, safe_to_flush_now: str, remain_local_for_now: str) -> dict[str, Any]:
    resume = plan.get('resume_state', {})
    checkpoint_id = f"pcp-{short_stamp()}-{plan.get('plan_id', '')}"
    return {
        'plan_checkpoint_id': checkpoint_id,
        'plan_id': plan.get('plan_id', ''),
        'checkpoint_time_text': utc_now(),
        'trigger': trigger,
        'active_task_id': plan.get('active_task_id', ''),
        'blocker_signature': blocker_signature,
        'failed_attempt_summary': failed_attempt_summary,
        'successful_mitigation': successful_mitigation,
        'reusable_lesson_candidate': reusable_lesson_candidate,
        'buffered_state_summary': multiline(resume.get('pending_flush_items', [])),
        'safe_to_flush_now': safe_to_flush_now,
        'remain_local_for_now': remain_local_for_now,
        'next_flush_trigger': resume.get('flush_trigger', ''),
        'best_next_move': plan.get('next_recommended_action', ''),
    }


def checkpoint_registry(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        'object_id': fields['plan_checkpoint_id'],
        'object_type': 'plan_checkpoint',
        'source_skill': 'dcoir-plan-tracker',
        'primary_title': fields['trigger'],
        'parent_object_id': fields['plan_id'],
        'session_id': '',
        'plan_id': fields['plan_id'],
        'status': 'active',
        'created_time_text': fields['checkpoint_time_text'],
        'updated_time_text': fields['checkpoint_time_text'],
        'is_active': True,
        'airtable_table_name': TABLES['plan_checkpoints']['name'],
        'airtable_record_id': '',
        'github_promotion_status': 'candidate',
        'importance': 'high',
        'tags': 'plan\ncheckpoint',
        'summary': fields['best_next_move'],
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
        emit({'base_id': BASE_ID, 'table': TABLES['plans'], 'fields': fields, 'registry': plan_registry(fields)}, args.output_json)
        return 0

    if args.cmd == 'tasks':
        rows = [task_fields(plan.get('plan_id', ''), row) for row in flatten_tasks(plan.get('tasks', []))]
        regs = [task_registry(row) for row in rows]
        emit({'base_id': BASE_ID, 'table': TABLES['plan_tasks'], 'records': rows, 'registry_records': regs}, args.output_json)
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
    emit({'base_id': BASE_ID, 'table': TABLES['plan_checkpoints'], 'fields': fields, 'registry': checkpoint_registry(fields)}, args.output_json)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
