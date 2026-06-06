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
FUNCTION_PATTERN = re.compile(r'^\s*function\s+([-A-Za-z0-9_]+)\b', re.MULTILINE)


def load_manifest(source_dir: Path) -> Dict:
    return json.loads((source_dir / 'project_sources' / 'collector' / 'manifests' / MANIFEST_NAME).read_text(encoding='utf-8'))


def normalize_function_name(name: str) -> str:
    return name.casefold()


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def load_manifest_source_texts(source_dir: Path, manifest: Dict) -> Dict[str, str]:
    rels = [manifest['collector_wrapper_source']] + manifest.get('collector_part_files', [])
    return {rel: read_text(source_dir / rel) for rel in rels if (source_dir / rel).exists()}


def get_combined_source_text(source_text_by_rel: Dict[str, str]) -> str:
    return '\n'.join(source_text_by_rel.values())


def find_function_definitions(source_dir: Path, manifest: Dict) -> Dict[str, List[Dict[str, object]]]:
    definitions: Dict[str, List[Dict[str, object]]] = {}
    for load_order, rel in enumerate([manifest['collector_wrapper_source']] + manifest.get('collector_part_files', [])):
        text = read_text(source_dir / rel)
        for line_number, line in enumerate(text.splitlines(), 1):
            match = re.match(r'^\s*function\s+([-A-Za-z0-9_]+)\b', line)
            if not match:
                continue
            name = match.group(1)
            normalized = normalize_function_name(name)
            definitions.setdefault(normalized, []).append({
                'name': name,
                'normalized_name': normalized,
                'path': rel,
                'line': line_number,
                'load_order': load_order,
            })
    return definitions


def extract_function_body(text: str, function_name: str) -> str:
    match = re.search(r'^\s*function\s+' + re.escape(function_name) + r'\b', text, re.MULTILINE)
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
            at_line_start = char == '\n'
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
            at_line_start = char == '\n'
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
            at_line_start = char == '\n'
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
        at_line_start = char == '\n'
        index += 1
    return ''.join(output)


def find_convert_to_json_calls(rel: str, text: str) -> List[Dict[str, object]]:
    clean_text = mask_powershell_non_code(text)
    command_pattern = re.compile(r'(?<![-.\w])(?:[-A-Za-z0-9_.]+\\)?ConvertTo-Json\b', re.IGNORECASE)
    return [
        {'path': rel, 'line': line_number, 'text': line.strip()}
        for line_number, line in enumerate(clean_text.splitlines(), 1)
        if command_pattern.search(line)
    ]


def build_dot_source_lines_for_functions(source_dir: Path, manifest: Dict, function_names: List[str]) -> str:
    targets = {normalize_function_name(name) for name in function_names}
    rels: List[str] = []
    for rel in manifest.get('collector_part_files', []):
        text = read_text(source_dir / rel)
        if any(normalize_function_name(match.group(1)) in targets for match in FUNCTION_PATTERN.finditer(text)):
            rels.append(rel)
    return '\n'.join(". '{0}'".format(str((source_dir / rel).resolve()).replace("'", "''")) for rel in rels)


def probe_powershell_behavior_shell(shell_path: str, requested_label: str) -> Dict[str, object]:
    result: Dict[str, object] = {
        'path': shell_path,
        'command': Path(shell_path).name,
        'requested_label': requested_label,
        'target': requested_label if requested_label == 'pwsh' else 'powershell_unclassified',
        'edition': '',
        'version': '',
    }
    probe_script = "$PSVersionTable.PSEdition + '|' + $PSVersionTable.PSVersion.ToString()"
    try:
        completed = subprocess.run(
            [shell_path, '-NoProfile', '-Command', probe_script],
            capture_output=True,
            text=True,
            timeout=20,
        )
        result['probe_returncode'] = completed.returncode
        result['probe_stdout'] = completed.stdout[-1000:]
        result['probe_stderr'] = completed.stderr[-1000:]
        if completed.returncode == 0:
            parts = next((line.strip() for line in completed.stdout.splitlines() if line.strip()), '').split('|', 1)
            if len(parts) == 2:
                result['edition'] = parts[0].strip()
                result['version'] = parts[1].strip()
    except Exception as exc:
        result['probe_error'] = str(exc)[-1000:]

    edition = str(result.get('edition', '')).casefold()
    version = str(result.get('version', ''))
    if edition == 'desktop' and version.startswith('5.1'):
        result['target'] = 'windows_powershell_5_1'
    elif edition == 'core':
        result['target'] = 'pwsh' if requested_label == 'pwsh' else 'powershell_core'
    elif requested_label == 'pwsh':
        result['target'] = 'pwsh'
    return result


def get_powershell_behavior_shells() -> List[Dict[str, object]]:
    candidates = [
        ('powershell', shutil.which('powershell') or shutil.which('powershell.exe')),
        ('pwsh', shutil.which('pwsh')),
    ]
    shells: List[Dict[str, object]] = []
    seen_paths = set()
    for requested_label, shell_path in candidates:
        if not shell_path:
            continue
        try:
            stable_path = str(Path(shell_path).resolve(strict=False))
        except Exception:
            stable_path = str(shell_path)
        if stable_path in seen_paths:
            continue
        seen_paths.add(stable_path)
        shells.append(probe_powershell_behavior_shell(shell_path, requested_label))
    return shells


