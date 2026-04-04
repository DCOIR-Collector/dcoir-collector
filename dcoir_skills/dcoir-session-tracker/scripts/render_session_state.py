#!/usr/bin/env python3
"""Render a DCOIR session-state markdown artifact from a JSON state file."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ORDER = [
    'session_only',
    'candidate_log01',
    'candidate_log02',
    'candidate_log03',
    'durable_preference_candidate',
    'new_skill_idea',
    'follow_on_validation',
    'blocked_or_needs_authority',
]


def load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('state file must contain a top-level JSON object')
    return data


def fmt_item(item: dict[str, Any]) -> str:
    lines = [f"- [{item.get('id', 'UNSPECIFIED')}] {item.get('title', 'untitled item')}"]
    for key in ['status', 'provenance', 'bucket', 'operator_language', 'detail', 'why', 'impact_if_missed', 'desired_outcome', 'next_action', 'promotion_target', 'persistence_status', 'buffer_state', 'flush_trigger', 'carry_forward_note']:
        value = item.get(key, '')
        if value:
            lines.append(f'  - {key}: {value}')
    related = item.get('related', [])
    if related:
        lines.append(f"  - related: {', '.join(str(x) for x in related)}")
    return '\n'.join(lines)


def section_lines(items: list[dict[str, Any]]) -> list[str]:
    return [fmt_item(item) for item in items] if items else ['- none']


def fmt_stage(entry: dict[str, Any]) -> list[str]:
    lines = [f"- {entry.get('title', 'untitled entry')}"]
    for key in ['action', 'status', 'why']:
        if entry.get(key):
            lines.append(f"  - {key}: {entry.get(key)}")
    if entry.get('target_paths'):
        lines.append(f"  - target_paths: {', '.join(entry['target_paths'])}")
    if entry.get('source_item_ids'):
        lines.append(f"  - source_item_ids: {', '.join(entry['source_item_ids'])}")
    return lines


def build_markdown(state: dict[str, Any]) -> str:
    exported_at = state.get('exported_at_utc') or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    authority_basis = state.get('authority_basis', [])
    imports_merged = state.get('imports_merged', [])
    durability_summary = state.get('durability_summary', {})
    schema_version = state.get('local_state_metadata', {}).get('schema_version', 4)
    lines = ['---', 'artifact_type: dcoir-session-state', f"schema_version: {schema_version}", f"project: {state.get('project', 'AFRICOM_SOC_IR / DCOIR')}", f'exported_at_utc: {exported_at}', 'authority_basis:']
    lines.extend([f'  - {item}' for item in authority_basis] or ['  - none-recorded'])
    lines.append(f"merge_mode: {state.get('merge_mode', 'merge')}")
    lines.append('imports_merged:')
    lines.extend([f'  - {item}' for item in imports_merged] or ['  - none'])
    lines.extend(['---', '', '# DCOIR Session State', '', '## Current phase', state.get('current_phase', 'not specified'), '', '## Best next move', state.get('best_next_move', 'not specified'), '', '## Close-out status', state.get('close_out_status', 'not specified'), '', '## Durability summary'])
    lines.append(f"- governed_github: {durability_summary.get('governed_github', 'not specified')}")
    lines.append(f"- exported_handoff_only: {durability_summary.get('exported_handoff_only', 'not specified')}")
    lines.append(f"- buffered_session_only: {durability_summary.get('buffered_session_only', 'not specified')}")
    if durability_summary.get('unresolved_closeout_gap'):
        lines.append(f"- unresolved_closeout_gap: {durability_summary.get('unresolved_closeout_gap')}")
    lines.extend(['', '## Open items'])
    for key in ORDER:
        lines.append(f'### {key}')
        lines.extend(section_lines(state.get('open_items', {}).get(key, [])))
        lines.append('')
    lines.append('## Completed or resolved this session')
    lines.extend(section_lines(state.get('completed', [])))
    lines.extend(['', '## Promotion-ready notes'])
    for key in ['log01', 'log02', 'log03']:
        lines.append(f'### {key.upper()} candidate text')
        lines.append(state.get('promotion_ready', {}).get(key, '') or 'none')
        lines.append('')
    lines.append('## Staged governed updates')
    staged = state.get('staged_governed_updates', [])
    if staged:
        for entry in staged:
            lines.extend(fmt_stage(entry))
    else:
        lines.append('- none')
    lines.extend(['', '## Staged todo actions'])
    staged_todo = state.get('staged_todo_actions', [])
    if staged_todo:
        for entry in staged_todo:
            lines.extend(fmt_stage(entry))
    else:
        lines.append('- none')
    lines.extend(['', '## Post-push cleanup'])
    cleanup = state.get('post_push_cleanup', [])
    lines.extend([f'- {item}' for item in cleanup] or ['- none'])
    lines.extend(['', '## Starter prompt for next session', state.get('starter_prompt', '') or 'none', '', '## Close-out verification notes'])
    lines.extend([f'- {note}' for note in state.get('closeout_verification', [])] or ['- none'])
    lines.extend(['', '## Provenance notes'])
    lines.extend([f'- {note}' for note in state.get('provenance_notes', [])] or ['- none'])
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print('Usage: python render_session_state.py state.json output.md')
        return 1
    state = load_state(Path(sys.argv[1]).resolve())
    output_path = Path(sys.argv[2]).resolve()
    output_path.write_text(build_markdown(state), encoding='utf-8')
    print(f'Wrote {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
