#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

MANIFEST_NAME = 'Gemini_Bundle_Source_Manifest.json.txt'
EXCLUDE = {'.DS_Store'}


def load_manifest(source_root: Path) -> dict:
    return json.loads((source_root / MANIFEST_NAME).read_text(encoding='utf-8'))


def derive_bundle_version(source_root: Path, manifest: dict) -> str:
    index_rel = manifest.get('topology', {}).get('generated_index_file')
    if index_rel:
        index_path = source_root / index_rel
        if index_path.exists():
            text = index_path.read_text(encoding='utf-8', errors='ignore')
            match = re.search(r'(?m)^Bundle version:\s*([0-9_]+)\s*$', text)
            if match:
                return match.group(1)
    return manifest['bundle_version']


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--version', default=None)
    args = ap.parse_args()

    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(source_root)
    version = args.version or derive_bundle_version(source_root, manifest)
    bundle_name = manifest['bundle_name']
    top_level = f"{bundle_name}_{version}"

    required = manifest.get('required_files', [])
    missing = []
    for rel in required:
        if rel in EXCLUDE:
            continue
        if not (source_root / rel).exists():
            missing.append(rel)
    if missing:
        raise SystemExit('Missing required source files: ' + ', '.join(missing))

    zip_path = output_dir / f"{bundle_name}_{version}.zip"
    count = 0
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_root.rglob('*')):
            if not path.is_file():
                continue
            if path.name in EXCLUDE:
                continue
            rel = path.relative_to(source_root)
            arc = Path(top_level) / rel
            zf.write(path, arc.as_posix())
            count += 1

    report = {
        'success': True,
        'source_root': str(source_root),
        'zip_path': str(zip_path),
        'bundle_name': bundle_name,
        'bundle_version': version,
        'top_level_folder': top_level,
        'file_count': count,
        'source_strategy': manifest.get('source_strategy')
    }
    report_path = output_dir / 'compile_dcoir_gemini_bundle_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
