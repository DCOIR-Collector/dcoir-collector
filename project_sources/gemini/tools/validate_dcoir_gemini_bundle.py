#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Gemini_Bundle_Source_Manifest.json'
AGENT_DIR = '01_GEMINI_AGENT_BUILD'
QUICK_START = '00_START_HERE/Gemini_Build_Quick_Start.md.txt'
ATTACHMENT_MAP = '00_START_HERE/Agent_Attachment_Map.md.txt'
DEFAULT_GENERATED_KNOWLEDGE_DIR = '02_PRIME_AGENT_ATTACHMENTS'
VISIBILITY_CHECKS = {
    'collector_artifact_interpretation_visibility': ['collector artifact', 'upload summary'],
    'collector_pivot_visibility': ['targeted collection', 'collector'],
    'ioc_ownership_visibility': ['ioc', 'provenance'],
    'mixed_format_ioc_parsing_visibility': ['csv', 'pdf', 'docx'],
    'false_positive_aware_security_product_behavior': ['false-positive-aware', 'security product'],
    'starter_prompt_visibility': ['starter prompt 1', 'starter prompt 2', 'starter prompt 3'],
    'operator_state_awareness_visibility': ['operator', 'analyst'],
}


def load_manifest(source_root: Path) -> Dict:
    return json.loads((source_root / MANIFEST_NAME).read_text(encoding='utf-8'))


def resolve_repo_root(source_root: Path) -> Path:
    return source_root.parent.parent.parent


def rel_posix(path: Path, source_root: Path) -> str:
    return path.relative_to(source_root).as_posix()


def generated_attachment_name(source_rel: str) -> str:
    name = Path(source_rel).name
    if not name.endswith('.md'):
        raise ValueError(f'Knowledge attachment source must be a markdown file: {source_rel}')
    return name + '.txt'


def gather_text(paths: List[Path]) -> str:
    parts: List[str] = []
    for path in paths:
        if path.exists() and path.is_file():
            try:
                parts.append(path.read_text(encoding='utf-8', errors='ignore').lower())
            except Exception:
                continue
    return '\n'.join(parts)


