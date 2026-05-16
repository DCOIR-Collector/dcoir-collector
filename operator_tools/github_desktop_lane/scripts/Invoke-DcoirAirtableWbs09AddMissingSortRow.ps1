[CmdletBinding()]
param(
    [ValidateSet('DryRun','Apply')][string]$Mode = 'DryRun',
    [string]$ConfirmToken,
    [string]$ManifestPath,
    [string]$TargetListFile,
    [switch]$AllTargetsFromDefaultList,
    [string]$BaseUrl,
    [switch]$EnableScreenshots,
    [switch]$UseChromeChannel,
    [string]$UserDataDir,
    [string]$ConnectOverCdpUrl,
    [int]$BrowserLaunchTimeoutSeconds = 90,
    [int]$ReloadAttempts = 3,
    [int]$ReloadTimeoutSeconds = 30,
    [int]$NetworkIdleTimeoutSeconds = 12,
    [switch]$NoAirtableReadyPause,
    [switch]$KeepBrowserOpenOnFailure,
    [switch]$FailOnSkipped
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-DcoirRequiredEnvironmentValue {
    param([Parameter(Mandatory = $true)][string]$Name)
    foreach ($scope in @('Process','User','Machine')) {
        $value = [Environment]::GetEnvironmentVariable($Name, $scope)
        if (-not [string]::IsNullOrWhiteSpace($value)) { return $value }
    }
    throw ('Missing required Local Configuration Registry variable: ' + $Name)
}

function Write-ToolLog {
    param([string]$Message)
    $line = ('{0} {1}' -f (Get-Date).ToUniversalTime().ToString('o'), $Message)
    Add-Content -LiteralPath $script:logPath -Value $line -Encoding UTF8
    Write-Host $line
}

function Invoke-DcoirNativeProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Label
    )
    Write-ToolLog ('Running native process: ' + $Label)
    & $FilePath @Arguments
    $exit = $LASTEXITCODE
    Write-ToolLog ($Label + ' exit code: ' + $exit)
    if ($exit -ne 0) { throw ($Label + ' failed with exit code ' + $exit) }
}

$requiredApplyToken = 'APPLY_WBS09_ADD_MISSING_SORT_ROW_BATCH'
if ($Mode -eq 'Apply' -and $ConfirmToken -ne $requiredApplyToken) {
    throw ('Apply mode requires -ConfirmToken ' + $requiredApplyToken)
}
if ($Mode -eq 'DryRun' -and -not [string]::IsNullOrWhiteSpace($ConfirmToken)) {
    throw 'DryRun mode must not be given an apply confirmation token.'
}
if (-not $AllTargetsFromDefaultList -and [string]::IsNullOrWhiteSpace($TargetListFile)) {
    throw 'Specify -AllTargetsFromDefaultList or -TargetListFile.'
}
if ($AllTargetsFromDefaultList -and -not [string]::IsNullOrWhiteSpace($TargetListFile)) {
    throw 'Use either -AllTargetsFromDefaultList or -TargetListFile, not both.'
}
if ($BrowserLaunchTimeoutSeconds -lt 10 -or $BrowserLaunchTimeoutSeconds -gt 300) { throw 'BrowserLaunchTimeoutSeconds must be between 10 and 300.' }
if ($ReloadAttempts -lt 1 -or $ReloadAttempts -gt 8) { throw 'ReloadAttempts must be between 1 and 8.' }
if ($ReloadTimeoutSeconds -lt 10 -or $ReloadTimeoutSeconds -gt 300) { throw 'ReloadTimeoutSeconds must be between 10 and 300.' }
if ($NetworkIdleTimeoutSeconds -lt 10 -or $NetworkIdleTimeoutSeconds -gt 300) { throw 'NetworkIdleTimeoutSeconds must be between 10 and 300.' }

$repo = Get-DcoirRequiredEnvironmentValue -Name 'DCOIR_REPO_ROOT'
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw ('DCOIR_REPO_ROOT does not exist or is not a directory: ' + $repo) }
$env:DCOIR_REPO_ROOT = $repo

