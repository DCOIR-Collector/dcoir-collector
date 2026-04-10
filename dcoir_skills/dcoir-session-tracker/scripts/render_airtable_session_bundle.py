#!/usr/bin/env python3
"""Render Airtable-ready payloads from dcoir-session-tracker local JSON state."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATE_PATH = Path('/mnt/data/dcoir_session_tracker/session_state.json')
BASE_ID = 'appM4KSwnVf3G3OTK'
TABLES = {
    'session_checkpoints': {'id': 'tblTe75HKZOJaPDGn', 'name': 'Session Checkpoints'},
    'idea_inbox': {'id': 'tblWwBxwrjZF6JR3r', 'name': 'Idea Inbox'},
    'tracking_registry': {'id': 'tblohiMxxVbDUnN77', 'name': 'Tracking Registry'},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def short_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')


def load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('state file must contain a top-level JSON object')
    return data


def state_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_items(items: list[dict[str, Any]]) -> str:
    return '\n'.join(f"- {item.get('title', '')}: {item.get('next_action', '')}".rstrip(': ') for item in items if item.get('title'))


def summarize_open_threads(state: dict[str, Any]) -> str:
    lines: list[str] = []
    for bucket, items in state.get('open_items', {}).items():
        if not items:
            continue
        lines.append(f'[{bucket}]')
        lines.extend(f"- {item.get('title', '')}" for item in items if item.get('title'))
    return '\n'.join(lines) or 'none recorded'


def summarize_ideas(state: dict[str, Any]) -> str:
    ideas = state.get('open_items', {}).get('new_skill_idea', [])
    if not ideas:
        return 'none recorded'
    return '\n'.join(f"- {item.get('title', '')}" for item in ideas if item.get('title'))


def summarize_candidates(state: dict[str, Any]) -> str:
    rows = []
    for item in state.get('staged_governed_updates', []):
        title = item.get('title', '').strip()
        if title:
            rows.append(f'- {title}')
    for key, text in (state.get('promotion_ready') or {}).items():
        if text:
            rows.append(f'- {key}: {text}')
    return '\n'.join(rows) or 'none recorded'


def summarize_constraints(state: dict[str, Any]) -> str:
    notes = state.get('provenance_notes', [])
    return '\n'.join(f'- {note}' for note in notes) or 'none recorded'


def build_checkpoint_fields(state: dict[str, Any], path: Path, session_id: str, trigger: str, checkpoint_status: str, github_status: str) -> dict[str, Any]:
    digest = state_hash(path)
    checkpoint_id = f"scp-{short_stamp()}-{digest[:6]}"
    return {
        'checkpoint_id': checkpoint_id,
        'session_id': session_id,
        'checkpoint_time_text': utc_now(),
        'trigger': trigger,
        'state_summary': state.get('current_phase', 'not specified'),
        'current_focus': state.get('best_next_move', 'not specified'),
        'open_threads': summarize_open_threads(state),
        'captured_ideas_summary': summarize_ideas(state),
        'decisions_constraints': summarize_constraints(state),
        'buffered_promotion_candidates': summarize_candidates(state),
        'next_recommended_move': state.get('best_next_move', 'not specified'),
        'github_promotion_status': github_status,
        'local_state_hash': digest,
        'resume_prompt': state.get('starter_prompt', ''),
        'checkpoint_status': checkpoint_status,
    }


def build_checkpoint_registry(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        'object_id': fields['checkpoint_id'],
        'object_type': 'session_checkpoint',
        'source_skill': 'dcoir-session-tracker',
        'primary_title': fields['trigger'],
        'parent_object_id': '',
        'session_id': fields['session_id'],
        'plan_id': '',
        'status': fields['checkpoint_status'],
        'created_time_text': fields['checkpoint_time_text'],
        'updated_time_text': fields['checkpoint_time_text'],
        'is_active': fields['checkpoint_status'] == 'active',
        'airtable_table_name': TABLES['session_checkpoints']['name'],
        'airtable_record_id': '',
        'github_promotion_status': fields['github_promotion_status'],
        'importance': 'medium',
        'tags': 'session\ncheckpoint',
        'summary': fields['state_summary'],
    }


def find_item(state: dict[str, Any], item_id: str) -> dict[str, Any] | None:
    for items in state.get('open_items', {}).values():
        for item in items:
            if item.get('id') == item_id:
                return item
    for item in state.get('completed', []):
        if item.get('id') == item_id:
            return item
    return None


def build_idea_fields(state: dict[str, Any], item: dict[str, Any], session_id: str, source_checkpoint_id: str) -> dict[str, Any]:
    return {
        'idea_id': item.get('id', ''),
        'session_id': session_id,
        'captured_time_text': utc_now(),
        'idea_title': item.get('title', ''),
        'idea_detail': item.get('detail', '') or item.get('title', ''),
        'why_it_matters': item.get('why', '') or item.get('impact_if_missed', ''),
        'related_area': infer_related_area(item),
        'suggested_promotion_target': item.get('promotion_target', ''),
        'status': infer_idea_status(item),
        'notes': item.get('carry_forward_note', '') or item.get('desired_outcome', ''),
        'promoted_to_github': item.get('persistence_status') == 'governed_written',
        'source_checkpoint_id': source_checkpoint_id,
    }


def build_idea_registry(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        'object_id': fields['idea_id'],
        'object_type': 'idea',
        'source_skill': 'dcoir-session-tracker',
        'primary_title': fields['idea_title'],
        'parent_object_id': fields.get('source_checkpoint_id', ''),
        'session_id': fields['session_id'],
        'plan_id': '',
        'status': fields['status'],
        'created_time_text': fields['captured_time_text'],
        'updated_time_text': fields['captured_time_text'],
        'is_active': fields['status'] not in {'done', 'dropped'},
        'airtable_table_name': TABLES['idea_inbox']['name'],
        'airtable_record_id': '',
        'github_promotion_status': 'promoted' if fields['promoted_to_github'] else 'candidate',
        'importance': 'high',
        'tags': 'idea\ntracker',
        'summary': fields['idea_detail'],
    }


def infer_related_area(item: dict[str, Any]) -> str:
    text = ' '.join([item.get('title', ''), item.get('detail', ''), ' '.join(item.get('related', []))]).lower()
    if 'github' in text:
        return 'GitHub'
    if 'skill' in text:
        return 'Skills'
    if 'gemini' in text:
        return 'Gemini'
    if 'drive' in text:
        return 'Drive'
    if 'validation' in text:
        return 'Validation'
    if 'collector' in text:
        return 'Collector'
    if 'prompt' in text:
        return 'Prompt Pack'
    return 'Other'


def infer_idea_status(item: dict[str, Any]) -> str:
    status = item.get('status', 'open')
    if status == 'done':
        return 'done'
    if item.get('persistence_status') == 'governed_written':
        return 'done'
    if item.get('buffer_state') == 'exported_in_handoff':
        return 'under_review'
    return 'new'


def emit(payload: dict[str, Any], output_json: str | None) -> None:
    text = json.dumps(payload, indent=2)
    if output_json:
        Path(output_json).write_text(text + '\n', encoding='utf-8')
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description='Render Airtable-ready payloads from dcoir-session-tracker local JSON state.')
    sub = parser.add_subparsers(dest='cmd', required=True)

    cp = sub.add_parser('checkpoint')
    cp.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    cp.add_argument('--session-id', required=True)
    cp.add_argument('--trigger', required=True)
    cp.add_argument('--checkpoint-status', default='active')
    cp.add_argument('--github-promotion-status', default='candidate')
    cp.add_argument('--output-json')

    idea = sub.add_parser('idea')
    idea.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    idea.add_argument('--session-id', required=True)
    idea.add_argument('--item-id', required=True)
    idea.add_argument('--source-checkpoint-id', required=True)
    idea.add_argument('--output-json')

    args = parser.parse_args()
    state = load_state(args.path)

    if args.cmd == 'checkpoint':
        fields = build_checkpoint_fields(state, args.path, args.session_id, args.trigger, args.checkpoint_status, args.github_promotion_status)
        emit({'base_id': BASE_ID, 'table': TABLES['session_checkpoints'], 'fields': fields, 'registry': build_checkpoint_registry(fields)}, args.output_json)
        return 0

    item = find_item(state, args.item_id)
    if item is None:
        raise SystemExit(f'item not found: {args.item_id}')
    fields = build_idea_fields(state, item, args.session_id, args.source_checkpoint_id)
    emit({'base_id': BASE_ID, 'table': TABLES['idea_inbox'], 'fields': fields, 'registry': build_idea_registry(fields)}, args.output_json)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
