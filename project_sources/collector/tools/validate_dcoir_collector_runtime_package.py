#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
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

def mask_powershell_non_code(text: str) -> str:
    output: List[str] = []
    index = 0
    quote_char = ''
    block_comment = False
    here_string_end = ''
    at_line_start = True
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ''
        if here_string_end:
            if at_line_start and char == here_string_end and next_char == '@':
                output.extend((' ', ' '))
                here_string_end = ''
                index += 2
                at_line_start = False
                continue
            output.append('\n' if char == '\n' else ' ')
            at_line_start = (char == '\n')
            index += 1
            continue
        if block_comment:
            if char == '#' and next_char == '>':
                output.extend((' ', ' '))
                block_comment = False
                index += 2
                at_line_start = False
                continue
            output.append('\n' if char == '\n' else ' ')
            at_line_start = (char == '\n')
            index += 1
            continue
        if quote_char:
            if char == quote_char:
                if quote_char == "'" and index + 1 < len(text) and text[index + 1] == "'":
                    output.extend((' ', ' '))
                    index += 2
                    continue
                if quote_char == '"' and index > 0 and text[index - 1] == '`':
                    output.append(' ')
                    index += 1
                    continue
                quote_char = ''
            output.append('\n' if char == '\n' else ' ')
            at_line_start = (char == '\n')
            index += 1
            continue
        if char == '@' and next_char in ("'", '"'):
            output.extend((' ', ' '))
            here_string_end = next_char
            index += 2
            at_line_start = False
            continue
        if char == '<' and next_char == '#':
            output.extend((' ', ' '))
            block_comment = True
            index += 2
            at_line_start = False
            continue
        if char == '#':
            while index < len(text) and text[index] != '\n':
                output.append(' ')
                index += 1
            continue
        if char in ("'", '"'):
            quote_char = char
            output.append(' ')
            index += 1
            at_line_start = False
            continue
        output.append(char)
        at_line_start = (char == '\n')
        index += 1
    return ''.join(output)

def find_convert_to_json_calls(rel: str, text: str) -> List[Dict[str, object]]:
    command_pattern = re.compile(r'(?<![-.\w])(?:[-A-Za-z0-9_.]+\\)?ConvertTo-Json\b', re.IGNORECASE)
    clean_text = mask_powershell_non_code(text)
    calls: List[Dict[str, object]] = []
    for line_number, line in enumerate(clean_text.splitlines(), 1):
        if not command_pattern.search(line):
            continue
        calls.append({'path': rel, 'line': line_number, 'text': line.strip()})
    return calls

