<#
DCOIR Actions Mode Ladder Runner.

Purpose:
  Run one workflow through a low-to-high mode/suite ladder with fail-fast gating.
  Each passed mode is a gate. On the first failed/non-success run, stop and do not
  dispatch heavier modes. Intended for manual-full-validation.yml suite ladders.

Output cleanup:
  By default, after the orchestrator creates the ChatGPT-friendly ZIP, this wrapper
  deletes the expanded run output folder so the operator keeps only ZIP artifacts.
#>
[CmdletBinding()]
param(
    [string]$Workflow = 'manual-full-validation.yml',
    [string]$Ref = 'main',
    [string[]]$Suites = @(
        'Core',
        'QuickAliases',
        'SessionBehavior',
        'Retrieval',
        'TargetedCollection',
        'ChunkingOversizeArtifact',
        'ChunkingReconstructionMetadata',
        'MajorVersion',
        'FailureGates',
        'FullRegression'
    ),
    [int]$PollIntervalSeconds = 30,
    [int]$TimeoutMinutes = 120,
    [switch]$DownloadArtifacts,
    [switch]$KeepOutputFolders
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ToolVersion = '2026-05-01.2'

function Get-DcoirMachineEnv {
    param([Parameter(Mandatory=$true)][string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    if ([string]::IsNullOrWhiteSpace($value)) { throw "$Name is not set as a Windows System variable." }
    return $value.Trim()
}

function Write-Step {
    param([string]$Message)
    Write-Host ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $Message)
}

function ConvertTo-SafeName {
    param([string]$Text)
    return (($Text -replace '[^A-Za-z0-9_.-]', '_').Trim('_'))
}

function Normalize-DcoirSuiteList {
    param([string[]]$RawSuites)
    $normalized = New-Object System.Collections.Generic.List[string]
    foreach ($item in @($RawSuites)) {
        if ([string]::IsNullOrWhiteSpace($item)) { continue }
        foreach ($part in ($item -split ',')) {
            $trimmed = $part.Trim()
            if (-not [string]::IsNullOrWhiteSpace($trimmed)) { [void]$normalized.Add($trimmed) }
        }
    }
    if ($normalized.Count -eq 0) { throw 'No suites were provided after normalization.' }
    return [string[]]$normalized.ToArray()
}

$Suites = Normalize-DcoirSuiteList -RawSuites $Suites

$repo = Get-DcoirMachineEnv -Name 'DCOIR_REPO_ROOT'
$downloads = Get-DcoirMachineEnv -Name 'DCOIR_DOWNLOADS_DIR'
$orchestrator = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirActionsWorkflowOrchestrator.ps1'
if (-not (Test-Path -LiteralPath $orchestrator -PathType Leaf)) { throw "Orchestrator not found: $orchestrator" }

Write-Step "DCOIR Actions Mode Ladder Runner v$ToolVersion"
Write-Step "Workflow=$Workflow Ref=$Ref"
Write-Step ("Suites={0}" -f ($Suites -join ', '))
Write-Step "Fail-fast is enabled. FullRegression should be last."

$results = @()
$failed = $false

foreach ($suite in $Suites) {
    if ($failed) { break }

    $safeSuite = ConvertTo-SafeName $suite
    $runSetId = "ladder-$((ConvertTo-SafeName $Workflow).Replace('.yml',''))-$safeSuite"
    $zipName = "dcoir_actions_${runSetId}.chatgpt.zip"
    $manifestPath = Join-Path $downloads "dcoir_actions_${runSetId}.json"

    Write-Step "Starting gate: $suite"

    $manifest = [ordered]@{
        run_set_id = $runSetId
        mode = 'dispatch'
        repo = 'malwaredevil/dcoir-collector'
        default_ref = $Ref
        dry_run = $false
        require_dispatch_confirmation = $true
        allow_multiple_live_dispatches = $false
        max_dispatch_count = 1
        poll_interval_seconds = $PollIntervalSeconds
        timeout_minutes = $TimeoutMinutes
        max_parallel = 1
        output = [ordered]@{
            folder = '%DCOIR_DOWNLOADS_DIR%'
            create_chatgpt_friendly_zip = $true
            download_artifacts = [bool]$DownloadArtifacts
            zip_name = $zipName
        }
        runs = @(
            [ordered]@{
                run_id = "gate-$safeSuite"
                workflow = $Workflow
                ref = $Ref
                inputs = [ordered]@{ suite = $suite }
                capture = [ordered]@{
                    summary = $true
                    jobs = $true
                    logs = $true
                    artifacts = [bool]$DownloadArtifacts
                }
            }
        )
    }

    $manifest | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

    $beforeDirs = @(Get-ChildItem -LiteralPath $downloads -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $orchestrator -ManifestJson $manifestPath -ConfirmDispatch
    $exitCode = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }

    $afterDirs = @(Get-ChildItem -LiteralPath $downloads -Directory -ErrorAction SilentlyContinue | Where-Object { $beforeDirs -notcontains $_.FullName -and $_.Name -like "*${runSetId}*" })
    $runDir = @($afterDirs | Sort-Object LastWriteTime -Descending | Select-Object -First 1)[0]
    $summaryPath = if ($runDir) { Join-Path $runDir.FullName 'orchestrator_summary.json' } else { $null }
    $zipPath = Join-Path $downloads $zipName

    $failedCount = 1
    $conclusion = 'unknown'
    if ($summaryPath -and (Test-Path -LiteralPath $summaryPath -PathType Leaf)) {
        $summary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
        if ($summary.PSObject.Properties.Name -contains 'failed_or_non_success_count') { $failedCount = [int]$summary.failed_or_non_success_count }
        if ($summary.PSObject.Properties.Name -contains 'records' -and $summary.records.Count -gt 0) { $conclusion = [string]$summary.records[0].conclusion }
    } elseif ($exitCode -eq 0 -and (Test-Path -LiteralPath $zipPath -PathType Leaf)) {
        $failedCount = 0
        $conclusion = 'zip-created-summary-not-found'
    }

    $results += [ordered]@{
        suite = $suite
        exit_code = $exitCode
        failed_or_non_success_count = $failedCount
        conclusion = $conclusion
        zip = $zipPath
        manifest = $manifestPath
        run_dir = if ($runDir) { $runDir.FullName } else { $null }
    }

    if (-not $KeepOutputFolders -and $runDir -and (Test-Path -LiteralPath $runDir.FullName -PathType Container)) {
        Write-Step "Cleaning expanded run folder: $($runDir.FullName)"
        Remove-Item -LiteralPath $runDir.FullName -Recurse -Force
    }

    if ($exitCode -ne 0 -or $failedCount -gt 0) {
        Write-Step "FAIL-FAST STOP at gate: $suite"
        $failed = $true
        break
    }

    Write-Step "Gate passed: $suite"
}

$resultPath = Join-Path $downloads 'dcoir_actions_mode_ladder_result.json'
$results | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $resultPath -Encoding UTF8

Write-Step 'Ladder complete.'
Write-Host "RESULT_JSON=$resultPath"
foreach ($r in $results) {
    if (Test-Path -LiteralPath $r.zip -PathType Leaf) { Write-Host "UPLOAD_FILE=$($r.zip)" }
}
if ($failed) { exit 1 }
exit 0
