#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json'

def load_manifest(source_dir: Path) -> Dict:
    return json.loads((source_dir / 'project_sources' / 'collector' / 'manifests' / MANIFEST_NAME).read_text(encoding='utf-8'))

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
    if manifest.get('source_strategy') != 'compile_single_runtime_then_package':
        errors.append('source_strategy must be compile_single_runtime_then_package for the collector runtime package')

    required_files = manifest.get('required_files', [])
    missing_required = [rel for rel in required_files if not (source_dir / rel).exists()]
    checks['required_files_present'] = len(missing_required) == 0
    checks['missing_required_files'] = missing_required
    if missing_required:
        errors.append('missing required files: ' + ', '.join(missing_required))

    collector_part_files = manifest.get('collector_part_files', [])
    checks['collector_part_count'] = len(collector_part_files)
    missing_parts = [rel for rel in collector_part_files if not (source_dir / rel).exists()]
    checks['missing_collector_part_files'] = missing_parts
    if missing_parts:
        errors.append('collector_part_files references missing files: ' + ', '.join(missing_parts))
    empty_parts = [rel for rel in collector_part_files if (source_dir / rel).exists() and not (source_dir / rel).read_text(encoding='utf-8').strip()]
    checks['empty_collector_part_files'] = empty_parts
    if empty_parts:
        errors.append('collector_part_files references empty files: ' + ', '.join(empty_parts))

    delivery_entries = manifest.get('delivery_zip_entries', [])
    checks['delivery_entry_count'] = len(delivery_entries)
    if not delivery_entries:
        errors.append('delivery_zip_entries is empty')

    expected_delivery_names = {'DCOIR_Collector.ps1.txt'}
    prohibited_delivery_names = {'run_DCOIR_Tests.ps1.txt'}
    actual_delivery_names = {Path(row.get('zip_path', '')).name for row in delivery_entries if row.get('zip_path')}
    checks['expected_delivery_names_present'] = expected_delivery_names.issubset(actual_delivery_names)
    checks['actual_delivery_names'] = sorted(actual_delivery_names)
    checks['prohibited_delivery_names_absent'] = actual_delivery_names.isdisjoint(prohibited_delivery_names)
    if not expected_delivery_names.issubset(actual_delivery_names):
        errors.append('delivery package must include DCOIR_Collector.ps1.txt')
    if not actual_delivery_names.isdisjoint(prohibited_delivery_names):
        errors.append('delivery package must not include harness files: ' + ', '.join(sorted(actual_delivery_names.intersection(prohibited_delivery_names))))

    delivery_rules = manifest.get('delivery_rules', {})
    require_txt = bool(delivery_rules.get('transport_safe_suffix_required_for_scripts'))
    checks['transport_safe_suffix_required_for_scripts'] = require_txt
    if require_txt:
        non_txt_entries = [row.get('zip_path', '') for row in delivery_entries if row.get('zip_path') and not row.get('zip_path', '').endswith('.txt')]
        checks['non_txt_delivery_entries'] = non_txt_entries
        if non_txt_entries:
            errors.append('delivery entries must use transport-safe .txt suffixes: ' + ', '.join(non_txt_entries))

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
