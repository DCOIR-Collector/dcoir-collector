<#
.SYNOPSIS
DCOIR collector PR #247 external-review fix helpers.

.DESCRIPTION
Applies narrowly scoped helper overrides for confirmation-decline paths found during the
PR #247 review loop. This part loads after the earlier helper definitions and before the
main collector entrypoint.

.FILE NAME
DCOIR_Collector.04I_PR247_External_Review_Fixes.ps1

.INPUTS
Current collector globals, run-root directory names, package name, and artifact paths.

.OUTPUTS
Maintained helper functions used by the compiled collector runtime.
#>

function Set-CollectPrepSkipReason {
  param([string]$Reason)
  $script:CollectPrepSkipReason = $Reason
}

<#
.SYNOPSIS
Deletes prior collector run directories before a new collect starts.

.DESCRIPTION
Overrides the earlier purge helper so a declined exact custom RunId purge follows the
same skipped collect-prep contract as declined package cleanup. Unsafe custom roots and
failed removals still stop collection as errors.

.FUNCTION NAME
Purge-PreviousRuns

.INPUTS
Root string and CurrentPackageName string.

.OUTPUTS
Boolean true when prior run/package purge did not block collect startup, false when a
required confirmation-decline path skipped collect preparation.
#>
function Purge-PreviousRuns {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param([string]$Root,[string]$CurrentPackageName)

  Set-CollectPrepSkipReason -Reason $null

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
        if ($PSCmdlet.ShouldProcess($expectedRunRoot, 'Remove existing custom collector run root')) {
          Remove-Item -LiteralPath $expectedRunRoot -Recurse -Force -ErrorAction SilentlyContinue
          if (Test-Path -LiteralPath $expectedRunRoot) {
            throw "Existing custom RunId directory could not be removed before collect: $expectedRunRoot"
          }
        } else {
          Set-CollectPrepSkipReason -Reason 'CUSTOM_RUN_PURGE_SKIPPED'
          return $false
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
      if ($PSCmdlet.ShouldProcess($dir.FullName, 'Remove previous collector run directory')) {
        Remove-Item -LiteralPath $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
      }
    }
  } catch {
    Add-CollectorError "Failed to purge previous DCOIR directories: $($_.Exception.Message)"
  }

  try {
    $pkg = Join-Path $Root $CurrentPackageName
    if (Test-Path -LiteralPath $pkg) {
      if ($PSCmdlet.ShouldProcess($pkg, 'Remove previous collector package')) {
        Remove-Item -LiteralPath $pkg -Force -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $pkg) {
          Set-CollectPrepSkipReason -Reason 'PACKAGE_PURGE_SKIPPED'
          return $false
        }
      } else {
        Set-CollectPrepSkipReason -Reason 'PACKAGE_PURGE_SKIPPED'
        return $false
      }
    }
  } catch {
    Add-CollectorError "Failed to remove previous collector package: $($_.Exception.Message)"
    Set-CollectPrepSkipReason -Reason 'PACKAGE_PURGE_SKIPPED'
    return $false
  }

  return $true
}

function Remove-UploadSafeChunkCompanionSet {
  param([System.Collections.ArrayList]$ChunkPaths)

  foreach ($chunkPath in @($ChunkPaths)) {
    if ([string]::IsNullOrWhiteSpace([string]$chunkPath)) { continue }
    if (Test-Path -LiteralPath $chunkPath) {
      Remove-Item -LiteralPath $chunkPath -Force -ErrorAction SilentlyContinue
    }
  }
  $ChunkPaths.Clear()
}

<#
.SYNOPSIS
Splits a real text artifact into upload-safe chunk companions.

.DESCRIPTION
Overrides the earlier chunk helper so any declined per-chunk write aborts the entire
chunk companion set as skipped instead of throwing through the collect top-level handler.
Already-written companions from the same helper call are removed before returning null.

.FUNCTION NAME
Split-TextArtifactIntoUploadSafeChunks

.INPUTS
Source artifact path, artifact directory, source key, target chunk size, and origin label.

