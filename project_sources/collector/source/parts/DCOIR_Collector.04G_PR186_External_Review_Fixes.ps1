<#
.SYNOPSIS
DCOIR collector PR #186 external-review fix overrides.

.DESCRIPTION
Applies narrowly scoped helper overrides for external review findings after the initial
PR #186 review-fix overrides and before the main collector entrypoint runs.

.FILE NAME
DCOIR_Collector.04G_PR186_External_Review_Fixes.ps1

.INPUTS
Current collector globals, run-root directory names, package name, and operator-supplied
or generated RunId value.

.OUTPUTS
Replacement helper functions used by the compiled collector runtime.
#>

<#
.SYNOPSIS
Checks whether an exact custom RunId root is safe to purge before collection.

.DESCRIPTION
Requires the expected run-root name plus collector ownership evidence before a custom
RunId collect may remove a pre-existing exact run root. A state-backed run root is treated
as collector-owned. A no-state run root must satisfy the same collector-created child
structure required by no-state cleanup. Unsafe existing roots are not removed.

.FUNCTION NAME
Test-DCOIRExactCustomRunRootPurgeCandidate

.INPUTS
DirectoryInfo object.

.OUTPUTS
Boolean.
#>
function Test-DCOIRExactCustomRunRootPurgeCandidate {
  param([object]$Directory)
  if (-not $Directory) { return $false }
  if (-not (Test-DCOIRRunDirectoryName -Name $Directory.Name)) { return $false }
  if (Test-Path -LiteralPath (Join-Path $Directory.FullName 'state.json')) { return $true }
  return (Test-DCOIRNoStateCleanupCandidate -Directory $Directory)
}

<#
.SYNOPSIS
Deletes prior collector run directories before a new collect starts.

.DESCRIPTION
Keeps blank/latest automatic purge bounded to timestamp-style collector run roots. When a
custom RunId is supplied for a new collect, also deletes only the exact expected custom
run root when collector ownership is proven by state.json or the no-state cleanup child
structure. If an unsafe exact custom root exists, collection stops before new artifacts are
written. This prevents stale reports, artifacts, logs, or bundles from a previous custom
RunId collect from being mixed into a new evidence bundle without deleting arbitrary
shared-root directories.

.FUNCTION NAME
Purge-PreviousRuns

.INPUTS
Root string and CurrentPackageName string.

