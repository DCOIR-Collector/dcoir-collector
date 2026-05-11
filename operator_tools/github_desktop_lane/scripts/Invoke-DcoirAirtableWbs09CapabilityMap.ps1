[CmdletBinding(DefaultParameterSetName='MapOnly')]
param(
  [string]$RepoRoot = $env:DCOIR_REPO_ROOT,
  [string]$DownloadsDir = $env:DCOIR_DOWNLOADS_DIR,
  [string]$ManifestPath,
  [string]$OutputDir,
  [string]$SchemaJson,
  [string]$EvidenceRoot,
  [string]$BaseId = $env:DCOIR_AIRTABLE_BASE_ID,
  [switch]$RequireLiveSchema,
  [switch]$NoLiveSchema,

  [switch]$CollectUiEvidence,
  [string[]]$UiEvidenceTargetKey,
  [switch]$DefaultUiEvidenceTargets,
  [switch]$EnableScreenshots,
  [switch]$UseChromeChannel,
  [string]$UserDataDir,
  [string]$ConnectOverCdpUrl,
  [switch]$ProbeDropdownOptions,
  [int]$MaxDropdownProbes = 12,
  [switch]$KeepBrowserOpenOnFailure
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Write-LogLine {
  param([string]$Message)
  $stamp = [DateTime]::UtcNow.ToString('o')
  Write-Host "$stamp $Message"
}

function Get-DcoirRequiredEnvironmentValue {
  param([Parameter(Mandatory = $true)][string]$Name)
  foreach ($scope in @('Process','User','Machine')) {
    $value = [Environment]::GetEnvironmentVariable($Name, $scope)
    if (-not [string]::IsNullOrWhiteSpace($value)) { return $value }
  }
  throw ('Missing required Local Configuration Registry variable: ' + $Name)
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = Get-DcoirRequiredEnvironmentValue -Name 'DCOIR_REPO_ROOT'
}
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
  throw "Repo root does not exist: $RepoRoot"
}

if ([string]::IsNullOrWhiteSpace($DownloadsDir)) {
  $DownloadsDir = Get-DcoirRequiredEnvironmentValue -Name 'DCOIR_DOWNLOADS_DIR'
}
$DownloadsDir = [System.IO.Path]::GetFullPath($DownloadsDir)
if (-not (Test-Path -LiteralPath $DownloadsDir -PathType Container)) {
  throw "DCOIR_DOWNLOADS_DIR does not exist or is not a directory: $DownloadsDir"
}

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
  $ManifestPath = Join-Path $RepoRoot 'operator_tools\github_desktop_lane\manifests\wbs09_airtable_native_views_manifest.json'
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
  throw "WBS09 manifest not found: $ManifestPath"
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
  $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
  $OutputDir = Join-Path $DownloadsDir "dcoir_wbs09_capability_map_$stamp"
}
$OutputDir = [System.IO.Path]::GetFullPath($OutputDir)

# Hard safety: generated output must live under DCOIR_DOWNLOADS_DIR unless the
# operator explicitly supplies another OutputDir. This avoids hidden temp clutter.
if (-not ($OutputDir.StartsWith($DownloadsDir, [System.StringComparison]::OrdinalIgnoreCase))) {
  throw "OutputDir must be under DCOIR_DOWNLOADS_DIR for governed visible artifact handling. OutputDir=$OutputDir DCOIR_DOWNLOADS_DIR=$DownloadsDir"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$scriptPath = Join-Path $RepoRoot 'operator_tools\github_desktop_lane\ui_automation\airtable_wbs09_views\scripts\airtable_wbs09_capability_map.mjs'
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
  throw "Capability map node script not found: $scriptPath"
}

$uiEvidenceTargets = @()
if ($UiEvidenceTargetKey -and $UiEvidenceTargetKey.Count -gt 0) {
  $uiEvidenceTargets += $UiEvidenceTargetKey
} elseif ($DefaultUiEvidenceTargets -or $CollectUiEvidence) {
  $uiEvidenceTargets += @(
    'Session Checkpoints::WBS09 - Needs Review',
    'Operator Tools Registry::WBS09 - Validation Due'
  )
}

if ($CollectUiEvidence -and $uiEvidenceTargets.Count -lt 1) {
  throw 'CollectUiEvidence requires at least one UiEvidenceTargetKey or DefaultUiEvidenceTargets.'
}

