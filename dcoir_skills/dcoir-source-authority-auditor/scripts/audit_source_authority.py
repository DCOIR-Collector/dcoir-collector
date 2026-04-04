#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence

CONTROL_FILE_CANDIDATES = {
    "manifest": [
        "project_sources/CP-01_DCOIR_Version_Manifest.txt",
        "CP-01_DCOIR_Version_Manifest.txt",
        "project_sources/DCOIR_Version_Manifest.txt",
        "DCOIR_Version_Manifest.txt",
    ],
    "change_log": [
        "project_sources/CP-02_DCOIR_Change_Log.txt",
        "CP-02_DCOIR_Change_Log.txt",
        "project_sources/DCOIR_Change_Log.txt",
        "DCOIR_Change_Log.txt",
    ],
}

ACTIVE_SURFACE_PATHS = {
    "manifest": "project_sources/CP-01_DCOIR_Version_Manifest.txt",
    "change_log": "project_sources/CP-02_DCOIR_Change_Log.txt",
    "session_handoff": "project_sources/LOG-03_DCOIR_Session_Handoff_Brief.txt",
    "session_resume": "project_sources/LOG-05_DCOIR_Session_Resume_Anchor_2026-04-03.txt",
    "todo_log": "project_sources/LOG-01_DCOIR_Todo_Log.txt",
    "todo_index": "project_sources/LOG-01_DCOIR_Todo_Index.txt",
    "active_now": "project_sources/todo/01_Active_Now.txt",
}

MANIFEST_SECTIONS = {
    "CURRENT GOVERNED GITHUB READABLE SOURCES": "governed_github_readable_sources",
    "CURRENT GOVERNED KNOWLEDGE SOURCES IN GITHUB": "governed_knowledge_sources",
    "CURRENT GOVERNED SETTINGS MIRRORS IN GITHUB": "governed_settings_mirrors",
    "CURRENT SUPPORTING ASSETS IN GITHUB": "supporting_assets",
}

STATE_ID_RE = re.compile(r"^Current state id\s*:?\s*(.+?)\s*$", re.IGNORECASE)
CP01_VERSION_RE = re.compile(r"^DCOIR Version Manifest\s+(\S+)\s*$", re.IGNORECASE)
CP02_VERSION_RE = re.compile(r"^Version:\s*(\S+)\s*$", re.IGNORECASE)


def resolve_control_file(source_dir: Path, candidates: Sequence[str]) -> Optional[Path]:
    for candidate in candidates:
        path = source_dir / candidate
        if path.exists():
            return path
    return None


def looks_like_path(value: str) -> bool:
    normalized = value.strip()
    return '/' in normalized or normalized.endswith(('.md', '.txt', '.yaml', '.yml', '.ps1', '.json'))


def parse_current_prose_manifest(text: str) -> Dict[str, List[str]]:
    parsed = {value: [] for value in MANIFEST_SECTIONS.values()}
    heading = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if not line.startswith('- ') and not line.startswith('Version:') and line.endswith(':') is False and line in {
            'Current control plane', 'Current repo guide', 'Current collector files', 'Current task-memory bank', 'Current governed helper-skill source', 'Current next work item'
        }:
            heading = line
            continue
        if line.startswith('- '):
            payload = line[2:].strip()
            value = payload.split(':', 1)[1].strip() if ':' in payload else payload
            if not looks_like_path(value):
                continue
            if heading in {'Current control plane', 'Current repo guide', 'Current collector files'}:
                parsed['governed_github_readable_sources'].append(value)
            elif heading == 'Current task-memory bank':
                if value.startswith('knowledge/'):
                    parsed['governed_knowledge_sources'].append(value)
                else:
                    parsed['governed_github_readable_sources'].append(value)
    return parsed


def parse_manifest(text: str) -> Dict[str, List[str]]:
    parsed = {value: [] for value in MANIFEST_SECTIONS.values()}
    current_section: Optional[str] = None
    for raw in text.splitlines():
        line = raw.strip()
        if line in MANIFEST_SECTIONS:
            current_section = MANIFEST_SECTIONS[line]
            continue
        if current_section and line.isupper() and not line.startswith('-'):
            current_section = None
            continue
        if current_section and line.startswith('- '):
            payload = line[2:].strip()
            if ':' in payload:
                _, value = payload.split(':', 1)
                parsed[current_section].append(value.strip())
            else:
                parsed[current_section].append(payload)
    if any(parsed.values()):
        return parsed
    return parse_current_prose_manifest(text)


