#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json.txt'
PATTERN = re.compile(r"(?ms)^\$collectorPartsRoot = .*?^foreach \(\$partFile in \$collectorPartFiles\) \{.*?^\}\s*")


def load_manifest(source_dir: Path) -> dict:
    return json.loads((source_dir / 'project_sources' / MANIFEST_NAME).read_text(encoding='utf-8'))


def build_inline_block(part_paths: List[Path]) -> str:
    blocks: List[str] = []
    blocks.append('# BEGIN COMPILED COLLECTOR PARTS')
    for part_path in part_paths:
        text = part_path.read_text(encoding='utf-8')
        if not text.endswith('\n'):
            text += '\n'
        blocks.append(f"# BEGIN {part_path.name}")
        blocks.append(text.rstrip('\n'))
        blocks.append(f"# END {part_path.name}")
        blocks.append('')
    blocks.append('# END COMPILED COLLECTOR PARTS')
    return '\n'.join(blocks) + '\n'


def patch_compiled_text(compiled_text: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    replacements = {
        "[void]$Baseline.ArtifactPaths.Add($scopePath)": "Add-BaselineArtifactPath -Baseline $Baseline -Path $scopePath",
        "[void]$Baseline.ArtifactPaths.Add($parallelPath)": "Add-BaselineArtifactPath -Baseline $Baseline -Path $parallelPath",
        "[void]$Baseline.ArtifactPaths.Add($planPath)": "Add-BaselineArtifactPath -Baseline $Baseline -Path $planPath",
    }
    patched = compiled_text
    for old, new in replacements.items():
        if old in patched:
            patched = patched.replace(old, new)
            notes.append(f"patched compiled runtime occurrence: {old}")
    return patched, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--version', default=None)
    args = ap.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(source_dir)
    wrapper_path = source_dir / manifest['collector_wrapper_source']
    harness_path = source_dir / manifest['harness_source']
    part_paths = [source_dir / rel for rel in manifest.get('collector_part_files', [])]

    wrapper_text = wrapper_path.read_text(encoding='utf-8')
    inline_block = build_inline_block(part_paths)
    if not PATTERN.search(wrapper_text):
        raise SystemExit('collector wrapper does not contain the expected collector_parts import block')

    compiled_text = PATTERN.sub(lambda _m: inline_block, wrapper_text, count=1)
    compiled_text, patch_notes = patch_compiled_text(compiled_text)

    if not compiled_text.endswith('\n'):
        compiled_text += '\n'

    compiled_root = output_dir / 'compiled_runtime'
    compiled_root.mkdir(parents=True, exist_ok=True)
    compiled_collector = compiled_root / manifest.get('compiled_runtime_name', 'DCOIR_Collector.ps1')
    compiled_harness = compiled_root / harness_path.name
    compiled_collector.write_text(compiled_text, encoding='utf-8')
    compiled_harness.write_text(harness_path.read_text(encoding='utf-8'), encoding='utf-8')

    report = {
        'success': True,
        'source_dir': str(source_dir),
        'compiled_collector_path': str(compiled_collector),
        'compiled_harness_path': str(compiled_harness),
        'compiled_runtime_name': compiled_collector.name,
        'collector_part_count': len(part_paths),
        'collector_part_files': [p.name for p in part_paths],
        'source_strategy': manifest.get('source_strategy'),
        'patch_notes': patch_notes,
    }
    report_path = output_dir / 'compile_dcoir_collector_runtime_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
