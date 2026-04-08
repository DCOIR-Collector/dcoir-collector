#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json.txt'

def load_manifest(source_dir: Path) -> dict:
    return json.loads((source_dir / 'project_sources' / MANIFEST_NAME).read_text(encoding='utf-8'))

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
    version = args.version or manifest['bundle_version']
    bundle_name = manifest['bundle_name']
    top_level = f"{bundle_name}_v{version}"

    zip_path = output_dir / f"{bundle_name}_v{version}.zip"
    emitted = []
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for row in manifest.get('runtime_zip_entries', []):
            src = source_dir / row['source']
            arc = Path(top_level) / row['zip_path']
            zf.write(src, arc.as_posix())
            emitted.append({'source': row['source'], 'zip_path': row['zip_path']})

    report = {
        'success': True,
        'source_dir': str(source_dir),
        'zip_path': str(zip_path),
        'bundle_name': bundle_name,
        'bundle_version': version,
        'top_level_folder': top_level,
        'file_count': len(emitted),
        'emitted_files': emitted,
        'retained_supporting_asset_path': manifest.get('retained_supporting_asset_path'),
    }
    report_path = output_dir / 'build_dcoir_collector_runtime_package_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
