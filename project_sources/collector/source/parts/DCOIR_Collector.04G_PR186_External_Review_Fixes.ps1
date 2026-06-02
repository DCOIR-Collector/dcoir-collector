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
Deletes prior collector run directories before a new collect starts.

.DESCRIPTION
Keeps blank/latest automatic purge bounded to timestamp-style collector run roots. When a
custom RunId is supplied for a new collect, also deletes only the exact expected custom
run root before Initialize-RunStructure can reuse it. If that exact root cannot be
removed, collection stops before new artifacts are written or bundled. This prevents
stale reports, artifacts, logs, or bundles from a previous custom-RunId collect from
being mixed into a new evidence bundle without broadening blank/latest cleanup behavior.

.FUNCTION NAME
Purge-PreviousRuns

.INPUTS
Root string and CurrentPackageName string.

.OUTPUTS
No direct output. Deletes prior strict-pattern collector run directories, the exact
expected custom run root when applicable, and the previous package file as side effects.
Throws when the exact custom run root remains after deletion.
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
