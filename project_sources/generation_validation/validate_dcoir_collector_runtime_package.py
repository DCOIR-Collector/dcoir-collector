#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json.txt'

def load_manifest(source_dir: Path) -> Dict:
    return json.loads((source_dir / 'project_sources' / MANIFEST_NAME).read_text(encoding='utf-8'))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(source_dir)
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, object] = {}

    checks['source_strategy'] = manifest.get('source_strategy')
    if manifest.get('source_strategy') != 'stored_source_package':
        errors.append('source_strategy must be stored_source_package for the collector runtime package')

    required_files = manifest.get('required_files', [])
    missing_required = [rel for rel in required_files if not (source_dir / rel).exists()]
    checks['required_files_present'] = len(missing_required) == 0
    checks['missing_required_files'] = missing_required
    if missing_required:
        errors.append('missing required files: ' + ', '.join(missing_required))

    runtime_entries = manifest.get('runtime_zip_entries', [])
    checks['runtime_entry_count'] = len(runtime_entries)
    if not runtime_entries:
        errors.append('runtime_zip_entries is empty')

    missing_runtime_sources = [row.get('source', '') for row in runtime_entries if row.get('source') and not (source_dir / row['source']).exists()]
    checks['missing_runtime_sources'] = missing_runtime_sources
    if missing_runtime_sources:
        errors.append('runtime_zip_entries references missing sources: ' + ', '.join(missing_runtime_sources))

    zip_paths = [row.get('zip_path', '') for row in runtime_entries]
    duplicate_zip_paths = sorted({zp for zp in zip_paths if zp and zip_paths.count(zp) > 1})
    checks['duplicate_zip_paths'] = duplicate_zip_paths
    if duplicate_zip_paths:
        errors.append('runtime_zip_entries contains duplicate zip_path values: ' + ', '.join(duplicate_zip_paths))

    expected_runtime_names = {'DCOIR_Collector.ps1', 'run_DCOIR_Tests.ps1'}
    actual_runtime_names = {Path(zp).name for zp in zip_paths if zp}
    checks['expected_runtime_names_present'] = expected_runtime_names.issubset(actual_runtime_names)
    checks['actual_runtime_names'] = sorted(actual_runtime_names)
    if not expected_runtime_names.issubset(actual_runtime_names):
        errors.append('runtime package must include DCOIR_Collector.ps1 and run_DCOIR_Tests.ps1 as zip entries')

    retained_asset = manifest.get('retained_supporting_asset_path')
    checks['retained_supporting_asset_path'] = retained_asset
    checks['retained_supporting_asset_exists'] = bool(retained_asset and (source_dir / retained_asset).exists())
    if retained_asset and not (source_dir / retained_asset).exists():
        warnings.append('retained supporting asset path does not currently exist in the workspace')

    success = len(errors) == 0
    report = {
        'success': success,
        'source_dir': str(source_dir),
        'bundle_name': manifest.get('bundle_name'),
        'bundle_version': manifest.get('bundle_version'),
        'checks': checks,
        'warnings': warnings,
        'errors': errors,
    }
    report_path = output_dir / 'validate_dcoir_collector_runtime_package_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if success else 1

if __name__ == '__main__':
    raise SystemExit(main())
