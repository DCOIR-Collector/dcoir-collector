$ErrorActionPreference = 'Stop'
$repo = $env:DCOIR_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { throw 'DCOIR_REPO_ROOT is not set' }
Set-Location $repo

git config user.name 'chatgpt-exec'
git config user.email 'chatgpt-exec@users.noreply.github.com'
git pull --ff-only origin main

$py = @'
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

repo = Path.cwd()
source_root = repo / 'project_sources/gemini/bundle_source'
agent_dir = source_root / '01_GEMINI_AGENT_BUILD'
prime_rel = '01_GEMINI_AGENT_BUILD/Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt'
prime_path = source_root / prime_rel
chunk_dir = agent_dir / 'prime_agent_chunks'
chunk_manifest_rel = '01_GEMINI_AGENT_BUILD/prime_agent_chunks/Prime_Agent_Chunks_Manifest.json'
chunk_manifest_path = source_root / chunk_manifest_rel
bundle_manifest_path = source_root / 'Gemini_Bundle_Source_Manifest.json'
tools_dir = repo / 'project_sources/gemini/tools'
reassemble_path = tools_dir / 'reassemble_dcoir_gemini_prime_agent.py'
build_path = tools_dir / 'build_dcoir_gemini_release.py'
validate_path = tools_dir / 'validate_dcoir_gemini_bundle.py'

if not prime_path.exists():
    raise SystemExit(f'Missing prime agent file: {prime_path}')

text = prime_path.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)
sha256 = hashlib.sha256(prime_path.read_bytes()).hexdigest()

# Split on top-level SECTION markers inside the prime-agent instruction. Keep all content byte-for-byte.
boundaries = [0]
for idx, line in enumerate(lines):
    if re.match(r'^SECTION\s+\d+[A-Z]?:', line):
        if idx not in boundaries:
            boundaries.append(idx)
boundaries = sorted(set(boundaries))
if len(boundaries) < 4:
    raise SystemExit(f'Not enough SECTION boundaries discovered for strategic chunking: {len(boundaries)}')

# Remove stale generated chunk files before rewriting.
chunk_dir.mkdir(parents=True, exist_ok=True)
for old in chunk_dir.glob('Prime_Agent_Chunk_*.md.txt'):
    old.unlink()

entries = []
for pos, start in enumerate(boundaries):
    end = boundaries[pos + 1] if pos + 1 < len(boundaries) else len(lines)
    chunk_lines = lines[start:end]
    first = ''.join(chunk_lines[:1]).strip()
    if pos == 0:
        title = 'Metadata_Description_And_Global_Opening'
    else:
        m = re.match(r'^SECTION\s+([0-9A-Z.]+):\s*(.+?)\s*$', first)
        raw_title = m.group(2) if m else first
        title = re.sub(r'[^A-Za-z0-9]+', '_', raw_title).strip('_')[:80] or f'Section_{pos:02d}'
    filename = f'Prime_Agent_Chunk_{pos:02d}_{title}.md.txt'
    rel = f'01_GEMINI_AGENT_BUILD/prime_agent_chunks/{filename}'
    path = source_root / rel
    chunk_text = ''.join(chunk_lines)
    path.write_text(chunk_text, encoding='utf-8')
    entries.append({
        'chunk_id': f'{pos:02d}',
        'title': title,
        'path': rel,
        'line_start': start + 1,
        'line_end': end,
        'line_count': end - start,
        'starts_with': first,
        'sha256': hashlib.sha256(chunk_text.encode('utf-8')).hexdigest(),
    })

chunk_manifest = {
    'schema': 'dcoir.gemini.prime_agent_chunks.v1',
    'source_prime_agent_file': prime_rel,
    'generated_prime_agent_file': prime_rel,
    'source_strategy': 'chunked_reassembled_prime_agent',
    'original_sha256_at_split': sha256,
    'original_line_count_at_split': len(lines),
    'chunk_count': len(entries),
    'reassembly': {
        'method': 'concatenate_chunks_in_manifest_order',
        'newline_policy': 'preserve_chunk_text_exactly',
        'expected_sha256': sha256,
    },
    'chunks': entries,
}
chunk_manifest_path.write_text(json.dumps(chunk_manifest, indent=2) + '\n', encoding='utf-8')

