<#
.SYNOPSIS
DCOIR collector JSON, state, and array utility helpers.

.DESCRIPTION
Provides shared JSON serialization guardrails, state-path helpers, state persistence,
no-state cleanup, object-to-hashtable conversion, and ArrayList normalization helpers.

.FILE NAME
DCOIR_Collector.01B_Json_State_And_Array_Utilities.ps1

.INPUTS
Collector state objects, JSON-serializable objects, filesystem paths, RunId values, and
generic object arrays.

.OUTPUTS
Serialized JSON text, state path values, normalized hashtables, ArrayList instances, and
cleanup results.
#>

<#
.SYNOPSIS
Records every exact ellipsis string path inside one object graph.

.DESCRIPTION
Walks dictionaries, arrays, and PSObject properties to find exact string values equal to
"...". The resulting path set is used to distinguish legitimate ellipsis strings already
present in source objects from ConvertTo-Json depth truncation sentinels introduced during
serialization.

.FUNCTION NAME
Add-CollectorJsonEllipsisPaths

.INPUTS
InputObject, current path, destination path set, max traversal depth, and current depth.

.OUTPUTS
No direct output. Updates PathSet as a side effect.
#>
function Add-CollectorJsonEllipsisPaths {
  param(
    [object]$InputObject,
    [string]$Path,
    [hashtable]$PathSet,
    [int]$MaxDepth,
    [int]$CurrentDepth = 0
  )

  if ($null -eq $InputObject) { return }
  if ([string]::IsNullOrWhiteSpace($Path)) { $Path = '$' }
  if ($InputObject -is [string]) {
    if ([string]$InputObject -eq '...') { $PathSet[$Path] = $true }
    return
  }
  if ($CurrentDepth -ge $MaxDepth) { return }

  if ($InputObject -is [System.Collections.IDictionary]) {
    foreach ($key in @($InputObject.Keys)) {
      $childPath = ('{0}.{1}' -f $Path, [string]$key)
      Add-CollectorJsonEllipsisPaths -InputObject $InputObject[$key] -Path $childPath -PathSet $PathSet -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1)
    }
    return
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
    $index = 0
    foreach ($item in @($InputObject)) {
      $childPath = ('{0}[{1}]' -f $Path, $index)
      Add-CollectorJsonEllipsisPaths -InputObject $item -Path $childPath -PathSet $PathSet -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1)
      $index += 1
    }
    return
  }

  $psProps = @()
  try { $psProps = @($InputObject.PSObject.Properties) } catch { $psProps = @() }
  foreach ($prop in $psProps) {
    $childPath = ('{0}.{1}' -f $Path, [string]$prop.Name)
    Add-CollectorJsonEllipsisPaths -InputObject $prop.Value -Path $childPath -PathSet $PathSet -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1)
  }
}

<#
.SYNOPSIS
Returns exact ellipsis string paths from one object graph.

.DESCRIPTION
Creates a path set for exact "..." strings found in an object graph. This supports
post-serialization truncation detection without flagging legitimate ellipsis values.

.FUNCTION NAME
Get-CollectorJsonEllipsisPathSet

.INPUTS
InputObject and optional max traversal depth.

.OUTPUTS
Hashtable keyed by path.
#>
function Get-CollectorJsonEllipsisPathSet {
  param([object]$InputObject,[int]$MaxDepth = 25)
  $paths = @{}
  Add-CollectorJsonEllipsisPaths -InputObject $InputObject -Path '$' -PathSet $paths -MaxDepth $MaxDepth
  return $paths
}

<#
.SYNOPSIS
Records object paths that exceed one ConvertTo-Json depth policy.

.DESCRIPTION
Walks dictionaries, arrays, and PSObject properties before serialization. PowerShell does
not consistently emit an exact "..." sentinel when ConvertTo-Json exceeds depth, so this
preflight identifies non-scalar objects that would be serialized at or beyond the policy
depth and records their paths as truncation risks.

.FUNCTION NAME
Add-CollectorJsonDepthRiskPaths

.INPUTS
InputObject, current path, destination path set, max JSON depth, and current depth.

