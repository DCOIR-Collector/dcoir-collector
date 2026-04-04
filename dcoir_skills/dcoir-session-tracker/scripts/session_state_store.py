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
        'post_push_cleanup': [],
        'starter_prompt': '',
        'closeout_verification': [],
        'provenance_notes': [],
        'local_state_metadata': {
            'schema_version': 3,
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
    data.setdefault('post_push_cleanup', [])
    data.setdefault('local_state_metadata', {})
    data['local_state_metadata'].setdefault('schema_version', 3)
    data['local_state_metadata'].setdefault('state_type', 'session_local_working_state')
    data['local_state_metadata'].setdefault('created_at_utc', now_utc())
    data['local_state_metadata']['state_path'] = str(path.resolve())
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    ensure_parent(path)
    stamp = now_utc()
    state['exported_at_utc'] = stamp
    state.setdefault('local_state_metadata', {})
    state['local_state_metadata']['schema_version'] = 3
    state['local_state_metadata']['updated_at_utc'] = stamp
    state['local_state_metadata']['state_path'] = str(path.resolve())
    path.write_text(json.dumps(state, indent=2, sort_keys=False) + '\n', encoding='utf-8')


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
        'post_push_cleanup_count': len(state.get('post_push_cleanup', [])),
    }


def cmd_init(args: argparse.Namespace) -> int:
    state = load_state(args.path)
    save_state(args.path, state)
    print(f'Initialized {args.path.resolve()}')
    return 0


def cmd_upsert(args: argparse.Namespace) -> int:
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
    print(f'Upserted {item["id"]} into {bucket}')
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
    print(f'Updated summary fields in {args.path.resolve()}')
    return 0


def cmd_stage_governed_update(args: argparse.Namespace) -> int:
    state = load_state(args.path)
    payload = json.loads(args.entry_json) if args.entry_json else json.loads(Path(args.entry_file).read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('entry payload must be a JSON object')
    state.setdefault('staged_governed_updates', []).append(normalize_stage(payload))
    save_state(args.path, state)
    print('Staged governed update entry')
    return 0


def cmd_clear_staged_governed_updates(args: argparse.Namespace) -> int:
    state = load_state(args.path)
    state['staged_governed_updates'] = []
    save_state(args.path, state)
    print('Cleared staged governed updates')
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

    clear_p = sub.add_parser('clear-staged-governed-updates')
    clear_p.add_argument('--path', type=Path, default=DEFAULT_STATE_PATH)
    clear_p.set_defaults(func=cmd_clear_staged_governed_updates)

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
