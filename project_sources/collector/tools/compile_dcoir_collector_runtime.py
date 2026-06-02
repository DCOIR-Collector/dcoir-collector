#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json'
PATTERN = re.compile(r"(?ms)^\$collectorPartsRoot = .*?^foreach \(\$partFile in \$collectorPartFiles\) \{.*?^\}\s*")


def load_manifest(source_dir: Path) -> dict:
    return json.loads((source_dir / 'project_sources' / 'collector' / 'manifests' / MANIFEST_NAME).read_text(encoding='utf-8'))


def build_inline_block(part_paths: List[Path]) -> str:
    blocks: List[str] = []
    blocks.append('# BEGIN COMPILED COLLECTOR PARTS')
    for part_path in part_paths:
        text = part_path.read_text(encoding='utf-8')
        if not text.strip():
            raise SystemExit(f'collector part file is empty: {part_path}')
        if not text.endswith('\n'):
            text += '\n'
        blocks.append(f"# BEGIN {part_path.name}")
        blocks.append(text.rstrip('\n'))
        blocks.append(f"# END {part_path.name}")
        blocks.append('')
    blocks.append('# END COMPILED COLLECTOR PARTS')
    return '\n'.join(blocks) + '\n'


def require_non_empty_list(manifest: dict, key: str) -> list:
    value = manifest.get(key)
    if not isinstance(value, list) or not value:
        raise SystemExit(f'{key} must be a non-empty list')
    return value


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
    if manifest.get('harness_source'):
        raise SystemExit('harness_source is not supported by the collector runtime package compiler')

    wrapper_path = source_dir / manifest['collector_wrapper_source']
    part_rels = require_non_empty_list(manifest, 'collector_part_files')
    part_paths = [source_dir / rel for rel in part_rels]
    missing_parts = [rel for rel, path in zip(part_rels, part_paths) if not path.exists()]
    if missing_parts:
        raise SystemExit('collector_part_files references missing files: ' + ', '.join(missing_parts))

    wrapper_text = wrapper_path.read_text(encoding='utf-8')
    inline_block = build_inline_block(part_paths)
    if not PATTERN.search(wrapper_text):
        raise SystemExit('collector wrapper does not contain the expected collector_parts import block')

    compiled_text = PATTERN.sub(lambda _m: inline_block, wrapper_text, count=1)

    if not compiled_text.endswith('\n'):
        compiled_text += '\n'

    compiled_root = output_dir / 'compiled_runtime'
    compiled_root.mkdir(parents=True, exist_ok=True)
    compiled_collector = compiled_root / manifest.get('compiled_runtime_name', 'DCOIR_Collector.ps1')
    compiled_collector.write_text(compiled_text, encoding='utf-8')

    report = {
        'success': True,
        'source_dir': str(source_dir),
        'compiled_collector_path': str(compiled_collector),
        'compiled_harness_path': None,
        'compiled_runtime_name': compiled_collector.name,
        'collector_part_count': len(part_paths),
        'collector_part_files': [p.name for p in part_paths],
        'source_strategy': manifest.get('source_strategy'),
    }
    report_path = output_dir / 'compile_dcoir_collector_runtime_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
