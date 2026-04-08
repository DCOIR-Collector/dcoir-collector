#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json.txt'
EXPECTED_PARTS = [
  'DCOIR_Collector.01_Core_State_And_Utilities.ps1',
  'DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1',
  'DCOIR_Collector.03A_Enrich_Session_State.ps1',
  'DCOIR_Collector.03B_Enrich_Actions_Review.ps1',
  'DCOIR_Collector.03C_Enrich_Actions_Retrieval.ps1',
  'DCOIR_Collector.04_Quick_Interface_And_Output.ps1',
  'DCOIR_Collector.05_Main_Entry.ps1',
]


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
    if manifest.get('source_strategy') != 'compile_single_runtime_then_package':
        errors.append('source_strategy must be compile_single_runtime_then_package for the collector delivery package')

    required_files = manifest.get('required_files', [])
    missing_required = [rel for rel in required_files if not (source_dir / rel).exists()]
    checks['required_files_present'] = len(missing_required) == 0
    checks['missing_required_files'] = missing_required
    if missing_required:
        errors.append('missing required files: ' + ', '.join(missing_required))

    wrapper_source = manifest.get('collector_wrapper_source')
    harness_source = manifest.get('harness_source')
    part_files = list(manifest.get('collector_part_files', []))
    checks['collector_wrapper_source'] = wrapper_source
    checks['harness_source'] = harness_source
    checks['collector_part_file_count'] = len(part_files)
    checks['collector_part_files'] = part_files

    expected_part_files = [f'project_sources/collector_parts/{name}' for name in EXPECTED_PARTS]
    checks['expected_collector_part_file_count'] = len(expected_part_files)
    checks['collector_part_set_complete'] = sorted(part_files) == sorted(expected_part_files)
    if sorted(part_files) != sorted(expected_part_files):
        errors.append('collector_part_files does not match the full expected maintained source-part set')

    compiled_runtime_name = manifest.get('compiled_runtime_name')
    checks['compiled_runtime_name'] = compiled_runtime_name
    if compiled_runtime_name != 'DCOIR_Collector.ps1':
        errors.append('compiled_runtime_name must be DCOIR_Collector.ps1')

    delivery_entries = manifest.get('delivery_zip_entries', [])
    checks['delivery_entry_count'] = len(delivery_entries)
    if len(delivery_entries) != 2:
        errors.append('delivery_zip_entries must contain exactly the compiled collector and the harness')

    zip_paths = [row.get('zip_path', '') for row in delivery_entries]
    duplicate_zip_paths = sorted({zp for zp in zip_paths if zp and zip_paths.count(zp) > 1})
    checks['duplicate_zip_paths'] = duplicate_zip_paths
    if duplicate_zip_paths:
        errors.append('delivery_zip_entries contains duplicate zip_path values: ' + ', '.join(duplicate_zip_paths))

    expected_delivery_names = {'DCOIR_Collector.ps1.txt', 'run_DCOIR_Tests.ps1.txt'}
    actual_delivery_names = {Path(zp).name for zp in zip_paths if zp}
    checks['expected_delivery_names_present'] = expected_delivery_names.issubset(actual_delivery_names)
    checks['actual_delivery_names'] = sorted(actual_delivery_names)
    if not expected_delivery_names.issubset(actual_delivery_names):
        errors.append('delivery package must include DCOIR_Collector.ps1.txt and run_DCOIR_Tests.ps1.txt')

    delivery_rules = manifest.get('delivery_rules', {})
    checks['transport_safe_suffix_required_for_scripts'] = bool(delivery_rules.get('transport_safe_suffix_required_for_scripts'))
    checks['script_suffix'] = delivery_rules.get('script_suffix')
    checks['pre_runtime_action'] = delivery_rules.get('pre_runtime_action')
    if delivery_rules.get('script_suffix') != '.txt':
        errors.append('delivery_rules.script_suffix must be .txt')

    non_txt_delivery_entries = [row.get('zip_path', '') for row in delivery_entries if not row.get('zip_path', '').endswith('.ps1.txt')]
    checks['non_txt_delivery_entries'] = non_txt_delivery_entries
    if non_txt_delivery_entries:
        errors.append('delivery entries must use transport-safe .ps1.txt names: ' + ', '.join(non_txt_delivery_entries))

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