def run_powershell_behavior_script(script: str, available_shells: List[Dict[str, object]]) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for shell in available_shells:
        label = str(shell.get('target', 'powershell_unclassified'))
        shell_path = str(shell.get('path', ''))
        with tempfile.NamedTemporaryFile('w', suffix='.ps1', encoding='utf-8', delete=False) as handle:
            handle.write(script)
            script_path = Path(handle.name)
        try:
            cmd = [shell_path, '-NoProfile']
            if label != 'windows_powershell_5_1':
                cmd.append('-NonInteractive')
            if label == 'windows_powershell_5_1':
                cmd.extend(['-ExecutionPolicy', 'Bypass'])
            cmd.extend(['-File', str(script_path)])
            completed = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            results.append({
                'target': label,
                'requested_label': shell.get('requested_label', ''),
                'command': shell.get('command', Path(shell_path).name),
                'edition': shell.get('edition', ''),
                'version': shell.get('version', ''),
                'status': 'passed' if completed.returncode == 0 else 'failed',
                'returncode': completed.returncode,
                'stdout': completed.stdout[-4000:],
                'stderr': completed.stderr[-4000:],
            })
        except Exception as exc:
            results.append({
                'target': label,
                'requested_label': shell.get('requested_label', ''),
                'command': shell.get('command', Path(shell_path).name),
                'edition': shell.get('edition', ''),
                'version': shell.get('version', ''),
                'status': 'failed',
                'returncode': None,
                'stdout': '',
                'stderr': str(exc)[-4000:],
            })
        finally:
            script_path.unlink(missing_ok=True)
    return results


def finalize_powershell_behavior_result(result: Dict[str, object], shell_results: List[Dict[str, object]]) -> Dict[str, object]:
    result['shell_results'] = shell_results
    failed = [row for row in shell_results if row['status'] == 'failed']
    win51 = next((row for row in shell_results if row['target'] == 'windows_powershell_5_1' and row['status'] == 'passed'), None)
    if failed:
        result['status'] = 'failed'
    elif win51:
        result['status'] = 'passed'
    elif shell_results:
        result['status'] = 'passed_without_windows_powershell_5_1'
    else:
        result['status'] = 'skipped_powershell_unavailable'
    return result


def behavior_base() -> Dict[str, object]:
    return {'available': False, 'status': 'skipped_powershell_unavailable', 'preferred_target': 'windows_powershell_5_1', 'shell_results': []}


def run_json_policy_behavior_tests(source_dir: Path, manifest: Dict) -> Dict[str, object]:
    result = behavior_base()
    shells = get_powershell_behavior_shells()
    if not shells:
        return result
    result['available'] = True
    dot_source = build_dot_source_lines_for_functions(source_dir, manifest, ['Add-CollectorError', 'Add-CollectorJsonEllipsisPaths', 'Convert-ToCollectorJsonText'])
    result['dotted_source_line_count'] = len([line for line in dot_source.splitlines() if line.strip()])
    script = f"""
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Global:CollectorErrors = New-Object System.Collections.ArrayList
$Global:CollectorNotes = New-Object System.Collections.ArrayList
$Global:ErrorsLogPath = $null
{dot_source}
function Assert-Condition {{ param([bool]$Condition,[string]$Message) if (-not $Condition) {{ throw $Message }} }}
$deep = [ordered]@{{ a = [ordered]@{{ b = [ordered]@{{ c = [ordered]@{{ d = [ordered]@{{ e = 'leaf' }} }} }} }} }}
$threw = $false
try {{ Convert-ToCollectorJsonText -InputObject $deep -Depth 3 -Label 'behavior deep object' -ThrowOnTruncation | Out-Null }} catch {{ $threw = $true }}
Assert-Condition $threw 'deep object truncation was not detected'
Assert-Condition ($Global:CollectorErrors.Count -ge 1) 'deep object truncation was not recorded'
$Global:CollectorErrors.Clear()
$legitimateEllipsis = [ordered]@{{ outer = [ordered]@{{ marker = '...' }} }}
Convert-ToCollectorJsonText -InputObject $legitimateEllipsis -Depth 5 -Label 'legitimate ellipsis' -ThrowOnTruncation | Out-Null
Assert-Condition ($Global:CollectorErrors.Count -eq 0) 'legitimate ellipsis string was treated as truncation'
$jsonl = Convert-ToCollectorJsonText -InputObject ([ordered]@{{ x = 1 }}) -Compress -AppendNewline -Label 'newline behavior'
Assert-Condition ($jsonl.EndsWith([Environment]::NewLine)) 'AppendNewline did not append the platform newline'
"""
    return finalize_powershell_behavior_result(result, run_powershell_behavior_script(script, shells))