.OUTPUTS
No direct output. Deletes prior strict-pattern collector run directories, a proven
collector-owned exact custom run root when applicable, and the previous package file as
side effects. Throws when the exact custom run root is unsafe or remains after deletion.
#>
function Purge-PreviousRuns {
  param([string]$Root,[string]$CurrentPackageName)

  try {
    $currentRunId = [string]$script:RunId
    if (-not [string]::IsNullOrWhiteSpace($currentRunId)) {
      $expectedRunRoot = Get-RunRoot -Root $Root -CurrentRunId $currentRunId
      $expectedRunName = Split-Path -Leaf $expectedRunRoot
      if ((Test-DCOIRRunDirectoryName -Name $expectedRunName) -and
          -not (Test-DCOIRBulkPurgeRunDirectoryName -Name $expectedRunName) -and
          (Test-Path -LiteralPath $expectedRunRoot)) {
        $expectedRunDir = Get-Item -LiteralPath $expectedRunRoot -ErrorAction SilentlyContinue
        if (-not (Test-DCOIRExactCustomRunRootPurgeCandidate -Directory $expectedRunDir)) {
          throw "Existing custom RunId directory is not collector-owned and will not be removed before collect: $expectedRunRoot"
        }
        Remove-Item -LiteralPath $expectedRunRoot -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $expectedRunRoot) {
          throw "Existing custom RunId directory could not be removed before collect: $expectedRunRoot"
        }
      }
    }
  } catch {
    Add-CollectorError "Failed to purge exact custom RunId directory: $($_.Exception.Message)"
    throw
  }

  try {
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
      Where-Object { Test-DCOIRBulkPurgeRunDirectoryName -Name $_.Name }
    foreach ($dir in $dirs) {
      Remove-Item -LiteralPath $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
  } catch {
    Add-CollectorError "Failed to purge previous DCOIR directories: $($_.Exception.Message)"
  }

  try {
    $pkg = Join-Path $Root $CurrentPackageName
    if (Test-Path -LiteralPath $pkg) {
      Remove-Item -LiteralPath $pkg -Force -ErrorAction SilentlyContinue
    }
  } catch {
    Add-CollectorError "Failed to remove previous collector package: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Adds bounded collect fields to the collection metadata artifact when absent.

.DESCRIPTION
Keeps collection_metadata.txt aligned with the run-window fields already emitted in the
metadata report so bundle-level validators and operators can read the bounded collection
shape from either metadata surface.

.FUNCTION NAME
Add-BoundedCollectFieldsToCollectionMetadataText

.INPUTS
Artifact name and candidate text.

.OUTPUTS
Text with Mode, Tier, Hours, and MaxEvents fields appended when the artifact is
collection_metadata.txt and those fields are absent.
#>
function Add-BoundedCollectFieldsToCollectionMetadataText {
  param([string]$Name,[string]$Text)

  if ($Name -ne 'collection_metadata.txt') { return $Text }
  $updated = [string]$Text
  $lines = New-Object System.Collections.ArrayList
  if ($updated -notmatch '(?m)^Mode=') { [void]$lines.Add('Mode=Collect') }
  if ($updated -notmatch '(?m)^Tier=') { [void]$lines.Add(('Tier={0}' -f $Tier)) }
  if ($updated -notmatch '(?m)^Hours=') { [void]$lines.Add(('Hours={0}' -f $Hours)) }
  if ($updated -notmatch '(?m)^MaxEvents=') { [void]$lines.Add(('MaxEvents={0}' -f $MaxEvents)) }
  if (@($lines).Count -gt 0) {
    if (-not $updated.EndsWith([Environment]::NewLine)) { $updated += [Environment]::NewLine }
    $updated += ((@($lines) -join [Environment]::NewLine) + [Environment]::NewLine)
  }
  return $updated
}

<#
.SYNOPSIS
Writes one collector artifact and a section-directory companion copy.

.DESCRIPTION
Preserves the existing prefixed root artifact path returned by Write-ArtifactText while
also writing a same-content companion under final_artifacts/<section>/<name>. The collect
bundle already includes the artifact directory recursively, and the section companion
keeps bundle validation aligned with the documented section/key artifact model without
changing existing response paths, manifests, or upload-budget behavior.

.FUNCTION NAME
Write-ArtifactText

.INPUTS
Artifact directory, section name, artifact name, and text content.

.OUTPUTS
The existing prefixed root artifact path.
#>
function Write-ArtifactText {
  param(
    [string]$ArtifactsDir,
    [string]$Section,
    [string]$Name,
    [string]$Text
  )

  Ensure-Directory -Path $ArtifactsDir
  $prefix = Get-BaselineArtifactPrefix -Name $Name
  $safeSection = ($Section -replace '[\/:*?"<>| ]','_')
  $safeName = ($Name -replace '[\/:*?"<>| ]','_')
  $artifactText = Add-BoundedCollectFieldsToCollectionMetadataText -Name $Name -Text $Text
  $path = Join-Path $ArtifactsDir ("{0}_{1}_{2}" -f $prefix, $safeSection, $safeName)
  Set-Content -Path $path -Value $artifactText -Encoding UTF8

  try {
    if (-not [string]::IsNullOrWhiteSpace($safeSection) -and -not [string]::IsNullOrWhiteSpace($safeName)) {
      $sectionDir = Join-Path $ArtifactsDir $safeSection
      Ensure-Directory -Path $sectionDir
      $sectionPath = Join-Path $sectionDir $safeName
      Set-Content -Path $sectionPath -Value $artifactText -Encoding UTF8
    }
  } catch {
    Add-CollectorError ("Failed to write section companion artifact [{0}/{1}]: {2}" -f $safeSection, $safeName, $_.Exception.Message)
  }

  return $path
}

<#
.SYNOPSIS
Returns Tier 2 deep-check root artifact paths that should be present in collect manifests.

.DESCRIPTION
Finds the prefixed root artifact files emitted for Tier 2 deep checks. These paths are
added to manifest_collect.json so the manifest inventories the same Tier 2 evidence that
is already included in the collect bundle.

.FUNCTION NAME
Get-Tier2DeepCheckManifestArtifactPaths

.INPUTS
Collector state hashtable.

.OUTPUTS
String array of existing Tier 2 deep-check artifact paths.
#>
function Get-Tier2DeepCheckManifestArtifactPaths {
  param([hashtable]$State)

  if (-not $State -or [string]::IsNullOrWhiteSpace([string]$State.ArtifactsDir) -or -not (Test-Path -LiteralPath $State.ArtifactsDir)) { return @() }

  $names = @(
    '28_TIER2_DEEP_CHECKS_tier2_reg_ifeo.txt',
    '29_TIER2_DEEP_CHECKS_tier2_reg_winlogon.txt',
    '30_TIER2_DEEP_CHECKS_tier2_reg_lsa.txt',
    '31_TIER2_DEEP_CHECKS_tier2_wmi_persistence.txt',
    '32_TIER2_DEEP_CHECKS_tier2_net_share.txt',
    '33_TIER2_DEEP_CHECKS_tier2_net_session.txt',
    '34_TIER2_DEEP_CHECKS_tier2_firewall_profiles.txt'
  )

  $paths = New-Object System.Collections.ArrayList
  foreach ($name in $names) {
    $path = Join-Path $State.ArtifactsDir $name
    if (Test-Path -LiteralPath $path) { [void]$paths.Add($path) }
  }
  return @($paths)
}

<#
.SYNOPSIS
Creates the run manifest JSON file with Tier 2 deep-check artifact inventory repair.

.DESCRIPTION
Preserves the original manifest behavior while appending existing Tier 2 deep-check root
artifact paths for Collect/T2 manifests. This keeps manifest_collect.json aligned with the
collect bundle contents and avoids downstream evidence-inventory gaps.

.FUNCTION NAME
New-Manifest

.INPUTS
ManifestPath, State, ModeName, TierName, Files array, ToolMap hashtable, and Extra
hashtable.

.OUTPUTS
String manifest path.
#>
function New-Manifest {
  param(
    [string]$ManifestPath,
    [hashtable]$State,
    [string]$ModeName,
    [string]$TierName,
    [string[]]$Files,
    [hashtable]$ToolMap,
    [hashtable]$Extra
  )

  $manifestFiles = New-Object System.Collections.ArrayList
  foreach ($file in @($Files)) {
    if ([string]::IsNullOrWhiteSpace($file)) { continue }
    if (-not @($manifestFiles).Contains($file)) { [void]$manifestFiles.Add($file) }
  }

  if (($ModeName -eq 'Collect') -and ($TierName -eq 'T2')) {
    foreach ($tier2Path in @(Get-Tier2DeepCheckManifestArtifactPaths -State $State)) {
      if (-not @($manifestFiles).Contains($tier2Path)) { [void]$manifestFiles.Add($tier2Path) }
    }
  }

  $manifest = [ordered]@{
    host = $env:COMPUTERNAME
    run_id = $State.RunId
    mode = $ModeName
    tier = $TierName
    script_version = $ScriptVersion
    created_local = (Get-Date).ToString('o')
    created_utc = (Get-Date).ToUniversalTime().ToString('o')
    files = @($manifestFiles)
    notes = @($Global:CollectorNotes)
    errors = @($Global:CollectorErrors)
    recommendations = @($Global:RecommendedActions)
    tool_map = $ToolMap
    extra = $Extra
  }
  Set-Content -Path $ManifestPath -Value ($manifest | ConvertTo-Json -Depth 12) -Encoding UTF8
  return $ManifestPath
}

<#
.SYNOPSIS
Synchronizes the collection metadata section companion before bundling.

.DESCRIPTION
Uses the existing prefixed root collection metadata artifact as the source of truth and
rewrites final_artifacts/COLLECTION_METADATA/collection_metadata.txt immediately before
bundle creation. This keeps the strict Tier 2 bundle verifier aligned with the emitted
collector artifact shape without fabricating metadata when the root artifact is missing.

.FUNCTION NAME
Sync-CollectionMetadataCompanionArtifact

.INPUTS
ArtifactsDir string.

.OUTPUTS
No direct output. Writes or refreshes the section companion artifact when the root
collection metadata artifact exists.
#>
function Sync-CollectionMetadataCompanionArtifact {
  param([string]$ArtifactsDir)

  if ([string]::IsNullOrWhiteSpace($ArtifactsDir) -or -not (Test-Path -LiteralPath $ArtifactsDir)) { return }

  $rootPath = Join-Path $ArtifactsDir '01_COLLECTION_METADATA_collection_metadata.txt'
  if (-not (Test-Path -LiteralPath $rootPath)) { return }

  try {
    $artifactText = Get-Content -LiteralPath $rootPath -Raw
    $sectionDir = Join-Path $ArtifactsDir 'COLLECTION_METADATA'
    Ensure-Directory -Path $sectionDir
    $sectionPath = Join-Path $sectionDir 'collection_metadata.txt'
    Set-Content -LiteralPath $sectionPath -Value $artifactText -Encoding UTF8
  } catch {
    Add-CollectorError ("Failed to synchronize collection metadata companion artifact: {0}" -f $_.Exception.Message)
  }
}

<#
.SYNOPSIS
Creates one ZIP bundle from the supplied paths after synchronizing metadata companions.

.DESCRIPTION
Preserves the original New-BundleZip behavior while refreshing collection metadata
section companions for any final_artifacts directory in the bundle input list. This makes
bundle-level metadata validation deterministic even when the verifier reads the section
companion path instead of the prefixed root artifact path.

.FUNCTION NAME
New-BundleZip

.INPUTS
BundlesDir string, BundleName string, and Paths string array.

.OUTPUTS
String bundle ZIP path.
#>
function New-BundleZip {
  param(
    [string]$BundlesDir,
    [string]$BundleName,
    [string[]]$Paths
  )

  foreach ($candidatePath in @($Paths)) {
    if ([string]::IsNullOrWhiteSpace($candidatePath) -or -not (Test-Path -LiteralPath $candidatePath)) { continue }
    $item = Get-Item -LiteralPath $candidatePath -ErrorAction SilentlyContinue
    if ($item -and $item.PSIsContainer -and ($item.Name -eq 'final_artifacts')) {
      Sync-CollectionMetadataCompanionArtifact -ArtifactsDir $item.FullName
    }
  }

  Ensure-Directory -Path $BundlesDir
  $bundlePath = Join-Path $BundlesDir $BundleName
  if (Test-Path -LiteralPath $bundlePath) {
    Remove-Item -LiteralPath $bundlePath -Force -ErrorAction SilentlyContinue
  }
  $existing = @($Paths | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
  if (@($existing).Count -eq 0) {
    throw 'No bundle inputs were found.'
  }
  Compress-Archive -LiteralPath $existing -DestinationPath $bundlePath -CompressionLevel Optimal -Force
  return $bundlePath
}