def run_json_policy_behavior_tests(source_dir: Path, core_rel: str) -> Dict[str, object]:
    result: Dict[str, object] = {
        'available': False,
        'status': 'skipped_powershell_unavailable',
        'preferred_target': 'windows_powershell_5_1',
        'shell_results': [],
    }
    shell_candidates = [
        ('windows_powershell_5_1', shutil.which('powershell') or shutil.which('powershell.exe')),
        ('pwsh', shutil.which('pwsh')),
    ]
    available_shells = [(label, path) for label, path in shell_candidates if path]
    if not available_shells:
        return result

    result['available'] = True
    core_path = (source_dir / core_rel).resolve()
    script = f"""
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Global:CollectorErrors = New-Object System.Collections.ArrayList
$Global:CollectorNotes = New-Object System.Collections.ArrayList
$Global:ErrorsLogPath = $null
. '{str(core_path).replace("'", "''")}'

function Assert-Condition {{
  param([bool]$Condition,[string]$Message)
  if (-not $Condition) {{ throw $Message }}
}}

$deep = [ordered]@{{ a = [ordered]@{{ b = [ordered]@{{ c = [ordered]@{{ d = [ordered]@{{ e = 'leaf' }} }} }} }} }}
$threw = $false
try {{
  Convert-ToCollectorJsonText -InputObject $deep -Depth 3 -Label 'behavior deep object' -ThrowOnTruncation | Out-Null
}} catch {{
  $threw = $true
}}
Assert-Condition $threw 'deep object truncation was not detected'
Assert-Condition ($Global:CollectorErrors.Count -ge 1) 'deep object truncation was not recorded'

$Global:CollectorErrors.Clear()
$legitimateEllipsis = [ordered]@{{ outer = [ordered]@{{ marker = '...' }} }}
Convert-ToCollectorJsonText -InputObject $legitimateEllipsis -Depth 5 -Label 'legitimate ellipsis' -ThrowOnTruncation | Out-Null
Assert-Condition ($Global:CollectorErrors.Count -eq 0) 'legitimate ellipsis string was treated as truncation'

$jsonl = Convert-ToCollectorJsonText -InputObject ([ordered]@{{ x = 1 }}) -Compress -AppendNewline -Label 'newline behavior'
Assert-Condition ($jsonl.EndsWith([Environment]::NewLine)) 'AppendNewline did not append the platform newline'
"""
    shell_results: List[Dict[str, object]] = []
    for label, shell_path in available_shells:
        with tempfile.NamedTemporaryFile('w', suffix='.ps1', encoding='utf-8', delete=False) as handle:
            handle.write(script)
            script_path = Path(handle.name)
        try:
            cmd = [shell_path, '-NoProfile']
            if label == 'pwsh':
                cmd.append('-NonInteractive')
            if label == 'windows_powershell_5_1':
                cmd.extend(['-ExecutionPolicy', 'Bypass'])
            cmd.extend(['-File', str(script_path)])
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        finally:
            script_path.unlink(missing_ok=True)
        shell_results.append({
            'target': label,
            'command': Path(shell_path).name,
            'status': 'passed' if completed.returncode == 0 else 'failed',
            'returncode': completed.returncode,
            'stdout': completed.stdout[-4000:],
            'stderr': completed.stderr[-4000:],
        })

    result['shell_results'] = shell_results
    failed_results = [row for row in shell_results if row['status'] == 'failed']
    windows_result = next((row for row in shell_results if row['target'] == 'windows_powershell_5_1'), None)
    if failed_results:
        result['status'] = 'failed'
    elif windows_result:
        result['status'] = 'passed'
    else:
        result['status'] = 'passed_without_windows_powershell_5_1'
    return result

def run_state_recursion_behavior_tests(source_dir: Path, core_rel: str) -> Dict[str, object]:
    result: Dict[str, object] = {
        'available': False,
        'status': 'skipped_powershell_unavailable',
        'preferred_target': 'windows_powershell_5_1',
        'shell_results': [],
    }
    shell_candidates = [
        ('windows_powershell_5_1', shutil.which('powershell') or shutil.which('powershell.exe')),
        ('pwsh', shutil.which('pwsh')),
    ]
    available_shells = [(label, path) for label, path in shell_candidates if path]
    if not available_shells:
        return result

    result['available'] = True
    core_path = (source_dir / core_rel).resolve()
    script = f"""
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Global:CollectorErrors = New-Object System.Collections.ArrayList
$Global:CollectorNotes = New-Object System.Collections.ArrayList
$Global:ErrorsLogPath = $null
. '{str(core_path).replace("'", "''")}'

function Assert-Condition {{
  param([bool]$Condition,[string]$Message)
  if (-not $Condition) {{ throw $Message }}
}}

$nested = [pscustomobject]@{{
  alpha = [ordered]@{{
    beta = @(
      [pscustomobject]@{{ gamma = 'leaf' }}
    )
  }}
}}
$converted = Convert-StateObjectToHashtable -InputObject $nested -Depth 8
Assert-Condition ($converted -is [hashtable]) 'converted root is not a hashtable'
Assert-Condition ($converted.alpha -is [hashtable]) 'nested dictionary was not preserved as hashtable'
Assert-Condition ($converted.alpha.beta[0].gamma -eq 'leaf') 'nested array/object value was not preserved'

$tooDeep = [ordered]@{{ a = [ordered]@{{ b = [ordered]@{{ c = [ordered]@{{ d = 'leaf' }} }} }} }}
$threw = $false
$message = ''
try {{
  Convert-StateObjectToHashtable -InputObject $tooDeep -Depth 3 | Out-Null
}} catch {{
  $threw = $true
  $message = [string]$_.Exception.Message
}}
Assert-Condition $threw 'state conversion depth overflow was not rejected'
Assert-Condition ($message -like '*Convert-StateObjectToHashtable*') 'depth error did not identify the converter'
Assert-Condition ($message -like '*depth 3*') 'depth error did not include the configured depth'
Assert-Condition ($message -like '*$.a.b.c*') 'depth error did not include the recursive path'
"""
    shell_results: List[Dict[str, object]] = []
    for label, shell_path in available_shells:
        with tempfile.NamedTemporaryFile('w', suffix='.ps1', encoding='utf-8', delete=False) as handle:
            handle.write(script)
            script_path = Path(handle.name)
        try:
            cmd = [shell_path, '-NoProfile']
            if label == 'pwsh':
                cmd.append('-NonInteractive')
            if label == 'windows_powershell_5_1':
                cmd.extend(['-ExecutionPolicy', 'Bypass'])
            cmd.extend(['-File', str(script_path)])
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        finally:
            script_path.unlink(missing_ok=True)
        shell_results.append({
            'target': label,
            'command': Path(shell_path).name,
            'status': 'passed' if completed.returncode == 0 else 'failed',
            'returncode': completed.returncode,
            'stdout': completed.stdout[-4000:],
            'stderr': completed.stderr[-4000:],
        })

    result['shell_results'] = shell_results
    failed_results = [row for row in shell_results if row['status'] == 'failed']
    windows_result = next((row for row in shell_results if row['target'] == 'windows_powershell_5_1'), None)
    if failed_results:
        result['status'] = 'failed'
    elif windows_result:
        result['status'] = 'passed'
    else:
        result['status'] = 'passed_without_windows_powershell_5_1'
    return result

