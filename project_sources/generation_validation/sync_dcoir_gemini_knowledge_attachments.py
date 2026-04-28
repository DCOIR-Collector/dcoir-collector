#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Gemini_Bundle_Source_Manifest.json.txt'
KNOWLEDGE_DIR = '02_PRIME_AGENT_ATTACHMENTS'


def load_manifest(source_root: Path) -> Dict:
    return json.loads((source_root / MANIFEST_NAME).read_text(encoding='utf-8'))


def derive_expected_knowledge_targets(source_root: Path) -> List[str]:
    manifest = load_manifest(source_root)
    required = manifest.get('required_files', [])
    return sorted(
        rel for rel in required
        if rel.startswith(f'{KNOWLEDGE_DIR}/') and Path(rel).name.startswith('Knowledge - ') and rel.endswith('.md.txt')
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--check-only', action='store_true')
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    expected_targets = derive_expected_knowledge_targets(source_root)
    errors: List[str] = []
    changed: List[str] = []
    unchanged: List[str] = []
    missing_sources: List[str] = []
    source_to_target: Dict[str, str] = {}

    for target_rel in expected_targets:
        target_name = Path(target_rel).name
        source_name = target_name[:-4]
        source_rel = f'knowledge/{source_name}'
        source_to_target[source_rel] = target_rel
        source_path = repo_root / source_rel
        target_path = source_root / target_rel
        if not source_path.exists():
            missing_sources.append(source_rel)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source_text = source_path.read_text(encoding='utf-8')
        if not source_text.endswith('\n'):
            source_text += '\n'
        current_text = target_path.read_text(encoding='utf-8') if target_path.exists() else None
        if current_text != source_text:
            if not args.check_only:
                target_path.write_text(source_text, encoding='utf-8')
            changed.append(target_rel)
        else:
            unchanged.append(target_rel)

    maintained_sources = sorted(
        p.relative_to(repo_root).as_posix()
        for p in (repo_root / 'knowledge').glob('Knowledge - *.md')
        if p.is_file()
    )
    unmapped_sources = [rel for rel in maintained_sources if rel not in source_to_target]

    if missing_sources:
        errors.append('missing maintained knowledge source files for manifest-required attachments: ' + ', '.join(missing_sources))
    if unmapped_sources:
        errors.append('maintained knowledge source files are not represented in the manifest attachment inventory: ' + ', '.join(unmapped_sources))

    report = {
        'success': len(errors) == 0,
        'repo_root': str(repo_root),
        'source_root': str(source_root),
        'check_only': args.check_only,
        'expected_target_files': expected_targets,
        'changed_files': changed,
        'unchanged_files': unchanged,
        'missing_source_files': missing_sources,
        'unmapped_source_files': unmapped_sources,
        'errors': errors,
    }
    report_path = output_dir / 'sync_dcoir_gemini_knowledge_attachments_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if len(errors) == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