def run_state_recursion_behavior_tests(source_dir: Path, manifest: Dict, worker_sentinel_body: str) -> Dict[str, object]:
    result = behavior_base()
    shells = get_powershell_behavior_shells()
    if not shells:
        return result
    result['available'] = True
    if not worker_sentinel_body:
        result['status'] = 'failed'
        result['shell_results'] = [{'target': 'source_extraction', 'command': 'extract_function_body', 'status': 'failed', 'returncode': 1, 'stdout': '', 'stderr': 'Test-WorkerJsonContainsEllipsisSentinel body could not be extracted'}]
        return result
    dot_source = build_dot_source_lines_for_functions(source_dir, manifest, ['Add-CollectorError', 'Convert-StateObjectToHashtable'])
    result['dotted_source_line_count'] = len([line for line in dot_source.splitlines() if line.strip()])
    script = f"""
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$Global:CollectorErrors = New-Object System.Collections.ArrayList
$Global:CollectorNotes = New-Object System.Collections.ArrayList
$Global:ErrorsLogPath = $null
{dot_source}
function Test-WorkerJsonContainsEllipsisSentinel {worker_sentinel_body}
function Assert-Condition {{ param([bool]$Condition,[string]$Message) if (-not $Condition) {{ throw $Message }} }}
$nested = [pscustomobject]@{{ alpha = [ordered]@{{ beta = @([pscustomobject]@{{ gamma = 'leaf' }}) }} }}
$converted = Convert-StateObjectToHashtable -InputObject $nested -Depth 8
Assert-Condition ($converted -is [hashtable]) 'converted root is not a hashtable'
Assert-Condition ($converted.alpha -is [hashtable]) 'nested dictionary was not preserved as hashtable'
Assert-Condition ($converted.alpha.beta[0].gamma -eq 'leaf') 'nested array/object value was not preserved'
$tooDeep = [ordered]@{{ a = [ordered]@{{ b = [ordered]@{{ c = [ordered]@{{ d = 'leaf' }} }} }} }}
$threw = $false; $message = ''
try {{ Convert-StateObjectToHashtable -InputObject $tooDeep -Depth 3 | Out-Null }} catch {{ $threw = $true; $message = [string]$_.Exception.Message }}
Assert-Condition $threw 'state conversion depth overflow was not rejected'
Assert-Condition ($message -like '*Convert-StateObjectToHashtable*') 'depth error did not identify the converter'
Assert-Condition ($message -like '*depth 3*') 'depth error did not include the configured depth'
Assert-Condition ($message -like '*$.a.b.c*') 'depth error did not include the recursive path'
$workerNormal = [pscustomobject]@{{ step_results = @([pscustomobject]@{{ text = 'normal output' }}) }}
Assert-Condition (-not (Test-WorkerJsonContainsEllipsisSentinel -InputObject $workerNormal -MaxDepth 8)) 'normal worker object was treated as an ellipsis sentinel'
$workerEllipsis = [pscustomobject]@{{ step_results = @([pscustomobject]@{{ text = '...' }}) }}
Assert-Condition (Test-WorkerJsonContainsEllipsisSentinel -InputObject $workerEllipsis -MaxDepth 8) 'nested worker ellipsis sentinel was not detected'
$workerTooDeep = [pscustomobject]@{{ a = [pscustomobject]@{{ b = [pscustomobject]@{{ c = 'leaf' }} }} }}
$workerThrew = $false; $workerMessage = ''
try {{ Test-WorkerJsonContainsEllipsisSentinel -InputObject $workerTooDeep -MaxDepth 2 | Out-Null }} catch {{ $workerThrew = $true; $workerMessage = [string]$_.Exception.Message }}
Assert-Condition $workerThrew 'worker sentinel depth overflow was not rejected'
Assert-Condition ($workerMessage -like '*Parallel worker result JSON sentinel scan*') 'worker sentinel depth error did not identify the scanner'
Assert-Condition ($workerMessage -like '*depth 2*') 'worker sentinel depth error did not include the configured depth'
Assert-Condition ($workerMessage -like '*$.a.b*') 'worker sentinel depth error did not include the recursive path'
"""
    return finalize_powershell_behavior_result(result, run_powershell_behavior_script(script, shells))


def run_suspicious_process_parent_context_behavior_tests(source_dir: Path, manifest: Dict) -> Dict[str, object]:
    result = behavior_base()
    shells = get_powershell_behavior_shells()
    if not shells:
        return result
    result['available'] = True
    dot_source = build_dot_source_lines_for_functions(source_dir, manifest, ['Convert-ProcessObjectToText', 'Get-SuspiciousProcessFindings'])
    result['dotted_source_line_count'] = len([line for line in dot_source.splitlines() if line.strip()])
    script = f"""
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
{dot_source}
function Assert-Condition {{ param([bool]$Condition,[string]$Message) if (-not $Condition) {{ throw $Message }} }}
function New-TestProcess {{
  param([int]$ProcessId,[int]$ParentProcessId,[string]$ParentProcessName,[string]$Name,[string]$ExecutablePath,[string]$CommandLine)
  [pscustomobject]@{{ ProcessId = $ProcessId; ParentProcessId = $ParentProcessId; ParentProcessName = $ParentProcessName; Name = $Name; ExecutablePath = $ExecutablePath; CommandLine = $CommandLine }}
}}
$childWithCurrentParent = [pscustomobject]@{{ ProcessId = 201; ParentProcessId = 200; Name = 'powershell.exe'; ExecutablePath = 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'; CommandLine = 'powershell.exe -NoLogo' }}
$processNameById = @{{ 200 = 'services.exe' }}
$validParentTimes = @{{ 200 = [datetime]'2026-01-01T00:00:00Z'; 201 = [datetime]'2026-01-01T00:00:10Z' }}
$validParentRow = Convert-ProcessObjectToText -Proc $childWithCurrentParent -StartTimeMap $validParentTimes -ProcessNameById $processNameById -ProcessStartTimeById $validParentTimes
Assert-Condition ($validParentRow.ParentProcessName -eq 'services.exe') 'current parent process name was not resolved'
$reusedParentTimes = @{{ 200 = [datetime]'2026-01-01T00:01:00Z'; 201 = [datetime]'2026-01-01T00:00:10Z' }}
$reusedParentRow = Convert-ProcessObjectToText -Proc $childWithCurrentParent -StartTimeMap $reusedParentTimes -ProcessNameById $processNameById -ProcessStartTimeById $reusedParentTimes
Assert-Condition ([string]::IsNullOrWhiteSpace([string]$reusedParentRow.ParentProcessName)) 'reused parent PID name was trusted'
$benignParentShell = New-TestProcess -ProcessId 101 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'powershell.exe' -ExecutablePath 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe' -CommandLine 'powershell.exe -NoLogo'
Assert-Condition (@(Get-SuspiciousProcessFindings -Processes @($benignParentShell) -ExcludedPids @()).Count -eq 0) 'benign-parent name-only PowerShell was not suppressed'
$encodedShell = New-TestProcess -ProcessId 102 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'powershell.exe' -ExecutablePath 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe' -CommandLine 'powershell.exe -EncodedCommand AAAA'
$encodedFindings = @(Get-SuspiciousProcessFindings -Processes @($encodedShell) -ExcludedPids @())
Assert-Condition ($encodedFindings.Count -eq 1) 'PowerShell command-line indicator was suppressed'
Assert-Condition ($encodedFindings[0].Reasons -like '*suspicious PowerShell style command line*') 'PowerShell command-line reason missing'
Assert-Condition ($encodedFindings[0].ParentProcessName -eq 'services.exe') 'PowerShell parent context missing'
$wmicCreate = New-TestProcess -ProcessId 103 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'wmic.exe' -ExecutablePath 'C:\\Windows\\System32\\wbem\\wmic.exe' -CommandLine 'wmic process call create \"cmd.exe /c whoami\"'
$wmicFindings = @(Get-SuspiciousProcessFindings -Processes @($wmicCreate) -ExcludedPids @())
Assert-Condition ($wmicFindings.Count -eq 1) 'WMIC process creation indicator was suppressed'
Assert-Condition ($wmicFindings[0].Reasons -like '*suspicious LOLBin usage*') 'WMIC LOLBin reason missing'
$wmicRemoteNode = New-TestProcess -ProcessId 105 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'wmic.exe' -ExecutablePath 'C:\\Windows\\System32\\wbem\\wmic.exe' -CommandLine 'wmic /node:DC01 process call create \"cmd.exe /c whoami\"'
$wmicRemoteFindings = @(Get-SuspiciousProcessFindings -Processes @($wmicRemoteNode) -ExcludedPids @())
Assert-Condition ($wmicRemoteFindings.Count -eq 1) 'WMIC remote node indicator was suppressed'
Assert-Condition ($wmicRemoteFindings[0].Reasons -like '*suspicious LOLBin usage*') 'WMIC remote node LOLBin reason missing'
$cmdHighRiskPath = New-TestProcess -ProcessId 104 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'cmd.exe' -ExecutablePath 'C:\\Temp\\cmd.exe' -CommandLine 'cmd.exe /c whoami'
$pathFindings = @(Get-SuspiciousProcessFindings -Processes @($cmdHighRiskPath) -ExcludedPids @())
Assert-Condition ($pathFindings.Count -eq 1) 'High-risk path indicator was suppressed'
Assert-Condition ($pathFindings[0].Reasons -like '*process running from high-risk path*') 'High-risk path reason missing'
"""
    return finalize_powershell_behavior_result(result, run_powershell_behavior_script(script, shells))


