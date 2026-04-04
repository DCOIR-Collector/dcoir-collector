#!/usr/bin/env python3
"""Maintain a real local DCOIR session-state JSON file."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATE_PATH = Path('/mnt/data/dcoir_session_tracker/session_state.json')
BUCKETS = [
    'session_only',
    'candidate_log01',
    'candidate_log02',
    'candidate_log03',
    'durable_preference_candidate',
    'new_skill_idea',
    'follow_on_validation',
    'blocked_or_needs_authority',
]
DEFAULT_TARGETS = {
    'candidate_log01': ['project_sources/LOG-01_DCOIR_Todo_Log.txt', 'project_sources/todo/01_Active_Now.txt'],
    'candidate_log02': ['project_sources/LOG-02_DCOIR_Lessons_Learned_Log.txt'],
    'candidate_log03': ['project_sources/LOG-03_DCOIR_Session_Handoff_Brief.txt'],
    'durable_preference_candidate': ['project_sources/LOG-01_DCOIR_Todo_Log.txt', 'project_sources/todo/01_Active_Now.txt'],
    'new_skill_idea': ['project_sources/LOG-01_DCOIR_Todo_Log.txt', 'project_sources/todo/01_Active_Now.txt'],
    'follow_on_validation': ['project_sources/LOG-01_DCOIR_Todo_Log.txt', 'project_sources/todo/01_Active_Now.txt'],
    'blocked_or_needs_authority': ['project_sources/LOG-01_DCOIR_Todo_Log.txt', 'project_sources/todo/01_Active_Now.txt'],
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def default_state(path: Path) -> dict[str, Any]:
    stamp = now_utc()
    return {
        'project': 'AFRICOM_SOC_IR / DCOIR',
        'exported_at_utc': stamp,
        'authority_basis': [],
        'merge_mode': 'merge',
        'imports_merged': ['current_chat'],
        'current_phase': 'not specified',
        'best_next_move': 'not specified',
        'close_out_status': 'not specified',
        'durability_summary': {
            'governed_github': 'not specified',
            'exported_handoff_only': 'not specified',
            'buffered_session_only': 'not specified',
        },
        'open_items': {bucket: [] for bucket in BUCKETS},
        'completed': [],
        'promotion_ready': {'log01': '', 'log02': '', 'log03': ''},
        'staged_governed_updates': [],
        'staged_todo_actions': [],
        'post_push_cleanup': [],
        'starter_prompt': '',
        'closeout_verification': [],
        'provenance_notes': [],
        'local_state_metadata': {
            'schema_version': 4,
            'state_type': 'session_local_working_state',
            'created_at_utc': stamp,
            'updated_at_utc': stamp,
            'state_path': str(path.resolve()),
        },
    }


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_state(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('state file must contain a top-level JSON object')
    data.setdefault('open_items', {})
    for bucket in BUCKETS:
        data['open_items'].setdefault(bucket, [])
    data.setdefault('completed', [])
    data.setdefault('promotion_ready', {'log01': '', 'log02': '', 'log03': ''})
    data.setdefault('staged_governed_updates', [])
    data.setdefault('staged_todo_actions', [])
    data.setdefault('post_push_cleanup', [])
    data.setdefault('local_state_metadata', {})
    data['local_state_metadata'].setdefault('schema_version', 4)
    data['local_state_metadata'].setdefault('state_type', 'session_local_working_state')
    data['local_state_metadata'].setdefault('created_at_utc', now_utc())
    data['local_state_metadata']['state_path'] = str(path.resolve())
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    ensure_parent(path)
    stamp = now_utc()
    state['exported_at_utc'] = stamp
    state.setdefault('local_state_metadata', {})
    state['local_state_metadata']['schema_version'] = 4
    state['local_state_metadata']['updated_at_utc'] = stamp
    state['local_state_metadata']['state_path'] = str(path.resolve())
    path.write_text(json.dumps(state, indent=2, sort_keys=False) + '\n', encoding='utf-8')

def print_presence_status(path: Path, state: dict[str, Any], status: str, notice: str, show_state: bool = False) -> None:
    payload = inspect_payload(path, state)
    print(f'local_state_status: {status}')
    print(f'local_state_notice: {notice}')
    print(f'path: {payload["path"]}')
    print(f'filename: {payload["filename"]}')
    print(f'size_bytes: {payload["size_bytes"]}')
    print(f'modified_time_utc: {payload["modified_time_utc"]}')
    print(f'sha256: {payload["sha256"]}')
    print(f'created_at_utc: {payload["created_at_utc"]}')
    print(f'updated_at_utc: {payload["updated_at_utc"]}')
    print('open_counts:')
    for bucket, count in payload['open_counts'].items():
        print(f'  - {bucket}: {count}')
    print(f'completed_count: {payload["completed_count"]}')
    print(f'staged_governed_update_count: {payload["staged_governed_update_count"]}')
    print(f'staged_todo_action_count: {payload["staged_todo_action_count"]}')
    print(f'post_push_cleanup_count: {payload["post_push_cleanup_count"]}')
    if show_state:
        print('state_json:')
        print(json.dumps(state, indent=2, sort_keys=False))


def emit_write_result(path: Path, state: dict[str, Any], primary_message: str, path_existed_before: bool) -> None:
    print(primary_message)
    if not path_existed_before:
        print_presence_status(
            path,
            state,
            'initialized_new_local_state',
            'no pre-existing local session-state file was present at this step, so a new session-local state file was initialized first',
        )


def remove_item_everywhere(state: dict[str, Any], item_id: str) -> tuple[dict[str, Any] | None, str | None]:
    for bucket in BUCKETS:
        items = state['open_items'].get(bucket, [])
        for idx, item in enumerate(items):
            if item.get('id') == item_id:
                return items.pop(idx), bucket
    for idx, item in enumerate(state.get('completed', [])):
        if item.get('id') == item_id:
            return state['completed'].pop(idx), 'completed'
    return None, None


def find_item(state: dict[str, Any], item_id: str) -> tuple[dict[str, Any] | None, str | None]:
    for bucket in BUCKETS:
        for item in state['open_items'].get(bucket, []):
            if item.get('id') == item_id:
                return item, bucket
    for item in state.get('completed', []):
        if item.get('id') == item_id:
            return item, 'completed'
    return None, None


def normalize_item(item: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = dict(existing or {})
    merged.update(item)
    if 'id' not in merged or not merged['id']:
        raise ValueError('item must include non-empty id')
    if 'title' not in merged or not merged['title']:
        raise ValueError('item must include non-empty title')
    merged.setdefault('status', 'open')
    merged.setdefault('provenance', 'current_chat')
    merged.setdefault('detail', merged.get('why', '') or merged['title'])
    merged.setdefault('why', '')
    merged.setdefault('next_action', '')
    merged.setdefault('related', [])
    merged.setdefault('operator_language', '')
    merged.setdefault('impact_if_missed', '')
    merged.setdefault('desired_outcome', '')
    merged.setdefault('promotion_target', '')
    merged.setdefault('carry_forward_note', '')
    merged.setdefault('buffer_state', 'buffered_session_local')
    merged.setdefault('persistence_status', 'session_only')
    merged.setdefault('flush_trigger', '')
    return merged


def normalize_stage(entry: dict[str, Any]) -> dict[str, Any]:
    entry = dict(entry)
    if not entry.get('title'):
        raise ValueError('staged update entry must include title')
    entry.setdefault('action', 'update')
    entry.setdefault('status', 'staged')
    entry.setdefault('target_paths', [])
    entry.setdefault('source_item_ids', [])
    entry.setdefault('why', '')
    return entry


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_payload(path: Path, state: dict[str, Any]) -> dict[str, Any]:
    stat = path.stat()
    open_counts = {bucket: len(state['open_items'].get(bucket, [])) for bucket in BUCKETS}
    return {
        'path': str(path.resolve()),
        'filename': path.name,
        'size_bytes': stat.st_size,
        'modified_time_utc': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'sha256': sha256_file(path),
        'created_at_utc': state.get('local_state_metadata', {}).get('created_at_utc', 'not recorded'),
        'updated_at_utc': state.get('local_state_metadata', {}).get('updated_at_utc', 'not recorded'),
        'open_counts': open_counts,
        'completed_count': len(state.get('completed', [])),
        'staged_governed_update_count': len(state.get('staged_governed_updates', [])),
        'staged_todo_action_count': len(state.get('staged_todo_actions', [])),
        'post_push_cleanup_count': len(state.get('post_push_cleanup', [])),
    }


def as_paths(value: Any, fallback_bucket: str | None = None) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in value.replace(';', ',').split(',') if part.strip()]
    return list(DEFAULT_TARGETS.get(fallback_bucket or '', []))


def derive_pre_push_review(state: dict[str, Any]) -> dict[str, Any]:
    existing_gov = {json.dumps(entry, sort_keys=True) for entry in state.get('staged_governed_updates', [])}
    existing_todo = {json.dumps(entry, sort_keys=True) for entry in state.get('staged_todo_actions', [])}
    staged_governed = list(state.get('staged_governed_updates', []))
    staged_todo = list(state.get('staged_todo_actions', []))
    cleanup = list(state.get('post_push_cleanup', []))
    safe_flush_now: list[str] = []
    remain_local: list[str] = []
    buffered_items: list[str] = []

    for bucket in BUCKETS:
        for item in state.get('open_items', {}).get(bucket, []):
            item_id = item.get('id', '')
            if item.get('buffer_state') == 'promoted_to_governed' or item.get('persistence_status') == 'governed_written':
                continue
            buffered_items.append(item_id)
            if bucket == 'session_only' and not item.get('promotion_target'):
                remain_local.append(item_id)
                continue
            targets = as_paths(item.get('promotion_target', ''), bucket)
            if not targets:
                remain_local.append(item_id)
                continue
            safe_flush_now.append(item_id)
            if bucket in {'candidate_log02', 'candidate_log03'}:
                entry = normalize_stage({
                    'title': f'promote {item_id} into governed target surfaces',
                    'target_paths': targets,
                    'source_item_ids': [item_id],
                    'action': 'update',
                    'why': item.get('why', '') or 'derived from pre-push review',
                })
                key = json.dumps(entry, sort_keys=True)
                if key not in existing_gov:
                    staged_governed.append(entry)
                    existing_gov.add(key)
            else:
                entry = normalize_stage({
                    'title': f'sync {item_id} into active todo surfaces',
                    'target_paths': targets,
                    'source_item_ids': [item_id],
                    'action': 'add_or_update',
                    'why': item.get('why', '') or 'derived from pre-push review',
                })
                key = json.dumps(entry, sort_keys=True)
                if key not in existing_todo:
                    staged_todo.append(entry)
                    existing_todo.add(key)
            cleanup_note = f'after push: mark {item_id} governed-written and clear staged entries that reference it'
            if cleanup_note not in cleanup:
                cleanup.append(cleanup_note)

    for item in state.get('completed', []):
        item_id = item.get('id', '')
        bucket = item.get('bucket', '')
        if not item_id:
            continue
        targets = as_paths(item.get('promotion_target', ''), bucket or 'candidate_log01')
        if bucket in {'candidate_log01', 'durable_preference_candidate', 'new_skill_idea', 'follow_on_validation', 'blocked_or_needs_authority'} or any('todo' in t.lower() or 'LOG-01' in t for t in targets):
            entry = normalize_stage({
                'title': f'remove or update completed item {item_id} in active todo surfaces',
                'target_paths': ['project_sources/LOG-01_DCOIR_Todo_Log.txt', 'project_sources/todo/01_Active_Now.txt'],
                'source_item_ids': [item_id],
                'action': 'remove_or_update',
                'why': item.get('completion_note', '') or 'completed item should no longer remain as active todo',
            })
            key = json.dumps(entry, sort_keys=True)
            if key not in existing_todo:
                staged_todo.append(entry)
                existing_todo.add(key)
            cleanup_note = f'after push: clear completed staged-todo action for {item_id}'
            if cleanup_note not in cleanup:
                cleanup.append(cleanup_note)

    best_next_move = 'apply the staged governed updates and staged todo actions in the same grouped push, then perform the post-push cleanup sequence'
    return {
        'inspection_expected': True,
        'buffered_items': buffered_items,
        'safe_flush_now': safe_flush_now,
        'remain_local': remain_local,
        'staged_governed_updates': staged_governed,
        'staged_todo_actions': staged_todo,
        'post_push_cleanup': cleanup,
        'best_next_move': best_next_move,
    }


def render_pre_push_review(review: dict[str, Any], inspection: dict[str, Any] | None = None) -> str:
    lines = ['# DCOIR Session Tracker Pre-Push Review', '']
    if inspection:
        lines.extend(['## Local session-state inspection', ''])
        for key in ['path', 'filename', 'size_bytes', 'modified_time_utc', 'sha256', 'created_at_utc', 'updated_at_utc']:
            lines.append(f'- {key}: {inspection.get(key, "")}')
        lines.append('- open_counts:')
        for bucket, count in inspection.get('open_counts', {}).items():
            lines.append(f'  - {bucket}: {count}')
        for key in ['completed_count', 'staged_governed_update_count', 'staged_todo_action_count', 'post_push_cleanup_count']:
            lines.append(f'- {key}: {inspection.get(key, 0)}')
        lines.append('')
    for title, key in [('Buffered items', 'buffered_items'), ('Safe to flush now', 'safe_flush_now'), ('Remain local for now', 'remain_local')]:
        lines.extend([f'## {title}', ''])
        vals = review.get(key, [])
        lines.extend([f'- {x}' for x in vals] or ['- none'])
        lines.append('')
    lines.extend(['## Staged governed updates', ''])
    if review.get('staged_governed_updates'):
        for entry in review['staged_governed_updates']:
            lines.append(f"- {entry.get('title', 'untitled staged update')}")
            lines.append(f"  - action: {entry.get('action', 'update')}")
            if entry.get('why'):
                lines.append(f"  - why: {entry.get('why')}")
            if entry.get('target_paths'):
                lines.append(f"  - target_paths: {', '.join(entry['target_paths'])}")
            if entry.get('source_item_ids'):
                lines.append(f"  - source_item_ids: {', '.join(entry['source_item_ids'])}")
    else:
        lines.append('- none')
    lines.extend(['', '## Staged todo actions', ''])
    if review.get('staged_todo_actions'):
        for entry in review['staged_todo_actions']:
            lines.append(f"- {entry.get('title', 'untitled staged todo action')}")
            lines.append(f"  - action: {entry.get('action', 'add_or_update')}")
            if entry.get('why'):
                lines.append(f"  - why: {entry.get('why')}")
            if entry.get('target_paths'):
                lines.append(f"  - target_paths: {', '.join(entry['target_paths'])}")
            if entry.get('source_item_ids'):
                lines.append(f"  - source_item_ids: {', '.join(entry['source_item_ids'])}")
    else:
        lines.append('- none')
    lines.extend(['', '## Post-push cleanup', ''])
    lines.extend([f'- {x}' for x in review.get('post_push_cleanup', [])] or ['- none'])
    lines.extend(['', '## Best next move', '', review.get('best_next_move', 'not specified'), ''])
    return '\n'.join(lines)


def cmd_init(args: argparse.Namespace) -> int:
    path_existed_before = args.path.exists()
    state = load_state(args.path)
    save_state(args.path, state)
    emit_write_result(args.path, load_state(args.path), f'Initialized {args.path.resolve()}', path_existed_before)
    return 0


def cmd_ensure_state(args: argparse.Namespace) -> int:
    path_existed_before = args.path.exists()
    state = load_state(args.path)
    if not path_existed_before:
        save_state(args.path, state)
        state = load_state(args.path)
        print_presence_status(
            args.path,
            state,
            'initialized_new_local_state',
            'no pre-existing local session-state file was present, so a new session-local state file was initialized for this session',
            show_state=args.show_state,
        )
        return 0
    print_presence_status(
        args.path,
        state,
        'existing_local_state_present',
        'existing local session-state file is present and inspectable',
        show_state=args.show_state,
    )
    return 0


def cmd_upsert(args: argparse.Namespace) -> int:
    path_existed_before = args.path.exists()
    state = load_state(args.path)
    payload = json.loads(args.item_json) if args.item_json else json.loads(Path(args.item_file).read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('item payload must be a JSON object')
    existing, existing_bucket = find_item(state, payload.get('id', ''))
    item = normalize_item(payload, existing)
    bucket = item.get('bucket') or (existing_bucket if existing_bucket in BUCKETS else None)
    if bucket not in BUCKETS:
        raise ValueError('item must include a valid bucket')
    item['bucket'] = bucket
    remove_item_everywhere(state, item['id'])
    state['open_items'][bucket].append(item)
    save_state(args.path, state)
    state = load_state(args.path)
    emit_write_result(args.path, state, f'Captured {item["id"]} into {bucket} and preserved it in the local session-state file', path_existed_before)
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    state = load_state(args.path)
    existing, _bucket = remove_item_everywhere(state, args.id)
    if existing is None:
        raise ValueError(f'item not found: {args.id}')
    existing['status'] = 'done'
    if args.note:
        existing['completion_note'] = args.note
    state['completed'].append(existing)
    save_state(args.path, state)
    print(f'Completed {args.id}')
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    state = load_state(args.path)
    existing, bucket = remove_item_everywhere(state, args.id)
    if existing is None:
        raise ValueError(f'item not found: {args.id}')
    save_state(args.path, state)
    print(f'Removed {args.id} from {bucket}')
    return 0


def cmd_set_summary(args: argparse.Namespace) -> int:
    path_existed_before = args.path.exists()
    state = load_state(args.path)
    if args.current_phase is not None:
        state['current_phase'] = args.current_phase
    if args.best_next_move is not None:
        state['best_next_move'] = args.best_next_move
    if args.close_out_status is not None:
        state['close_out_status'] = args.close_out_status
    if args.governed_github is not None:
        state.setdefault('durability_summary', {})['governed_github'] = args.governed_github
    if args.exported_handoff_only is not None:
        state.setdefault('durability_summary', {})['exported_handoff_only'] = args.exported_handoff_only
    if args.buffered_session_only is not None:
        state.setdefault('durability_summary', {})['buffered_session_only'] = args.buffered_session_only
    if args.unresolved_closeout_gap is not None:
        state.setdefault('durability_summary', {})['unresolved_closeout_gap'] = args.unresolved_closeout_gap
    if args.starter_prompt is not None:
        state['starter_prompt'] = args.starter_prompt
    if args.add_note:
        state.setdefault('provenance_notes', []).extend(args.add_note)
    if args.add_verification:
        state.setdefault('closeout_verification', []).extend(args.add_verification)
    save_state(args.path, state)
    state = load_state(args.path)
    emit_write_result(args.path, state, f'Updated summary fields in {args.path.resolve()}', path_existed_before)
    return 0


def cmd_stage_governed_update(args: argparse.Namespace) -> int:
    path_existed_before = args.path.exists()
    state = load_state(args.path)
    payload = json.loads(args.entry_json) if args.entry_json else json.loads(Path(args.entry_file).read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('entry payload must be a JSON object')
    state.setdefault('staged_governed_updates', []).append(normalize_stage(payload))
    save_state(args.path, state)
    state = load_state(args.path)
    emit_write_result(args.path, state, 'Staged governed update entry', path_existed_before)
    return 0


def cmd_stage_todo_action(args: argparse.Namespace) -> int:
    path_existed_before = args.path.exists()
    state = load_state(args.path)
    payload = json.loads(args.entry_json) if args.entry_json else json.loads(Path(args.entry_file).read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('todo action payload must be a JSON object')
    state.setdefault('staged_todo_actions', []).append(normalize_stage(payload))
    save_state(args.path, state)
    state = load_state(args.path)
    emit_write_result(args.path, state, 'Staged todo action entry', path_existed_before)
    return 0


def cmd_clear_staged_governed_updates(args: argparse.Namespace) -> int:
    state = load_state(args.path)
    state['staged_governed_updates'] = []
    save_state(args.path, state)
    print('Cleared staged governed updates')
    return 0


def cmd_clear_staged_todo_actions(args: argparse.Namespace) -> int:
    state = load_state(args.path)
    state['staged_todo_actions'] = []
    save_state(args.path, state)
    print('Cleared staged todo actions')
    return 0


def cmd_mark_governed_written(args: argparse.Namespace) -> int:
    state = load_state(args.path)
    item, bucket = find_item(state, args.id)
    if item is None:
        raise ValueError(f'item not found: {args.id}')
    item['buffer_state'] = 'promoted_to_governed'
    item['persistence_status'] = 'governed_written'
    if args.note:
        item['governed_write_note'] = args.note
    save_state(args.path, state)
    print(f'Marked {args.id} governed_written in {bucket}')
    return 0


def cmd_derive_pre_push_review(args: argparse.Namespace) -> int:
    path_existed_before = args.path.exists()
    state = load_state(args.path)
    inspection = inspect_payload(args.path, state) if args.path.exists() else None
    review = derive_pre_push_review(state)
    if args.update_state:
        state['staged_governed_updates'] = review['staged_governed_updates']
        state['staged_todo_actions'] = review['staged_todo_actions']
        state['post_push_cleanup'] = review['post_push_cleanup']
        state['best_next_move'] = review['best_next_move']
        save_state(args.path, state)
        if args.path.exists():
            state = load_state(args.path)
            inspection = inspect_payload(args.path, state)
    if args.output_json:
        Path(args.output_json).write_text(json.dumps({'inspection': inspection, 'review': review}, indent=2) + '\n', encoding='utf-8')
    if args.output_md:
        Path(args.output_md).write_text(render_pre_push_review(review, inspection), encoding='utf-8')
    print(render_pre_push_review(review, inspection))
    if args.update_state and not path_existed_before and args.path.exists():
        print_presence_status(
            args.path,
            state,
            'initialized_new_local_state',
            'no pre-existing local session-state file was present when deriving the pre-push review, so a new session-local state file was initialized first',
        )
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    if not args.path.exists():
        raise FileNotFoundError(f'state file does not exist: {args.path}')
    state = load_state(args.path)
    payload = inspect_payload(args.path, state)
    print(f'path: {payload["path"]}')
    print(f'filename: {payload["filename"]}')
    print(f'size_bytes: {payload["size_bytes"]}')
    print(f'modified_time_utc: {payload["modified_time_utc"]}')
    print(f'sha256: {payload["sha256"]}')
    print(f'created_at_utc: {payload["created_at_utc"]}')
    print(f'updated_at_utc: {payload["updated_at_utc"]}')
    print('open_counts:')
    for bucket, count in payload['open_counts'].items():
        print(f'  - {bucket}: {count}')
    print(f'completed_count: {payload["completed_count"]}')
    print(f'staged_governed_update_count: {payload["staged_governed_update_count"]}')
    print(f'staged_todo_action_count: {payload["staged_todo_action_count"]}')
    print(f'post_push_cleanup_count: {payload["post_push_cleanup_count"]}')
    if args.show_state:
        print('state_json:')
        print(json.dumps(state, indent=2, sort_keys=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Maintain a real local DCOIR session-state JSON file.')
    sub = parser.add_subparsers(dest='cmd', required=True)

    init_p = sub.add_parser('init')
    init_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    init_p.set_defaults(func=cmd_init)

    upsert_p = sub.add_parser('upsert')
    upsert_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    upsert_group = upsert_p.add_mutually_exclusive_group(required=True)
    upsert_group.add_argument('--item-json')
    upsert_group.add_argument('--item-file')
    upsert_p.set_defaults(func=cmd_upsert)

    complete_p = sub.add_parser('complete')
    complete_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    complete_p.add_argument('--id', required=True)
    complete_p.add_argument('--note')
    complete_p.set_defaults(func=cmd_complete)

    remove_p = sub.add_parser('remove')
    remove_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    remove_p.add_argument('--id', required=True)
    remove_p.set_defaults(func=cmd_remove)

    stage_p = sub.add_parser('stage-governed-update')
    stage_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    group = stage_p.add_mutually_exclusive_group(required=True)
    group.add_argument('--entry-json')
    group.add_argument('--entry-file')
    stage_p.set_defaults(func=cmd_stage_governed_update)

    stage_todo_p = sub.add_parser('stage-todo-action')
    stage_todo_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    group2 = stage_todo_p.add_mutually_exclusive_group(required=True)
    group2.add_argument('--entry-json')
    group2.add_argument('--entry-file')
    stage_todo_p.set_defaults(func=cmd_stage_todo_action)

    clear_p = sub.add_parser('clear-staged-governed-updates')
    clear_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    clear_p.set_defaults(func=cmd_clear_staged_governed_updates)

    clear_todo_p = sub.add_parser('clear-staged-todo-actions')
    clear_todo_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    clear_todo_p.set_defaults(func=cmd_clear_staged_todo_actions)

    governed_p = sub.add_parser('mark-governed-written')
    governed_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    governed_p.add_argument('--id', required=True)
    governed_p.add_argument('--note')
    governed_p.set_defaults(func=cmd_mark_governed_written)

    summary_p = sub.add_parser('set-summary')
    summary_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    summary_p.add_argument('--current-phase')
    summary_p.add_argument('--best-next-move')
    summary_p.add_argument('--close-out-status')
    summary_p.add_argument('--governed-github')
    summary_p.add_argument('--exported-handoff-only')
    summary_p.add_argument('--buffered-session-only')
    summary_p.add_argument('--unresolved-closeout-gap')
    summary_p.add_argument('--starter-prompt')
    summary_p.add_argument('--add-note', action='append')
    summary_p.add_argument('--add-verification', action='append')
    summary_p.set_defaults(func=cmd_set_summary)

    review_p = sub.add_parser('derive-pre-push-review')
    review_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    review_p.add_argument('--output-md')
    review_p.add_argument('--output-json')
    review_p.add_argument('--update-state', action='store_true')
    review_p.set_defaults(func=cmd_derive_pre_push_review)

    ensure_p = sub.add_parser('ensure-state')
    ensure_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    ensure_p.add_argument('--show-state', action='store_true')
    ensure_p.set_defaults(func=cmd_ensure_state)

    inspect_p = sub.add_parser('inspect')
    inspect_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    inspect_p.add_argument('--show-state', action='store_true')
    inspect_p.set_defaults(func=cmd_inspect)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