.OUTPUTS
No direct output. Updates PathSet as a side effect.
#>
function Add-CollectorJsonDepthRiskPaths {
  param(
    [object]$InputObject,
    [string]$Path,
    [hashtable]$PathSet,
    [int]$MaxDepth,
    [int]$CurrentDepth = 0
  )

  if ($null -eq $InputObject) { return }
  if ([string]::IsNullOrWhiteSpace($Path)) { $Path = '$' }
  if (($InputObject -is [string]) -or ($InputObject -is [System.ValueType])) { return }
  if ($CurrentDepth -ge $MaxDepth) {
    $PathSet[$Path] = $true
    return
  }

  if ($InputObject -is [System.Collections.IDictionary]) {
    foreach ($key in @($InputObject.Keys)) {
      $childPath = ('{0}.{1}' -f $Path, [string]$key)
      Add-CollectorJsonDepthRiskPaths -InputObject $InputObject[$key] -Path $childPath -PathSet $PathSet -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1)
    }
    return
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
    $index = 0
    foreach ($item in @($InputObject)) {
      $childPath = ('{0}[{1}]' -f $Path, $index)
      Add-CollectorJsonDepthRiskPaths -InputObject $item -Path $childPath -PathSet $PathSet -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1)
      $index += 1
    }
    return
  }

  $psProps = @()
  try { $psProps = @($InputObject.PSObject.Properties) } catch { $psProps = @() }
  foreach ($prop in $psProps) {
    $childPath = ('{0}.{1}' -f $Path, [string]$prop.Name)
    Add-CollectorJsonDepthRiskPaths -InputObject $prop.Value -Path $childPath -PathSet $PathSet -MaxDepth $MaxDepth -CurrentDepth ($CurrentDepth + 1)
  }
}

<#
.SYNOPSIS
Returns object paths that exceed one ConvertTo-Json depth policy.

.DESCRIPTION
Creates a path set for non-scalar source objects that would be serialized at or beyond the
configured JSON depth.

.FUNCTION NAME
Get-CollectorJsonDepthRiskPathSet

.INPUTS
InputObject and max JSON depth.

.OUTPUTS
Hashtable keyed by path.
#>
function Get-CollectorJsonDepthRiskPathSet {
  param([object]$InputObject,[int]$MaxDepth = 20)
  $paths = @{}
  Add-CollectorJsonDepthRiskPaths -InputObject $InputObject -Path '$' -PathSet $paths -MaxDepth $MaxDepth
  return $paths
}

<#
.SYNOPSIS
Serializes one collector object to JSON with truncation detection.

.DESCRIPTION
Uses one collector-wide JSON depth policy, checks the source graph for depth-risk paths,
parses the emitted JSON back, and compares exact ellipsis-string paths against the
original object. If source depth exceeds policy or ConvertTo-Json introduced an ellipsis
sentinel at a path that was not already an exact ellipsis string, the helper records an
operator-visible collector error and can throw for truth surfaces.

.FUNCTION NAME
Convert-ToCollectorJsonText

.INPUTS
InputObject, optional depth, compression flag, newline flag, label, and truncation policy.

.OUTPUTS
JSON string, optionally newline-terminated.
#>
function Convert-ToCollectorJsonText {
  param(
    [object]$InputObject,
    [int]$Depth = 20,
    [switch]$Compress,
    [switch]$AppendNewline,
    [string]$Label = 'collector JSON',
    [switch]$ThrowOnTruncation
  )

  $jsonArgs = @{ Depth = $Depth; ErrorAction = 'Stop' }
  if ($Compress) { $jsonArgs['Compress'] = $true }
  $sourceDepthRisks = Get-CollectorJsonDepthRiskPathSet -InputObject $InputObject -MaxDepth $Depth
  if (@($sourceDepthRisks.Keys).Count -gt 0) {
    $depthRiskPaths = @($sourceDepthRisks.Keys | Sort-Object)
    $message = ('JSON serialization for [{0}] exceeds configured depth {1}; non-scalar source object paths at risk: {2}' -f $Label, $Depth, ($depthRiskPaths -join ', '))
    Add-CollectorError $message
    if ($ThrowOnTruncation) { throw $message }
  }
  $json = $InputObject | ConvertTo-Json @jsonArgs

  try {
    $parsed = $json | ConvertFrom-Json -ErrorAction Stop
    $emittedEllipsis = Get-CollectorJsonEllipsisPathSet -InputObject $parsed -MaxDepth ([Math]::Max($Depth + 5, 25))
    if (@($emittedEllipsis.Keys).Count -gt 0) {
      $sourceEllipsis = Get-CollectorJsonEllipsisPathSet -InputObject $InputObject -MaxDepth ([Math]::Max($Depth + 5, 25))
      $truncatedPaths = @($emittedEllipsis.Keys | Where-Object { -not $sourceEllipsis.ContainsKey($_) } | Sort-Object)
      if (@($truncatedPaths).Count -gt 0) {
        $message = ('JSON serialization for [{0}] appears truncated at depth {1}; ConvertTo-Json emitted ellipsis sentinel at: {2}' -f $Label, $Depth, ($truncatedPaths -join ', '))
        Add-CollectorError $message
        if ($ThrowOnTruncation) { throw $message }
      }
    }
  } catch {
    if ($ThrowOnTruncation) { throw }
  }

  if ($AppendNewline) { return ($json + [Environment]::NewLine) }
  return $json
}

