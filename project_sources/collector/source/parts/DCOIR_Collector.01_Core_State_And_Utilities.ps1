<#
.SYNOPSIS
DCOIR collector core state and utility helpers.

.DESCRIPTION
Provides the core logging, filesystem, state-management, command-capture, artifact,
process, event, staging, manifest, and packaging helpers used across collect, enrich,
cleanup, validation, and bundle-generation paths.

.FILE NAME
DCOIR_Collector.01_Core_State_And_Utilities.ps1

.INPUTS
Collector runtime globals, filesystem paths, command/process details, state objects,
tool names, event objects, and artifact/report content.

.OUTPUTS
Collector notes/errors/recommendations, command-capture objects and text, state and
artifact paths, manifest/bundle outputs, and supporting helper return values.
#>

<#
.SYNOPSIS
Adds one collector error to the in-memory error list and optional error log.

.DESCRIPTION
Validates the supplied message, appends it to the global collector error list, and
writes a timestamped entry to the durable errors log when that log path is configured.

.FUNCTION NAME
Add-CollectorError

.INPUTS
Message string.

.OUTPUTS
No direct output. Updates global error state and optional log file.
#>
function Add-CollectorError {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:CollectorErrors.Add($Message)
  if ($Global:ErrorsLogPath) {
    Add-Content -Path $Global:ErrorsLogPath -Value ("[{0}] ERROR {1}" -f ((Get-Date).ToUniversalTime().ToString("o")), $Message) -Encoding UTF8
  }
}

<#
.SYNOPSIS
Adds one collector note to the in-memory notes list.

.DESCRIPTION
Ignores blank input and appends a note to the global collector notes collection.

.FUNCTION NAME
Add-CollectorNote

.INPUTS
Message string.

.OUTPUTS
No direct output. Updates global note state.
#>
function Add-CollectorNote {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:CollectorNotes.Add($Message)
}

<#
.SYNOPSIS
Adds one analyst recommendation to the in-memory recommendation list.

.DESCRIPTION
Ignores blank input and appends the supplied recommendation to the global follow-up
queue used by metadata and analyst review artifacts.

.FUNCTION NAME
Add-Recommendation

.INPUTS
Message string.

.OUTPUTS
No direct output. Updates global recommendation state.
#>
function Add-Recommendation {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:RecommendedActions.Add($Message)
}

<#
.SYNOPSIS
Ensures that one directory exists.

.DESCRIPTION
Creates the requested directory path when it does not already exist.

.FUNCTION NAME
Ensure-Directory

.INPUTS
Mandatory Path string.

.OUTPUTS
No direct output. Creates the directory as a side effect when needed.
#>
function Ensure-Directory {
  param([Parameter(Mandatory=$true)][string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -Path $Path -ItemType Directory -Force | Out-Null
  }
}

<#
.SYNOPSIS
Deletes one path when it exists.

.DESCRIPTION
Silently removes the supplied file or directory path when it is nonblank and present.

.FUNCTION NAME
Remove-IfExists

.INPUTS
LiteralPath string.

.OUTPUTS
No direct output. Removes the target as a side effect when present.
#>
function Remove-IfExists {
  param([string]$LiteralPath)
  if (-not [string]::IsNullOrWhiteSpace($LiteralPath) -and (Test-Path -LiteralPath $LiteralPath)) {
    Remove-Item -LiteralPath $LiteralPath -Recurse -Force -ErrorAction SilentlyContinue
  }
}

<#
.SYNOPSIS
Joins argument tokens into one safe process-argument string.

.DESCRIPTION
Skips null values and quotes arguments that contain whitespace or quotes so downstream
process-start calls receive a stable command-line string.

.FUNCTION NAME
Join-ArgString

.INPUTS
String array of arguments.

.OUTPUTS
String containing the joined argument list.
#>
function Join-ArgString {
  param([string[]]$Arguments)
  if (-not $Arguments) { return "" }
  $parts = foreach ($arg in $Arguments) {
    if ($null -eq $arg) { continue }
    if ($arg -match '[\s"]') {
      '"' + ($arg -replace '"', '\"') + '"'
    } else {
      $arg
    }
  }
  return ($parts -join ' ')
}

<#
.SYNOPSIS
Checks whether one collector runtime path candidate is usable.

.DESCRIPTION
Rejects blank paths and PowerShell host executable paths so the primary PS1 lane keeps
using the collector script path, while the optional EXE lane can still use a real EXE
runtime path when appropriate.

.FUNCTION NAME
Test-CollectorRuntimePathCandidate

.INPUTS
Path string.

.OUTPUTS
Boolean indicating whether the candidate is a usable collector runtime path.
#>
function Test-CollectorRuntimePathCandidate {
  param([string]$Path)

  if ([string]::IsNullOrWhiteSpace($Path)) { return $false }

  try {
    $leaf = [System.IO.Path]::GetFileName($Path)
    if ($leaf -in @("powershell.exe", "pwsh.exe", "powershell", "pwsh")) { return $false }
    return $true
  } catch {
    return $false
  }
}

<#
.SYNOPSIS
Returns the absolute path to the active collector runtime.

.DESCRIPTION
Resolves the collector path by preferring the script path for PowerShell execution,
checking safe MyInvocation metadata without strict-mode property failures, and falling
back to the optional EXE process path only when the process itself is the collector
runtime rather than powershell.exe or pwsh.exe.

.FUNCTION NAME
Get-CollectorAbsolutePath

.INPUTS
No direct parameters.

.OUTPUTS
String absolute path to the active collector script or optional EXE runtime.
#>
function Get-CollectorAbsolutePath {
  foreach ($candidate in @($ScriptFilePath, $PSCommandPath, $MyInvocation.PSCommandPath)) {
    if (Test-CollectorRuntimePathCandidate -Path $candidate) {
      return [System.IO.Path]::GetFullPath([string]$candidate)
    }
  }

  try {
    $cmd = $MyInvocation.MyCommand
    if ($null -ne $cmd) {
      $pathProperty = $cmd.PSObject.Properties['Path']
      if ($pathProperty -and (Test-CollectorRuntimePathCandidate -Path ([string]$pathProperty.Value))) {
        return [System.IO.Path]::GetFullPath([string]$pathProperty.Value)
      }
      $sourceProperty = $cmd.PSObject.Properties['Source']
      if ($sourceProperty -and (Test-CollectorRuntimePathCandidate -Path ([string]$sourceProperty.Value))) {
        return [System.IO.Path]::GetFullPath([string]$sourceProperty.Value)
      }
    }
  } catch { }

  try {
    $processPath = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    if (Test-CollectorRuntimePathCandidate -Path $processPath) {
      return [System.IO.Path]::GetFullPath($processPath)
    }
  } catch { }

  return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path "DCOIR_Collector.ps1"))
}

<#
.SYNOPSIS
Builds the reusable PowerShell command base for the collector.

.DESCRIPTION
Returns the standard powershell.exe invocation string used in workflow guidance and
operator-facing next-step output.

.FUNCTION NAME
Get-CollectorPowerShellCommandBase

.INPUTS
No direct parameters.

.OUTPUTS
String command base for running the collector script.
#>
function Get-CollectorPowerShellCommandBase {
  $collectorPath = Get-CollectorAbsolutePath
  return ("powershell.exe -NoProfile -ExecutionPolicy Bypass -File '{0}'" -f $collectorPath)
}

<#
.SYNOPSIS
Builds the response-action delete-script command text.

.DESCRIPTION
Returns the operator-facing Elastic response-action string used to delete the uploaded
collector script explicitly when cleanup should remove the script too.

.FUNCTION NAME
Get-CollectorDeleteScriptCommandText

.INPUTS
No direct parameters.

.OUTPUTS
String response-action command text.
#>
function Get-CollectorDeleteScriptCommandText {
  $collectorPath = Get-CollectorAbsolutePath
  return ('execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command Remove-Item -LiteralPath ''{0}'' -Force" --comment "Remove uploaded DCOIR_Collector script"' -f $collectorPath)
}

<#
.SYNOPSIS
Writes one execution-step log record.

.DESCRIPTION
Builds the text and JSONL execution-log entries for a step, including timing, exit code,
command text, artifact path, and message, then appends them to the configured execution
logs when those paths are present.

.FUNCTION NAME
Write-StepLog

.INPUTS
StepName, Status, StartTime, EndTime, ExitCode, Command, ArtifactPath, and Message.