def build_authority_sets(parsed: Dict[str, List[str]]) -> Dict[str, set[str]]:
    explicit = set()
    supporting = set(parsed['supporting_assets'])
    patterns = set()
    for section in (
        'governed_github_readable_sources',
        'governed_knowledge_sources',
        'governed_settings_mirrors',
    ):
        for item in parsed[section]:
            if '*' in item:
                patterns.add(item)
            else:
                explicit.add(item)
                explicit.add(Path(item).name)
    for item in supporting:
        explicit.add(item)
        explicit.add(Path(item).name)
    return {
        'explicit': explicit,
        'supporting': set(supporting),
        'patterns': patterns,
    }


def pattern_matches(requested_item: str, patterns: set[str]) -> bool:
    normalized = requested_item.strip()
    basename = Path(normalized).name
    if 'knowledge/*.md' in patterns:
        if normalized.startswith('knowledge/') and normalized.endswith('.md'):
            return True
        if basename.endswith('.md') and ('knowledge/' in normalized or normalized == basename):
            return True
    return False


def request_is_current(requested_item: str, authority: Dict[str, set[str]]) -> bool:
    normalized = requested_item.strip()
    basename = Path(normalized).name
    return (
        normalized in authority['explicit']
        or basename in authority['explicit']
        or pattern_matches(normalized, authority['patterns'])
    )


def verify_workspace_state(source_dir: Path, parsed: Dict[str, List[str]]) -> List[str]:
    missing: List[str] = []
    for section in (
        'governed_github_readable_sources',
        'governed_settings_mirrors',
        'supporting_assets',
    ):
        for item in parsed[section]:
            if '*' in item:
                continue
            if not (source_dir / item).exists():
                missing.append(item)
    if 'knowledge/*.md' in parsed['governed_knowledge_sources']:
        knowledge_dir = source_dir / 'knowledge'
        if not knowledge_dir.exists() or not any(knowledge_dir.glob('*.md')):
            missing.append('knowledge/*.md')
    return missing


def parse_current_state_id(text: str) -> Optional[str]:
    lines = text.splitlines()
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        match = STATE_ID_RE.match(stripped)
        if match:
            value = match.group(1).strip()
            if value:
                return value
        if stripped.lower() == 'current state id' and idx + 1 < len(lines):
            nxt = lines[idx + 1].strip()
            if nxt.startswith('- '):
                return nxt[2:].strip()
    return None


def parse_version(text: str, role: str) -> Optional[str]:
    regex = CP01_VERSION_RE if role == 'manifest' else CP02_VERSION_RE if role == 'change_log' else None
    if regex is None:
        return None
    for raw in text.splitlines():
        match = regex.match(raw.strip())
        if match:
            return match.group(1).strip()
    return None


def check_active_surface_alignment(source_dir: Path) -> dict:
    present = {}
    missing_surfaces = []
    state_ids = {}
    missing_state_id = []
    versions = {}

    for role, rel_path in ACTIVE_SURFACE_PATHS.items():
        path = source_dir / rel_path
        if not path.exists():
            missing_surfaces.append(rel_path)
            continue
        text = path.read_text(encoding='utf-8')
        present[role] = rel_path
        state_id = parse_current_state_id(text)
        if state_id is None:
            missing_state_id.append(rel_path)
        else:
            state_ids[rel_path] = state_id
        version = parse_version(text, role)
        if version:
            versions[rel_path] = version

    if missing_state_id:
        return {
            'outcome': 'hard_stop_conflict',
            'reason': 'stamped active surface missing required current_state_id',
            'affected_surfaces': missing_state_id,
            'present_surfaces': list(present.values()),
            'best_next_move': 'add the shared current_state_id to every stamped active surface before proceeding',
        }

    unique_state_ids = sorted(set(state_ids.values()))
    if len(unique_state_ids) > 1:
        grouped = {}
        for path, state_id in state_ids.items():
            grouped.setdefault(state_id, []).append(path)
        return {
            'outcome': 'hard_stop_conflict',
            'reason': 'current_state_id mismatch across active enforcement surfaces',
            'state_id_groups': grouped,
            'present_surfaces': list(present.values()),
            'best_next_move': 'refresh the smallest grouped active-surface set needed to restore one shared current_state_id',
        }

    if len(set(versions.values())) > 1:
        return {
            'outcome': 'hard_stop_conflict',
            'reason': 'CP-01 and CP-02 version mismatch',
            'version_map': versions,
            'present_surfaces': list(present.values()),
            'best_next_move': 'realign the control-plane version pair before trusting the active continuity surface set',
        }

    if missing_surfaces:
        return {
            'outcome': 'proceed_bounded',
            'reason': 'active enforcement surface set is partial but no contradiction is proven in the available surfaces',
            'missing_surfaces': missing_surfaces,
            'present_surfaces': list(present.values()),
            'shared_state_id': unique_state_ids[0] if unique_state_ids else None,
            'best_next_move': 'continue only with bounded claims and call out the missing active surfaces explicitly',
        }

    return {
        'outcome': 'clear_to_proceed',
        'reason': 'active enforcement surfaces share one current_state_id and the control-plane version pair aligns',
        'present_surfaces': list(present.values()),
        'shared_state_id': unique_state_ids[0] if unique_state_ids else None,
        'version_map': versions,
        'best_next_move': 'proceed with the narrower source-authority review using the aligned active continuity surface set',
    }