<#
.SYNOPSIS
Formats one process-capture object into durable text.

.DESCRIPTION
Builds the combined command, exit-code, stdout, and stderr text block used in many
collector artifacts.

.FUNCTION NAME
Get-CombinedProcessOutput

.INPUTS
Result object returned by Invoke-ProcessCapture or Invoke-CmdCapture.

.OUTPUTS
String containing the combined process output text.
#>
function Get-CombinedProcessOutput {
  param($Result)
  $lines = New-Object System.Collections.ArrayList
  [void]$lines.Add(("COMMAND={0}" -f $Result.Command))
  [void]$lines.Add(("EXIT_CODE={0}" -f $Result.ExitCode))
  [void]$lines.Add("")
  [void]$lines.Add("STDOUT:")
  [void]$lines.Add(($Result.StdOut))
  [void]$lines.Add("")
  [void]$lines.Add("STDERR:")
  [void]$lines.Add(($Result.StdErr))
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Creates a new collector run identifier.

.DESCRIPTION
Returns the current local timestamp in the standard DCOIR run-id format.

.FUNCTION NAME
Get-NewRunId

.INPUTS
No direct parameters.

.OUTPUTS
String run identifier.
#>
function Get-NewRunId {
  return (Get-Date -Format "yyyyMMdd_HHmmss")
}

<#
.SYNOPSIS
Builds the run-root path for one run identifier.

.DESCRIPTION
Combines the root path, hostname, and run identifier into the standard DCOIR run-root
folder name.

.FUNCTION NAME
Get-RunRoot

.INPUTS
Root string and CurrentRunId string.

.OUTPUTS
String run-root path.
#>
function Get-RunRoot {
  param([string]$Root,[string]$CurrentRunId)
  return (Join-Path $Root ("DCOIR_{0}_{1}" -f $env:COMPUTERNAME, $CurrentRunId))
}


<#
.SYNOPSIS
Builds the state-file path for one run.

.DESCRIPTION
Returns the state.json path inside the resolved run-root directory.

.FUNCTION NAME
Get-StatePath

.INPUTS
Root string and CurrentRunId string.

.OUTPUTS
String state-file path.
#>
function Get-StatePath {
  param([string]$Root,[string]$CurrentRunId)
  return (Join-Path (Get-RunRoot -Root $Root -CurrentRunId $CurrentRunId) "state.json")
}

<#
.SYNOPSIS
Saves the collector state to disk.

.DESCRIPTION
Serializes the supplied state hashtable to JSON and writes it to the state path stored
inside the state object.

.FUNCTION NAME
Save-State

.INPUTS
Mandatory State hashtable.

.OUTPUTS
State path string when state.json is written, or null when WhatIf/confirmation skips the write.
#>
function Save-State {
  [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
  param([Parameter(Mandatory=$true)][hashtable]$State)
  $json = Convert-ToCollectorJsonText -InputObject $State -Label 'state.json' -ThrowOnTruncation
  if ($PSCmdlet.ShouldProcess($State.StatePath, 'Write collector state')) {
    Set-Content -Path $State.StatePath -Value $json -Encoding UTF8 -ErrorAction Stop
    return $State.StatePath
  }
  return $null
}

<#
.SYNOPSIS
Removes a bounded no-state collector run directory.

.DESCRIPTION
Used by cleanup mode after early collect failures where a run directory was created before
state.json was saved. Deletes only the expected or latest DCOIR_* run directory under the
selected OutRoot and the configured package file under that same root.

.FUNCTION NAME
Invoke-NoStateCleanup

.INPUTS
Root string, optional CurrentRunId, and current package name.

.OUTPUTS
Hashtable describing cleanup status and targets.
#>
function Invoke-NoStateCleanup {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param([string]$Root,[string]$CurrentRunId,[string]$CurrentPackageName)

  $targets = New-Object System.Collections.ArrayList
  $runDir = Find-LatestDCOIRRunDirectory -Root $Root -CurrentRunId $CurrentRunId
  if ($runDir -and (Test-DCOIRNoStateCleanupCandidate -Directory $runDir)) {
    [void]$targets.Add($runDir.FullName)
  }

  $pkg = Join-Path $Root $CurrentPackageName
  if (Test-Path -LiteralPath $pkg) { [void]$targets.Add($pkg) }

  $removed = New-Object System.Collections.ArrayList
  $failed = New-Object System.Collections.ArrayList
  $skipped = New-Object System.Collections.ArrayList
  foreach ($target in @($targets)) {
    try {
      if ($PSCmdlet.ShouldProcess($target, 'Remove no-state collector cleanup target')) {
        Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop
        [void]$removed.Add($target)
      } else {
        [void]$skipped.Add($target)
      }
    } catch {
      [void]$failed.Add(("{0} :: {1}" -f $target, $_.Exception.Message))
    }
  }

  $status = if (@($targets).Count -eq 0) {
    'NO_TARGET_FOUND'
  } elseif (@($skipped).Count -gt 0 -and @($removed).Count -eq 0 -and @($failed).Count -eq 0) {
    'SKIPPED'
  } elseif (@($skipped).Count -gt 0 -or @($failed).Count -gt 0) {
    'PARTIAL'
  } else {
    'MISSING_STATE_ORPHAN_CLEANED'
  }

  return @{
    Status = $status
    RunRoot = if ($runDir) { $runDir.FullName } else { $null }
    RemovedTargets = @($removed)
    FailedTargets = @($failed)
    SkippedTargets = @($skipped)
    TargetCount = @($targets).Count
    RemovedCount = @($removed).Count
    SkippedCount = @($skipped).Count
    FailedCount = @($failed).Count
  }
}

<#
.SYNOPSIS
Recursively converts a deserialized state object into plain hashtables and arrays.

.DESCRIPTION
Normalizes dictionaries, enumerable collections, and PSObject properties into plain
PowerShell hashtables and arrays so saved state can be reused consistently. Stops with a
descriptive error when the object graph exceeds the configured depth limit.

.FUNCTION NAME
Convert-StateObjectToHashtable

.INPUTS
InputObject to normalize, optional maximum depth, current recursion depth, and current
object path.

.OUTPUTS
Hashtable, array, scalar, or null matching the normalized input structure.
#>
function Convert-StateObjectToHashtable {
  param(
    [object]$InputObject,
    [int]$Depth = 20,
    [int]$CurrentDepth = 0,
    [string]$Path = '$'
  )

  if ($null -eq $InputObject) { return $null }
  if ([string]::IsNullOrWhiteSpace($Path)) { $Path = '$' }
  if (($InputObject -is [string]) -or ($InputObject -is [System.ValueType])) { return $InputObject }
  if ($CurrentDepth -ge $Depth) {
    throw ('Convert-StateObjectToHashtable exceeded configured depth {0} at path {1}.' -f $Depth, $Path)
  }

  if ($InputObject -is [System.Collections.IDictionary]) {
    $hash = @{}
    foreach ($key in @($InputObject.Keys)) {
      $childPath = ('{0}.{1}' -f $Path, [string]$key)
      $hash[$key] = Convert-StateObjectToHashtable -InputObject $InputObject[$key] -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath
    }
    return $hash
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
    $list = @()
    $index = 0
    foreach ($item in @($InputObject)) {
      $childPath = ('{0}[{1}]' -f $Path, $index)
      $list += ,(Convert-StateObjectToHashtable -InputObject $item -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath)
      $index += 1
    }
    return ,$list
  }

  $psProps = @()
  try { $psProps = @($InputObject.PSObject.Properties) } catch { $psProps = @() }
  if (@($psProps).Count -gt 0 -and -not ($InputObject -is [string])) {
    $hash = @{}
    foreach ($prop in $psProps) {
      $childPath = ('{0}.{1}' -f $Path, [string]$prop.Name)
      $hash[$prop.Name] = Convert-StateObjectToHashtable -InputObject $prop.Value -Depth $Depth -CurrentDepth ($CurrentDepth + 1) -Path $childPath
    }
    return $hash
  }

  return $InputObject
}

<#
.SYNOPSIS
Normalizes one input into an ArrayList.

.DESCRIPTION
Returns an empty ArrayList for null, expands enumerable non-string/non-dictionary input
into an ArrayList, or wraps a single scalar object into an ArrayList.

.FUNCTION NAME
Convert-ToArrayList

.INPUTS
InputObject to normalize.

.OUTPUTS
System.Collections.ArrayList.
#>
function Convert-ToArrayList {
  param([object]$InputObject)

  $list = New-Object System.Collections.ArrayList

  if ($null -eq $InputObject) {
    return $list
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string]) -and -not ($InputObject -is [System.Collections.IDictionary])) {
    foreach ($item in $InputObject) {
      [void]$list.Add($item)
    }
    return $list
  }

  [void]$list.Add($InputObject)
  return $list
}
