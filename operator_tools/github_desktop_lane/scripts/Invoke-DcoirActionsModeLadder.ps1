<#
DCOIR Actions Mode Ladder Runner.
Harness only: creates a fail-fast sequential JSON manifest and executes the core orchestrator.
#>
[CmdletBinding()]
param(
    [string]$Workflow = 'manual-full-validation.yml',
    [string]$Ref = 'main',
    [string[]]$Suites = @('Core','QuickAliases','SessionBehavior','Retrieval','TargetedCollection','ChunkingOversizeArtifact','ChunkingReconstructionMetadata','MajorVersion','FailureGates','FullRegression'),
    [int]$PollIntervalSeconds = 30,
    [int]$TimeoutMinutes = 120,
    [switch]$DownloadArtifacts,
    [switch]$KeepOutputFolders
)
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ToolVersion = '2026-05-01.3'
function Get-DcoirMachineEnv { param([Parameter(Mandatory=$true)][string]$Name) $value = [Environment]::GetEnvironmentVariable($Name,'Machine'); if ([string]::IsNullOrWhiteSpace($value)) { throw "$Name is not set as a Windows System variable." }; return $value.Trim() }
function Write-Step { param([string]$Message) Write-Host ("[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $Message) }
function ConvertTo-SafeName { param([string]$Text) return (($Text -replace '[^A-Za-z0-9_.-]', '_').Trim('_')) }
function Normalize-DcoirSuiteList { param([string[]]$RawSuites) $list = New-Object System.Collections.Generic.List[string]; foreach ($item in @($RawSuites)) { if ([string]::IsNullOrWhiteSpace($item)) { continue }; foreach ($part in ($item -split ',')) { $trimmed = $part.Trim(); if (-not [string]::IsNullOrWhiteSpace($trimmed)) { [void]$list.Add($trimmed) } } }; if ($list.Count -eq 0) { throw 'No suites were provided after normalization.' }; return [string[]]$list.ToArray() }
$Suites = Normalize-DcoirSuiteList -RawSuites $Suites
$repo = Get-DcoirMachineEnv -Name 'DCOIR_REPO_ROOT'
$downloads = Get-DcoirMachineEnv -Name 'DCOIR_DOWNLOADS_DIR'
$orchestrator = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirActionsWorkflowOrchestrator.ps1'
$runSetId = "ladder-$((ConvertTo-SafeName $Workflow).Replace('.yml',''))-$((ConvertTo-SafeName ($Suites -join '_')))"
$manifestPath = Join-Path $downloads "dcoir_actions_${runSetId}.json"
$zipName = "dcoir_actions_${runSetId}.chatgpt.zip"
$runs = @()
foreach ($suite in $Suites) { $safeSuite = ConvertTo-SafeName $suite; $runs += [ordered]@{ run_id="gate-$safeSuite"; workflow=$Workflow; ref=$Ref; inputs=[ordered]@{ suite=$suite }; capture=[ordered]@{ summary=$true; jobs=$true; logs=$true; artifacts=[bool]$DownloadArtifacts } } }
$manifest = [ordered]@{ run_set_id=$runSetId; mode='dispatch'; repo='malwaredevil/dcoir-collector'; default_ref=$Ref; dry_run=$false; require_dispatch_confirmation=$true; allow_multiple_live_dispatches=$true; max_dispatch_count=$runs.Count; fail_fast=$true; poll_interval_seconds=$PollIntervalSeconds; timeout_minutes=$TimeoutMinutes; max_parallel=1; output=[ordered]@{ folder='%DCOIR_DOWNLOADS_DIR%'; create_chatgpt_friendly_zip=$true; cleanup_output_folder_after_zip=(-not [bool]$KeepOutputFolders); download_artifacts=[bool]$DownloadArtifacts; zip_name=$zipName }; runs=$runs }
$manifest | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Step "DCOIR Actions Mode Ladder Runner v$ToolVersion"
Write-Step "Created manifest: $manifestPath"
Write-Step "Executing orchestrator. Watch GitHub Actions for one active $Workflow gate at a time."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $orchestrator -ManifestJson $manifestPath -ConfirmDispatch
$exitCode = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
Write-Host "UPLOAD_FILE=$(Join-Path $downloads $zipName)"
Write-Host "UPLOAD_FILE=$manifestPath"
exit $exitCode