def add_missing_errors(prefix: str, check_map: Dict[str, object], required_keys: List[str], errors: List[str]) -> None:
    for key in required_keys:
        if not check_map.get(key):
            errors.append(prefix + key)


def validate_unique_function_definitions(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    definitions = find_function_definitions(source_dir, manifest)
    duplicates = {name: rows for name, rows in definitions.items() if len(rows) > 1}
    checks['function_definition_count'] = sum(len(rows) for rows in definitions.values())
    checks['unique_function_count'] = len(definitions)
    checks['duplicate_function_count'] = len(duplicates)
    checks['duplicate_function_names'] = sorted(duplicates)
    checks['duplicate_function_original_names'] = {name: sorted({row['name'] for row in rows}) for name, rows in sorted(duplicates.items())}
    checks['duplicate_function_definitions'] = {name: rows for name, rows in sorted(duplicates.items())}
    if duplicates:
        errors.append('duplicate function definitions are not allowed: ' + ', '.join(sorted(duplicates)))
    if manifest.get('function_override_manifest'):
        errors.append('function_override_manifest is obsolete; collector functions must be defined once')


def validate_collect_metadata_report_write_ordering(source_dir: Path, checks: Dict[str, object], errors: List[str]) -> None:
    main_rel = 'project_sources/collector/source/parts/DCOIR_Collector.05_Main_Entry.ps1'
    helper_rel = 'project_sources/collector/source/parts/DCOIR_Collector.04H_PR212_Metadata_Finalization_Fixes.ps1'
    text = read_text(source_dir / main_rel)
    helper = read_text(source_dir / helper_rel)
    out: Dict[str, object] = {'path': main_rel, 'helper_path': helper_rel}
    checks['collect_metadata_report_write_ordering'] = out
    if not text or not helper:
        out['checked'] = False
        errors.append('collect metadata report source/helper is missing')
        return
    markers = {
        'metadata': '$metadataText = New-MetadataReport -State $state -ToolMap $toolMap',
        'write': 'Write-ReportFile -Path $metadataReportPath -Text $metadataText',
        'upload_artifacts': '$uploadArtifacts = New-CollectUploadArtifactsWithLateMetadataReport -State $state -Baseline $baseline',
        'upload_summary': '$state.UploadSummaryPath = $uploadArtifacts.UploadSummaryPath',
        'upload_budget': '$state.UploadBudgetManifestPath = $uploadArtifacts.UploadManifestPath',
        'default_upload_set': '$state.DefaultGeminiUploadSetStatus = $uploadArtifacts.DefaultSetStatus',
        'upload_safe_chunk': '$state.UploadSafeChunkManifestPath = $uploadArtifacts.UploadSafeChunkManifestPath',
        'analyst_overview': '$state.AnalystOverviewPath = New-AnalystOverviewArtifactWithLateMetadataReport -State $state -Baseline $baseline',
        'bundle_name': '$bundleName = ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId)',
        'bundle_path': '$bundlePath = Join-Path $state.BundlesDir $bundleName',
        'collect_bundle': '$state.CollectBundlePath = $bundlePath',
        'manifest': 'New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json")',
        'bundle_call': 'New-BundleZip -BundlesDir $state.BundlesDir -BundleName $bundleName',
    }
    pos = {key: text.find(value) for key, value in markers.items()}
    metadata_positions = [m.start() for m in re.finditer(re.escape(markers['metadata']), text)]
    write_positions = [m.start() for m in re.finditer(re.escape(markers['write']), text)]
    out.update({
        'checked': True,
        'metadata_report_call_count': len(metadata_positions),
        'metadata_report_write_count': len(write_positions),
        'placeholder_metadata_file_absent': 'New-Item -ItemType File -Path $metadataReportPath' not in text,
        'late_bound_upload_builder_used': pos['upload_artifacts'] != -1,
        'late_bound_overview_builder_used': pos['analyst_overview'] != -1,
        'old_upload_builder_not_used_in_collect': 'New-CollectUploadArtifacts -State $state -Baseline $baseline' not in text,
        'old_overview_builder_not_used_in_collect': 'New-AnalystOverviewArtifact -State $state -Baseline $baseline' not in text,
        'late_bound_metadata_manifest_flag': 'metadata_report_late_bound_after_upload_artifacts = $true' in helper,
        'late_bound_recommended_row_flag': 'late_bound_after_upload_artifacts = [bool]$isLateBoundMetadata' in helper,
        'late_bound_metadata_not_budgeted': 'if (-not $isLateBoundMetadata) { $safeTotal += $sizeKB }' in helper,
        'late_bound_metadata_not_resolved': 'if ($pathExists)' in helper and 'Resolve-Path -LiteralPath $pathText' in helper and '$pathText' in helper,
        'overview_includes_late_bound_metadata_path': "($pair.Label -eq 'METADATA_REPORT_PATH')" in helper,
    })
    if len(metadata_positions) != 1:
        errors.append('collect mode must call New-MetadataReport exactly once after late-bound collect fields are populated')
    if len(write_positions) != 1:
        errors.append('collect mode must write the metadata report exactly once')
    if metadata_positions:
        first_metadata = metadata_positions[0]
        for key in ('upload_artifacts', 'upload_summary', 'upload_budget', 'default_upload_set', 'upload_safe_chunk', 'analyst_overview', 'bundle_name', 'bundle_path', 'collect_bundle'):
            out[f'{key}_before_metadata'] = pos[key] != -1 and pos[key] < first_metadata
        out['metadata_before_manifest'] = pos['manifest'] != -1 and first_metadata < pos['manifest']
        out['metadata_before_bundle'] = pos['bundle_call'] != -1 and first_metadata < pos['bundle_call']
    else:
        for key in ('upload_artifacts', 'upload_summary', 'upload_budget_manifest', 'default_upload_set_status', 'upload_safe_chunk_manifest', 'analyst_overview', 'bundle_name', 'bundle_path', 'collect_bundle_path'):
            out[f'{key}_before_metadata'] = False
        out['metadata_before_manifest'] = False
        out['metadata_before_bundle'] = False
    if write_positions:
        out['metadata_write_before_manifest'] = pos['manifest'] != -1 and write_positions[0] < pos['manifest']
        out['metadata_write_before_bundle'] = pos['bundle_call'] != -1 and write_positions[0] < pos['bundle_call']
    else:
        out['metadata_write_before_manifest'] = False
        out['metadata_write_before_bundle'] = False
    out['metadata_write_follows_metadata_call'] = bool(metadata_positions and write_positions and metadata_positions[0] < write_positions[0])
    alias = {
        'upload_budget_manifest_before_metadata': out.get('upload_budget_before_metadata', False),
        'default_upload_set_status_before_metadata': out.get('default_upload_set_before_metadata', False),
        'upload_safe_chunk_manifest_before_metadata': out.get('upload_safe_chunk_before_metadata', False),
        'collect_bundle_path_before_metadata': out.get('collect_bundle_before_metadata', False),
    }
    out.update(alias)
    add_missing_errors('collect metadata report write ordering check failed: ', out, [
        'placeholder_metadata_file_absent', 'late_bound_upload_builder_used', 'late_bound_overview_builder_used',
        'old_upload_builder_not_used_in_collect', 'old_overview_builder_not_used_in_collect',
        'upload_artifacts_before_metadata', 'upload_summary_before_metadata', 'upload_budget_manifest_before_metadata',
        'default_upload_set_status_before_metadata', 'upload_safe_chunk_manifest_before_metadata', 'analyst_overview_before_metadata',
        'bundle_name_before_metadata', 'bundle_path_before_metadata', 'collect_bundle_path_before_metadata',
        'metadata_before_manifest', 'metadata_write_before_manifest', 'metadata_before_bundle', 'metadata_write_before_bundle',
        'metadata_write_follows_metadata_call', 'late_bound_metadata_manifest_flag', 'late_bound_recommended_row_flag',
        'late_bound_metadata_not_budgeted', 'late_bound_metadata_not_resolved', 'overview_includes_late_bound_metadata_path',
    ], errors)


def validate_collect_manifest_bundle_ordering(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    rel = 'project_sources/collector/source/parts/DCOIR_Collector.05_Main_Entry.ps1'
    text = read_text(source_dir / rel)
    out: Dict[str, object] = {'path': rel}
    checks['collect_manifest_bundle_ordering'] = out
    if not text:
        out['checked'] = False
        errors.append('collect manifest ordering source is missing: ' + rel)
        return
    manifest_marker = 'New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json")'
    bundle_name_marker = '$bundleName = ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId)'
    bundle_path_marker = '$bundlePath = Join-Path $state.BundlesDir $bundleName'
    state_path_marker = '$state.CollectBundlePath = $bundlePath'
    bundle_call_marker = 'New-BundleZip -BundlesDir $state.BundlesDir -BundleName $bundleName'
    manifest_pos = text.find(manifest_marker)
    bundle_call_pos = text.find(bundle_call_marker)
    out.update({
        'checked': True,
        'collect_manifest_call_count': text.count(manifest_marker),
        'collect_bundle_null_present': 'collect_bundle = $null' in text,
        'bundle_name_precomputed_before_manifest': text.find(bundle_name_marker) != -1 and text.find(bundle_name_marker) < manifest_pos,
        'bundle_path_precomputed_before_manifest': text.find(bundle_path_marker) != -1 and text.find(bundle_path_marker) < manifest_pos,
        'state_collect_bundle_path_set_before_manifest': text.find(state_path_marker) != -1 and text.find(state_path_marker) < manifest_pos,
        'manifest_written_before_bundle': manifest_pos != -1 and bundle_call_pos != -1 and manifest_pos < bundle_call_pos,
        'bundle_call_uses_precomputed_name': bundle_call_pos != -1,
        'manifest_in_bundle_inputs': bundle_call_pos != -1 and '$collectManifest' in text[bundle_call_pos:bundle_call_pos + 1200],
    })
    if out['collect_manifest_call_count'] != 1:
        errors.append('collect mode must write manifest_collect.json exactly once before bundle creation')
    if out['collect_bundle_null_present']:
        errors.append('collect mode must not write manifest_collect.json with collect_bundle = $null')
    add_missing_errors('collect manifest/bundle ordering check failed: ', out, [
        'bundle_name_precomputed_before_manifest', 'bundle_path_precomputed_before_manifest', 'state_collect_bundle_path_set_before_manifest',
        'manifest_written_before_bundle', 'bundle_call_uses_precomputed_name', 'manifest_in_bundle_inputs',
    ], errors)


def validate_bundle_metadata_sync_terminates(source_dir: Path, checks: Dict[str, object], errors: List[str]) -> None:
    rel = 'project_sources/collector/source/parts/DCOIR_Collector.04G_PR186_External_Review_Fixes.ps1'
    text = read_text(source_dir / rel)
    out: Dict[str, object] = {'path': rel}
    checks['bundle_metadata_sync_error_handling'] = out
    if not text:
        out['checked'] = False
        errors.append('bundle metadata sync helper source is missing: ' + rel)
        return
    sync_body = extract_function_body(text, 'Sync-CollectionMetadataCompanionArtifact')
    bundle_body = extract_function_body(text, 'New-BundleZip')
    catch_match = re.search(r'catch\s*{(?P<body>.*?)^\s*}', sync_body, re.DOTALL | re.MULTILINE)
    catch_body = catch_match.group('body') if catch_match else ''
    out.update({
        'checked': True,
        'sync_function_present': bool(sync_body),
        'bundle_function_present': bool(bundle_body),
        'bundle_invokes_sync': 'Sync-CollectionMetadataCompanionArtifact' in bundle_body,
        'sync_catch_records_collector_error': 'Add-CollectorError' in catch_body,
        'sync_catch_throws_after_error': re.search(r'\bthrow\b', catch_body) is not None,
    })
    if not out['sync_function_present']:
        errors.append('Sync-CollectionMetadataCompanionArtifact function is missing')
    if not out['bundle_function_present']:
        errors.append('New-BundleZip function is missing')
    if not out['bundle_invokes_sync']:
        errors.append('New-BundleZip must synchronize collection metadata companions before compression')
    if not out['sync_catch_records_collector_error']:
        errors.append('metadata companion sync failures must be recorded with Add-CollectorError')
    if not out['sync_catch_throws_after_error']:
        errors.append('metadata companion sync failures must terminate bundle creation after recording the error')


def validate_json_serialization_policy(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    out: Dict[str, object] = {}
    checks['json_serialization_policy'] = out
    texts = load_manifest_source_texts(source_dir, manifest)
    collector = get_combined_source_text(texts)
    reports = texts.get('project_sources/collector/source/parts/DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1', '')
    parallel_rel = 'project_sources/collector/source/parts/DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1'
    parallel = texts.get(parallel_rel, '')
    manifest_text = texts.get('project_sources/collector/source/parts/DCOIR_Collector.04G_PR186_External_Review_Fixes.ps1', '')
    for function_name in ('Add-CollectorJsonEllipsisPaths', 'Get-CollectorJsonEllipsisPathSet', 'Add-CollectorJsonDepthRiskPaths', 'Get-CollectorJsonDepthRiskPathSet', 'Convert-ToCollectorJsonText'):
        out[f'{function_name}_present'] = bool(extract_function_body(collector, function_name))
        if not out[f'{function_name}_present']:
            errors.append(f'collector JSON serialization helper is missing: {function_name}')
    body = extract_function_body(collector, 'Convert-ToCollectorJsonText')
    json_helper_rel = next((rel for rel, text in texts.items() if extract_function_body(text, 'Convert-ToCollectorJsonText')), '')
    out.update({
        'shared_helper_default_depth_20': '[int]$Depth = 20' in body,
        'shared_helper_checks_source_depth_risks': 'Get-CollectorJsonDepthRiskPathSet -InputObject $InputObject -MaxDepth $Depth' in body,
        'shared_helper_parses_emitted_json': 'ConvertFrom-Json -ErrorAction Stop' in body,
        'shared_helper_compares_source_ellipsis_paths': '$sourceEllipsis.ContainsKey($_)' in body,
        'shared_helper_records_collector_error': 'Add-CollectorError $message' in body,
        'shared_helper_can_throw': 'if ($ThrowOnTruncation) { throw $message }' in body,
        'save_state_uses_shared_helper': "Convert-ToCollectorJsonText -InputObject $State -Label 'state.json' -ThrowOnTruncation" in collector,
        'step_log_uses_shared_helper': "Convert-ToCollectorJsonText -InputObject $obj -Compress -Label 'execution step JSONL'" in collector,
        'safe_json_uses_shared_helper': "Convert-ToCollectorJsonText -InputObject $InputObject -Label 'safe JSON artifact' -AppendNewline -ThrowOnTruncation" in reports,
        'manifest_uses_shared_helper': "Convert-ToCollectorJsonText -InputObject $manifest -Label 'manifest JSON' -ThrowOnTruncation" in manifest_text,
        'worker_uses_depth_20': '$workerJson = $workerResult | ConvertTo-Json -Depth 20 -ErrorAction Stop' in parallel,
        'worker_parses_and_checks_sentinel': 'ConvertFrom-Json -ErrorAction Stop' in parallel and 'Test-WorkerJsonContainsEllipsisSentinel' in parallel and 'Parallel worker result JSON' in parallel,
    })
    out['shared_helper_behavior_tests'] = run_json_policy_behavior_tests(source_dir, manifest)
    add_missing_errors('collector JSON serialization policy check failed: ', out, [
        'shared_helper_default_depth_20', 'shared_helper_checks_source_depth_risks', 'shared_helper_parses_emitted_json',
        'shared_helper_compares_source_ellipsis_paths', 'shared_helper_records_collector_error', 'shared_helper_can_throw',
        'save_state_uses_shared_helper', 'step_log_uses_shared_helper', 'safe_json_uses_shared_helper',
        'manifest_uses_shared_helper', 'worker_uses_depth_20', 'worker_parses_and_checks_sentinel',
    ], errors)
    if out['shared_helper_behavior_tests']['status'] == 'failed':
        errors.append('collector JSON serialization policy behavior tests failed')
    approved_raw_calls = {
        (json_helper_rel, '$json = $InputObject | ConvertTo-Json @jsonArgs'),
        (parallel_rel, '$workerJson = $workerResult | ConvertTo-Json -Depth 20 -ErrorAction Stop'),
    }
    raw_calls: List[Dict[str, object]] = []
    unapproved: List[Dict[str, object]] = []
    for rel, text in texts.items():
        for row in find_convert_to_json_calls(rel, text):
            raw_calls.append(row)
            if (rel, row['text']) not in approved_raw_calls:
                unapproved.append(row)
    out['raw_convert_to_json_calls'] = raw_calls
    out['raw_convert_to_json_detector'] = 'broad_unqualified_or_module_qualified_command_scan_with_comment_stripping'
    out['unapproved_raw_convert_to_json_calls'] = unapproved
    out['unapproved_raw_convert_to_json_absent'] = not unapproved
    if unapproved:
        errors.append('collector source must route JSON serialization through the approved policy helpers; unapproved raw ConvertTo-Json calls: ' + ', '.join(f"{row['path']}:{row['line']}" for row in unapproved))


def validate_state_recursion_policy(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    out: Dict[str, object] = {}
    checks['state_recursion_policy'] = out
    texts = load_manifest_source_texts(source_dir, manifest)
    collector = get_combined_source_text(texts)
    parallel = texts.get('project_sources/collector/source/parts/DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1', '')
    main_entry = texts.get('project_sources/collector/source/parts/DCOIR_Collector.05_Main_Entry.ps1', '')
    converter = extract_function_body(collector, 'Convert-StateObjectToHashtable')
    sentinel = extract_function_body(parallel, 'Test-WorkerJsonContainsEllipsisSentinel')
    out.update({
        'convert_state_object_to_hashtable_present': bool(converter),
        'converter_default_depth_20': '[int]$Depth = 20' in converter,
        'converter_tracks_current_depth': '[int]$CurrentDepth = 0' in converter,
        'converter_tracks_path': "[string]$Path = '$'" in converter,
        'converter_throws_at_depth_limit': 'Convert-StateObjectToHashtable exceeded configured depth {0} at path {1}.' in converter,
        'converter_dictionary_recursion_passes_depth_path': 'Convert-StateObjectToHashtable -InputObject $InputObject[$key] -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in converter,
        'converter_enumerable_recursion_passes_depth_path': 'Convert-StateObjectToHashtable -InputObject $item -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in converter,
        'converter_property_recursion_passes_depth_path': 'Convert-StateObjectToHashtable -InputObject $prop.Value -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in converter,
        'load_state_uses_default_converter_policy': 'Convert-StateObjectToHashtable -InputObject $loaded' in main_entry,
        'worker_sentinel_present': bool(sentinel),
        'worker_sentinel_default_max_depth_25': '[int]$MaxDepth = 25' in sentinel,
        'worker_sentinel_tracks_current_depth': '[int]$CurrentDepth = 0' in sentinel,
        'worker_sentinel_tracks_path': "[string]$Path = '$'" in sentinel,
        'worker_sentinel_throws_at_depth_limit': 'Parallel worker result JSON sentinel scan exceeded configured depth {0} at path {1}.' in sentinel,
        'worker_sentinel_enumerable_recursion_passes_depth_path': 'Test-WorkerJsonContainsEllipsisSentinel -InputObject $item -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in sentinel,
        'worker_sentinel_property_recursion_passes_depth_path': 'Test-WorkerJsonContainsEllipsisSentinel -InputObject $prop.Value -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1) -Path $childPath' in sentinel,
    })
    out['state_recursion_behavior_tests'] = run_state_recursion_behavior_tests(source_dir, manifest, sentinel)
    add_missing_errors('collector state recursion policy check failed: ', out, [
        'convert_state_object_to_hashtable_present', 'converter_default_depth_20', 'converter_tracks_current_depth', 'converter_tracks_path',
        'converter_throws_at_depth_limit', 'converter_dictionary_recursion_passes_depth_path', 'converter_enumerable_recursion_passes_depth_path',
        'converter_property_recursion_passes_depth_path', 'load_state_uses_default_converter_policy', 'worker_sentinel_present',
        'worker_sentinel_default_max_depth_25', 'worker_sentinel_tracks_current_depth', 'worker_sentinel_tracks_path',
        'worker_sentinel_throws_at_depth_limit', 'worker_sentinel_enumerable_recursion_passes_depth_path',
        'worker_sentinel_property_recursion_passes_depth_path',
    ], errors)
    if out['state_recursion_behavior_tests']['status'] == 'failed':
        errors.append('collector state recursion policy behavior tests failed')


def validate_suspicious_process_parent_context_policy(source_dir: Path, manifest: Dict, checks: Dict[str, object], errors: List[str]) -> None:
    out: Dict[str, object] = {}
    checks['suspicious_process_parent_context_policy'] = out
    texts = load_manifest_source_texts(source_dir, manifest)
    collector = get_combined_source_text(texts)
    reports = texts.get('project_sources/collector/source/parts/DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1', '')
    convert = extract_function_body(collector, 'Convert-ProcessObjectToText')
    inventory = extract_function_body(collector, 'Get-ProcessInventory')
    suspicious = extract_function_body(collector, 'Get-SuspiciousProcessFindings')
    out.update({
        'convert_process_object_present': bool(convert),
        'process_inventory_present': bool(inventory),
        'suspicious_process_findings_present': bool(suspicious),
        'convert_accepts_process_name_lookup': '[hashtable]$ProcessNameById' in convert,
        'convert_accepts_process_start_lookup': '[hashtable]$ProcessStartTimeById' in convert,
        'parent_process_id_normalized': '$parentProcessId = [int]$Proc.ParentProcessId' in convert,
        'parent_process_name_resolved': '$parentName = [string]$ProcessNameById[$parentProcessId]' in convert,
        'parent_start_time_checked_before_name_resolution': '$parentStartTime = $ProcessStartTimeById[$parentProcessId]' in convert and '$parentPrecedesChild = ([datetime]$parentStartTime -le [datetime]$created)' in convert,
        'inventory_builds_parent_name_map': '$processNameById[[int]$p.ProcessId] = [string]$p.Name' in inventory,
        'inventory_passes_parent_name_map': '-ProcessNameById $processNameById' in inventory,
        'inventory_passes_parent_start_map': '-ProcessStartTimeById $startTimeMap' in inventory,
        'finding_reads_parent_name': '$parentNameValue = [string]$proc.ParentProcessName' in suspicious,
        'name_only_lolbin_pattern_present': '$nameOnlyLolbinPattern' in suspicious,
        'benign_name_only_lolbin_limited_to_common_shells': "$benignNameOnlyLolbinPattern = '^(powershell|pwsh|cmd|wmic)(\\.exe)?$'" in suspicious,
        'wmic_command_line_indicators_present': 'wmic' in suspicious and 'process\\s+call\\s+create' in suspicious and '/node:' in suspicious,
        'known_benign_parent_pattern_present': all(marker in suspicious for marker in ('$knownBenignLolbinParentPattern', 'svchost', 'services', 'trustedinstaller', 'tiworker', 'wuauclt', 'msiexec')),
        'suppresses_only_known_benign_name_only_hits': 'if (-not $isKnownBenignNameOnlyLolbin -or @($reasons).Count -gt 0)' in suspicious,
        'finding_includes_parent_process_id': 'ParentProcessId = $proc.ParentProcessId' in suspicious,
        'finding_includes_parent_process_name': 'ParentProcessName = $proc.ParentProcessName' in suspicious,
        'process_inventory_reports_parent_name': 'Select-Object ProcessId, ParentProcessId, ParentProcessName, Name' in reports,
        'recommendations_include_parent_context': 'parent={0} ({1})' in reports,
    })
    out['parent_context_behavior_tests'] = run_suspicious_process_parent_context_behavior_tests(source_dir, manifest)
    add_missing_errors('collector suspicious-process parent-context policy check failed: ', out, [key for key in out if key != 'parent_context_behavior_tests'], errors)
    if out['parent_context_behavior_tests']['status'] == 'failed':
        errors.append('collector suspicious-process parent-context behavior tests failed')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()

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
    checks['required_files_present'] = not missing_required
    checks['missing_required_files'] = missing_required
    if missing_required:
        errors.append('missing required files: ' + ', '.join(missing_required))

    collector_parts = manifest.get('collector_part_files', [])
    checks['collector_part_count'] = len(collector_parts)
    missing_parts = [rel for rel in collector_parts if not (source_dir / rel).exists()]
    empty_parts = [rel for rel in collector_parts if (source_dir / rel).exists() and not read_text(source_dir / rel).strip()]
    checks['missing_collector_part_files'] = missing_parts
    checks['empty_collector_part_files'] = empty_parts
    if missing_parts:
        errors.append('collector_part_files references missing files: ' + ', '.join(missing_parts))
    if empty_parts:
        errors.append('collector_part_files references empty files: ' + ', '.join(empty_parts))

    validate_unique_function_definitions(source_dir, manifest, checks, errors)
    validate_collect_metadata_report_write_ordering(source_dir, checks, errors)
    validate_collect_manifest_bundle_ordering(source_dir, manifest, checks, errors)
    validate_bundle_metadata_sync_terminates(source_dir, checks, errors)
    validate_json_serialization_policy(source_dir, manifest, checks, errors)
    validate_state_recursion_policy(source_dir, manifest, checks, errors)
    validate_suspicious_process_parent_context_policy(source_dir, manifest, checks, errors)

    entries = manifest.get('delivery_zip_entries', [])
    expected = {'DCOIR_Collector.ps1.txt'}
    prohibited = {'run_DCOIR_Tests.ps1.txt'}
    actual = {Path(row.get('zip_path', '')).name for row in entries if row.get('zip_path')}
    checks['delivery_entry_count'] = len(entries)
    checks['expected_delivery_names_present'] = expected.issubset(actual)
    checks['actual_delivery_names'] = sorted(actual)
    checks['prohibited_delivery_names_absent'] = actual.isdisjoint(prohibited)
    checks['transport_safe_suffix_required_for_scripts'] = bool(manifest.get('delivery_rules', {}).get('transport_safe_suffix_required_for_scripts'))
    if not entries:
        errors.append('delivery_zip_entries is empty')
    if not checks['expected_delivery_names_present']:
        errors.append('delivery package must include DCOIR_Collector.ps1.txt')
    if not checks['prohibited_delivery_names_absent']:
        errors.append('delivery package must not include harness files: ' + ', '.join(sorted(actual.intersection(prohibited))))
    if checks['transport_safe_suffix_required_for_scripts']:
        non_txt = [row.get('zip_path', '') for row in entries if row.get('zip_path') and not row.get('zip_path', '').endswith('.txt')]
        checks['non_txt_delivery_entries'] = non_txt
        if non_txt:
            errors.append('delivery entries must use transport-safe .txt suffixes: ' + ', '.join(non_txt))

    report = {
        'success': not errors,
        'source_dir': str(source_dir),
        'bundle_name': manifest.get('bundle_name'),
        'bundle_version': manifest.get('bundle_version'),
        'checks': checks,
        'warnings': warnings,
        'errors': errors,
    }
    (output_dir / 'validate_dcoir_collector_runtime_package_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
