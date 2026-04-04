#!/usr/bin/env python3
"""Ensure or inspect the local plan_state.json file for a plan-tracker plan folder."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from plan_templates import make_empty_plan_state, write_plan_folder


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flatten_tasks(tasks: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for task in tasks:
        rows.append(task)
        rows.extend(flatten_tasks(task.get('children', [])))
    return rows


def print_status(path: Path, state: dict, status: str, notice: str) -> None:
    stat = path.stat()
    rows = flatten_tasks(state.get('tasks', []))
    print(f'local_plan_state_status: {status}')
    print(f'local_plan_state_notice: {notice}')
    print(f'path: {path.resolve()}')
    print(f'filename: {path.name}')
    print(f'size_bytes: {stat.st_size}')
    print(f'modified_time_utc: {datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}')
    print(f'sha256: {sha256_file(path)}')
    print(f'plan_id: {state.get("plan_id", "not recorded")}')
    print(f'active_task_id: {state.get("active_task_id", "")}')
    print(f'task_count: {len(rows)}')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('plan_dir')
    parser.add_argument('--title')
    parser.add_argument('--objective')
    parser.add_argument('--owner', default='assistant')
    args = parser.parse_args()

    plan_dir = Path(args.plan_dir)
    plan_path = plan_dir / 'plan_state.json'

    if plan_path.exists():
        state = json.loads(plan_path.read_text(encoding='utf-8'))
        print_status(plan_path, state, 'existing_local_plan_state_present', 'existing local plan_state.json is present and inspectable')
        return 0

    non_state_files = [p for p in plan_dir.glob('*') if p.name != 'plan_state.json'] if plan_dir.exists() else []
    if non_state_files and (args.title is None or args.objective is None):
        print('local_plan_state_status: missing_expected_local_plan_state')
        print('local_plan_state_notice: no pre-existing local plan_state.json was present for this plan folder, so continuity cannot be treated as file-backed until the local plan state is deliberately repaired or reinitialized')
        print(f'expected_path: {plan_path.resolve()}')
        return 2

    if args.title is None or args.objective is None:
        print('local_plan_state_status: cannot_initialize_without_minimum_plan_metadata')
        print('local_plan_state_notice: no local plan_state.json was present and no title/objective were supplied for initializing a new local plan folder')
        print(f'expected_path: {plan_path.resolve()}')
        return 2

    plan_id = plan_dir.name
    state = make_empty_plan_state(plan_id, args.title, args.objective, owner=args.owner)
    write_plan_folder(plan_dir, state)
    state = json.loads(plan_path.read_text(encoding='utf-8'))
    print_status(plan_path, state, 'initialized_new_local_plan_state', 'no pre-existing local plan_state.json was present, so a new local plan-state file was initialized for this session')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
