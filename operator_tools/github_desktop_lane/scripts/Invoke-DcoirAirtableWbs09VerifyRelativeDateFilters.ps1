[CmdletBinding(DefaultParameterSetName='SupportedPrimitive')]
param(
    [Parameter(ParameterSetName='SupportedPrimitive')][switch]$AllSupportedRelativeDateTargets,
    [Parameter(ParameterSetName='Explicit')][string[]]$TargetKey,
    [Parameter(ParameterSetName='SupportedPrimitive')][string]$ConfirmToken,
    [string]$ManifestPath,
    [string]$CapabilityMapPath,
    [string]$BaseUrl,
    [int]$MaxTargets = 0,
    [switch]$EnableScreenshots,
    [switch]$UseChromeChannel,
    [string]$UserDataDir,
    [string]$ConnectOverCdpUrl,
    [int]$BrowserLaunchTimeoutSeconds = 45,
    [switch]$NoOperatorReadyPause,
    [switch]$KeepBrowserOpenOnFailure,
    [switch]$FailOnGap
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

if ($AllSupportedRelativeDateTargets -and $ConfirmToken -ne 'VERIFY_WBS09_RELATIVE_DATE_FILTERS') {
    throw 'Broad read-only verification requires -ConfirmToken VERIFY_WBS09_RELATIVE_DATE_FILTERS.'
}

if (-not $AllSupportedRelativeDateTargets -and (-not $TargetKey -or $TargetKey.Count -lt 1)) {
    throw 'Use either -AllSupportedRelativeDateTargets with confirmation token or one or more -TargetKey values.'
}

if ($BrowserLaunchTimeoutSeconds -lt 10 -or $BrowserLaunchTimeoutSeconds -gt 300) {
    throw 'BrowserLaunchTimeoutSeconds must be between 10 and 300.'
}

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

if ([string]::IsNullOrWhiteSpace($CapabilityMapPath)) {
    $CapabilityMapPath = Join-Path $repo 'operator_tools\github_desktop_lane\manifests\wbs09_airtable_capability_map.generated.json'
}
if (-not (Test-Path -LiteralPath $CapabilityMapPath -PathType Leaf)) { throw ('Capability map not found: ' + $CapabilityMapPath) }

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$outDir = Join-Path $downloads ('dcoir_wbs09_verify_relative_date_filters_' + $timestamp)
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$logPath = Join-Path $outDir 'verify_relative_date_filters_launcher.log'

function Write-ToolLog {
    param([string]$Message)
    $line = ('{0} {1}' -f (Get-Date).ToUniversalTime().ToString('o'), $Message)
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
    Write-Host $line
}

Write-ToolLog 'Starting DCOIR WBS09 verify relative-date filters launcher.'
Write-ToolLog ('Repo root: ' + $repo)
Write-ToolLog ('Output directory: ' + $outDir)
Write-ToolLog ('Manifest path: ' + $ManifestPath)
Write-ToolLog ('Capability map path: ' + $CapabilityMapPath)
Write-ToolLog ('All supported relative-date targets: ' + [string]$AllSupportedRelativeDateTargets)
$targetKeyCount = 0
if ($TargetKey) { $targetKeyCount = $TargetKey.Count }
Write-ToolLog ('Target key count: ' + [string]$targetKeyCount)
Write-ToolLog ('Max targets: ' + [string]$MaxTargets)
Write-ToolLog ('Browser launch timeout seconds: ' + $BrowserLaunchTimeoutSeconds)
Write-ToolLog ('Operator ready pause enabled: ' + (-not $NoOperatorReadyPause))
Write-ToolLog ('Fail on gap: ' + [string]$FailOnGap)

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) { throw 'Node.js is required but was not found on PATH. Run Install-DcoirAirtableWbs09UiViewPrereqs.ps1 first.' }

$nodeScript = Join-Path $toolRoot 'scripts\airtable_wbs09_verify_relative_date_filters.mjs'
if (-not (Test-Path -LiteralPath $nodeScript -PathType Leaf)) { throw ('Node script not found: ' + $nodeScript) }

$argsList = @(
    $nodeScript,
    '--manifest', $ManifestPath,
    '--capability-map', $CapabilityMapPath,
    '--output-dir', $outDir
)

if ($AllSupportedRelativeDateTargets) { $argsList += '--all-supported-relative-date-targets' }
if ($TargetKey -and $TargetKey.Count -gt 0) { foreach ($key in $TargetKey) { $argsList += @('--target-key', $key) } }
if ($MaxTargets -gt 0) { $argsList += @('--max-targets', ([string]$MaxTargets)) }
if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) { $argsList += @('--base-url', $BaseUrl) }
if ($EnableScreenshots) { $argsList += '--enable-screenshots' }
if ($UseChromeChannel) { $argsList += '--use-chrome-channel' }
if (-not [string]::IsNullOrWhiteSpace($UserDataDir)) { $argsList += @('--user-data-dir', $UserDataDir) }
if (-not [string]::IsNullOrWhiteSpace($ConnectOverCdpUrl)) { $argsList += @('--connect-cdp-url', $ConnectOverCdpUrl) }
$argsList += @('--browser-launch-timeout-ms', ([string]($BrowserLaunchTimeoutSeconds * 1000)))
if (-not $NoOperatorReadyPause) { $argsList += '--operator-ready-before-launch' }
if ($KeepBrowserOpenOnFailure) { $argsList += '--keep-browser-open-on-failure' }
if ($FailOnGap) { $argsList += '--fail-on-gap' }

Push-Location $toolRoot
try {
    Write-ToolLog ('Invoking node with safe argument count: ' + $argsList.Count)
    & $node.Source @argsList
    $exit = $LASTEXITCODE
    Write-ToolLog ('Node exit code: ' + $exit)
    if ($exit -ne 0) { throw ('WBS09 verify relative-date filters failed with exit code ' + $exit) }
    Write-ToolLog 'Verify relative-date filters launcher completed successfully.'
    Write-Host ('Output directory: ' + $outDir)
}
finally {
    Pop-Location
}
