[CmdletBinding(DefaultParameterSetName='DryRun')]
param(
    [Parameter(ParameterSetName='DryRun')][switch]$DryRun,
    [Parameter(ParameterSetName='Calibrate')][switch]$CalibrateSelectors,
    [Parameter(ParameterSetName='Execute')][switch]$ExecuteCreateViewsOnly,
    [Parameter(ParameterSetName='Execute')][string]$ConfirmToken,
    [switch]$ExperimentalConfigureFilters,
    [string]$ManifestPath,
    [string]$BaseUrl,
    [int]$MaxViews = 0,
    [int]$StartIndex = 1,
    [string]$TableName,
    [switch]$EnableScreenshots,
    [switch]$ContinueOnFailure,
    [switch]$UseChromeChannel,
    [string]$UserDataDir,
    [string]$ConnectOverCdpUrl,
    [switch]$KeepBrowserOpenOnFailure
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

if ($StartIndex -lt 1) { throw 'StartIndex must be 1 or greater. Use -StartIndex 2 to skip the already-created first manifest view.' }

$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
if ([string]::IsNullOrWhiteSpace($repo)) { throw 'Missing required Local Configuration Registry variable: DCOIR_REPO_ROOT' }
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw ('DCOIR_REPO_ROOT does not exist or is not a directory: ' + $repo) }

$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing required Local Configuration Registry variable: DCOIR_DOWNLOADS_DIR' }
if (-not (Test-Path -LiteralPath $downloads -PathType Container)) { throw ('DCOIR_DOWNLOADS_DIR does not exist or is not a directory: ' + $downloads) }

$toolRoot = Join-Path $repo 'operator_tools\github_desktop_lane\ui_automation\airtable_wbs09_views'
if (-not (Test-Path -LiteralPath $toolRoot -PathType Container)) { throw ('Tool root not found. Did you apply/push/pull the repo bundle? ' + $toolRoot) }

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $ManifestPath = Join-Path $repo 'operator_tools\github_desktop_lane\manifests\wbs09_airtable_native_views_manifest.json'
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw ('Manifest not found: ' + $ManifestPath) }

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$outDir = Join-Path $downloads ('dcoir_wbs09_airtable_ui_views_' + $timestamp)
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$logPath = Join-Path $outDir 'launcher.log'

function Write-ToolLog {
    param([string]$Message)
    $line = ('{0} {1}' -f (Get-Date).ToUniversalTime().ToString('o'), $Message)
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
    Write-Host $line
}

Write-ToolLog 'Starting DCOIR WBS09 Airtable UI view tool launcher.'
Write-ToolLog ('Repo root: ' + $repo)
Write-ToolLog ('Output directory: ' + $outDir)
Write-ToolLog ('Manifest path: ' + $ManifestPath)
Write-ToolLog ('Start index: ' + $StartIndex)

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) { throw 'Node.js is required but was not found on PATH. Run Install-DcoirAirtableWbs09UiViewPrereqs.ps1 first.' }

$nodeScript = Join-Path $toolRoot 'scripts\airtable_wbs09_ui_views.mjs'
if (-not (Test-Path -LiteralPath $nodeScript -PathType Leaf)) { throw ('Node script not found: ' + $nodeScript) }

$argsList = @(
    $nodeScript,
    '--manifest', $ManifestPath,
    '--output-dir', $outDir
)

if ($ExecuteCreateViewsOnly) {
    if ($ConfirmToken -ne 'CREATE_WBS09_NATIVE_VIEWS') { throw 'Execute mode requires -ConfirmToken CREATE_WBS09_NATIVE_VIEWS' }
    $argsList += @('--execute-create-views-only','--confirm','CREATE_WBS09_NATIVE_VIEWS')
} elseif ($CalibrateSelectors) {
    $argsList += '--calibration-mode'
} else {
    $argsList += '--dry-run'
}

if ($ExperimentalConfigureFilters) { $argsList += '--experimental-configure-filters' }
if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) { $argsList += @('--base-url', $BaseUrl) }
if ($StartIndex -gt 1) { $argsList += @('--start-index', [string]$StartIndex) }
if ($MaxViews -gt 0) { $argsList += @('--max-views', [string]$MaxViews) }
if (-not [string]::IsNullOrWhiteSpace($TableName)) { $argsList += @('--table-name', $TableName) }
if ($EnableScreenshots) { $argsList += '--enable-screenshots' }
if ($ContinueOnFailure) { $argsList += '--continue-on-failure' }
if ($UseChromeChannel) { $argsList += '--use-chrome-channel' }
if (-not [string]::IsNullOrWhiteSpace($UserDataDir)) { $argsList += @('--user-data-dir', $UserDataDir) }
if (-not [string]::IsNullOrWhiteSpace($ConnectOverCdpUrl)) { $argsList += @('--connect-cdp-url', $ConnectOverCdpUrl) }
if ($KeepBrowserOpenOnFailure) { $argsList += '--keep-browser-open-on-failure' }

Push-Location $toolRoot
try {
    Write-ToolLog ('Invoking node with safe argument count: ' + $argsList.Count)
    & $node.Source @argsList
    $exit = $LASTEXITCODE
    Write-ToolLog ('Node exit code: ' + $exit)
    if ($exit -ne 0) { throw ('WBS09 UI view tool failed with exit code ' + $exit) }
    Write-ToolLog 'Launcher completed successfully.'
    Write-Host ('Output directory: ' + $outDir)
}
finally {
    Pop-Location
}
