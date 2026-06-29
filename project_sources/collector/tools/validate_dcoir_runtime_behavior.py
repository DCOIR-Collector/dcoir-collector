#!/usr/bin/env python3
"""PowerShell behavior probes for collector runtime-package validation."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

from validate_dcoir_runtime_common import build_dot_source_lines_for_functions


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
    script = rf"""
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
    script = rf"""
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
    script = rf"""
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
{dot_source}
function Assert-Condition {{ param([bool]$Condition,[string]$Message) if (-not $Condition) {{ throw $Message }} }}
function New-TestProcess {{
  param([int]$ProcessId,[int]$ParentProcessId,[string]$ParentProcessName,[string]$Name,[string]$ExecutablePath,[string]$CommandLine)
  [pscustomobject]@{{ ProcessId = $ProcessId; ParentProcessId = $ParentProcessId; ParentProcessName = $ParentProcessName; Name = $Name; ExecutablePath = $ExecutablePath; CommandLine = $CommandLine }}
}}
$childWithCurrentParent = [pscustomobject]@{{ ProcessId = 201; ParentProcessId = 200; Name = 'powershell.exe'; ExecutablePath = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'; CommandLine = 'powershell.exe -NoLogo' }}
$processNameById = @{{ 200 = 'services.exe' }}
$validParentTimes = @{{ 200 = [datetime]'2026-01-01T00:00:00Z'; 201 = [datetime]'2026-01-01T00:00:10Z' }}
$validParentRow = Convert-ProcessObjectToText -Proc $childWithCurrentParent -StartTimeMap $validParentTimes -ProcessNameById $processNameById -ProcessStartTimeById $validParentTimes
Assert-Condition ($validParentRow.ParentProcessName -eq 'services.exe') 'current parent process name was not resolved'
$reusedParentTimes = @{{ 200 = [datetime]'2026-01-01T00:01:00Z'; 201 = [datetime]'2026-01-01T00:00:10Z' }}
$reusedParentRow = Convert-ProcessObjectToText -Proc $childWithCurrentParent -StartTimeMap $reusedParentTimes -ProcessNameById $processNameById -ProcessStartTimeById $reusedParentTimes
Assert-Condition ([string]::IsNullOrWhiteSpace([string]$reusedParentRow.ParentProcessName)) 'reused parent PID name was trusted'
$benignParentShell = New-TestProcess -ProcessId 101 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'powershell.exe' -ExecutablePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -CommandLine 'powershell.exe -NoLogo'
Assert-Condition (@(Get-SuspiciousProcessFindings -Processes @($benignParentShell) -ExcludedPids @()).Count -eq 0) 'benign-parent name-only PowerShell was not suppressed'
$encodedShell = New-TestProcess -ProcessId 102 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'powershell.exe' -ExecutablePath 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -CommandLine 'powershell.exe -EncodedCommand AAAA'
$encodedFindings = @(Get-SuspiciousProcessFindings -Processes @($encodedShell) -ExcludedPids @())
Assert-Condition ($encodedFindings.Count -eq 1) 'PowerShell command-line indicator was suppressed'
Assert-Condition ($encodedFindings[0].Reasons -like '*suspicious PowerShell style command line*') 'PowerShell command-line reason missing'
Assert-Condition ($encodedFindings[0].ParentProcessName -eq 'services.exe') 'PowerShell parent context missing'
$wmicCreate = New-TestProcess -ProcessId 103 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'wmic.exe' -ExecutablePath 'C:\Windows\System32\wbem\wmic.exe' -CommandLine 'wmic process call create "cmd.exe /c whoami"'
$wmicFindings = @(Get-SuspiciousProcessFindings -Processes @($wmicCreate) -ExcludedPids @())
Assert-Condition ($wmicFindings.Count -eq 1) 'WMIC process creation indicator was suppressed'
Assert-Condition ($wmicFindings[0].Reasons -like '*suspicious LOLBin usage*') 'WMIC LOLBin reason missing'
$wmicRemoteNode = New-TestProcess -ProcessId 105 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'wmic.exe' -ExecutablePath 'C:\Windows\System32\wbem\wmic.exe' -CommandLine 'wmic /node:DC01 process call create "cmd.exe /c whoami"'
$wmicRemoteFindings = @(Get-SuspiciousProcessFindings -Processes @($wmicRemoteNode) -ExcludedPids @())
Assert-Condition ($wmicRemoteFindings.Count -eq 1) 'WMIC remote node indicator was suppressed'
Assert-Condition ($wmicRemoteFindings[0].Reasons -like '*suspicious LOLBin usage*') 'WMIC remote node LOLBin reason missing'
$cmdHighRiskPath = New-TestProcess -ProcessId 104 -ParentProcessId 4 -ParentProcessName 'services.exe' -Name 'cmd.exe' -ExecutablePath 'C:\Temp\cmd.exe' -CommandLine 'cmd.exe /c whoami'
$pathFindings = @(Get-SuspiciousProcessFindings -Processes @($cmdHighRiskPath) -ExcludedPids @())
Assert-Condition ($pathFindings.Count -eq 1) 'High-risk path indicator was suppressed'
Assert-Condition ($pathFindings[0].Reasons -like '*process running from high-risk path*') 'High-risk path reason missing'
"""
    return finalize_powershell_behavior_result(result, run_powershell_behavior_script(script, shells))
