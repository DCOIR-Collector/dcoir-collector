#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json'
FUNCTION_PATTERN = re.compile(r'^\s*function\s+([-A-Za-z0-9_]+)\b')
VALID_OVERRIDE_STATUS = {'long_term', 'temporary'}

def load_manifest(source_dir: Path) -> Dict:
    return json.loads((source_dir / 'project_sources' / 'collector' / 'manifests' / MANIFEST_NAME).read_text(encoding='utf-8'))

def find_function_definitions(source_dir: Path, manifest: Dict) -> Dict[str, List[Dict[str, object]]]:
    source_rels = [manifest['collector_wrapper_source']] + manifest.get('collector_part_files', [])
    definitions: Dict[str, List[Dict[str, object]]] = {}
    for load_order, rel in enumerate(source_rels):
        path = source_dir / rel
        if not path.exists():
            continue
        for line_number, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
            match = FUNCTION_PATTERN.match(line)
            if not match:
                continue
            definitions.setdefault(match.group(1), []).append({
                'path': rel,
                'line': line_number,
                'load_order': load_order,
            })
    return definitions

def validate_function_override_manifest(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    definitions = find_function_definitions(source_dir, manifest)
    duplicate_definitions = {name: rows for name, rows in definitions.items() if len(rows) > 1}
    actual_duplicate_names = set(duplicate_definitions)
    checks['duplicate_function_count'] = len(actual_duplicate_names)
    checks['duplicate_function_names'] = sorted(actual_duplicate_names)

    override_manifest_rel = manifest.get('function_override_manifest')
    checks['function_override_manifest'] = override_manifest_rel
    if not override_manifest_rel:
        if actual_duplicate_names:
            errors.append('function_override_manifest is required when collector source allows duplicate function definitions')
        return

    override_manifest_path = source_dir / override_manifest_rel
    checks['function_override_manifest_present'] = override_manifest_path.exists()
    if not override_manifest_path.exists():
        errors.append('function_override_manifest references missing file: ' + override_manifest_rel)
        return

    try:
        override_manifest = json.loads(override_manifest_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        errors.append(f'function_override_manifest is not valid JSON: {override_manifest_rel}: {exc}')
        return

    checks['function_override_manifest_schema'] = override_manifest.get('schema_version')
    if override_manifest.get('schema_version') != 'dcoir_collector_function_override_manifest_v1':
        errors.append('function_override_manifest schema_version must be dcoir_collector_function_override_manifest_v1')

    entries = override_manifest.get('overrides')
    if not isinstance(entries, list):
        errors.append('function_override_manifest overrides must be a list')
        entries = []

    manifest_names: set[str] = set()
    duplicate_manifest_names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append('function_override_manifest overrides entries must be objects')
            continue

        function_name = entry.get('function_name')
        if not isinstance(function_name, str) or not function_name.strip():
            errors.append('function_override_manifest override entry missing function_name')
            continue
        if function_name in manifest_names:
            duplicate_manifest_names.add(function_name)
        manifest_names.add(function_name)

        if not isinstance(entry.get('rationale'), str) or not entry.get('rationale', '').strip():
            errors.append(f'override {function_name} must include a non-empty rationale')
        if entry.get('override_status') not in VALID_OVERRIDE_STATUS:
            errors.append(f'override {function_name} override_status must be one of: {", ".join(sorted(VALID_OVERRIDE_STATUS))}')

        actual_rows = duplicate_definitions.get(function_name)
        if actual_rows is None:
            errors.append(f'override {function_name} is documented but is not duplicated in collector source')
            continue

        manifest_rows = entry.get('definitions')
        if not isinstance(manifest_rows, list) or len(manifest_rows) != len(actual_rows):
            errors.append(f'override {function_name} definitions must contain exactly {len(actual_rows)} rows')
            continue

        malformed_rows = [row for row in manifest_rows if not isinstance(row, dict)]
        if malformed_rows:
            errors.append(f'override {function_name} definitions entries must be objects')
            continue

        for expected, documented in zip(actual_rows, manifest_rows):
            if documented.get('path') != expected['path'] or documented.get('line') != expected['line'] or documented.get('load_order') != expected['load_order']:
                errors.append(
                    f'override {function_name} definition drift: expected '
                    f'{expected["path"]}:{expected["line"]} load_order {expected["load_order"]}'
                )
            role = documented.get('role')
            expected_role = 'active' if expected is actual_rows[-1] else 'superseded'
            if role != expected_role:
                errors.append(f'override {function_name} definition role must be {expected_role} for {expected["path"]}:{expected["line"]}')

        active_definition = entry.get('active_definition')
        if not isinstance(active_definition, dict):
            errors.append(f'override {function_name} active_definition must be an object')
            continue
        active_row = actual_rows[-1]
        if active_definition.get('path') != active_row['path'] or active_definition.get('line') != active_row['line']:
            errors.append(f'override {function_name} active_definition must be {active_row["path"]}:{active_row["line"]}')

    if duplicate_manifest_names:
        errors.append('function_override_manifest contains duplicate override entries: ' + ', '.join(sorted(duplicate_manifest_names)))

    undocumented = sorted(actual_duplicate_names - manifest_names)
    stale = sorted(manifest_names - actual_duplicate_names)
    checks['undocumented_duplicate_functions'] = undocumented
    checks['stale_override_manifest_entries'] = stale
    if undocumented:
        errors.append('undocumented duplicate functions: ' + ', '.join(undocumented))
    if stale:
        errors.append('stale override manifest entries: ' + ', '.join(stale))

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

    validate_function_override_manifest(source_dir, manifest, checks, errors)

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
