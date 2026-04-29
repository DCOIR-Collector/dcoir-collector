#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Gemini_Bundle_Source_Manifest.json'
VISIBILITY_CHECKS = {
    'collector_artifact_interpretation_visibility': ['collector artifact', 'upload summary'],
    'collector_pivot_visibility': ['targeted collection', 'collector'],
    'ioc_ownership_visibility': ['ioc', 'provenance'],
    'mixed_format_ioc_parsing_visibility': ['csv', 'pdf', 'docx'],
    'false_positive_aware_security_product_behavior': ['false-positive-aware', 'security product'],
    'starter_prompt_visibility': ['starter prompt 1', 'starter prompt 2', 'starter prompt 3'],
    'operator_state_awareness_visibility': ['operator', 'analyst'],
}
AGENT_DIR = '01_GEMINI_AGENT_BUILD'
KNOWLEDGE_DIR = '02_PRIME_AGENT_ATTACHMENTS'
QUICK_START = '00_START_HERE/Gemini_Build_Quick_Start.md.txt'
ATTACHMENT_MAP = '00_START_HERE/Agent_Attachment_Map.md.txt'


def load_manifest(source_root: Path) -> Dict:
    return json.loads((source_root / MANIFEST_NAME).read_text(encoding='utf-8'))


def gather_text(paths: List[Path]) -> str:
    parts: List[str] = []
    for path in paths:
        if path.exists() and path.is_file():
            try:
                parts.append(path.read_text(encoding='utf-8', errors='ignore').lower())
            except Exception:
                continue
    return '\n'.join(parts)


def rel_posix(path: Path, source_root: Path) -> str:
    return path.relative_to(source_root).as_posix()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()

    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(source_root)
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, object] = {}

    if manifest.get('source_strategy') != 'stored_source_compile':
        errors.append('source_strategy must be stored_source_compile for routine Gemini shipment')
    checks['source_strategy'] = manifest.get('source_strategy')

    required_files = manifest.get('required_files', [])
    missing_files = [rel for rel in required_files if not (source_root / rel).exists()]
    checks['required_files_present'] = len(missing_files) == 0
    checks['missing_required_files'] = missing_files
    if missing_files:
        errors.append('missing required files: ' + ', '.join(missing_files))

    operator_files = [source_root / rel for rel in required_files if rel != MANIFEST_NAME]
    non_txt = [str(p.relative_to(source_root)) for p in operator_files if p.exists() and p.suffix != '.txt']
    checks['operator_facing_txt_suffixes'] = len(non_txt) == 0
    checks['non_txt_operator_files'] = non_txt
    if non_txt:
        warnings.append('some operator-facing files do not end with .txt: ' + ', '.join(non_txt))

    manifest_knowledge = sorted(
        rel for rel in required_files
        if rel.startswith(f'{KNOWLEDGE_DIR}/') and Path(rel).name.startswith('Knowledge - ') and rel.endswith('.md.txt')
    )
    discovered_knowledge = sorted(
        rel_posix(p, source_root)
        for p in (source_root / KNOWLEDGE_DIR).glob('Knowledge - *.md.txt')
        if p.is_file()
    )
    missing_knowledge = [rel for rel in manifest_knowledge if rel not in discovered_knowledge]
    extra_knowledge = [rel for rel in discovered_knowledge if rel not in manifest_knowledge]
    checks['manifest_knowledge_files'] = manifest_knowledge
    checks['discovered_knowledge_files'] = discovered_knowledge
    checks['knowledge_attachment_inventory_exact_match'] = len(missing_knowledge) == 0 and len(extra_knowledge) == 0
    checks['missing_knowledge_files'] = missing_knowledge
    checks['extra_unlisted_knowledge_files'] = extra_knowledge
    if missing_knowledge or extra_knowledge:
        errors.append('knowledge attachment inventory drift detected between manifest and attachment directory')

    topology = manifest.get('topology', {})
    prime_rel = topology.get('prime_agent_file')
    sub_rel_list = list(topology.get('sub_agent_files', []))
    checks['topology_source'] = topology.get('topology_source_of_truth', 'missing')
    checks['manifest_prime_agent_file'] = prime_rel
    checks['manifest_sub_agent_files'] = sub_rel_list
    checks['manifest_sub_agent_count'] = len(sub_rel_list)

    discovered_prime = sorted(rel_posix(p, source_root) for p in (source_root / AGENT_DIR).glob('Prime_Agent_*.txt') if p.is_file())
    discovered_sub = sorted(rel_posix(p, source_root) for p in (source_root / AGENT_DIR).glob('Sub_Agent_*.txt') if p.is_file())
    checks['discovered_prime_files'] = discovered_prime
    checks['discovered_sub_agent_files'] = discovered_sub
    checks['discovered_sub_agent_count'] = len(discovered_sub)

    if prime_rel and discovered_prime != [prime_rel]:
        errors.append('prime agent file discovered in source tree does not match manifest topology')
    if sorted(sub_rel_list) != discovered_sub:
        errors.append('discovered sub-agent files do not exactly match manifest topology')
    checks['topology_exact_match'] = bool(prime_rel and discovered_prime == [prime_rel] and sorted(sub_rel_list) == discovered_sub)

    attachment_map_path = source_root / ATTACHMENT_MAP
    attachment_map_text = attachment_map_path.read_text(encoding='utf-8', errors='ignore').lower() if attachment_map_path.exists() else ''
    map_missing_titles = [Path(rel).name[:-7].lower() for rel in manifest_knowledge if Path(rel).name[:-7].lower() not in attachment_map_text]
    checks['attachment_map_mentions_all_manifest_knowledge_files'] = len(map_missing_titles) == 0
    checks['attachment_map_missing_titles'] = map_missing_titles
    if map_missing_titles:
        errors.append('attachment map does not mention every manifest-listed knowledge attachment file')

    combined = gather_text(list((source_root / AGENT_DIR).glob('*.txt')) + [source_root / QUICK_START]).lower()
    for key, needles in VISIBILITY_CHECKS.items():
        present = all(needle in combined for needle in needles)
        checks[key] = present
        if not present:
            warnings.append(f'visibility check did not find all markers for {key}: {needles}')

    success = len(errors) == 0
    report = {'success': success, 'source_root': str(source_root), 'bundle_name': manifest.get('bundle_name'), 'bundle_version': manifest.get('bundle_version'), 'checks': checks, 'warnings': warnings, 'errors': errors}
    report_path = output_dir / 'validate_dcoir_gemini_bundle_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