bundle = json.loads(bundle_manifest_path.read_text(encoding='utf-8'))
bundle['prime_agent_source_mode'] = 'chunked_reassembled'
bundle['prime_agent_chunk_manifest'] = chunk_manifest_rel
topology = bundle.setdefault('topology', {})
topology['prime_agent_file'] = prime_rel
topology['prime_agent_chunk_manifest'] = chunk_manifest_rel
topology['prime_agent_chunk_sources'] = [e['path'] for e in entries]
# The canonical compiled prime file remains required for Gemini packaging; chunk files are edit sources.
required = list(bundle.get('required_files', []))
for rel in [chunk_manifest_rel, *[e['path'] for e in entries]]:
    if rel not in required:
        required.append(rel)
bundle['required_files'] = required
bundle_manifest_path.write_text(json.dumps(bundle, indent=2) + '\n', encoding='utf-8')

reassemble_code = r'''#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MANIFEST_NAME = 'Gemini_Bundle_Source_Manifest.json'


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--check-only', action='store_true')
    args = ap.parse_args()

    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    bundle_manifest = load_json(source_root / MANIFEST_NAME)
    mode = bundle_manifest.get('prime_agent_source_mode')
    report = {
        'success': True,
        'source_root': str(source_root),
        'mode': mode,
        'action': 'none',
    }
    if mode != 'chunked_reassembled':
        report_path = output_dir / 'reassemble_dcoir_gemini_prime_agent_report.json'
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
        return 0

    chunk_manifest_rel = bundle_manifest.get('prime_agent_chunk_manifest')
    if not chunk_manifest_rel:
        raise SystemExit('prime_agent_chunk_manifest is required when prime_agent_source_mode=chunked_reassembled')
    chunk_manifest = load_json(source_root / chunk_manifest_rel)
    target_rel = chunk_manifest['generated_prime_agent_file']
    target_path = source_root / target_rel
    chunks = chunk_manifest.get('chunks', [])
    if not chunks:
        raise SystemExit('Prime agent chunk manifest has no chunks')

    parts = []
    missing = []
    for entry in chunks:
        path = source_root / entry['path']
        if not path.exists():
            missing.append(entry['path'])
            continue
        text = path.read_text(encoding='utf-8')
        expected = entry.get('sha256')
        actual = sha256_text(text)
        if expected and actual != expected:
            raise SystemExit(f"Chunk sha256 mismatch for {entry['path']}: expected {expected}, got {actual}")
        parts.append(text)
    if missing:
        raise SystemExit('Missing prime agent chunks: ' + ', '.join(missing))

    assembled = ''.join(parts)
    assembled_sha = sha256_text(assembled)
    expected_sha = chunk_manifest.get('reassembly', {}).get('expected_sha256')
    if expected_sha and assembled_sha != expected_sha:
        raise SystemExit(f'Reassembled prime agent sha256 mismatch: expected {expected_sha}, got {assembled_sha}')

    current = target_path.read_text(encoding='utf-8') if target_path.exists() else ''
    current_sha = sha256_text(current) if target_path.exists() else None
    if args.check_only and current != assembled:
        raise SystemExit('Canonical prime agent file does not match chunk reassembly')
    if not args.check_only:
        target_path.write_text(assembled, encoding='utf-8')

    report.update({
        'action': 'checked' if args.check_only else 'reassembled',
        'target': target_rel,
        'chunk_manifest': chunk_manifest_rel,
        'chunk_count': len(chunks),
        'assembled_sha256': assembled_sha,
        'previous_target_sha256': current_sha,
        'matches_previous_target': current == assembled,
    })
    report_path = output_dir / 'reassemble_dcoir_gemini_prime_agent_report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
'''
reassemble_path.write_text(reassemble_code, encoding='utf-8')