$downloads = Get-DcoirRequiredEnvironmentValue -Name 'DCOIR_DOWNLOADS_DIR'
if (-not (Test-Path -LiteralPath $downloads -PathType Container)) { throw ('DCOIR_DOWNLOADS_DIR does not exist or is not a directory: ' + $downloads) }
$env:DCOIR_DOWNLOADS_DIR = $downloads

$toolRoot = Join-Path $repo 'operator_tools\github_desktop_lane\ui_automation\airtable_wbs09_views'
if (-not (Test-Path -LiteralPath $toolRoot -PathType Container)) { throw ('Tool root not found. Did you apply/pull the repo bundle? ' + $toolRoot) }

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $ManifestPath = Join-Path $repo 'operator_tools\github_desktop_lane\manifests\wbs09_airtable_native_views_manifest.json'
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw ('Manifest not found: ' + $ManifestPath) }

if ($AllTargetsFromDefaultList) {
    $TargetListFile = Join-Path $repo 'operator_tools\github_desktop_lane\manifests\wbs09_add_missing_sort_row_targets.v1.json'
}
if (-not (Test-Path -LiteralPath $TargetListFile -PathType Leaf)) { throw ('Target list file not found: ' + $TargetListFile) }

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$outDir = Join-Path $downloads ('dcoir_wbs09_add_missing_sort_row_' + $Mode.ToLowerInvariant() + '_' + $timestamp)
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$script:logPath = Join-Path $outDir 'add_missing_sort_row_launcher.log'

Write-ToolLog 'Starting DCOIR WBS09 add-missing-sort-row operation-class launcher.'
Write-ToolLog ('Mode: ' + $Mode)
Write-ToolLog ('Repo root: ' + $repo)
Write-ToolLog ('Output directory: ' + $outDir)
Write-ToolLog ('Manifest path: ' + $ManifestPath)
Write-ToolLog ('Target list file: ' + $TargetListFile)
Write-ToolLog ('Airtable-ready pause enabled: ' + (-not $NoAirtableReadyPause))

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) { throw 'Node.js is required but was not found on PATH. Run Install-DcoirAirtableWbs09UiViewPrereqs.ps1 first.' }

$nodeScript = Join-Path $toolRoot 'scripts\airtable_wbs09_add_missing_sort_row.mjs'
if (-not (Test-Path -LiteralPath $nodeScript -PathType Leaf)) { throw ('Node script not found: ' + $nodeScript) }

$argsList = @(
    $nodeScript,
    '--manifest', $ManifestPath,
    '--output-dir', $outDir,
    '--target-list-file', $TargetListFile,
    '--mode', $Mode.ToLowerInvariant(),
    '--browser-launch-timeout-ms', ([string]($BrowserLaunchTimeoutSeconds * 1000)),
    '--reload-attempts', ([string]$ReloadAttempts),
    '--reload-timeout-ms', ([string]($ReloadTimeoutSeconds * 1000)),
    '--network-idle-timeout-ms', ([string]($NetworkIdleTimeoutSeconds * 1000))
)

if ($Mode -eq 'Apply') { $argsList += @('--confirm-token', $ConfirmToken) }
if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) { $argsList += @('--base-url', $BaseUrl) }
if ($EnableScreenshots) { $argsList += '--enable-screenshots' }
if ($UseChromeChannel) { $argsList += '--use-chrome-channel' }
if (-not [string]::IsNullOrWhiteSpace($UserDataDir)) { $argsList += @('--user-data-dir', $UserDataDir) }
if (-not [string]::IsNullOrWhiteSpace($ConnectOverCdpUrl)) { $argsList += @('--connect-cdp-url', $ConnectOverCdpUrl) }
if ($NoAirtableReadyPause) { $argsList += '--no-airtable-ready-prompt' }
if ($KeepBrowserOpenOnFailure) { $argsList += '--keep-browser-open-on-failure' }
if ($FailOnSkipped) { $argsList += '--fail-on-skipped' }

Push-Location $toolRoot
try {
    Write-ToolLog ('Invoking node with safe argument count: ' + $argsList.Count)
    Invoke-DcoirNativeProcess -FilePath $node.Source -Arguments $argsList -Label 'node airtable_wbs09_add_missing_sort_row'
    Write-ToolLog 'Add-missing-sort-row operation-class launcher completed successfully.'
    Write-Host ('Output directory: ' + $outDir)
}
finally {
    Pop-Location
}