.OUTPUTS
No direct output. Appends to execution text and JSONL logs as a side effect.
#>
function Write-StepLog {
  param(
    [string]$StepName,
    [string]$Status,
    [datetime]$StartTime,
    [datetime]$EndTime,
    [int]$ExitCode,
    [string]$Command,
    [string]$ArtifactPath,
    [string]$Message
  )

  $durationMs = [int]([TimeSpan]($EndTime - $StartTime)).TotalMilliseconds
  $txtLine = "[{0}] {1} {2} duration_ms={3} exit_code={4}" -f $EndTime.ToUniversalTime().ToString("o"), $Status, $StepName, $durationMs, $ExitCode
  if ($ArtifactPath) { $txtLine += (" artifact={0}" -f $ArtifactPath) }
  if ($Message) { $txtLine += (" message={0}" -f $Message) }

  if ($Global:ExecutionTxtPath) {
    Add-Content -Path $Global:ExecutionTxtPath -Value $txtLine -Encoding UTF8
    if ($Command) {
      Add-Content -Path $Global:ExecutionTxtPath -Value ("  COMMAND={0}" -f $Command) -Encoding UTF8
    }
  }

  if ($Global:ExecutionJsonlPath) {
    $obj = [ordered]@{
      ts_utc = $EndTime.ToUniversalTime().ToString("o")
      run_id = $Global:CurrentRunId
      step = $StepName
      status = $Status
      duration_ms = $durationMs
      exit_code = $ExitCode
      command = $Command
      artifact_path = $ArtifactPath
      message = $Message
    }
    Add-Content -Path $Global:ExecutionJsonlPath -Value ($obj | ConvertTo-Json -Compress) -Encoding UTF8
  }
}

<#
.SYNOPSIS
Runs one external process and captures its output.

.DESCRIPTION
Builds the process start info, captures stdout and stderr, validates the exit code
against the allowed list, writes the execution-step log entry, and returns one capture
object describing the result.

.FUNCTION NAME
Invoke-ProcessCapture

.INPUTS
Mandatory FilePath and StepName, optional argument array, and optional allowed exit-code
list.

.OUTPUTS
PSCustomObject containing StdOut, StdErr, ExitCode, Command, and Status.
#>
function Invoke-ProcessCapture {
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$Arguments,
    [Parameter(Mandatory=$true)][string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )

  $startTime = Get-Date
  $commandText = $FilePath
  if ($Arguments) {
    $commandText = "$FilePath $(Join-ArgString -Arguments $Arguments)"
  }

  try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = (Join-ArgString -Arguments $Arguments)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    $endTime = Get-Date
    $status = "OK"
    $message = ""
    if (@($AllowedExitCodes) -notcontains [int]$proc.ExitCode) {
      $status = "ERROR"
      $message = ("ExitCode={0}" -f $proc.ExitCode)
      Add-CollectorError ("Step [{0}] failed. {1}. Command: {2}" -f $StepName, $message, $commandText)
    }

    Write-StepLog -StepName $StepName -Status $status -StartTime $startTime -EndTime $endTime -ExitCode $proc.ExitCode -Command $commandText -ArtifactPath "" -Message $message

    return [pscustomobject]@{
      StdOut = $stdout
      StdErr = $stderr
      ExitCode = [int]$proc.ExitCode
      Command = $commandText
      Status = $status
    }
  } catch {
    $endTime = Get-Date
    $message = $_.Exception.Message
    Add-CollectorError ("Step [{0}] raised an exception. {1}. Command: {2}" -f $StepName, $message, $commandText)
    Write-StepLog -StepName $StepName -Status "EXCEPTION" -StartTime $startTime -EndTime $endTime -ExitCode -1 -Command $commandText -ArtifactPath "" -Message $message
    return [pscustomobject]@{
      StdOut = ""
      StdErr = $message
      ExitCode = -1
      Command = $commandText
      Status = "EXCEPTION"
    }
  }
}

<#
.SYNOPSIS
Runs one cmd.exe command and captures its output.

.DESCRIPTION
Wraps Invoke-ProcessCapture for cmd.exe /c execution of the supplied command string.

.FUNCTION NAME
Invoke-CmdCapture

.INPUTS
Mandatory Command and StepName, optional allowed exit-code list.