def audit(source_dir: Path, requested: List[str]) -> dict:
    manifest = resolve_control_file(source_dir, CONTROL_FILE_CANDIDATES['manifest'])
    change = resolve_control_file(source_dir, CONTROL_FILE_CANDIDATES['change_log'])
    if not manifest or not change:
        return {
            'outcome': 'hard_stop_conflict',
            'reason': 'missing control-plane file',
            'authoritative_basis_used': {
                'manifest': str(manifest) if manifest else None,
                'change_log': str(change) if change else None,
            },
            'best_next_move': 'restore the current manifest and change log before proceeding',
        }

    parsed = parse_manifest(manifest.read_text(encoding='utf-8'))
    authority = build_authority_sets(parsed)
    missing = verify_workspace_state(source_dir, parsed)
    if missing:
        return {
            'outcome': 'hard_stop_conflict',
            'reason': 'current manifest-listed source or asset missing from workspace',
            'missing_items': sorted(missing),
            'authoritative_basis_used': {
                'manifest': str(manifest.relative_to(source_dir)),
                'change_log': str(change.relative_to(source_dir)),
                'manifest_sections': list(MANIFEST_SECTIONS.keys()),
            },
            'best_next_move': 'restore the missing current file set before proceeding',
        }

    normalized_requested = [item.strip() for item in requested if item and item.strip()]
    non_current = [
        item for item in normalized_requested
        if not item.startswith('dcoir-')
        and not request_is_current(item, authority)
    ]
    if non_current:
        return {
            'outcome': 'hard_stop_conflict',
            'reason': 'requested non-current file as authority',
            'non_current_requests': sorted(non_current),
            'authoritative_basis_used': {
                'manifest': str(manifest.relative_to(source_dir)),
                'change_log': str(change.relative_to(source_dir)),
                'current_governed_sections': parsed,
            },
            'best_next_move': 'use the current manifest-listed GitHub source for that role or explicitly ask for historical reference use',
        }

    alignment = check_active_surface_alignment(source_dir)
    if alignment['outcome'] == 'hard_stop_conflict':
        return {
            'outcome': alignment['outcome'],
            'reason': alignment['reason'],
            'authoritative_basis_used': {
                'manifest': str(manifest.relative_to(source_dir)),
                'change_log': str(change.relative_to(source_dir)),
                'current_governed_sections': parsed,
            },
            'active_surface_alignment': alignment,
            'best_next_move': alignment['best_next_move'],
        }

    outcome = alignment['outcome']
    reason = 'current control plane resolves, requested items are compatible with the GitHub-primary authority model, and the available active-surface checks did not contradict each other'
    return {
        'outcome': outcome,
        'reason': reason,
        'authoritative_basis_used': {
            'manifest': str(manifest.relative_to(source_dir)),
            'change_log': str(change.relative_to(source_dir)),
            'current_governed_sections': parsed,
        },
        'active_surface_alignment': alignment,
        'best_next_move': alignment['best_next_move'],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True)
    ap.add_argument('--requested-json', required=True)
    ap.add_argument('--output-json', required=True)
    args = ap.parse_args()
    requested = json.loads(Path(args.requested_json).read_text(encoding='utf-8')).get('requested_items', [])
    result = audit(Path(args.source_dir), requested)
    out = Path(args.output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['outcome'] != 'hard_stop_conflict' else 1


if __name__ == '__main__':
    raise SystemExit(main())