.OUTPUTS
Ordered chunk metadata hashtable, or null when the complete chunk set was skipped.
#>
function Split-TextArtifactIntoUploadSafeChunks {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param(
    [string]$SourcePath,
    [string]$ArtifactsDir,
    [string]$SourceKey,
    [int]$TargetChunkKB,
    [string]$Origin = 'collector_production_upload_safe'
  )

  $chunkPaths = New-Object System.Collections.ArrayList
  $chunkSizes = New-Object System.Collections.ArrayList
  $chunkSha256 = New-Object System.Collections.ArrayList
  $targetBytes = [Math]::Max(1, $TargetChunkKB) * 1024
  $sourceBytes = [System.IO.File]::ReadAllBytes($SourcePath)
  $safeKey = ($SourceKey -replace '[\/:*?"<>| ]','_')
  $chunkIndex = 1
  $offset = 0

  if ($sourceBytes.Length -eq 0) {
    $chunkPath = Join-Path $ArtifactsDir ("90_UPLOAD_SAFE_CHUNKS_{0}_chunk_{1:000}.txt" -f $safeKey, $chunkIndex)
    if ($PSCmdlet.ShouldProcess($chunkPath, 'Write upload-safe empty chunk companion')) {
      [System.IO.File]::WriteAllBytes($chunkPath, [byte[]]@())
      [void]$chunkPaths.Add($chunkPath)
      [void]$chunkSizes.Add((Get-FileSizeKB -Path $chunkPath))
      [void]$chunkSha256.Add((Get-FileSha256 -Path $chunkPath))
    } else {
      Remove-UploadSafeChunkCompanionSet -ChunkPaths $chunkPaths
      return $null
    }
  }

  while ($offset -lt $sourceBytes.Length) {
    $length = Get-Utf8SafeChunkLength -Bytes $sourceBytes -Offset $offset -TargetBytes $targetBytes
    if ($length -le 0) { $length = [Math]::Min($targetBytes, ($sourceBytes.Length - $offset)) }
    $chunkBytes = New-Object byte[] $length
    [Array]::Copy($sourceBytes, $offset, $chunkBytes, 0, $length)
    $chunkPath = Join-Path $ArtifactsDir ("90_UPLOAD_SAFE_CHUNKS_{0}_chunk_{1:000}.txt" -f $safeKey, $chunkIndex)
    if ($PSCmdlet.ShouldProcess($chunkPath, 'Write upload-safe chunk companion')) {
      [System.IO.File]::WriteAllBytes($chunkPath, $chunkBytes)
      [void]$chunkPaths.Add($chunkPath)
      [void]$chunkSizes.Add((Get-FileSizeKB -Path $chunkPath))
      [void]$chunkSha256.Add((Get-FileSha256 -Path $chunkPath))
    } else {
      Remove-UploadSafeChunkCompanionSet -ChunkPaths $chunkPaths
      return $null
    }
    $offset += $length
    $chunkIndex += 1
  }

  return [ordered]@{
    origin = $Origin
    source_artifact_key = $SourceKey
    source_path = $SourcePath
    source_size_kb = Get-FileSizeKB -Path $SourcePath
    source_size_bytes = $sourceBytes.Length
    source_sha256 = Get-FileSha256 -Path $SourcePath
    target_chunk_kb = $TargetChunkKB
    chunk_count = @($chunkPaths).Count
    chunk_paths = @($chunkPaths)
    chunk_file_sizes_kb = @($chunkSizes)
    chunk_sha256 = @($chunkSha256)
    reconstruction_order = 'Concatenate chunk_paths in listed order as bytes to reconstruct the original source artifact exactly.'
  }
}

<#
.SYNOPSIS
Creates upload-safe chunk companions for selected oversized real artifacts.

.DESCRIPTION
Overrides the earlier companion builder so skipped chunk sets are simply omitted from the
manifest row list instead of being treated as successful empty companions.

.FUNCTION NAME
New-ProductionUploadSafeChunkCompanions

.INPUTS
Collector state, artifact map, and upload budget.

.OUTPUTS
Array of ordered manifest rows.
#>
function New-ProductionUploadSafeChunkCompanions {
  [CmdletBinding()]
  param([hashtable]$State,[hashtable]$ArtifactMap,[hashtable]$Budget)

  $rows = New-Object System.Collections.ArrayList
  foreach ($key in @('security_filtered','powershell_operational_filtered','taskscheduler_operational_filtered')) {
    if (-not $ArtifactMap.ContainsKey($key)) { continue }
    $sourcePath = [string]$ArtifactMap[$key]
    if ([string]::IsNullOrWhiteSpace($sourcePath) -or -not (Test-Path -LiteralPath $sourcePath)) { continue }
    $sourceSizeKB = Get-FileSizeKB -Path $sourcePath
    if ($sourceSizeKB -le [int]$Budget.SafePerFileKB) { continue }

    $chunkResult = Split-TextArtifactIntoUploadSafeChunks -SourcePath $sourcePath -ArtifactsDir $State.ArtifactsDir -SourceKey $key -TargetChunkKB ([Math]::Min(700, [int]$Budget.SafePerFileKB))
    if (-not $chunkResult) { continue }
    if ([int]$chunkResult.chunk_count -le 0) { continue }
    [void]$rows.Add($chunkResult)
    foreach ($chunkPath in @($chunkResult.chunk_paths)) {
      [void]$ArtifactMap.Add(("{0}_upload_safe_chunk_{1:000}" -f $key, (@($ArtifactMap.Keys | Where-Object { $_ -like ("{0}_upload_safe_chunk_*" -f $key) }).Count + 1)), $chunkPath)
    }
  }

  return @($rows)
}