.OUTPUTS
PSCustomObject containing the captured cmd.exe result.
#>
function Invoke-CmdCapture {
  param(
    [Parameter(Mandatory=$true)][string]$Command,
    [Parameter(Mandatory=$true)][string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  return (Invoke-ProcessCapture -FilePath "cmd.exe" -Arguments @("/c", $Command) -StepName $StepName -AllowedExitCodes $AllowedExitCodes)
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
Checks whether a directory name matches the collector run-root pattern.

.DESCRIPTION
Limits cleanup discovery to run roots created by this collector on the current host.

.FUNCTION NAME
Test-DCOIRRunDirectoryName

.INPUTS
Directory name string.

.OUTPUTS
Boolean.
#>
function Test-DCOIRRunDirectoryName {
  param([string]$Name)
  if ([string]::IsNullOrWhiteSpace($Name)) { return $false }
  $hostPattern = [regex]::Escape([string]$env:COMPUTERNAME)
  return [regex]::IsMatch($Name, ("^DCOIR_{0}_\d{{8}}_\d{{6}}$" -f $hostPattern))
}

<#
.SYNOPSIS
Checks whether a no-state directory is safe for fallback cleanup.

.DESCRIPTION
Requires both a strict collector run-root name and collector-created child structure
before no-state cleanup may remove the directory.

.FUNCTION NAME
Test-DCOIRNoStateCleanupCandidate

.INPUTS
DirectoryInfo object.

.OUTPUTS
Boolean.
#>
function Test-DCOIRNoStateCleanupCandidate {
  param([object]$Directory)
  if (-not $Directory) { return $false }
  if (-not (Test-DCOIRRunDirectoryName -Name $Directory.Name)) { return $false }
  if (Test-Path -LiteralPath (Join-Path $Directory.FullName 'state.json')) { return $false }
  $requiredChildren = @('tools','reports','final_artifacts','logs','bundles')
  foreach ($child in $requiredChildren) {
    if (-not (Test-Path -LiteralPath (Join-Path $Directory.FullName $child))) { return $false }
  }
  return $true
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
No direct output. Writes state.json as a side effect.
#>
function Save-State {
  param([Parameter(Mandatory=$true)][hashtable]$State)
  $json = $State | ConvertTo-Json -Depth 12
  Set-Content -Path $State.StatePath -Value $json -Encoding UTF8
}

<#
.SYNOPSIS
Loads a saved collector state object from disk.

.DESCRIPTION
Loads the latest run state when no run ID is supplied, or the specific run state when a
run ID is given, and returns the deserialized state object.

.FUNCTION NAME
Load-State

.INPUTS
Root string and optional CurrentRunId string.

.OUTPUTS
Deserialized state object.
#>
function Load-State {
  param([string]$Root,[string]$CurrentRunId)

  if ([string]::IsNullOrWhiteSpace($CurrentRunId)) {
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
      Where-Object { Test-DCOIRRunDirectoryName -Name $_.Name } |
      Sort-Object LastWriteTime -Descending
    if (-not $dirs) {
      throw "No DCOIR run directories found under $Root"
    }
    $selected = $dirs | Select-Object -First 1
    $statePath = Join-Path $selected.FullName "state.json"
    if (-not (Test-Path -LiteralPath $statePath)) {
      throw "State file not found: $statePath"
    }
    return (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
  }

  $statePath = Get-StatePath -Root $Root -CurrentRunId $CurrentRunId
  if (-not (Test-Path -LiteralPath $statePath)) {
    throw "State file not found: $statePath"
  }

  return (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
}

<#
.SYNOPSIS
Finds the newest collector run directory under a root.

.DESCRIPTION
Selects only directories matching the collector run-root naming pattern under the supplied
root. When a RunId is supplied, only the expected host/run-id directory is considered.

.FUNCTION NAME
Find-LatestDCOIRRunDirectory

.INPUTS
Root string and optional CurrentRunId string.

.OUTPUTS
DirectoryInfo object or null.
#>
function Find-LatestDCOIRRunDirectory {
  param([string]$Root,[string]$CurrentRunId)

  if ([string]::IsNullOrWhiteSpace($Root) -or -not (Test-Path -LiteralPath $Root)) { return $null }
  if (-not [string]::IsNullOrWhiteSpace($CurrentRunId)) {
    $expected = Get-RunRoot -Root $Root -CurrentRunId $CurrentRunId
    if (Test-Path -LiteralPath $expected) { return Get-Item -LiteralPath $expected }
    return $null
  }

  $dirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
    Where-Object { Test-DCOIRRunDirectoryName -Name $_.Name } |
    Sort-Object LastWriteTime -Descending
  return ($dirs | Select-Object -First 1)
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
  foreach ($target in @($targets)) {
    try {
      Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop
      [void]$removed.Add($target)
    } catch {
      [void]$failed.Add(("{0} :: {1}" -f $target, $_.Exception.Message))
    }
  }

  $status = if (@($targets).Count -eq 0) {
    'NO_TARGET_FOUND'
  } elseif (@($failed).Count -gt 0) {
    'PARTIAL_FAILED'
  } else {
    'MISSING_STATE_ORPHAN_CLEANED'
  }

  return @{
    Status = $status
    RunRoot = if ($runDir) { $runDir.FullName } else { $null }
    RemovedTargets = @($removed)
    FailedTargets = @($failed)
    TargetCount = @($targets).Count
  }
}

<#
.SYNOPSIS
Recursively converts a deserialized state object into plain hashtables and arrays.

.DESCRIPTION
Normalizes dictionaries, enumerable collections, and PSObject properties into plain
PowerShell hashtables and arrays so saved state can be reused consistently.

.FUNCTION NAME
Convert-StateObjectToHashtable

.INPUTS
InputObject to normalize.

.OUTPUTS
Hashtable, array, scalar, or null matching the normalized input structure.
#>
function Convert-StateObjectToHashtable {
  param([object]$InputObject)

  if ($null -eq $InputObject) { return $null }

  if ($InputObject -is [System.Collections.IDictionary]) {
    $hash = @{}
    foreach ($key in $InputObject.Keys) {
      $hash[$key] = Convert-StateObjectToHashtable -InputObject $InputObject[$key]
    }
    return $hash
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
    $list = @()
    foreach ($item in $InputObject) {
      $list += ,(Convert-StateObjectToHashtable -InputObject $item)
    }
    return $list
  }

  $psProps = @()
  try { $psProps = @($InputObject.PSObject.Properties) } catch { $psProps = @() }
  if (@($psProps).Count -gt 0 -and -not ($InputObject -is [string])) {
    $hash = @{}
    foreach ($prop in $psProps) {
      $hash[$prop.Name] = Convert-StateObjectToHashtable -InputObject $prop.Value
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

<#
.SYNOPSIS
Returns the active script directory.

.DESCRIPTION
Resolves the script directory from ScriptFilePath first, then PSScriptRoot, and finally
falls back to the current working directory.

.FUNCTION NAME
Get-ScriptDirectory

.INPUTS
No direct parameters.

.OUTPUTS
String script-directory path.
#>
function Get-ScriptDirectory {
  if (-not [string]::IsNullOrWhiteSpace($ScriptFilePath)) {
    return (Split-Path -Parent $ScriptFilePath)
  }
  if ($PSScriptRoot) {
    return $PSScriptRoot
  }
  return (Get-Location).Path
}

<#
.SYNOPSIS
Resolves one staged tool path from the tools directory.

.DESCRIPTION
Checks the 64-bit and standard executable names for the requested Sysinternals-style
base tool name and returns the first existing path.

.FUNCTION NAME
Resolve-Tool

.INPUTS
ToolsDir string and BaseName string.

.OUTPUTS
String tool path or null when the tool is absent.
#>
function Resolve-Tool {
  param([string]$ToolsDir,[string]$BaseName)

  $candidates = @(
    (Join-Path $ToolsDir ("{0}64.exe" -f $BaseName)),
    (Join-Path $ToolsDir ("{0}.exe" -f $BaseName))
  )

  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) { return $candidate }
  }
  return $null
}

<#
.SYNOPSIS
Builds the standard report-section header lines.

.DESCRIPTION
Returns the blank line and divider pattern used before each named report section.

.FUNCTION NAME
New-SectionHeader

.INPUTS
Name string for the section title.

.OUTPUTS
String array containing the section header lines.
#>
function New-SectionHeader {
  param([string]$Name)
  return @(
    ""
    ("=" * 80)
    $Name
    ("=" * 80)
    ""
  )
}

<#
.SYNOPSIS
Appends one named section to a StringBuilder report.

.DESCRIPTION
Writes the standard section header and the supplied text to the StringBuilder.

.FUNCTION NAME
Add-Section

.INPUTS
Builder StringBuilder, section Name string, and Text string.

.OUTPUTS
No direct output. Appends to the StringBuilder as a side effect.
#>
function Add-Section {
  param(
    [System.Text.StringBuilder]$Builder,
    [string]$Name,
    [string]$Text
  )
  foreach ($line in (New-SectionHeader -Name $Name)) {
    [void]$Builder.AppendLine($line)
  }
  [void]$Builder.AppendLine(($Text | Out-String))
}

<#
.SYNOPSIS
Formats one object into a wide text block.

.DESCRIPTION
Returns an empty string for null input and otherwise uses Out-String with width 500.

.FUNCTION NAME
Convert-ToTextBlock

.INPUTS
InputObject to format.

.OUTPUTS
String text block.
#>
function Convert-ToTextBlock {
  param([object]$InputObject)
  if ($null -eq $InputObject) { return "" }
  return ($InputObject | Out-String -Width 500)
}

<#
.SYNOPSIS
Creates the run directory structure for one collector run.

.DESCRIPTION
Builds the standard run-root, tools, reports, artifacts, enrich-sessions, logs, and
bundles directories and returns their paths plus the state-file path.

.FUNCTION NAME
Initialize-RunStructure

.INPUTS
Root string and CurrentRunId string.

.OUTPUTS
Hashtable containing the run-structure paths.
#>
function Initialize-RunStructure {
  param([string]$Root,[string]$CurrentRunId)

  $runRoot = Get-RunRoot -Root $Root -CurrentRunId $CurrentRunId
  $toolsDir = Join-Path $runRoot "tools"
  $reportsDir = Join-Path $runRoot "reports"
  $artifactsDir = Join-Path $runRoot "final_artifacts"
  $enrichSessionsDir = Join-Path $runRoot "enrich_sessions"
  $logsDir = Join-Path $runRoot "logs"
  $bundlesDir = Join-Path $runRoot "bundles"

  Ensure-Directory -Path $Root
  Ensure-Directory -Path $runRoot
  Ensure-Directory -Path $toolsDir
  Ensure-Directory -Path $reportsDir
  Ensure-Directory -Path $artifactsDir
  Ensure-Directory -Path $enrichSessionsDir
  Ensure-Directory -Path $logsDir
  Ensure-Directory -Path $bundlesDir

  return @{
    RunRoot = $runRoot
    ToolsDir = $toolsDir
    ReportsDir = $reportsDir
    ArtifactsDir = $artifactsDir
    EnrichSessionsDir = $enrichSessionsDir
    LogsDir = $logsDir
    BundlesDir = $bundlesDir
    StatePath = (Join-Path $runRoot "state.json")
  }
}

<#
.SYNOPSIS
Purges prior DCOIR run folders and the previous package file.

.DESCRIPTION
Deletes prior collector run directories under the out-root and removes the prior package ZIP when
present so a fresh collect run starts from a clean workspace.

.FUNCTION NAME
Purge-PreviousRuns

.INPUTS
Root string and CurrentPackageName string.

.OUTPUTS
No direct output. Deletes prior strict-pattern collector run directories and package file as a side effect.
#>
function Purge-PreviousRuns {
  param([string]$Root,[string]$CurrentPackageName)

  try {
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
      Where-Object { Test-DCOIRRunDirectoryName -Name $_.Name }
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
    Add-CollectorError "Failed to purge previous package file: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Moves the package ZIP into the out-root when needed.

.DESCRIPTION
Looks for the current package in the script directory first, moves it into the out-root
when necessary, or returns the already-present out-root package path.

.FUNCTION NAME
Move-PackageToOutRoot

.INPUTS
Root string and CurrentPackageName string.

.OUTPUTS
String package path in the out-root.
#>
function Move-PackageToOutRoot {
  param([string]$Root,[string]$CurrentPackageName)

  $scriptDir = Get-ScriptDirectory
  $sourcePath = Join-Path $scriptDir $CurrentPackageName
  $destPath = Join-Path $Root $CurrentPackageName
  $checkedPaths = @($sourcePath, $destPath)

  if (Test-Path -LiteralPath $sourcePath) {
    if ($sourcePath -ne $destPath) {
      Move-Item -LiteralPath $sourcePath -Destination $destPath -Force
    }
    return $destPath
  }

  if (Test-Path -LiteralPath $destPath) {
    return $destPath
  }

  throw ("Package not found: {0}. CheckedPaths={1}" -f $CurrentPackageName, ($checkedPaths -join '; '))
}

<#
.SYNOPSIS
Expands the package ZIP into the tools directory.

.DESCRIPTION
Recreates the tools directory and extracts the package ZIP into it, throwing on
extraction failure.

.FUNCTION NAME
Expand-PackageToTools

.INPUTS
PackagePath string and ToolsDir string.

.OUTPUTS
No direct output. Recreates and populates the tools directory.
#>
function Expand-PackageToTools {
  param([string]$PackagePath,[string]$ToolsDir)

  try {
    Remove-IfExists -LiteralPath $ToolsDir
    Ensure-Directory -Path $ToolsDir
    Expand-Archive -LiteralPath $PackagePath -DestinationPath $ToolsDir -Force
  } catch {
    throw "Failed to expand package [$PackagePath] to [$ToolsDir]: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Returns the numeric prefix used for one baseline artifact name.

.DESCRIPTION
Maps well-known baseline artifact names to stable ordering prefixes used in final
artifact filenames.

.FUNCTION NAME
Get-BaselineArtifactPrefix

.INPUTS
Name string for the artifact file.

.OUTPUTS
String prefix value.
#>
function Get-BaselineArtifactPrefix {
  param([string]$Name)
  switch ($Name.ToLowerInvariant()) {
    "collection_metadata.txt" { "01" }
    "collection_notes_and_limitations.txt" { "02" }
    "time_host.txt" { "03" }
    "systeminfo.txt" { "04" }
    "whoami_all.txt" { "05" }
    "sessions.txt" { "06" }
    "logon_sessions_wmi.txt" { "07" }
    "process_inventory.txt" { "08" }
    "pslist.txt" { "09" }
    "ipconfig_all.txt" { "10" }
    "netstat_abno.txt" { "11" }
    "structured_net.txt" { "12" }
    "dns_cache.txt" { "13" }
    "route_print.txt" { "14" }
    "arp_a.txt" { "15" }
    "tcpvcon.txt" { "16" }
    "pipelist.txt" { "17" }
    "services.txt" { "18" }
    "scheduled_tasks.txt" { "19" }
    "run_hklm.txt" { "20" }
    "run_hku_loaded_users.txt" { "21" }
    "autorunsc.csv.txt" { "22" }
    "defender_status.txt" { "23" }
    "firewall_profiles.txt" { "24" }
    "security_filtered.txt" { "25" }
    "security_high_signal_summary.txt" { "25A" }
    "powershell_operational_filtered.txt" { "26" }
    "taskscheduler_operational_filtered.txt" { "27" }
    "tier2_reg_ifeo.txt" { "28" }
    "tier2_reg_winlogon.txt" { "29" }
    "tier2_reg_lsa.txt" { "30" }
    "tier2_wmi_persistence.txt" { "31" }
    "tier2_net_share.txt" { "32" }
    "tier2_net_session.txt" { "33" }
    "tier2_firewall_profiles.txt" { "34" }
    "analyst_follow_up_queue.txt" { "35" }
    default { "99" }
  }
}

<#
.SYNOPSIS
Writes one named artifact text file.

.DESCRIPTION
Builds the prefixed artifact filename from the section and name, writes the supplied
text into the artifacts directory, and returns the artifact path.

.FUNCTION NAME
Write-ArtifactText

.INPUTS
ArtifactsDir string, Section string, Name string, and Text string.

.OUTPUTS
String artifact path.
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
  $safeSection = ($Section -replace '[\\/:*?"<>| ]','_')
  $safeName = ($Name -replace '[\\/:*?"<>| ]','_')
  $path = Join-Path $ArtifactsDir ("{0}_{1}_{2}" -f $prefix, $safeSection, $safeName)
  Set-Content -Path $path -Value $Text -Encoding UTF8
  return $path
}

<#
.SYNOPSIS
Returns the next enrichment-session action sequence number.

.DESCRIPTION
Counts the existing text artifacts in the session artifacts directory and returns the
next sequential number.

.FUNCTION NAME
Get-SessionActionSequence

.INPUTS
SessionArtifactsDir string.

.OUTPUTS
Integer sequence number.
#>
function Get-SessionActionSequence {
  param([string]$SessionArtifactsDir)
  $count = @(Get-ChildItem -LiteralPath $SessionArtifactsDir -File -Filter "*.txt" -ErrorAction SilentlyContinue).Count
  return ($count + 1)
}

<#
.SYNOPSIS
Writes one enrichment-session artifact text file.

.DESCRIPTION
Builds the sequential enrich artifact filename, writes the supplied text, and returns
the created session artifact path.

.FUNCTION NAME
Write-SessionArtifactText

.INPUTS
SessionArtifactsDir string, ActionName string, TargetLabel string, and Text string.

.OUTPUTS
String session artifact path.
#>
function Write-SessionArtifactText {
  param(
    [string]$SessionArtifactsDir,
    [string]$ActionName,
    [string]$TargetLabel,
    [string]$Text
  )
  Ensure-Directory -Path $SessionArtifactsDir
  $seq = Get-SessionActionSequence -SessionArtifactsDir $SessionArtifactsDir
  $safeAction = ($ActionName -replace '[\\/:*?"<>| ]','_')
  $safeTarget = ($TargetLabel -replace '[\\/:*?"<>| ]','_')
  if ([string]::IsNullOrWhiteSpace($safeTarget)) { $safeTarget = "artifact" }
  if ($safeTarget.Length -gt 80) { $safeTarget = $safeTarget.Substring(0,80) }
  $path = Join-Path $SessionArtifactsDir ("{0:D2}_ENRICH_{1}_{2}.txt" -f $seq, $safeAction, $safeTarget)
  Set-Content -Path $path -Value $Text -Encoding UTF8
  return $path
}

<#
.SYNOPSIS
Collects loaded-user HKU Run-key text.

.DESCRIPTION
Enumerates loaded HKU SID hives, collects each loaded Run key, and returns the combined
text surface. Returns a bounded explanatory message when no loaded user Run keys exist.

.FUNCTION NAME
Get-LoadedUserRunKeysText

.INPUTS
No direct parameters.

.OUTPUTS
String containing loaded-user HKU Run-key text or an explanatory/error message.
#>
function Get-LoadedUserRunKeysText {
  try {
    $lines = New-Object System.Collections.ArrayList
    $sidPattern = '^S-1-5-21-\d+-\d+-\d+-\d+$'
    $hku = Get-ChildItem -Path Registry::HKEY_USERS -ErrorAction SilentlyContinue
    foreach ($key in $hku) {
      if ($key.PSChildName -notmatch $sidPattern) { continue }
      $runPath = "Registry::HKEY_USERS\$($key.PSChildName)\Software\Microsoft\Windows\CurrentVersion\Run"
      if (Test-Path -LiteralPath $runPath) {
        [void]$lines.Add(("SID={0}" -f $key.PSChildName))
        [void]$lines.Add((Get-ItemProperty -LiteralPath $runPath | Format-List * | Out-String -Width 500))
      }
    }
    if (@($lines).Count -eq 0) {
      return "No loaded user HKU Run keys were found. Offline profile hives were not loaded by design."
    }
    return ($lines -join [Environment]::NewLine)
  } catch {
    Add-CollectorError "Failed to enumerate loaded user HKU Run keys: $($_.Exception.Message)"
    return "ERROR: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Returns the human-readable name for one Windows logon type.

.DESCRIPTION
Maps known numeric logon-type values to analyst-friendly names.

.FUNCTION NAME
Get-LogonTypeName

.INPUTS
LogonType integer.

.OUTPUTS
String logon-type name.
#>
function Get-LogonTypeName {
  param([int]$LogonType)
  switch ($LogonType) {
    0 { "System" }
    2 { "Interactive" }
    3 { "Network" }
    4 { "Batch" }
    5 { "Service" }
    7 { "Unlock" }
    8 { "NetworkCleartext" }
    9 { "NewCredentials" }
    10 { "RemoteInteractive" }
    11 { "CachedInteractive" }
    default { "Unknown" }
  }
}

<#
.SYNOPSIS
Builds the WMI logon-session text surface.

.DESCRIPTION
Collects Win32_LogonSession and Win32_LoggedOnUser association data, correlates account
rows to logon sessions, and returns an analyst-friendly text surface.

.FUNCTION NAME
Get-LogonSessionsWmiText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the WMI logon-session text surface or an error message.
#>
function Get-LogonSessionsWmiText {
  try {
    $sb = New-Object System.Text.StringBuilder
    $sessionsRaw = @(Get-CimInstance -ClassName Win32_LogonSession -ErrorAction Stop)
    $sessions = $sessionsRaw | Select-Object LogonId, LogonType, AuthenticationPackage, StartTime

    $assocRows = New-Object System.Collections.ArrayList
    $seen = @{}

    foreach ($sess in $sessionsRaw) {
      try {
        $accounts = @(Get-CimAssociatedInstance -InputObject $sess -Association Win32_LoggedOnUser -ResultClassName Win32_Account -ErrorAction Stop)
        foreach ($acct in $accounts) {
          $row = [pscustomobject]@{
            LogonId = [string]$sess.LogonId
            Domain = [string]$acct.Domain
            User = [string]$acct.Name
            SID = [string]$acct.SID
            Source = "AssociatedInstance"
          }
          $key = "{0}|{1}|{2}|{3}" -f $row.LogonId, $row.Domain, $row.User, $row.SID
          if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            [void]$assocRows.Add($row)
          }
        }
      } catch { }
    }

    $assocs = @(Get-CimInstance -ClassName Win32_LoggedOnUser -ErrorAction SilentlyContinue)
    foreach ($assoc in $assocs) {
      $ante = [string]$assoc.Antecedent
      $dep = [string]$assoc.Dependent

      $domain = ""
      $user = ""
      $sid = ""
      $logonId = ""

      if ($ante -match 'Domain="([^"]+)",Name="([^"]+)"') {
        $domain = $matches[1]
        $user = $matches[2]
      }
      if ($ante -match 'SID="([^"]+)"') {
        $sid = $matches[1]
      }
      if ($dep -match 'LogonId="?([^",]+)"?') {
        $logonId = $matches[1]
      }

      $row = [pscustomobject]@{
        LogonId = $logonId
        Domain = $domain
        User = $user
        SID = $sid
        Source = "ParsedAssociation"
      }
      $key = "{0}|{1}|{2}|{3}" -f $row.LogonId, $row.Domain, $row.User, $row.SID
      if (-not $seen.ContainsKey($key)) {
        $seen[$key] = $true
        [void]$assocRows.Add($row)
      }
    }

    [void]$sb.AppendLine("WIN32_LOGONSESSION")
    foreach ($sess in ($sessions | Sort-Object LogonId)) {
      $typeName = Get-LogonTypeName -LogonType ([int]$sess.LogonType)
      [void]$sb.AppendLine(("LogonId={0}" -f $sess.LogonId))
      [void]$sb.AppendLine(("LogonType={0} ({1})" -f $sess.LogonType, $typeName))
      [void]$sb.AppendLine(("AuthenticationPackage={0}" -f $sess.AuthenticationPackage))
      [void]$sb.AppendLine(("StartTime={0}" -f $sess.StartTime))
      $matchesForSession = @($assocRows | Where-Object { $_.LogonId -eq ([string]$sess.LogonId) })
      if (@($matchesForSession).Count -gt 0) {
        [void]$sb.AppendLine("Accounts:")
        foreach ($m in $matchesForSession | Sort-Object Domain, User, SID) {
          if ($m.SID) {
            [void]$sb.AppendLine(("  {0}\{1} SID={2} Source={3}" -f $m.Domain, $m.User, $m.SID, $m.Source))
          } else {
            [void]$sb.AppendLine(("  {0}\{1} Source={2}" -f $m.Domain, $m.User, $m.Source))
          }
        }
      }
      [void]$sb.AppendLine("-" * 60)
    }

    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("WIN32_LOGGEDONUSER_ASSOCIATIONS")
    [void]$sb.AppendLine((Convert-ToTextBlock -InputObject ($assocRows | Sort-Object LogonId, Domain, User, SID)))

    return $sb.ToString().TrimEnd()
  } catch {
    Add-CollectorError "Failed to collect WMI logon sessions: $($_.Exception.Message)"
    return "ERROR collecting WMI logon sessions: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Converts one Win32_Process object into the normalized process-inventory row.

.DESCRIPTION
Resolves owner and creation time details for one process and returns the normalized
PSCustomObject used by the process inventory.

.FUNCTION NAME
Convert-ProcessObjectToText

.INPUTS
Proc object and StartTimeMap hashtable.

.OUTPUTS
PSCustomObject containing normalized process-inventory fields.
#>
function Convert-ProcessObjectToText {
  param(
    [object]$Proc,
    [hashtable]$StartTimeMap
  )

  $owner = ""
  try {
    $ownerInfo = Invoke-CimMethod -InputObject $Proc -MethodName GetOwner -ErrorAction Stop
    if ($ownerInfo.ReturnValue -eq 0) {
      $owner = "{0}\{1}" -f $ownerInfo.Domain, $ownerInfo.User
    }
  } catch { }

  $created = $null
  try {
    $procId = [int]$Proc.ProcessId
    if ($StartTimeMap -and $StartTimeMap.ContainsKey($procId)) {
      $created = $StartTimeMap[$procId]
    } elseif ($Proc.CreationDate) {
      $created = [System.Management.ManagementDateTimeConverter]::ToDateTime($Proc.CreationDate)
    }
  } catch { }

  return [pscustomobject]@{
    ProcessId       = $Proc.ProcessId
    ParentProcessId = $Proc.ParentProcessId
    Name            = $Proc.Name
    ExecutablePath  = $Proc.ExecutablePath
    CommandLine     = $Proc.CommandLine
    Owner           = $owner
    CreationTime    = $created
  }
}

<#
.SYNOPSIS
Builds the normalized Win32_Process inventory.

.DESCRIPTION
Collects current process start times, queries Win32_Process, converts each row into the
normalized process-inventory form, and returns the sorted process list.

.FUNCTION NAME
Get-ProcessInventory

.INPUTS
No direct parameters.

.OUTPUTS
Array of normalized process-inventory rows.
#>
function Get-ProcessInventory {
  try {
    $startTimeMap = @{}
    try {
      foreach ($gp in @(Get-Process -ErrorAction SilentlyContinue)) {
        try {
          $startTimeMap[[int]$gp.Id] = $gp.StartTime
        } catch { }
      }
    } catch { }

    $raw = Get-CimInstance -ClassName Win32_Process -ErrorAction Stop
    $items = foreach ($p in $raw) {
      Convert-ProcessObjectToText -Proc $p -StartTimeMap $startTimeMap
    }
    return $items | Sort-Object ProcessId
  } catch {
    Add-CollectorError "Failed to collect Win32_Process inventory: $($_.Exception.Message)"
    return @()
  }
}

<#
.SYNOPSIS
Builds a key-value map from one event record’s EventData section.

.DESCRIPTION
Parses the event record XML and returns a hashtable containing EventData values keyed
by name or synthetic DataN names when the event field is unnamed.

.FUNCTION NAME
Get-EventDataMap

.INPUTS
EventRecord object.

.OUTPUTS
Hashtable of event-data values.
#>
function Get-EventDataMap {
  param([object]$EventRecord)

  $map = @{}
  try {
    $xml = [xml]$EventRecord.ToXml()
    if ($xml -and $xml.Event -and $xml.Event.EventData) {
      $index = 0
      foreach ($node in @($xml.Event.EventData.Data)) {
        $index += 1
        $name = [string]$node.Name
        if ([string]::IsNullOrWhiteSpace($name)) {
          $name = "Data{0}" -f $index
        }
        $value = [string]$node.'#text'
        $map[$name] = $value
      }
    }
  } catch { }
  return $map
}

<#
.SYNOPSIS
Returns one value from an event-data map.

.DESCRIPTION
Safely returns the named value from the supplied event-data map or an empty string when
no such key exists.

.FUNCTION NAME
Get-EventMapValue

.INPUTS
Map hashtable and Key string.

.OUTPUTS
String event-data value or empty string.
#>
function Get-EventMapValue {
  param(
    [hashtable]$Map,
    [string]$Key
  )
  if ($null -eq $Map) { return "" }
  if ([string]::IsNullOrWhiteSpace($Key)) { return "" }
  if ($Map.ContainsKey($Key)) {
    return [string]$Map[$Key]
  }
  return ""
}

<#
.SYNOPSIS
Builds the baseline Security high-signal summary.

.DESCRIPTION
Queries the key Security event IDs for the last WindowHours, suppresses routine machine
and service noise, and returns the analyst-facing high-signal summary text.

.FUNCTION NAME
Get-SecurityHighSignalSummaryText

.INPUTS
WindowHours integer and Take integer limiting the returned summary volume.

.OUTPUTS
String containing the Security high-signal summary or an explanatory/error message.
#>
function Get-SecurityHighSignalSummaryText {
  param(
    [int]$WindowHours = 24,
    [int]$Take = 200
  )

  try {
    $ids = @(4624,4625,4648,4672,4688,4697,4698)
    $startTime = (Get-Date).AddHours(-1 * [math]::Abs($WindowHours))
    $fh = @{
      LogName = "Security"
      StartTime = $startTime
      Id = $ids
    }

    $events = @(Get-WinEvent -FilterHashtable $fh -ErrorAction Stop |
      Sort-Object TimeCreated -Descending |
      Select-Object -First ($Take * 4))

    if (@($events).Count -eq 0) {
      Add-CollectorNote "No high-signal Security events were found in the selected window."
      return "No high-signal Security events were found in the selected window."
    }

    $interesting = New-Object System.Collections.ArrayList
    $suppressed = New-Object System.Collections.ArrayList

    foreach ($ev in $events) {
      $m = Get-EventDataMap -EventRecord $ev

      $subjectUser = Get-EventMapValue -Map $m -Key 'SubjectUserName'
      $subjectDomain = Get-EventMapValue -Map $m -Key 'SubjectDomainName'
      $targetUser = Get-EventMapValue -Map $m -Key 'TargetUserName'
      $targetDomain = Get-EventMapValue -Map $m -Key 'TargetDomainName'
      $logonType = Get-EventMapValue -Map $m -Key 'LogonType'

      $subjectIsMachine = ($subjectUser -like '*$')
      $targetIsMachine = ($targetUser -like '*$')
      $subjectIsBuiltinService = $subjectUser -in @('SYSTEM','LOCAL SERVICE','NETWORK SERVICE','ANONYMOUS LOGON')
      $targetIsBuiltinService = $targetUser -in @('SYSTEM','LOCAL SERVICE','NETWORK SERVICE','ANONYMOUS LOGON')
      $isServiceStyleLogon = $logonType -in @('0','5')

      $suppress = $false
      $suppressReason = $null

      switch ([int]$ev.Id) {
        4624 {
          if (($subjectIsMachine -or $targetIsMachine -or $subjectIsBuiltinService -or $targetIsBuiltinService) -and $isServiceStyleLogon) {
            $suppress = $true
            $suppressReason = "routine successful service or machine logon"
          }
        }
        4672 {
          if ($subjectIsMachine -or $subjectIsBuiltinService) {
            $suppress = $true
            $suppressReason = "routine special privileges assignment for service or machine account"
          }
        }
      }

      if ($suppress) {
        [void]$suppressed.Add([pscustomobject]@{
          Id = $ev.Id
          TimeCreated = $ev.TimeCreated
          Reason = $suppressReason
          Account = ("{0}\{1}" -f $subjectDomain, $subjectUser).Trim('\\')
          LogonType = $logonType
        })
      } else {
        [void]$interesting.Add([pscustomobject]@{
          EventRecord = $ev
          EventData = $m
        })
      }
    }

    $interesting = @($interesting | Sort-Object { $_.EventRecord.TimeCreated } -Descending | Select-Object -First $Take)

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add("SECURITY_HIGH_SIGNAL_SUMMARY")
    [void]$lines.Add(("WINDOW_HOURS={0}" -f $WindowHours))
    [void]$lines.Add(("RAW_EVENT_COUNT={0}" -f @($events).Count))
    [void]$lines.Add(("INTERESTING_EVENT_COUNT={0}" -f @($interesting).Count))
    [void]$lines.Add(("SUPPRESSED_EVENT_COUNT={0}" -f @($suppressed).Count))
    [void]$lines.Add("")

    $counts = $interesting | Group-Object { $_.EventRecord.Id } | Sort-Object Name
    [void]$lines.Add("INTERESTING_EVENT_COUNTS")
    foreach ($g in $counts) {
      [void]$lines.Add(("Id={0} Count={1}" -f $g.Name, $g.Count))
    }

    if (@($suppressed).Count -gt 0) {
      [void]$lines.Add("")
      [void]$lines.Add("SUPPRESSED_EVENT_COUNTS")
      $suppressedCounts = $suppressed | Group-Object Id, Reason | Sort-Object Name
      foreach ($g in $suppressedCounts) {
        [void]$lines.Add(("{0} Count={1}" -f $g.Name, $g.Count))
      }
    }

    [void]$lines.Add("")
    [void]$lines.Add("EVENT_SUMMARY")

    foreach ($item in $interesting) {
      $ev = $item.EventRecord
      $m = $item.EventData
      $summary = ""
      switch ([int]$ev.Id) {
        4624 {
          $summary = "Successful logon Target={0}\\{1} LogonType={2} SourceIp={3} Workstation={4}" -f (Get-EventMapValue -Map $m -Key 'TargetDomainName'), (Get-EventMapValue -Map $m -Key 'TargetUserName'), (Get-EventMapValue -Map $m -Key 'LogonType'), (Get-EventMapValue -Map $m -Key 'IpAddress'), (Get-EventMapValue -Map $m -Key 'WorkstationName')
        }
        4625 {
          $summary = "Failed logon Target={0}\\{1} LogonType={2} SourceIp={3} Status={4} SubStatus={5}" -f (Get-EventMapValue -Map $m -Key 'TargetDomainName'), (Get-EventMapValue -Map $m -Key 'TargetUserName'), (Get-EventMapValue -Map $m -Key 'LogonType'), (Get-EventMapValue -Map $m -Key 'IpAddress'), (Get-EventMapValue -Map $m -Key 'Status'), (Get-EventMapValue -Map $m -Key 'SubStatus')
        }
        4648 {
          $summary = "Explicit credentials Subject={0}\\{1} TargetServer={2} Process={3} SourceIp={4}" -f (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName'), (Get-EventMapValue -Map $m -Key 'TargetServerName'), (Get-EventMapValue -Map $m -Key 'ProcessName'), (Get-EventMapValue -Map $m -Key 'IpAddress')
        }
        4672 {
          $summary = "Special privileges assigned Subject={0}\\{1} Privileges={2}" -f (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName'), (Get-EventMapValue -Map $m -Key 'PrivilegeList')
        }
        4688 {
          $summary = "Process created NewProcess={0} ParentProcess={1} Subject={2}\\{3} CommandLine={4}" -f (Get-EventMapValue -Map $m -Key 'NewProcessName'), (Get-EventMapValue -Map $m -Key 'ParentProcessName'), (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName'), (Get-EventMapValue -Map $m -Key 'CommandLine')
        }
        4697 {
          $summary = "Service installed Name={0} File={1} Subject={2}\\{3}" -f (Get-EventMapValue -Map $m -Key 'ServiceName'), (Get-EventMapValue -Map $m -Key 'ServiceFileName'), (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName')
        }
        4698 {
          $summary = "Scheduled task created TaskName={0} Subject={1}\\{2}" -f (Get-EventMapValue -Map $m -Key 'TaskName'), (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName')
        }
        default {
          $summary = ($ev.Message -replace "`r", "" -replace "`n", " ")
        }
      }

      [void]$lines.Add(("[{0}] Id={1} {2}" -f $ev.TimeCreated.ToString("o"), $ev.Id, $summary.Trim()))
    }

    return ($lines -join [Environment]::NewLine)
  } catch {
    Add-CollectorError "Failed to collect condensed Security summary: $($_.Exception.Message)"
    return "ERROR collecting condensed Security summary: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Returns suspicious-process heuristic findings from the process inventory.

.DESCRIPTION
Applies command-line, path, and LOLBin heuristics to the process inventory while
excluding specified PIDs, then returns the suspicious findings list.

.FUNCTION NAME
Get-SuspiciousProcessFindings

.INPUTS
Processes array and ExcludedPids integer array.

.OUTPUTS
ArrayList of suspicious process finding objects.
#>
function Get-SuspiciousProcessFindings {
  param([object[]]$Processes,[int[]]$ExcludedPids)

  $findings = New-Object System.Collections.ArrayList
  foreach ($proc in $Processes) {
    if (@($ExcludedPids) -contains [int]$proc.ProcessId) { continue }

    $reasons = New-Object System.Collections.ArrayList
    $cmd = [string]$proc.CommandLine
    $pathValue = [string]$proc.ExecutablePath
    $nameValue = [string]$proc.Name

    $isCollectorSelfRun = ($cmd -match '(?i)DCOIR_Collector\.ps1') -and ($nameValue -match '^(powershell|pwsh|cmd)(\.exe)?$')
    $isDefenderDlpUserAgent = ($nameValue -match '^(DlpUserAgent)(\.exe)?$') -and ($pathValue -match '(?i)\\ProgramData\\Microsoft\\Windows Defender\\Platform\\[^\\]+\\DlpUserAgent\.exe$')
    if ($isCollectorSelfRun -or $isDefenderDlpUserAgent) { continue }

    if ($cmd -match '(?i)(-enc\b|-encodedcommand\b|downloadstring|frombase64string|iex\b|invoke-expression\b|-w\s+hidden|-nop\b|-noni\b)') {
      [void]$reasons.Add("suspicious PowerShell style command line")
    }
    if ($cmd -match '(?i)(mshta\.exe.*http|regsvr32\.exe.*(http|scrobj)|rundll32\.exe.*(appdata|temp|programdata)|wscript\.exe|cscript\.exe)') {
      [void]$reasons.Add("suspicious LOLBin usage")
    }
    if ($pathValue -match '(?i)\\AppData\\|\\Temp\\|\\ProgramData\\') {
      [void]$reasons.Add("process running from high-risk path")
    }
    if ($nameValue -match '^(powershell|pwsh|rundll32|regsvr32|mshta|wscript|cscript|cmd|certutil|bitsadmin|wmic|psexec)(\.exe)?$') {
      [void]$reasons.Add("living-off-the-land process")
    }

    if (@($reasons).Count -gt 0) {
      [void]$findings.Add([pscustomobject]@{
        ProcessId = $proc.ProcessId
        Name = $proc.Name
        ExecutablePath = $proc.ExecutablePath
        CommandLine = $proc.CommandLine
        Reasons = ($reasons -join '; ')
      })
    }
  }
  return $findings
}

<#
.SYNOPSIS
Builds the structured TCP and UDP baseline text surface.

.DESCRIPTION
Queries Get-NetTCPConnection and Get-NetUDPEndpoint, formats both views, and returns the
combined text block.

.FUNCTION NAME
Get-BaselineNetText

.INPUTS
No direct parameters.

.OUTPUTS
String containing structured TCP and UDP text or an error message.
#>
function Get-BaselineNetText {
  try {
    $tcp = Get-NetTCPConnection -ErrorAction Stop |
      Sort-Object State, OwningProcess, LocalAddress, LocalPort |
      Select-Object State, LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess
    $udp = Get-NetUDPEndpoint -ErrorAction Stop |
      Sort-Object OwningProcess, LocalAddress, LocalPort |
      Select-Object LocalAddress, LocalPort, OwningProcess
    $text = @()
    $text += "TCP CONNECTIONS"
    $text += ($tcp | Format-Table -AutoSize | Out-String -Width 500)
    $text += ""
    $text += "UDP ENDPOINTS"
    $text += ($udp | Format-Table -AutoSize | Out-String -Width 500)
    return ($text -join [Environment]::NewLine)
  } catch {
    Add-CollectorError "Failed to collect structured TCP/UDP data: $($_.Exception.Message)"
    return "ERROR: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Exports baseline event-log text for the requested channel.

.DESCRIPTION
Queries the requested event channel for the last WindowHours with optional event IDs and
renders the results into analyst-facing text.

.FUNCTION NAME
Get-EventText

.INPUTS
Channel string, WindowHours integer, optional event IDs, and Take integer.

.OUTPUTS
String containing event-log text or an explanatory/error message.
#>
function Get-EventText {
  param(
    [Parameter(Mandatory=$true)][string]$Channel,
    [int]$WindowHours = 24,
    [int[]]$Ids,
    [int]$Take = 500
  )

  try {
    $startTime = (Get-Date).AddHours(-1 * [math]::Abs($WindowHours))
    $fh = @{
      LogName = $Channel
      StartTime = $startTime
    }
    if ($Ids -and @($Ids).Count -gt 0) { $fh.Id = $Ids }

    $events = Get-WinEvent -FilterHashtable $fh -ErrorAction Stop |
      Sort-Object TimeCreated -Descending |
      Select-Object -First $Take

    if (@($events).Count -eq 0) {
      Add-CollectorNote ("No events were found for channel [{0}] in the selected window." -f $Channel)
      return ("No events were found for channel [{0}] in the selected window." -f $Channel)
    }

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add(("CHANNEL={0}" -f $Channel))
    [void]$lines.Add(("WINDOW_HOURS={0}" -f $WindowHours))
    [void]$lines.Add(("EVENT_COUNT={0}" -f @($events).Count))
    [void]$lines.Add("")

    foreach ($ev in $events) {
      [void]$lines.Add(("TimeCreated={0}" -f $ev.TimeCreated.ToString("o")))
      [void]$lines.Add(("Id={0}" -f $ev.Id))
      [void]$lines.Add(("Provider={0}" -f $ev.ProviderName))
      [void]$lines.Add(("Level={0}" -f $ev.LevelDisplayName))
      [void]$lines.Add(("RecordId={0}" -f $ev.RecordId))
      [void]$lines.Add(("MachineName={0}" -f $ev.MachineName))
      if ($ev.TaskDisplayName) { [void]$lines.Add(("Task={0}" -f $ev.TaskDisplayName)) }
      if ($ev.UserId) { [void]$lines.Add(("UserId={0}" -f $ev.UserId.Value)) }
      [void]$lines.Add("Message:")
      [void]$lines.Add(($ev.Message -replace "`r", ""))
      [void]$lines.Add("-" * 60)
    }

    return ($lines -join [Environment]::NewLine)
  } catch {
    $msg = $_.Exception.Message
    if ($msg -match 'No events were found') {
      Add-CollectorNote ("No events were found for channel [{0}] in the selected window." -f $Channel)
      return ("No events were found for channel [{0}] in the selected window." -f $Channel)
    }
    Add-CollectorError "Failed to collect event log text for [$Channel]: $msg"
    return "ERROR collecting event log text for [$Channel]: $msg"
  }
}

<#
.SYNOPSIS
Collects Microsoft Defender status text.

.DESCRIPTION
Uses Get-MpComputerStatus when available and returns a formatted Defender status block,
or a bounded explanatory/error message when unavailable.

.FUNCTION NAME
Get-DefenderStatusText

.INPUTS
No direct parameters.

.OUTPUTS
String containing Defender status text or an explanatory/error message.
#>
function Get-DefenderStatusText {
  try {
    if (Get-Command Get-MpComputerStatus -ErrorAction SilentlyContinue) {
      return ((Get-MpComputerStatus | Format-List * | Out-String -Width 500).TrimEnd())
    }
    return "Get-MpComputerStatus is not available on this endpoint."
  } catch {
    Add-CollectorError "Failed to collect Defender status: $($_.Exception.Message)"
    return "ERROR: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Runs one cmd.exe step and returns its combined output text.

.DESCRIPTION
Wraps Invoke-CmdCapture and formats the result into the durable combined process-output
text block.

.FUNCTION NAME
Get-CmdText

.INPUTS
Command string, StepName string, and optional allowed exit-code list.

.OUTPUTS
String containing the combined command output text.
#>
function Get-CmdText {
  param(
    [string]$Command,
    [string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  $result = Invoke-CmdCapture -Command $Command -StepName $StepName -AllowedExitCodes $AllowedExitCodes
  return (Get-CombinedProcessOutput -Result $result)
}

<#
.SYNOPSIS
Collects registry-query text with bounded absent-key handling.

.DESCRIPTION
Runs reg query for the requested registry path, returns a bounded absent-key text block
for exit code 1, and otherwise returns the combined command output text.

.FUNCTION NAME
Get-RegistryQueryText

.INPUTS
RegistryPath string and StepName string.

.OUTPUTS
String containing registry-query output or a bounded absent-key explanation.
#>
function Get-RegistryQueryText {
  param([string]$RegistryPath,[string]$StepName)

  $cmd = ('reg query "{0}"' -f $RegistryPath)
  $result = Invoke-CmdCapture -Command $cmd -StepName $StepName -AllowedExitCodes @(0,1)
  if ($result.ExitCode -eq 1) {
    $message = "Registry key absent or not readable: $RegistryPath"
    Add-CollectorNote $message
    return (@(
      "COMMAND=reg query `"$RegistryPath`""
      "EXIT_CODE=1"
      ""
      "STDOUT:"
      ""
      ""
      "STDERR:"
      $message
    ) -join [Environment]::NewLine)
  }
  return (Get-CombinedProcessOutput -Result $result)
}

<#
.SYNOPSIS
Runs one staged external tool and returns its combined text output.

.DESCRIPTION
Wraps Invoke-ProcessCapture for a staged tool executable and formats the result into the
standard combined output text block.

.FUNCTION NAME
Invoke-ToolToText

.INPUTS
ToolPath string, argument array, StepName string, and optional allowed exit-code list.

.OUTPUTS
String containing the combined tool output text.
#>
function Invoke-ToolToText {
  param(
    [string]$ToolPath,
    [string[]]$Arguments,
    [string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  $result = Invoke-ProcessCapture -FilePath $ToolPath -Arguments $Arguments -StepName $StepName -AllowedExitCodes $AllowedExitCodes
  return (Get-CombinedProcessOutput -Result $result)
}

<#
.SYNOPSIS
Builds a unique staged filename.

.DESCRIPTION
Combines the supplied prefix, hostname, timestamp, GUID fragment, and extension into a
unique staged artifact filename.

.FUNCTION NAME
New-StageName

.INPUTS
Prefix string and Extension string.

.OUTPUTS
String staged filename.
#>
function New-StageName {
  param([string]$Prefix,[string]$Extension)
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $guid = ([guid]::NewGuid().ToString("N")).Substring(0,8)
  return ("{0}_{1}_{2}_{3}{4}" -f $Prefix, $env:COMPUTERNAME, $ts, $guid, $Extension)
}

<#
.SYNOPSIS
Resolves the binary path for one Windows service.

.DESCRIPTION
Queries Win32_Service for the requested service name and extracts the executable path
from the service PathName field.

.FUNCTION NAME
Get-ServiceBinaryPath

.INPUTS
Name string for the service.

.OUTPUTS
String service-binary path or null when unresolved.
#>
function Get-ServiceBinaryPath {
  param([string]$Name)
  try {
    $svc = Get-CimInstance -ClassName Win32_Service -Filter ("Name='{0}'" -f ($Name -replace "'", "''")) -ErrorAction Stop
    if (-not $svc) { return $null }
    $pn = [string]$svc.PathName
    if ([string]::IsNullOrWhiteSpace($pn)) { return $null }
    if ($pn.StartsWith('"')) {
      return ($pn -replace '^"([^"]+)".*$', '$1')
    }
    return ($pn -replace '^([^\s]+).*$', '$1')
  } catch {
    Add-CollectorError "Failed to resolve service binary for [$Name]: $($_.Exception.Message)"
    return $null
  }
}

<#
.SYNOPSIS
Stages a copy of one filesystem path into the staged directory.

.DESCRIPTION
Validates that the source path exists, ensures the staged directory exists, copies the
source into a unique staged filename, and returns the staged path.

.FUNCTION NAME
Stage-PathCopy

.INPUTS
SourcePath string and StagedDir string.

.OUTPUTS
String staged copy path.
#>
function Stage-PathCopy {
  param([string]$SourcePath,[string]$StagedDir)
  if (-not (Test-Path -LiteralPath $SourcePath)) {
    throw "Path not found: $SourcePath"
  }
  Ensure-Directory -Path $StagedDir
  $leaf = Split-Path -Leaf $SourcePath
  $dest = Join-Path $StagedDir (New-StageName -Prefix ("STAGED_" + $leaf) -Extension "")
  Copy-Item -LiteralPath $SourcePath -Destination $dest -Force
  return $dest
}

<#
.SYNOPSIS
Exports one scheduled task XML surface.

.DESCRIPTION
Runs schtasks.exe /query /xml for the requested task name and returns the combined
command output text.

.FUNCTION NAME
Get-TaskXml

.INPUTS
TaskName string.

.OUTPUTS
String containing task XML command output or an error message.
#>
function Get-TaskXml {
  param([string]$TaskName)
  try {
    $result = Invoke-ProcessCapture -FilePath "schtasks.exe" -Arguments @("/query","/tn",$TaskName,"/xml") -StepName "ENRICH_PULL_TASK_XML"
    return (Get-CombinedProcessOutput -Result $result)
  } catch {
    Add-CollectorError "Failed to export task XML for [$TaskName]: $($_.Exception.Message)"
    return "ERROR exporting task XML: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Exports a filtered EVTX file for the requested channel.

.DESCRIPTION
Builds the timediff-based XPath query for the requested window and optional event IDs,
invokes wevtutil.exe, and verifies that the EVTX file was created.

.FUNCTION NAME
Export-FilteredEvtx

.INPUTS
LogChannel string, WindowHours integer, optional event IDs, OutPath string, and
ScratchDir string.

.OUTPUTS
No direct output. Writes the EVTX file to OutPath or throws on failure.
#>
function Export-FilteredEvtx {
  param(
    [string]$LogChannel,
    [int]$WindowHours,
    [int[]]$Ids,
    [string]$OutPath,
    [string]$ScratchDir
  )

  Ensure-Directory -Path $ScratchDir
  $parentDir = Split-Path -Parent $OutPath
  if (-not [string]::IsNullOrWhiteSpace($parentDir)) {
    Ensure-Directory -Path $parentDir
  }

  $ms = [math]::Abs($WindowHours) * 3600000
  $systemParts = @("TimeCreated[timediff(@SystemTime) <= $ms]")
  if ($Ids -and @($Ids).Count -gt 0) {
    $idExpr = "(" + (($Ids | ForEach-Object { "EventID=$_"} ) -join " or ") + ")"
    $systemParts += $idExpr
  }
  $xpath = "*[System[" + ($systemParts -join " and ") + "]]"

  $args = @(
    "epl",
    $LogChannel,
    $OutPath,
    "/q:$xpath",
    "/ow:true"
  )

  $result = Invoke-ProcessCapture -FilePath "wevtutil.exe" -Arguments $args -StepName ("ENRICH_LOGRAW_{0}" -f ($LogChannel -replace '[\\/:*?"<>|]','_'))
  if ($result.ExitCode -ne 0) {
    throw "wevtutil.exe returned exit code $($result.ExitCode)"
  }
  if (-not (Test-Path -LiteralPath $OutPath)) {
    throw "EVTX export did not create output file."
  }
}

<#
.SYNOPSIS
Builds the tool map for the staged tools directory.

.DESCRIPTION
Resolves the expected collector helper tools from the staged tools directory and returns
the resulting tool-path map.

.FUNCTION NAME
Get-ToolMap

.INPUTS
ToolsDir string.

.OUTPUTS
Hashtable mapping tool names to resolved paths.
#>
function Get-ToolMap {
  param([string]$ToolsDir)
  return @{
    accesschk = Resolve-Tool -ToolsDir $ToolsDir -BaseName "accesschk"
    autorunsc = Resolve-Tool -ToolsDir $ToolsDir -BaseName "autorunsc"
    listdlls = Resolve-Tool -ToolsDir $ToolsDir -BaseName "listdlls"
    pipelist = Resolve-Tool -ToolsDir $ToolsDir -BaseName "pipelist"
    pslist = Resolve-Tool -ToolsDir $ToolsDir -BaseName "pslist"
    sigcheck = Resolve-Tool -ToolsDir $ToolsDir -BaseName "sigcheck"
    streams = Resolve-Tool -ToolsDir $ToolsDir -BaseName "streams"
    strings = Resolve-Tool -ToolsDir $ToolsDir -BaseName "strings"
    tcpvcon = Resolve-Tool -ToolsDir $ToolsDir -BaseName "tcpvcon"
  }
}

<#
.SYNOPSIS
Builds the tool-availability table text.

.DESCRIPTION
Formats the tool map into an analyst-friendly table showing tool presence and resolved
path.

.FUNCTION NAME
Get-CommandAvailabilityTable

.INPUTS
ToolMap hashtable.

.OUTPUTS
String containing the tool-availability table.
#>
function Get-CommandAvailabilityTable {
  param([hashtable]$ToolMap)
  $rows = foreach ($key in ($ToolMap.Keys | Sort-Object)) {
    [pscustomobject]@{
      Tool = $key
      Present = [bool]($ToolMap[$key])
      Path = $ToolMap[$key]
    }
  }
  return ($rows | Format-Table -AutoSize | Out-String -Width 500)
}

<#
.SYNOPSIS
Creates the run manifest JSON file.

.DESCRIPTION
Builds the standard manifest object for the current run, including files, notes, errors,
recommendations, tool map, and extra metadata, writes it to disk, and returns the path.

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

  $manifest = [ordered]@{
    host = $env:COMPUTERNAME
    run_id = $State.RunId
    mode = $ModeName
    tier = $TierName
    script_version = $ScriptVersion
    created_local = (Get-Date).ToString("o")
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    files = @($Files)
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
Creates one ZIP bundle from the supplied paths.

.DESCRIPTION
Ensures the bundles directory exists, removes any prior bundle with the same name,
filters the input list to existing paths, creates the ZIP archive, and returns the final
bundle path.

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

  Ensure-Directory -Path $BundlesDir
  $bundlePath = Join-Path $BundlesDir $BundleName
  if (Test-Path -LiteralPath $bundlePath) {
    Remove-Item -LiteralPath $bundlePath -Force -ErrorAction SilentlyContinue
  }
  $existing = @($Paths | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
  if (@($existing).Count -eq 0) {
    throw "No bundle inputs were found."
  }
  Compress-Archive -LiteralPath $existing -DestinationPath $bundlePath -CompressionLevel Optimal -Force
  return $bundlePath
}