$oldDownloadsEnv = $env:DCOIR_DOWNLOADS_DIR
try {
  if ($CollectUiEvidence) {
    $discoveryScript = Join-Path $RepoRoot 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09ViewDiscovery.ps1'
    if (-not (Test-Path -LiteralPath $discoveryScript -PathType Leaf)) {
      throw "View discovery launcher not found: $discoveryScript"
    }

    $uiRoot = Join-Path $OutputDir 'ui_evidence'
    New-Item -ItemType Directory -Force -Path $uiRoot | Out-Null

    # Keep generated UI evidence in the same visible governed output tree.
    $env:DCOIR_DOWNLOADS_DIR = $uiRoot

    Write-LogLine 'Collecting UI evidence inside capability map output directory.'
    Write-LogLine "UI evidence root: $uiRoot"
    Write-LogLine "UI evidence target count: $($uiEvidenceTargets.Count)"

    foreach ($targetKey in $uiEvidenceTargets) {
      if ([string]::IsNullOrWhiteSpace($targetKey)) { continue }

      Write-LogLine "Collecting UI evidence target: $targetKey"

      # Use named-parameter splatting instead of string-argument arrays.
      # PowerShell 5.1 can mis-bind script arguments from string arrays when this
      # launcher is called from another script; hashtable splatting keeps
      # TargetKey bound to Invoke-DcoirAirtableWbs09ViewDiscovery.ps1 rather than
      # being interpreted as a positional argument to this wrapper.
      $discoveryParams = @{
        TargetKey = @($targetKey)
        MaxDropdownProbes = $MaxDropdownProbes
      }
      if ($ProbeDropdownOptions.IsPresent) { $discoveryParams['ProbeDropdownOptions'] = $true }
      if ($EnableScreenshots.IsPresent) { $discoveryParams['EnableScreenshots'] = $true }
      if ($UseChromeChannel.IsPresent) { $discoveryParams['UseChromeChannel'] = $true }
      if (-not [string]::IsNullOrWhiteSpace($UserDataDir)) { $discoveryParams['UserDataDir'] = $UserDataDir }
      if (-not [string]::IsNullOrWhiteSpace($ConnectOverCdpUrl)) { $discoveryParams['ConnectOverCdpUrl'] = $ConnectOverCdpUrl }
      if ($KeepBrowserOpenOnFailure.IsPresent) { $discoveryParams['KeepBrowserOpenOnFailure'] = $true }

      & $discoveryScript @discoveryParams
      $exit = $LASTEXITCODE
      if ($exit -ne 0) {
        throw "View discovery failed during capability-map UI evidence collection for target '$targetKey' with exit code $exit"
      }
    }

    if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) {
      $EvidenceRoot = $uiRoot
    }
  }
}
finally {
  $env:DCOIR_DOWNLOADS_DIR = $oldDownloadsEnv
}

if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) {
  $EvidenceRoot = $DownloadsDir
}

$evidenceRootObjects = @()
if (-not [string]::IsNullOrWhiteSpace($EvidenceRoot) -and (Test-Path -LiteralPath $EvidenceRoot)) {
  $evidenceRootObjects = Get-ChildItem -LiteralPath $EvidenceRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^dcoir_wbs09_(view_discovery|view_panel_readback|apply_validation_due_view|apply_sort_direction)_' } |
    Sort-Object LastWriteTime -Descending |
    ForEach-Object { $_.FullName }
}
$evidenceRootsJson = Join-Path $OutputDir 'evidence_roots.ps1_discovered.json'
@($evidenceRootObjects) | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $evidenceRootsJson -Encoding UTF8

$nodeArgs = @(
  $scriptPath,
  '--manifest', $ManifestPath,
  '--output-dir', $OutputDir,
  '--evidence-root', $EvidenceRoot,
  '--evidence-roots-json', $evidenceRootsJson
)

if (-not [string]::IsNullOrWhiteSpace($SchemaJson)) {
  $nodeArgs += @('--schema-json', $SchemaJson)
}
if (-not [string]::IsNullOrWhiteSpace($BaseId)) {
  $nodeArgs += @('--base-id', $BaseId)
}
if ($RequireLiveSchema.IsPresent) {
  $nodeArgs += '--require-live-schema'
}
if ($NoLiveSchema.IsPresent) {
  $nodeArgs += '--no-live-schema'
}
if ($CollectUiEvidence.IsPresent) {
  $nodeArgs += '--ui-evidence-collected'
}

Write-LogLine 'Starting DCOIR WBS09 capability map launcher.'
Write-LogLine "Repo root: $RepoRoot"
Write-LogLine "Output directory: $OutputDir"
Write-LogLine "Manifest path: $ManifestPath"
Write-LogLine "Evidence root: $EvidenceRoot"
Write-LogLine "Evidence roots discovered by PowerShell: $(@($evidenceRootObjects).Count)"
Write-LogLine "Evidence roots JSON: $evidenceRootsJson"
if (-not [string]::IsNullOrWhiteSpace($SchemaJson)) { Write-LogLine "Schema JSON: $SchemaJson" }
if (-not [string]::IsNullOrWhiteSpace($BaseId)) { Write-LogLine 'Airtable base id source: provided/env' }
Write-LogLine "Live schema mode: $(-not $NoLiveSchema.IsPresent); RequireLiveSchema=$($RequireLiveSchema.IsPresent)"
Write-LogLine "Collect UI evidence: $($CollectUiEvidence.IsPresent)"
Write-LogLine "Invoking node with safe argument count: $($nodeArgs.Count)"

$nodeOutput = & node @nodeArgs 2>&1
$nodeExitCode = $LASTEXITCODE

if ($null -ne $nodeOutput) {
  foreach ($line in $nodeOutput) {
    if ($null -ne $line) { Write-Host ([string]$line) }
  }
}

Write-LogLine "Node exit code: $nodeExitCode"
if ($nodeExitCode -ne 0) {
  throw ('WBS09 capability map failed with exit code ' + $nodeExitCode)
}

Write-LogLine 'Capability map launcher completed successfully.'
Write-Host "Output directory: $OutputDir"