build_text = build_path.read_text(encoding='utf-8')
if "name': 'reassemble_prime_agent'" not in build_text:
    build_text = build_text.replace(
        "    validate_script = script_root / 'validate_dcoir_gemini_bundle.py'\n    scenario_script = script_root / 'validate_dcoir_gemini_behavior_scenarios.py'\n    compile_script = script_root / 'compile_dcoir_gemini_bundle.py'\n",
        "    validate_script = script_root / 'validate_dcoir_gemini_bundle.py'\n    scenario_script = script_root / 'validate_dcoir_gemini_behavior_scenarios.py'\n    compile_script = script_root / 'compile_dcoir_gemini_bundle.py'\n    reassemble_script = script_root / 'reassemble_dcoir_gemini_prime_agent.py'\n"
    )
    build_text = build_text.replace(
        "    steps = []\n\n    if not args.skip_validation:\n",
        "    steps = []\n\n    reassemble_cmd = [sys.executable, str(reassemble_script), '--source-root', str(source_root), '--output-dir', str(output_dir)]\n    reassemble_proc = run_step(reassemble_cmd)\n    steps.append({\n        'name': 'reassemble_prime_agent',\n        'cmd': reassemble_cmd,\n        'returncode': reassemble_proc.returncode,\n        'stdout': reassemble_proc.stdout,\n        'stderr': reassemble_proc.stderr,\n    })\n    if reassemble_proc.returncode != 0:\n        write_report(output_dir, {'success': False, 'stage': 'reassemble_prime_agent', 'steps': steps})\n        return 1\n\n    if not args.skip_validation:\n"
    )
build_path.write_text(build_text, encoding='utf-8')

validate_text = validate_path.read_text(encoding='utf-8')
if 'prime_agent_chunk_reassembly_matches_canonical' not in validate_text:
    insertion = r'''

    prime_source_mode = manifest.get('prime_agent_source_mode')
    checks['prime_agent_source_mode'] = prime_source_mode
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
                canonical = (source_root / prime_rel).read_text(encoding='utf-8') if prime_rel and (source_root / prime_rel).exists() else ''
                checks['prime_agent_chunk_reassembly_matches_canonical'] = assembled == canonical
                if assembled != canonical:
                    errors.append('prime agent chunk reassembly does not match canonical prime agent file')
    elif prime_source_mode not in (None, 'single_file'):
        warnings.append('unrecognized prime_agent_source_mode: ' + str(prime_source_mode))
'''
    needle = "    checks['topology_exact_match'] = bool(prime_rel and discovered_prime == [prime_rel] and sorted(sub_rel_list) == discovered_sub)\n"
    validate_text = validate_text.replace(needle, needle + insertion)
validate_path.write_text(validate_text, encoding='utf-8')

# Verify reassembly and validation before committing.
out_dir = repo / 'chatgpt_staging/work/prime_agent_chunk_refactor_001_validation'
out_dir.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, str(reassemble_path), '--source-root', str(source_root), '--output-dir', str(out_dir), '--check-only'], check=True)
subprocess.run([sys.executable, str(validate_path), '--source-root', str(source_root), '--output-dir', str(out_dir)], check=True)

report = {
    'success': True,
    'prime_agent_sha256': sha256,
    'prime_agent_lines': len(lines),
    'chunk_count': len(entries),
    'chunk_manifest': chunk_manifest_rel,
    'changed_paths': [
        'project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json',
        chunk_manifest_rel,
        *[e['path'] for e in entries],
        'project_sources/gemini/tools/reassemble_dcoir_gemini_prime_agent.py',
        'project_sources/gemini/tools/build_dcoir_gemini_release.py',
        'project_sources/gemini/tools/validate_dcoir_gemini_bundle.py',
    ],
}
(repo / 'chatgpt_staging/work/prime_agent_chunk_refactor_001_validation/prime_agent_chunk_refactor_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
'@

$script = Join-Path $env:DCOIR_CONFIG_DIR 'prime_agent_chunk_refactor.py'
$py | Out-File -FilePath $script -Encoding utf8
python $script

# Commit and push the generated repo changes.
git add project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json `
  project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/prime_agent_chunks `
  project_sources/gemini/tools/reassemble_dcoir_gemini_prime_agent.py `
  project_sources/gemini/tools/build_dcoir_gemini_release.py `
  project_sources/gemini/tools/validate_dcoir_gemini_bundle.py

if (git diff --cached --quiet) {
  Write-Host 'No prime-agent chunking changes to commit.'
} else {
  git commit -m 'Chunk Gemini prime agent source for managed editing'
  git push origin HEAD:main
}
