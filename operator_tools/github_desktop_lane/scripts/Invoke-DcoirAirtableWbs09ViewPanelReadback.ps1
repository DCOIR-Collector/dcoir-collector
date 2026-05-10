[CmdletBinding(DefaultParameterSetName='Representative')]
param(
    [Parameter(ParameterSetName='Representative')][switch]$DefaultRepresentativeTargets,
    [Parameter(ParameterSetName='Explicit')][string[]]$TargetKey,
    [Parameter(ParameterSetName='All')][switch]$AllManifestViews,
    [Parameter(ParameterSetName='All')][string]$ConfirmToken,
    [string]$ManifestPath,
    [string]$BaseUrl,
    [switch]$EnableScreenshots,
    [switch]$UseChromeChannel,
    [string]$UserDataDir,
    [string]$ConnectOverCdpUrl,
    [switch]$KeepBrowserOpenOnFailure
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

if ($AllManifestViews -and $ConfirmToken -ne 'READBACK_ALL_MANIFEST_VIEWS') {
    throw 'All-manifest readback is read-only but broad. Use -ConfirmToken READBACK_ALL_MANIFEST_VIEWS only when intentionally running all manifest views.'
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$outDir = Join-Path $downloads ('dcoir_wbs09_view_panel_readback_' + $timestamp)
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$logPath = Join-Path $outDir 'panel_readback_launcher.log'

function Write-ToolLog {
    param([string]$Message)
    $line = ('{0} {1}' -f (Get-Date).ToUniversalTime().ToString('o'), $Message)
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
    Write-Host $line
}

Write-ToolLog 'Starting DCOIR WBS09 Airtable view panel readback launcher.'
Write-ToolLog ('Repo root: ' + $repo)
Write-ToolLog ('Output directory: ' + $outDir)
Write-ToolLog ('Manifest path: ' + $ManifestPath)

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) { throw 'Node.js is required but was not found on PATH. Run Install-DcoirAirtableWbs09UiViewPrereqs.ps1 first.' }

$nodeScript = Join-Path $toolRoot 'scripts\airtable_wbs09_view_panel_readback.mjs'
if (-not (Test-Path -LiteralPath $nodeScript -PathType Leaf)) { throw ('Node script not found: ' + $nodeScript) }

$argsList = @(
    $nodeScript,
    '--manifest', $ManifestPath,
    '--output-dir', $outDir
)

if ($AllManifestViews) { $argsList += '--all-manifest-views' }
elseif ($TargetKey -and $TargetKey.Count -gt 0) { foreach ($key in $TargetKey) { $argsList += @('--target-key', $key) } }
else { $argsList += '--default-representative-targets' }

if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) { $argsList += @('--base-url', $BaseUrl) }
if ($EnableScreenshots) { $argsList += '--enable-screenshots' }
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
    if ($exit -ne 0) { throw ('WBS09 panel readback failed with exit code ' + $exit) }
    Write-ToolLog 'Panel readback launcher completed successfully.'
    Write-Host ('Output directory: ' + $outDir)
}
finally {
    Pop-Location
}