def validate_state_recursion_policy(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    recursion_checks: Dict[str, object] = {}
    checks['state_recursion_policy'] = recursion_checks

    source_rels = [manifest['collector_wrapper_source']] + manifest.get('collector_part_files', [])
    source_text_by_rel: Dict[str, str] = {}
    for rel in source_rels:
        path = source_dir / rel
        if path.exists():
            source_text_by_rel[rel] = path.read_text(encoding='utf-8', errors='ignore')

    core_rel = 'project_sources/collector/source/parts/DCOIR_Collector.01_Core_State_And_Utilities.ps1'
    parallel_rel = 'project_sources/collector/source/parts/DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1'
    main_entry_rel = 'project_sources/collector/source/parts/DCOIR_Collector.05_Main_Entry.ps1'

    core_text = source_text_by_rel.get(core_rel, '')
    parallel_text = source_text_by_rel.get(parallel_rel, '')
    main_entry_text = source_text_by_rel.get(main_entry_rel, '')
    converter_body = extract_function_body(core_text, 'Convert-StateObjectToHashtable')
    worker_sentinel_body = extract_function_body(parallel_text, 'Test-WorkerJsonContainsEllipsisSentinel')

    recursion_checks['convert_state_object_to_hashtable_present'] = bool(converter_body)
    recursion_checks['converter_default_depth_20'] = '[int]$Depth = 20' in converter_body
    recursion_checks['converter_tracks_current_depth'] = '[int]$CurrentDepth = 0' in converter_body
    recursion_checks['converter_tracks_path'] = "[string]$Path = '$'" in converter_body
    recursion_checks['converter_throws_at_depth_limit'] = 'Convert-StateObjectToHashtable exceeded configured depth {0} at path {1}.' in converter_body
    recursion_checks['converter_dictionary_recursion_passes_depth_path'] = (
        'Convert-StateObjectToHashtable -InputObject $InputObject[$key] -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in converter_body
    )
    recursion_checks['converter_enumerable_recursion_passes_depth_path'] = (
        'Convert-StateObjectToHashtable -InputObject $item -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in converter_body
    )
    recursion_checks['converter_property_recursion_passes_depth_path'] = (
        'Convert-StateObjectToHashtable -InputObject $prop.Value -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in converter_body
    )
    recursion_checks['load_state_uses_default_converter_policy'] = 'Convert-StateObjectToHashtable -InputObject $loaded' in main_entry_text

    recursion_checks['worker_sentinel_present'] = bool(worker_sentinel_body)
    recursion_checks['worker_sentinel_default_max_depth_25'] = '[int]$MaxDepth = 25' in worker_sentinel_body
    recursion_checks['worker_sentinel_tracks_current_depth'] = '[int]$CurrentDepth = 0' in worker_sentinel_body
    recursion_checks['worker_sentinel_tracks_path'] = "[string]$Path = '$'" in worker_sentinel_body
    recursion_checks['worker_sentinel_throws_at_depth_limit'] = 'Parallel worker result JSON sentinel scan exceeded configured depth {0} at path {1}.' in worker_sentinel_body
    recursion_checks['worker_sentinel_enumerable_recursion_passes_depth_path'] = (
        'Test-WorkerJsonContainsEllipsisSentinel -InputObject $item -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in worker_sentinel_body
    )
    recursion_checks['worker_sentinel_property_recursion_passes_depth_path'] = (
        'Test-WorkerJsonContainsEllipsisSentinel -InputObject $prop.Value -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in worker_sentinel_body
    )
    recursion_checks['state_recursion_behavior_tests'] = run_state_recursion_behavior_tests(source_dir, core_rel)

    for key in (
        'convert_state_object_to_hashtable_present',
        'converter_default_depth_20',
        'converter_tracks_current_depth',
        'converter_tracks_path',
        'converter_throws_at_depth_limit',
        'converter_dictionary_recursion_passes_depth_path',
        'converter_enumerable_recursion_passes_depth_path',
        'converter_property_recursion_passes_depth_path',
        'load_state_uses_default_converter_policy',
        'worker_sentinel_present',
        'worker_sentinel_default_max_depth_25',
        'worker_sentinel_tracks_current_depth',
        'worker_sentinel_tracks_path',
        'worker_sentinel_throws_at_depth_limit',
        'worker_sentinel_enumerable_recursion_passes_depth_path',
        'worker_sentinel_property_recursion_passes_depth_path',
    ):
        if not recursion_checks[key]:
            errors.append('collector state recursion policy check failed: ' + key)
    if recursion_checks['state_recursion_behavior_tests']['status'] == 'failed':
        errors.append('collector state recursion policy behavior tests failed')

def validate_collect_metadata_report_write_ordering(source_dir: Path, checks: Dict[str, object], errors: List[str]) -> None:
    main_entry_rel = 'project_sources/collector/source/parts/DCOIR_Collector.05_Main_Entry.ps1'
    helper_rel = 'project_sources/collector/source/parts/DCOIR_Collector.04H_PR212_Metadata_Finalization_Fixes.ps1'
    main_entry_path = source_dir / main_entry_rel
    helper_path = source_dir / helper_rel
    metadata_checks: Dict[str, object] = {'path': main_entry_rel, 'helper_path': helper_rel}
    checks['collect_metadata_report_write_ordering'] = metadata_checks
    if not main_entry_path.exists():
        metadata_checks['checked'] = False
        errors.append('collect metadata report source is missing: ' + main_entry_rel)
        return
    if not helper_path.exists():
        metadata_checks['checked'] = False
        errors.append('collect metadata late-bound helper source is missing: ' + helper_rel)
        return

    text = main_entry_path.read_text(encoding='utf-8', errors='ignore')
    helper_text = helper_path.read_text(encoding='utf-8', errors='ignore')
    metadata_marker = '$metadataText = New-MetadataReport -State $state -ToolMap $toolMap'
    write_marker = 'Write-ReportFile -Path $metadataReportPath -Text $metadataText'
    placeholder_marker = 'New-Item -ItemType File -Path $metadataReportPath'
    upload_artifacts_marker = '$uploadArtifacts = New-CollectUploadArtifactsWithLateMetadataReport -State $state -Baseline $baseline'
    upload_summary_marker = '$state.UploadSummaryPath = $uploadArtifacts.UploadSummaryPath'
    upload_budget_marker = '$state.UploadBudgetManifestPath = $uploadArtifacts.UploadManifestPath'
    default_upload_set_marker = '$state.DefaultGeminiUploadSetStatus = $uploadArtifacts.DefaultSetStatus'
    upload_safe_chunk_marker = '$state.UploadSafeChunkManifestPath = $uploadArtifacts.UploadSafeChunkManifestPath'
    analyst_overview_marker = '$state.AnalystOverviewPath = New-AnalystOverviewArtifactWithLateMetadataReport -State $state -Baseline $baseline'
    bundle_name_marker = '$bundleName = ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId)'
    bundle_path_marker = '$bundlePath = Join-Path $state.BundlesDir $bundleName'
    collect_bundle_marker = '$state.CollectBundlePath = $bundlePath'
    manifest_marker = 'New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json")'
    bundle_call_marker = 'New-BundleZip -BundlesDir $state.BundlesDir -BundleName $bundleName'

    metadata_positions = [match.start() for match in re.finditer(re.escape(metadata_marker), text)]
    write_positions = [match.start() for match in re.finditer(re.escape(write_marker), text)]
    upload_artifacts_pos = text.find(upload_artifacts_marker)
    upload_summary_pos = text.find(upload_summary_marker)
    upload_budget_pos = text.find(upload_budget_marker)
    default_upload_set_pos = text.find(default_upload_set_marker)
    upload_safe_chunk_pos = text.find(upload_safe_chunk_marker)
    analyst_overview_pos = text.find(analyst_overview_marker)
    bundle_name_pos = text.find(bundle_name_marker)
    bundle_path_pos = text.find(bundle_path_marker)
    collect_bundle_pos = text.find(collect_bundle_marker)
    manifest_pos = text.find(manifest_marker)
    bundle_call_pos = text.find(bundle_call_marker)

    metadata_checks['checked'] = True
    metadata_checks['metadata_report_call_count'] = len(metadata_positions)
    metadata_checks['metadata_report_write_count'] = len(write_positions)
    metadata_checks['placeholder_metadata_file_absent'] = placeholder_marker not in text
    metadata_checks['late_bound_upload_builder_used'] = upload_artifacts_pos != -1
    metadata_checks['late_bound_overview_builder_used'] = analyst_overview_pos != -1
    metadata_checks['old_upload_builder_not_used_in_collect'] = 'New-CollectUploadArtifacts -State $state -Baseline $baseline' not in text
    metadata_checks['old_overview_builder_not_used_in_collect'] = 'New-AnalystOverviewArtifact -State $state -Baseline $baseline' not in text
    metadata_checks['upload_artifacts_before_metadata'] = bool(metadata_positions) and upload_artifacts_pos != -1 and upload_artifacts_pos < metadata_positions[0]
    metadata_checks['upload_summary_before_metadata'] = bool(metadata_positions) and upload_summary_pos != -1 and upload_summary_pos < metadata_positions[0]
    metadata_checks['upload_budget_manifest_before_metadata'] = bool(metadata_positions) and upload_budget_pos != -1 and upload_budget_pos < metadata_positions[0]
    metadata_checks['default_upload_set_status_before_metadata'] = bool(metadata_positions) and default_upload_set_pos != -1 and default_upload_set_pos < metadata_positions[0]
    metadata_checks['upload_safe_chunk_manifest_before_metadata'] = bool(metadata_positions) and upload_safe_chunk_pos != -1 and upload_safe_chunk_pos < metadata_positions[0]
    metadata_checks['analyst_overview_before_metadata'] = bool(metadata_positions) and analyst_overview_pos != -1 and analyst_overview_pos < metadata_positions[0]
    metadata_checks['bundle_name_before_metadata'] = bool(metadata_positions) and bundle_name_pos != -1 and bundle_name_pos < metadata_positions[0]
    metadata_checks['bundle_path_before_metadata'] = bool(metadata_positions) and bundle_path_pos != -1 and bundle_path_pos < metadata_positions[0]
    metadata_checks['collect_bundle_path_before_metadata'] = bool(metadata_positions) and collect_bundle_pos != -1 and collect_bundle_pos < metadata_positions[0]
    metadata_checks['metadata_before_manifest'] = bool(metadata_positions) and manifest_pos != -1 and metadata_positions[0] < manifest_pos
    metadata_checks['metadata_write_before_manifest'] = bool(write_positions) and manifest_pos != -1 and write_positions[0] < manifest_pos
    metadata_checks['metadata_before_bundle'] = bool(metadata_positions) and bundle_call_pos != -1 and metadata_positions[0] < bundle_call_pos
    metadata_checks['metadata_write_before_bundle'] = bool(write_positions) and bundle_call_pos != -1 and write_positions[0] < bundle_call_pos
    metadata_checks['metadata_write_follows_metadata_call'] = bool(metadata_positions) and bool(write_positions) and metadata_positions[0] < write_positions[0]
    metadata_checks['late_bound_metadata_manifest_flag'] = 'metadata_report_late_bound_after_upload_artifacts = $true' in helper_text
    metadata_checks['late_bound_recommended_row_flag'] = 'late_bound_after_upload_artifacts = [bool]$isLateBoundMetadata' in helper_text
    metadata_checks['late_bound_metadata_not_budgeted'] = 'if (-not $isLateBoundMetadata) { $safeTotal += $sizeKB }' in helper_text
    metadata_checks['late_bound_metadata_not_resolved'] = (
        'if ($pathExists)' in helper_text
        and 'Resolve-Path -LiteralPath $pathText' in helper_text
        and '$pathText' in helper_text
    )
    metadata_checks['overview_includes_late_bound_metadata_path'] = "($pair.Label -eq 'METADATA_REPORT_PATH')" in helper_text

    if len(metadata_positions) != 1:
        errors.append('collect mode must call New-MetadataReport exactly once after late-bound collect fields are populated')
    if len(write_positions) != 1:
        errors.append('collect mode must write the metadata report exactly once')
    for key in (
        'placeholder_metadata_file_absent',
        'late_bound_upload_builder_used',
        'late_bound_overview_builder_used',
        'old_upload_builder_not_used_in_collect',
        'old_overview_builder_not_used_in_collect',
        'upload_artifacts_before_metadata',
        'upload_summary_before_metadata',
        'upload_budget_manifest_before_metadata',
        'default_upload_set_status_before_metadata',
        'upload_safe_chunk_manifest_before_metadata',
        'analyst_overview_before_metadata',
        'bundle_name_before_metadata',
        'bundle_path_before_metadata',
        'collect_bundle_path_before_metadata',
        'metadata_before_manifest',
        'metadata_write_before_manifest',
        'metadata_before_bundle',
        'metadata_write_before_bundle',
        'metadata_write_follows_metadata_call',
        'late_bound_metadata_manifest_flag',
        'late_bound_recommended_row_flag',
        'late_bound_metadata_not_budgeted',
        'late_bound_metadata_not_resolved',
        'overview_includes_late_bound_metadata_path',
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

def validate_json_serialization_policy(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    policy_checks: Dict[str, object] = {}
    checks['json_serialization_policy'] = policy_checks

    source_rels = [manifest['collector_wrapper_source']] + manifest.get('collector_part_files', [])
    source_text_by_rel: Dict[str, str] = {}
    for rel in source_rels:
        path = source_dir / rel
        if path.exists():
            source_text_by_rel[rel] = path.read_text(encoding='utf-8', errors='ignore')

    core_rel = 'project_sources/collector/source/parts/DCOIR_Collector.01_Core_State_And_Utilities.ps1'
    reports_rel = 'project_sources/collector/source/parts/DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1'
    parallel_rel = 'project_sources/collector/source/parts/DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1'
    manifest_rel = 'project_sources/collector/source/parts/DCOIR_Collector.04G_PR186_External_Review_Fixes.ps1'

    core_text = source_text_by_rel.get(core_rel, '')
    reports_text = source_text_by_rel.get(reports_rel, '')
    parallel_text = source_text_by_rel.get(parallel_rel, '')
    manifest_text = source_text_by_rel.get(manifest_rel, '')

    for function_name in (
        'Add-CollectorJsonEllipsisPaths',
        'Get-CollectorJsonEllipsisPathSet',
        'Add-CollectorJsonDepthRiskPaths',
        'Get-CollectorJsonDepthRiskPathSet',
        'Convert-ToCollectorJsonText',
    ):
        policy_checks[f'{function_name}_present'] = bool(extract_function_body(core_text, function_name))
        if not policy_checks[f'{function_name}_present']:
            errors.append(f'collector JSON serialization helper is missing: {function_name}')

    policy_checks['shared_helper_default_depth_20'] = '[int]$Depth = 20' in extract_function_body(core_text, 'Convert-ToCollectorJsonText')
    policy_checks['shared_helper_checks_source_depth_risks'] = 'Get-CollectorJsonDepthRiskPathSet -InputObject $InputObject -MaxDepth $Depth' in extract_function_body(core_text, 'Convert-ToCollectorJsonText')
    policy_checks['shared_helper_parses_emitted_json'] = 'ConvertFrom-Json -ErrorAction Stop' in extract_function_body(core_text, 'Convert-ToCollectorJsonText')
    policy_checks['shared_helper_compares_source_ellipsis_paths'] = '$sourceEllipsis.ContainsKey($_)' in extract_function_body(core_text, 'Convert-ToCollectorJsonText')
    policy_checks['shared_helper_records_collector_error'] = 'Add-CollectorError $message' in extract_function_body(core_text, 'Convert-ToCollectorJsonText')
    policy_checks['shared_helper_can_throw'] = 'if ($ThrowOnTruncation) { throw $message }' in extract_function_body(core_text, 'Convert-ToCollectorJsonText')
    policy_checks['save_state_uses_shared_helper'] = "Convert-ToCollectorJsonText -InputObject $State -Label 'state.json' -ThrowOnTruncation" in core_text
    policy_checks['step_log_uses_shared_helper'] = "Convert-ToCollectorJsonText -InputObject $obj -Compress -Label 'execution step JSONL'" in core_text
    policy_checks['safe_json_uses_shared_helper'] = "Convert-ToCollectorJsonText -InputObject $InputObject -Label 'safe JSON artifact' -AppendNewline -ThrowOnTruncation" in reports_text
    policy_checks['manifest_uses_shared_helper'] = "Convert-ToCollectorJsonText -InputObject $manifest -Label 'manifest JSON' -ThrowOnTruncation" in manifest_text
    policy_checks['worker_uses_depth_20'] = '$workerJson = $workerResult | ConvertTo-Json -Depth 20 -ErrorAction Stop' in parallel_text
    policy_checks['worker_parses_and_checks_sentinel'] = (
        'ConvertFrom-Json -ErrorAction Stop' in parallel_text
        and 'Test-WorkerJsonContainsEllipsisSentinel' in parallel_text
        and 'Parallel worker result JSON' in parallel_text
    )
    policy_checks['shared_helper_behavior_tests'] = run_json_policy_behavior_tests(source_dir, core_rel)

    for key in (
        'shared_helper_default_depth_20',
        'shared_helper_checks_source_depth_risks',
        'shared_helper_parses_emitted_json',
        'shared_helper_compares_source_ellipsis_paths',
        'shared_helper_records_collector_error',
        'shared_helper_can_throw',
        'save_state_uses_shared_helper',
        'step_log_uses_shared_helper',
        'safe_json_uses_shared_helper',
        'manifest_uses_shared_helper',
        'worker_uses_depth_20',
        'worker_parses_and_checks_sentinel',
    ):
        if not policy_checks[key]:
            errors.append('collector JSON serialization policy check failed: ' + key)
    if policy_checks['shared_helper_behavior_tests']['status'] == 'failed':
        errors.append('collector JSON serialization policy behavior tests failed')

    approved_raw_calls = {
        (core_rel, '$json = $InputObject | ConvertTo-Json @jsonArgs'),
        (parallel_rel, '$workerJson = $workerResult | ConvertTo-Json -Depth 20 -ErrorAction Stop'),
    }
    raw_calls: List[Dict[str, object]] = []
    unapproved_raw_calls: List[Dict[str, object]] = []
    for rel, text in source_text_by_rel.items():
        for row in find_convert_to_json_calls(rel, text):
            raw_calls.append(row)
            if (rel, row['text']) not in approved_raw_calls:
                unapproved_raw_calls.append(row)

    policy_checks['raw_convert_to_json_calls'] = raw_calls
    policy_checks['raw_convert_to_json_detector'] = 'broad_unqualified_or_module_qualified_command_scan_with_comment_stripping'
    policy_checks['unapproved_raw_convert_to_json_calls'] = unapproved_raw_calls
    policy_checks['unapproved_raw_convert_to_json_absent'] = len(unapproved_raw_calls) == 0
    if unapproved_raw_calls:
        errors.append(
            'collector source must route JSON serialization through the approved policy helpers; unapproved raw ConvertTo-Json calls: '
            + ', '.join(f"{row['path']}:{row['line']}" for row in unapproved_raw_calls)
        )

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
    validate_json_serialization_policy(source_dir, manifest, checks, errors)
    validate_state_recursion_policy(source_dir, manifest, checks, errors)

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
