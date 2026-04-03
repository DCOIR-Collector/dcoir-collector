#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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

MANIFEST_SECTIONS = {
    "CURRENT GOVERNED GITHUB READABLE SOURCES": "governed_github_readable_sources",
    "CURRENT GOVERNED KNOWLEDGE SOURCES IN GITHUB": "governed_knowledge_sources",
    "CURRENT GOVERNED SETTINGS MIRRORS IN GITHUB": "governed_settings_mirrors",
    "CURRENT SUPPORTING ASSETS IN GITHUB": "supporting_assets",
}


def resolve_control_file(source_dir: Path, candidates: Sequence[str]) -> Optional[Path]:
    for candidate in candidates:
        path = source_dir / candidate
        if path.exists():
            return path
    return None



def parse_current_prose_manifest(text: str) -> Dict[str, List[str]]:
    parsed = {value: [] for value in MANIFEST_SECTIONS.values()}
    heading = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if not line.startswith('- ') and not line.startswith('Version:') and line.endswith(':') is False and line in {
            'Current control plane', 'Current repo guide', 'Current collector files', 'Current task-memory bank', 'Current next work item'
        }:
            heading = line
            continue
        if line.startswith('- '):
            payload = line[2:].strip()
            value = payload.split(':',1)[1].strip() if ':' in payload else payload
            if heading in {'Current control plane','Current repo guide','Current collector files'}:
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

    bounded = any(Path(item).name.startswith('LOG-') for item in normalized_requested)
    return {
        'outcome': 'proceed_bounded' if bounded else 'clear_to_proceed',
        'reason': 'current control plane resolves and requested items are compatible with the GitHub-primary authority model',
        'authoritative_basis_used': {
            'manifest': str(manifest.relative_to(source_dir)),
            'change_log': str(change.relative_to(source_dir)),
            'current_governed_sections': parsed,
        },
        'best_next_move': 'proceed using the current manifest-defined GitHub readable source set',
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