def marker_count(text: str, labels: List[str]) -> int:
    lowered = text.lower()
    total = 0
    for label in labels:
        total += lowered.count(label.lower())
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()

    source_root = Path(args.source_root).resolve()
    repo_root = resolve_repo_root(source_root)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(source_root)
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, object] = {}

    expected_strategy = 'stored_source_compile_with_direct_knowledge_attachment_generation'
    checks['source_strategy'] = manifest.get('source_strategy')
    if manifest.get('source_strategy') != expected_strategy:
        errors.append(f'source_strategy must be {expected_strategy} for direct Knowledge packaging')

    required_files = manifest.get('required_files', [])
    missing_files = [rel for rel in required_files if not (source_root / rel).exists()]
    checks['required_files_present'] = len(missing_files) == 0
    checks['missing_required_files'] = missing_files
    if missing_files:
        errors.append('missing required source-root files: ' + ', '.join(missing_files))

    generated_dir = manifest.get('generated_knowledge_attachment_dir', DEFAULT_GENERATED_KNOWLEDGE_DIR)
    knowledge_sources = sorted(manifest.get('knowledge_attachment_sources', []))
    discovered_sources = sorted(
        p.relative_to(repo_root).as_posix()
        for p in (repo_root / 'knowledge').glob('Knowledge - *.md')
        if p.is_file()
    )
    missing_sources = [rel for rel in knowledge_sources if not (repo_root / rel).exists()]
    unlisted_sources = [rel for rel in discovered_sources if rel not in knowledge_sources]
    stale_sources = [rel for rel in knowledge_sources if rel not in discovered_sources]
    checks['knowledge_attachment_sources'] = knowledge_sources
    checks['discovered_knowledge_sources'] = discovered_sources
    checks['knowledge_source_inventory_exact_match'] = not missing_sources and not unlisted_sources and not stale_sources
    checks['missing_knowledge_sources'] = missing_sources
    checks['unlisted_knowledge_sources'] = unlisted_sources
    checks['stale_manifest_knowledge_sources'] = stale_sources
    if missing_sources or unlisted_sources or stale_sources:
        errors.append('knowledge source inventory drift detected between manifest and knowledge/')

    generated_dupes = [rel for rel in required_files if rel.startswith(f'{generated_dir}/Knowledge - ')]
    source_duplicate_files = sorted(
        p.relative_to(source_root).as_posix()
        for p in (source_root / generated_dir).glob('Knowledge - *.md.txt')
        if p.is_file()
    )
    checks['expected_generated_knowledge_attachments'] = sorted(f'{generated_dir}/{generated_attachment_name(rel)}' for rel in knowledge_sources)
    checks['manifest_has_no_generated_knowledge_duplicates'] = len(generated_dupes) == 0
    checks['source_tree_has_no_generated_knowledge_duplicates'] = len(source_duplicate_files) == 0
    checks['generated_knowledge_duplicates_in_manifest'] = generated_dupes
    checks['generated_knowledge_duplicates_in_source_tree'] = source_duplicate_files
    if generated_dupes:
        errors.append('manifest required_files still lists generated Knowledge attachment copies')
    if source_duplicate_files:
        errors.append('bundle_source still contains generated Knowledge attachment copies; delete them and let compile generate them from knowledge/')

    operator_files = [source_root / rel for rel in required_files if rel != MANIFEST_NAME]
    non_txt = [p.relative_to(source_root).as_posix() for p in operator_files if p.exists() and p.suffix != '.txt']
    checks['operator_facing_txt_suffixes'] = len(non_txt) == 0
    checks['non_txt_operator_files'] = non_txt
    if non_txt:
        warnings.append('some operator-facing files do not end with .txt: ' + ', '.join(non_txt))

    topology = manifest.get('topology', {})
    prime_rel = topology.get('prime_agent_file')
    sub_rel_list = list(topology.get('sub_agent_files', []))
    prime_source_mode = manifest.get('prime_agent_source_mode')
    prime_runtime_mode = manifest.get('prime_agent_runtime_mode')
    runtime_generated_files = list(manifest.get('runtime_generated_files', []))
    source_only_files = set(manifest.get('source_only_files', []))
    source_only_dirs = set(manifest.get('source_only_dirs', []))

    checks['topology_source'] = topology.get('topology_source_of_truth', 'missing')
    checks['manifest_prime_agent_file'] = prime_rel
    checks['manifest_sub_agent_files'] = sub_rel_list
    checks['manifest_sub_agent_count'] = len(sub_rel_list)
    checks['prime_agent_source_mode'] = prime_source_mode
    checks['prime_agent_runtime_mode'] = prime_runtime_mode
    checks['runtime_generated_files'] = runtime_generated_files
    checks['source_only_files'] = sorted(source_only_files)
    checks['source_only_dirs'] = sorted(source_only_dirs)

    discovered_prime = sorted(rel_posix(p, source_root) for p in (source_root / AGENT_DIR).glob('Prime_Agent_*.txt') if p.is_file())
    discovered_sub = sorted(rel_posix(p, source_root) for p in (source_root / AGENT_DIR).glob('Sub_Agent_*.txt') if p.is_file())
    checks['discovered_prime_files'] = discovered_prime
    checks['discovered_sub_agent_files'] = discovered_sub
    checks['discovered_sub_agent_count'] = len(discovered_sub)

    if prime_source_mode == 'chunked_reassembled' and prime_runtime_mode == 'generated_from_chunks':
        allowed_prime = discovered_prime in ([], [prime_rel])
        if not allowed_prime:
            errors.append('chunked prime agent mode allows zero or one generated canonical prime file only')
        if prime_rel not in runtime_generated_files:
            errors.append('runtime_generated_files must include manifest topology prime_agent_file in chunked mode')
    else:
        allowed_prime = bool(prime_rel and discovered_prime == [prime_rel])
        if prime_rel and discovered_prime != [prime_rel]:
            errors.append('prime agent file discovered in source tree does not match manifest topology')
    if sorted(sub_rel_list) != discovered_sub:
        errors.append('discovered sub-agent files do not exactly match manifest topology')
    checks['topology_exact_match'] = bool(prime_rel and allowed_prime and sorted(sub_rel_list) == discovered_sub)

    if prime_source_mode == 'chunked_reassembled':
        chunk_manifest_rel = manifest.get('prime_agent_chunk_manifest')
        checks['prime_agent_chunk_manifest'] = chunk_manifest_rel
        if not chunk_manifest_rel:
            errors.append('prime_agent_chunk_manifest is required when prime_agent_source_mode=chunked_reassembled')
        else:
            chunk_manifest_path = source_root / chunk_manifest_rel
            checks['prime_agent_chunk_manifest_exists'] = chunk_manifest_path.exists()
            if not chunk_manifest_path.exists():
                errors.append('prime agent chunk manifest is missing: ' + chunk_manifest_rel)
            else:
                chunk_manifest = json.loads(chunk_manifest_path.read_text(encoding='utf-8'))
                chunk_entries = list(chunk_manifest.get('chunks', []))
                chunk_sources = [entry.get('path') for entry in chunk_entries]
                topology_chunk_sources = list(topology.get('prime_agent_chunk_sources', []))
                checks['prime_agent_chunk_count'] = len(chunk_entries)
                checks['prime_agent_chunk_sources_match_topology'] = chunk_sources == topology_chunk_sources
                if chunk_sources != topology_chunk_sources:
                    errors.append('prime agent chunk sources do not match manifest topology prime_agent_chunk_sources')
                missing_chunks = [rel for rel in chunk_sources if not rel or not (source_root / rel).exists()]
                checks['missing_prime_agent_chunks'] = missing_chunks
                if missing_chunks:
                    errors.append('missing prime agent chunks: ' + ', '.join(missing_chunks))
                assembled = ''.join((source_root / rel).read_text(encoding='utf-8') for rel in chunk_sources if rel and (source_root / rel).exists())
                canonical_path = source_root / prime_rel if prime_rel else None
                canonical_exists = bool(canonical_path and canonical_path.exists())
                checks['prime_agent_generated_canonical_exists'] = canonical_exists
                if canonical_exists:
                    canonical = canonical_path.read_text(encoding='utf-8')
                    checks['prime_agent_chunk_reassembly_matches_canonical'] = assembled == canonical
                    if assembled != canonical:
                        errors.append('prime agent chunk reassembly does not match canonical prime agent file')
                else:
                    checks['prime_agent_chunk_reassembly_matches_canonical'] = True
                    checks['prime_agent_chunk_reassembly_sha256_only'] = True
                if assembled.count('```') % 2 != 0:
                    errors.append('reassembled prime agent has unbalanced markdown code fences')
                if 'Prime_Agent_Chunks_Manifest' in assembled or 'prime_agent_chunks/' in assembled:
                    errors.append('reassembled prime agent appears to contain source-only chunk metadata')
                name_markers = marker_count(assembled, ['### Agent name', 'Agent name:'])
                description_markers = marker_count(assembled, ['### Agent description', 'Agent description:'])
                checks['prime_agent_agent_name_marker_count'] = name_markers
                checks['prime_agent_agent_description_marker_count'] = description_markers
                if name_markers != 1 or description_markers != 1:
                    errors.append('reassembled prime agent must contain exactly one Agent name and one Agent description block')
    elif prime_source_mode not in (None, 'single_file'):
        warnings.append('unrecognized prime_agent_source_mode: ' + str(prime_source_mode))

    attachment_map_path = source_root / ATTACHMENT_MAP
    attachment_map_text = attachment_map_path.read_text(encoding='utf-8', errors='ignore').lower() if attachment_map_path.exists() else ''
    map_missing_titles = [Path(rel).stem.lower() for rel in knowledge_sources if Path(rel).stem.lower() not in attachment_map_text]
    checks['attachment_map_mentions_all_knowledge_source_files'] = len(map_missing_titles) == 0
    checks['attachment_map_missing_titles'] = map_missing_titles
    if map_missing_titles:
        errors.append('attachment map does not mention every manifest-listed knowledge source file')

    combined_paths = list((source_root / AGENT_DIR).glob('*.txt')) + [source_root / QUICK_START] + [repo_root / rel for rel in knowledge_sources]
    combined = gather_text(combined_paths).lower()
    for key, needles in VISIBILITY_CHECKS.items():
        present = all(needle in combined for needle in needles)
        checks[key] = present
        if not present:
            warnings.append(f'visibility check did not find all markers for {key}: {needles}')

    success = len(errors) == 0
    report = {
        'success': success,
        'source_root': str(source_root),
        'repo_root': str(repo_root),
        'bundle_name': manifest.get('bundle_name'),
        'bundle_version': manifest.get('bundle_version'),
        'checks': checks,
        'warnings': warnings,
        'errors': errors,
    }
    report_path = output_dir / 'validate_dcoir_gemini_bundle_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
