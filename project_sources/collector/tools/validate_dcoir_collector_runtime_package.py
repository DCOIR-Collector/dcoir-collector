#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json'
FUNCTION_PATTERN = re.compile(r'^\s*function\s+([-A-Za-z0-9_]+)\b')

def load_manifest(source_dir: Path) -> Dict:
    return json.loads((source_dir / 'project_sources' / 'collector' / 'manifests' / MANIFEST_NAME).read_text(encoding='utf-8'))

def normalize_function_name(name: str) -> str:
    return name.casefold()

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
            function_name = match.group(1)
            normalized_name = normalize_function_name(function_name)
            definitions.setdefault(normalized_name, []).append({
                'name': function_name,
                'normalized_name': normalized_name,
                'path': rel,
                'line': line_number,
                'load_order': load_order,
            })
    return definitions

def validate_unique_function_definitions(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    definitions = find_function_definitions(source_dir, manifest)
    duplicate_definitions = {name: rows for name, rows in definitions.items() if len(rows) > 1}
    checks['function_definition_count'] = sum(len(rows) for rows in definitions.values())
    checks['unique_function_count'] = len(definitions)
    checks['duplicate_function_count'] = len(duplicate_definitions)
    checks['duplicate_function_names'] = sorted(duplicate_definitions)
    checks['duplicate_function_original_names'] = {
        name: sorted({row['name'] for row in rows}) for name, rows in sorted(duplicate_definitions.items())
    }
    checks['duplicate_function_definitions'] = {
        name: rows for name, rows in sorted(duplicate_definitions.items())
    }
    if duplicate_definitions:
        errors.append(
            'duplicate function definitions are not allowed: '
            + ', '.join(sorted(duplicate_definitions))
        )

    if manifest.get('function_override_manifest'):
        errors.append('function_override_manifest is obsolete; collector functions must be defined once')

def extract_function_body(text: str, function_name: str) -> str:
    pattern = re.compile(r'^\s*function\s+' + re.escape(function_name) + r'\b', re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ''

    brace_start = text.find('{', match.end())
    if brace_start == -1:
        return ''

    depth = 0
    for index in range(brace_start, len(text)):
        char = text[index]
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[brace_start:index + 1]
    return text[brace_start:]

def validate_collect_metadata_report_write_ordering(source_dir: Path, checks: Dict[str, object], errors: List[str]) -> None:
    main_entry_rel = 'project_sources/collector/source/parts/DCOIR_Collector.05_Main_Entry.ps1'
    main_entry_path = source_dir / main_entry_rel
    metadata_checks: Dict[str, object] = {'path': main_entry_rel}
    checks['collect_metadata_report_write_ordering'] = metadata_checks
    if not main_entry_path.exists():
        metadata_checks['checked'] = False
        errors.append('collect metadata report source is missing: ' + main_entry_rel)
        return

    text = main_entry_path.read_text(encoding='utf-8', errors='ignore')
    metadata_marker = '$metadataText = New-MetadataReport -State $state -ToolMap $toolMap'
    write_marker = 'Write-ReportFile -Path $metadataReportPath -Text $metadataText'
    upload_summary_marker = '$state.UploadSummaryPath = $uploadArtifacts.UploadSummaryPath'
    analyst_overview_marker = '$state.AnalystOverviewPath = New-AnalystOverviewArtifact -State $state -Baseline $baseline'
    bundle_name_marker = '$bundleName = ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId)'
    bundle_path_marker = '$bundlePath = Join-Path $state.BundlesDir $bundleName'
    collect_bundle_marker = '$state.CollectBundlePath = $bundlePath'
    manifest_marker = 'New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json")'
    bundle_call_marker = 'New-BundleZip -BundlesDir $state.BundlesDir -BundleName $bundleName'

    metadata_positions = [match.start() for match in re.finditer(re.escape(metadata_marker), text)]
    write_positions = [match.start() for match in re.finditer(re.escape(write_marker), text)]
    upload_summary_pos = text.find(upload_summary_marker)
    analyst_overview_pos = text.find(analyst_overview_marker)
    bundle_name_pos = text.find(bundle_name_marker)
    bundle_path_pos = text.find(bundle_path_marker)
    collect_bundle_pos = text.find(collect_bundle_marker)
    manifest_pos = text.find(manifest_marker)
    bundle_call_pos = text.find(bundle_call_marker)

    metadata_checks['checked'] = True
    metadata_checks['metadata_report_call_count'] = len(metadata_positions)
    metadata_checks['metadata_report_write_count'] = len(write_positions)
    metadata_checks['upload_summary_before_metadata'] = bool(metadata_positions) and upload_summary_pos != -1 and upload_summary_pos < metadata_positions[0]
    metadata_checks['analyst_overview_before_metadata'] = bool(metadata_positions) and analyst_overview_pos != -1 and analyst_overview_pos < metadata_positions[0]
    metadata_checks['bundle_name_before_metadata'] = bool(metadata_positions) and bundle_name_pos != -1 and bundle_name_pos < metadata_positions[0]
    metadata_checks['bundle_path_before_metadata'] = bool(metadata_positions) and bundle_path_pos != -1 and bundle_path_pos < metadata_positions[0]
    metadata_checks['collect_bundle_path_before_metadata'] = bool(metadata_positions) and collect_bundle_pos != -1 and collect_bundle_pos < metadata_positions[0]
    metadata_checks['metadata_before_manifest'] = bool(metadata_positions) and manifest_pos != -1 and metadata_positions[0] < manifest_pos
    metadata_checks['metadata_write_before_manifest'] = bool(write_positions) and manifest_pos != -1 and write_positions[0] < manifest_pos
    metadata_checks['metadata_before_bundle'] = bool(metadata_positions) and bundle_call_pos != -1 and metadata_positions[0] < bundle_call_pos
    metadata_checks['metadata_write_before_bundle'] = bool(write_positions) and bundle_call_pos != -1 and write_positions[0] < bundle_call_pos
    metadata_checks['metadata_write_follows_metadata_call'] = bool(metadata_positions) and bool(write_positions) and metadata_positions[0] < write_positions[0]

    if len(metadata_positions) != 1:
        errors.append('collect mode must call New-MetadataReport exactly once after late-bound collect fields are populated')
    if len(write_positions) != 1:
        errors.append('collect mode must write the metadata report exactly once')
    for key in (
        'upload_summary_before_metadata',
        'analyst_overview_before_metadata',
        'bundle_name_before_metadata',
        'bundle_path_before_metadata',
        'collect_bundle_path_before_metadata',
        'metadata_before_manifest',
        'metadata_write_before_manifest',
        'metadata_before_bundle',
        'metadata_write_before_bundle',
        'metadata_write_follows_metadata_call',
    ):
        if not metadata_checks[key]:
            errors.append('collect metadata report write ordering check failed: ' + key)

def validate_collect_manifest_bundle_ordering(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    main_entry_rel = 'project_sources/collector/source/parts/DCOIR_Collector.05_Main_Entry.ps1'
    main_entry_path = source_dir / main_entry_rel
    ordering_checks: Dict[str, object] = {'path': main_entry_rel}
    checks['collect_manifest_bundle_ordering'] = ordering_checks
    if not main_entry_path.exists():
        ordering_checks['checked'] = False
        errors.append('collect manifest ordering source is missing: ' + main_entry_rel)
        return

    text = main_entry_path.read_text(encoding='utf-8', errors='ignore')
    manifest_marker = 'New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json")'
    bundle_name_marker = '$bundleName = ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId)'
    bundle_path_marker = '$bundlePath = Join-Path $state.BundlesDir $bundleName'
    state_path_marker = '$state.CollectBundlePath = $bundlePath'
    bundle_call_marker = 'New-BundleZip -BundlesDir $state.BundlesDir -BundleName $bundleName'

    manifest_call_count = text.count(manifest_marker)
    ordering_checks['checked'] = True
    ordering_checks['collect_manifest_call_count'] = manifest_call_count
    ordering_checks['collect_bundle_null_present'] = 'collect_bundle = $null' in text

    bundle_name_pos = text.find(bundle_name_marker)
    bundle_path_pos = text.find(bundle_path_marker)
    state_path_pos = text.find(state_path_marker)
    manifest_pos = text.find(manifest_marker)
    bundle_call_pos = text.find(bundle_call_marker)

    ordering_checks['bundle_name_precomputed_before_manifest'] = bundle_name_pos != -1 and bundle_name_pos < manifest_pos
    ordering_checks['bundle_path_precomputed_before_manifest'] = bundle_path_pos != -1 and bundle_path_pos < manifest_pos
    ordering_checks['state_collect_bundle_path_set_before_manifest'] = state_path_pos != -1 and state_path_pos < manifest_pos
    ordering_checks['manifest_written_before_bundle'] = manifest_pos != -1 and bundle_call_pos != -1 and manifest_pos < bundle_call_pos
    ordering_checks['bundle_call_uses_precomputed_name'] = bundle_call_pos != -1
    ordering_checks['manifest_in_bundle_inputs'] = (
        bundle_call_pos != -1 and '$collectManifest' in text[bundle_call_pos:bundle_call_pos + 1200]
    )

    if manifest_call_count != 1:
        errors.append('collect mode must write manifest_collect.json exactly once before bundle creation')
    if ordering_checks['collect_bundle_null_present']:
        errors.append('collect mode must not write manifest_collect.json with collect_bundle = $null')
    for key in (
        'bundle_name_precomputed_before_manifest',
        'bundle_path_precomputed_before_manifest',
        'state_collect_bundle_path_set_before_manifest',
        'manifest_written_before_bundle',
        'bundle_call_uses_precomputed_name',
        'manifest_in_bundle_inputs',
    ):
        if not ordering_checks[key]:
            errors.append('collect manifest/bundle ordering check failed: ' + key)

def validate_bundle_metadata_sync_terminates(source_dir: Path, checks: Dict[str, object], errors: List[str]) -> None:
    helper_rel = 'project_sources/collector/source/parts/DCOIR_Collector.04G_PR186_External_Review_Fixes.ps1'
    helper_path = source_dir / helper_rel
    sync_checks: Dict[str, object] = {'path': helper_rel}
    checks['bundle_metadata_sync_error_handling'] = sync_checks
    if not helper_path.exists():
        sync_checks['checked'] = False
        errors.append('bundle metadata sync helper source is missing: ' + helper_rel)
        return

    text = helper_path.read_text(encoding='utf-8', errors='ignore')
    sync_body = extract_function_body(text, 'Sync-CollectionMetadataCompanionArtifact')
    bundle_body = extract_function_body(text, 'New-BundleZip')
    catch_match = re.search(r'catch\s*{(?P<body>.*?)^\s*}', sync_body, re.DOTALL | re.MULTILINE)
    catch_body = catch_match.group('body') if catch_match else ''

    sync_checks['checked'] = True
    sync_checks['sync_function_present'] = bool(sync_body)
    sync_checks['bundle_function_present'] = bool(bundle_body)
    sync_checks['bundle_invokes_sync'] = 'Sync-CollectionMetadataCompanionArtifact' in bundle_body
    sync_checks['sync_catch_records_collector_error'] = 'Add-CollectorError' in catch_body
    sync_checks['sync_catch_throws_after_error'] = re.search(r'\bthrow\b', catch_body) is not None

    if not sync_checks['sync_function_present']:
        errors.append('Sync-CollectionMetadataCompanionArtifact function is missing')
    if not sync_checks['bundle_function_present']:
        errors.append('New-BundleZip function is missing')
    if not sync_checks['bundle_invokes_sync']:
        errors.append('New-BundleZip must synchronize collection metadata companions before compression')
    if not sync_checks['sync_catch_records_collector_error']:
        errors.append('metadata companion sync failures must be recorded with Add-CollectorError')
    if not sync_checks['sync_catch_throws_after_error']:
        errors.append('metadata companion sync failures must terminate bundle creation after recording the error')

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

    validate_unique_function_definitions(source_dir, manifest, checks, errors)
    validate_collect_metadata_report_write_ordering(source_dir, checks, errors)
    validate_collect_manifest_bundle_ordering(source_dir, manifest, checks, errors)
    validate_bundle_metadata_sync_terminates(source_dir, checks, errors)

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
