param(
  [ValidateSet("Collect","Enrich","Cleanup")]
  [string]$Mode = "Collect",

  [ValidateSet("T1","T2")]
  [string]$Tier = "T1",

  [int]$Hours = 24,

  [string]$OutRoot = "C:\Temp",

  [string]$PackageName = "DCOIR_Collector.zip",

  [string]$RunId,

  [ValidateSet(
    "SigcheckPath",
    "ListDllsPid",
    "AccessChkFile",
    "AccessChkService",
    "AccessChkReg",
    "StringsPath",
    "StreamsPath",
    "TcpvconRefresh",
    "LogText",
    "LogRaw",
    "PullSuspiciousFile",
    "PullScriptOrConfig",
    "PullTaskXml",
    "PullServiceBinary",
    "PullWmiReferencedFile"
  )]
  [string]$Action,

  [int]$TargetPid,
  [string]$Path,
  [string]$ServiceName,
  [string]$RegistryPath,
  [string]$LogName,
  [int[]]$EventId,
  [int]$MaxEvents = 500,
  [string]$EnrichSessionId,
  [switch]$NewEnrichSession,
  [switch]$FinalizeEnrichSession,
  [string]$Quick,
  [string]$Target,
  [string]$Target2,

  [switch]$Targeted,
  [ValidateSet("Generic","PopupWindow","ScriptExecution","PersistenceFollowUp","NetworkOnly","ProcessAndPowerShell")]
  [string]$TargetProfile = "Generic",
  [string]$WindowStart,
  [string]$WindowEnd,
  [string[]]$IncludeArtifactCategory,
  [string]$FocusProcess,
  [string]$FocusPath,
  [string]$FocusIndicator,
  [string]$FocusIndicatorType,
  [string]$UserReport,

  [Alias("help","h","?")]
  [switch]$ShowHelp,

  [Alias("version","ver","buildinfo")]
  [switch]$ShowVersion
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Continue"

<#
.SYNOPSIS
Checks whether one runtime path candidate is usable for collector self-location.

.DESCRIPTION
Rejects blank paths and host shell executable paths such as powershell.exe or pwsh.exe
so script-mode execution does not mistake the PowerShell host for the collector source.

.FUNCTION NAME
Test-DCOIRRuntimePathCandidate

.INPUTS
Path string.

.OUTPUTS
Boolean indicating whether the candidate is a usable collector runtime path.
#>
function Test-DCOIRRuntimePathCandidate {
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
Resolves the collector runtime path for script and optional EXE execution.

.DESCRIPTION
Prefers script-specific paths such as PSCommandPath and MyInvocation.PSCommandPath for
PowerShell script execution, then safely checks MyInvocation.MyCommand properties, and
finally falls back to the current process executable path for the optional EXE variant.
The resolver avoids strict-mode property errors when PS2EXE command metadata lacks a
Path property.

.FUNCTION NAME
Resolve-DCOIRRuntimePath

.INPUTS
No direct parameters.

.OUTPUTS
String absolute path to the active collector script or optional EXE runtime.
#>
function Resolve-DCOIRRuntimePath {
  foreach ($candidate in @($PSCommandPath, $MyInvocation.PSCommandPath)) {
    if (Test-DCOIRRuntimePathCandidate -Path $candidate) {
      return [System.IO.Path]::GetFullPath([string]$candidate)
    }
  }

  try {
    $cmd = $MyInvocation.MyCommand
    if ($null -ne $cmd) {
      $pathProperty = $cmd.PSObject.Properties['Path']
      if ($pathProperty -and (Test-DCOIRRuntimePathCandidate -Path ([string]$pathProperty.Value))) {
        return [System.IO.Path]::GetFullPath([string]$pathProperty.Value)
      }
      $sourceProperty = $cmd.PSObject.Properties['Source']
      if ($sourceProperty -and (Test-DCOIRRuntimePathCandidate -Path ([string]$sourceProperty.Value))) {
        return [System.IO.Path]::GetFullPath([string]$sourceProperty.Value)
      }
    }
  } catch { }

  try {
    $processPath = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    if (Test-DCOIRRuntimePathCandidate -Path $processPath) {
      return [System.IO.Path]::GetFullPath($processPath)
    }
  } catch { }

  return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path "DCOIR_Collector.ps1"))
}

$ScriptFilePath = Resolve-DCOIRRuntimePath
$ScriptVersion = "4.0.7"

$Global:CollectorErrors = New-Object System.Collections.ArrayList
$Global:CollectorNotes = New-Object System.Collections.ArrayList
$Global:RecommendedActions = New-Object System.Collections.ArrayList
$Global:ExecutionTxtPath = $null
$Global:ExecutionJsonlPath = $null
$Global:ErrorsLogPath = $null
$Global:CurrentRunId = $null
$script:ContextualHelpTopic = $null

# BEGIN COMPILED COLLECTOR PARTS
# BEGIN DCOIR_Collector.01_Core_State_And_Utilities.ps1
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
# END DCOIR_Collector.01_Core_State_And_Utilities.ps1

# BEGIN DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1
<#
.SYNOPSIS
DCOIR collector baseline collection and reporting helpers.

.DESCRIPTION
Builds the baseline collection surface, including execution-context and audit-policy
artifacts, host, identity, process, network, persistence, security, and event-log
artifacts, plus the analyst-facing baseline report, metadata report, upload summary, and
attachment-budget manifest.

.FILE NAME
DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1

.INPUTS
Collector state and tool-map hashtables, current tier and hour settings, artifact paths,
and collector-global notes, errors, recommendations, and targeted runtime settings.

.OUTPUTS
Baseline and metadata report text, upload-summary artifacts, attachment-budget manifest
artifacts, and helper return values used by the collector runtime.
#>

<#
.SYNOPSIS
Returns the Gemini upload budget thresholds used by the collector.

.DESCRIPTION
Defines the hard and safe per-file and total-size thresholds used to decide whether the
recommended Gemini upload set fits comfortably within the environment budget.

.FUNCTION NAME
Get-CollectorUploadBudget

.INPUTS
No direct parameters.

.OUTPUTS
Hashtable containing hard and safe per-file and total-size budget values in KB.
#>
function Get-CollectorUploadBudget {
  return @{
    HardPerFileKB = 1000
    HardTotalKB = 2000
    SafePerFileKB = 900
    SafeTotalKB = 1800
  }
}

<#
.SYNOPSIS
Returns the size of one file in KB.

.DESCRIPTION
Checks whether the file exists and returns a rounded-up KB size for the file. Returns
zero when the path does not exist.

.FUNCTION NAME
Get-FileSizeKB

.INPUTS
Path string for the file to inspect.

.OUTPUTS
Integer file size in KB.
#>
function Get-FileSizeKB {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) { return 0 }
  return [int][Math]::Ceiling(((Get-Item -LiteralPath $Path).Length) / 1KB)
}

<#
.SYNOPSIS
Returns the SHA256 hash for one file when available.

.DESCRIPTION
Computes a SHA256 digest for provenance and reconstruction metadata. Returns an empty
string when the path is blank, missing, or cannot be hashed.

.FUNCTION NAME
Get-FileSha256

.INPUTS
Path string for the file to inspect.

.OUTPUTS
SHA256 hash string or an empty string.
#>
function Get-FileSha256 {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) { return "" }
  try {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
  } catch {
    Add-CollectorError ("Failed to hash file [{0}]: {1}" -f $Path, $_.Exception.Message)
    return ""
  }
}

<#
.SYNOPSIS
Builds deterministic test padding for a text artifact.

.DESCRIPTION
Reads a process-scoped environment variable containing a requested KB value and returns
repeatable text content of at least that size. Used only by harness tests to make a real
collector artifact key exceed the upload-safe chunk threshold.

.FUNCTION NAME
Get-TestTextPaddingFromEnvironment

.INPUTS
Environment variable name.

.OUTPUTS
String containing deterministic padding or an empty string.
#>
function Get-TestTextPaddingFromEnvironment {
  param([string]$Name)
  $raw = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if ([string]::IsNullOrWhiteSpace($raw)) { return "" }
  [int]$requestedKB = 0
  if (-not [int]::TryParse($raw, [ref]$requestedKB) -or $requestedKB -le 0) { return "" }

  $line = 'DCOIR_PRODUCTION_CHUNK_TEST_PAYLOAD|ABCDEFGHIJKLMNOPQRSTUVWXYZ|0123456789|line='
  $sb = New-Object System.Text.StringBuilder
  $index = 0
  while ([System.Text.Encoding]::UTF8.GetByteCount($sb.ToString()) -lt ($requestedKB * 1024)) {
    [void]$sb.AppendLine(('{0}{1:000000}' -f $line, $index))
    $index += 1
  }
  return $sb.ToString()
}

<#
.SYNOPSIS
Chooses a UTF-8 safe byte length for one upload-safe chunk.

.DESCRIPTION
Returns a chunk length that stays within the target byte budget without ending in the
middle of a UTF-8 multibyte character whenever the source bytes are valid UTF-8.

.FUNCTION NAME
Get-Utf8SafeChunkLength

.INPUTS
Source byte array, current offset, and target chunk byte count.

.OUTPUTS
Integer byte length for the next chunk.
#>
function Get-Utf8SafeChunkLength {
  param([byte[]]$Bytes,[int]$Offset,[int]$TargetBytes)

  $remaining = $Bytes.Length - $Offset
  if ($remaining -le 0) { return 0 }
  $length = [Math]::Min($TargetBytes, $remaining)
  if (($Offset + $length) -ge $Bytes.Length) { return $length }

  $end = $Offset + $length
  $lead = $end - 1
  while (($lead -gt $Offset) -and (($Bytes[$lead] -band 0xC0) -eq 0x80)) { $lead -= 1 }
  $leadByte = $Bytes[$lead]

  if (($leadByte -band 0x80) -eq 0) { return $length }
  if (($leadByte -band 0xE0) -eq 0xC0) { $charLength = 2 }
  elseif (($leadByte -band 0xF0) -eq 0xE0) { $charLength = 3 }
  elseif (($leadByte -band 0xF8) -eq 0xF0) { $charLength = 4 }
  else { return $length }

  if (($lead + $charLength) -le $end) { return $length }
  $safeLength = $lead - $Offset
  if ($safeLength -gt 0) { return $safeLength }
  return [Math]::Min($charLength, $remaining)
}

<#
.SYNOPSIS
Splits a real text artifact into upload-safe chunk companions.

.DESCRIPTION
Creates ordered byte-preserving chunks that can be concatenated to reconstruct the original
artifact exactly. The source artifact is preserved; this helper writes derivative chunk
companions plus metadata used by the aggregate upload-safe chunk manifest.

.FUNCTION NAME
Split-TextArtifactIntoUploadSafeChunks

.INPUTS
Source artifact path, artifact directory, source key, target chunk size, and origin label.

.OUTPUTS
Ordered hashtable describing chunk paths, sizes, hashes, source provenance, and reconstruction.
#>
function Split-TextArtifactIntoUploadSafeChunks {
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
    [System.IO.File]::WriteAllBytes($chunkPath, [byte[]]@())
    [void]$chunkPaths.Add($chunkPath)
    [void]$chunkSizes.Add((Get-FileSizeKB -Path $chunkPath))
    [void]$chunkSha256.Add((Get-FileSha256 -Path $chunkPath))
  }

  while ($offset -lt $sourceBytes.Length) {
    $length = Get-Utf8SafeChunkLength -Bytes $sourceBytes -Offset $offset -TargetBytes $targetBytes
    if ($length -le 0) { $length = [Math]::Min($targetBytes, ($sourceBytes.Length - $offset)) }
    $chunkBytes = New-Object byte[] $length
    [Array]::Copy($sourceBytes, $offset, $chunkBytes, 0, $length)
    $chunkPath = Join-Path $ArtifactsDir ("90_UPLOAD_SAFE_CHUNKS_{0}_chunk_{1:000}.txt" -f $safeKey, $chunkIndex)
    [System.IO.File]::WriteAllBytes($chunkPath, $chunkBytes)
    [void]$chunkPaths.Add($chunkPath)
    [void]$chunkSizes.Add((Get-FileSizeKB -Path $chunkPath))
    [void]$chunkSha256.Add((Get-FileSha256 -Path $chunkPath))
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
Detects selected human-readable artifact keys that exceed the configured safe per-file
budget, writes ordered chunk companions, and returns manifest rows for the normal collect
handoff surfaces.

.FUNCTION NAME
New-ProductionUploadSafeChunkCompanions

.INPUTS
Collector state, artifact map, and upload budget.

.OUTPUTS
Array of ordered manifest rows.
#>
function New-ProductionUploadSafeChunkCompanions {
  param([hashtable]$State,[hashtable]$ArtifactMap,[hashtable]$Budget)

  $rows = New-Object System.Collections.ArrayList
  foreach ($key in @('security_filtered','powershell_operational_filtered','taskscheduler_operational_filtered')) {
    if (-not $ArtifactMap.ContainsKey($key)) { continue }
    $sourcePath = [string]$ArtifactMap[$key]
    if ([string]::IsNullOrWhiteSpace($sourcePath) -or -not (Test-Path -LiteralPath $sourcePath)) { continue }
    $sourceSizeKB = Get-FileSizeKB -Path $sourcePath
    if ($sourceSizeKB -le [int]$Budget.SafePerFileKB) { continue }

    $chunkResult = Split-TextArtifactIntoUploadSafeChunks -SourcePath $sourcePath -ArtifactsDir $State.ArtifactsDir -SourceKey $key -TargetChunkKB ([Math]::Min(700, [int]$Budget.SafePerFileKB))
    [void]$rows.Add($chunkResult)
    foreach ($chunkPath in @($chunkResult.chunk_paths)) {
      [void]$ArtifactMap.Add(("{0}_upload_safe_chunk_{1:000}" -f $key, (@($ArtifactMap.Keys | Where-Object { $_ -like ("{0}_upload_safe_chunk_*" -f $key) }).Count + 1)), $chunkPath)
    }
  }

  return @($rows)
}

<#
.SYNOPSIS
Converts one object into safe JSON text for artifact writing.

.DESCRIPTION
Serializes the supplied object with a high JSON depth and appends a trailing newline so
artifact JSON text files remain stable and readable.

.FUNCTION NAME
Convert-ToSafeJsonText

.INPUTS
InputObject to serialize.

.OUTPUTS
String containing newline-terminated JSON text.
#>
function Convert-ToSafeJsonText {
  param([object]$InputObject)
  return (($InputObject | ConvertTo-Json -Depth 12) + [Environment]::NewLine)
}

<#
.SYNOPSIS
Determines whether the current collector context is elevated.

.DESCRIPTION
Queries the current Windows identity and returns true when the current principal is in
the local Administrators role. Returns false on any lookup error.

.FUNCTION NAME
Test-CollectorIsElevated

.INPUTS
No direct parameters.

.OUTPUTS
Boolean indicating whether the current collector context is elevated.
#>
function Test-CollectorIsElevated {
  try {
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch {
    return $false
  }
}

<#
.SYNOPSIS
Builds the execution-context text artifact.

.DESCRIPTION
Collects the current user, elevation state, host, process, PowerShell version, and
working-directory context, then adds a short diagnostic note describing the expected
visibility posture for elevated versus non-elevated collection.

.FUNCTION NAME
Get-CollectorExecutionContextText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the execution-context text artifact.
#>
function Get-CollectorExecutionContextText {
  $isElevated = Test-CollectorIsElevated
  $identityName = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  $lines = @(
    'EXECUTION_CONTEXT',
    ("UserContext={0}" -f $identityName),
    ("IsElevated={0}" -f $isElevated),
    ("Host={0}" -f $env:COMPUTERNAME),
    ("ProcessId={0}" -f $PID),
    ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion),
    ("CurrentDirectory={0}" -f (Get-Location).Path)
  )
  if ($isElevated) {
    $lines += 'DiagnosticContext=Elevated execution should allow owner-aware netstat capture and broader Security log visibility when audit policy supports it.'
  } else {
    $lines += 'DiagnosticContext=Non-elevated execution can restrict owner-aware netstat capture and Security log visibility on some hosts.'
  }
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Collects the audit-policy text artifact.

.DESCRIPTION
Runs auditpol for the key Security auditing subcategories and returns the combined
captured output text.

.FUNCTION NAME
Get-SecurityAuditPolicyText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the combined audit-policy command output.
#>
function Get-SecurityAuditPolicyText {
  $result = Invoke-CmdCapture -Command 'auditpol /get /subcategory:"Logon","Logoff","Special Logon","Process Creation"' -StepName 'SECURITY_AUDIT_POLICY' -AllowedExitCodes @(0)
  return (Get-CombinedProcessOutput -Result $result)
}

<#
.SYNOPSIS
Builds the netstat capture bundle for the current run.

.DESCRIPTION
Attempts owner-aware netstat capture first, classifies elevation-required or other
failure modes, optionally captures a PID-only supplemental netstat surface, and returns
both text surfaces plus the owner-aware capture status.

.FUNCTION NAME
Get-NetstatCaptureBundle

.INPUTS
IsElevated boolean describing the current collector context.

.OUTPUTS
Hashtable containing owner-aware text, owner-aware status, owner-aware exit code, and
optional PID-only text.
#>
function Get-NetstatCaptureBundle {
  param([bool]$IsElevated)

  $ownerAwareResult = Invoke-CmdCapture -Command 'netstat -abno' -StepName 'NETWORK_NETSTAT_OWNER_AWARE' -AllowedExitCodes @(0,1)
  $ownerAwareText = Get-CombinedProcessOutput -Result $ownerAwareResult
  $combinedOutput = (([string]$ownerAwareResult.StdOut) + ' ' + ([string]$ownerAwareResult.StdErr)).Trim()
  $requiresElevation = ($ownerAwareResult.ExitCode -ne 0) -and ($combinedOutput -match '(?i)requires elevation')

  $pidOnlyResult = $null
  $pidOnlyText = $null
  $status = 'OWNER_AWARE_OK'

  if ($requiresElevation) {
    $status = 'OWNER_AWARE_REQUIRES_ELEVATION'
    Add-CollectorNote 'Owner-aware netstat capture (netstat -abno) requires elevation in the current execution context. A supplemental PID-only netstat capture was collected separately, but executable ownership attribution remains unavailable until an elevated run.'
    $pidOnlyResult = Invoke-CmdCapture -Command 'netstat -ano' -StepName 'NETWORK_NETSTAT_PID_ONLY' -AllowedExitCodes @(0)
    $pidOnlyText = Get-CombinedProcessOutput -Result $pidOnlyResult
  } elseif ($ownerAwareResult.ExitCode -ne 0) {
    $status = 'OWNER_AWARE_FAILED'
    Add-CollectorError ('Owner-aware netstat capture (netstat -abno) failed for a reason other than missing elevation. Review the artifact for the exact command output. ExitCode={0}' -f $ownerAwareResult.ExitCode)
  }

  return @{
    OwnerAwareText = $ownerAwareText
    OwnerAwareStatus = $status
    OwnerAwareExitCode = [int]$ownerAwareResult.ExitCode
    PidOnlyText = $pidOnlyText
  }
}

<#
.SYNOPSIS
Creates the collect upload summary and attachment-budget manifest.

.DESCRIPTION
Selects the default analyst-first Gemini upload set, evaluates it against the safe and
hard environment budgets, writes the upload summary text and JSON manifest, and returns
the key status values to the caller.

.FUNCTION NAME
New-CollectUploadArtifacts

.INPUTS
Collector state hashtable and baseline result hashtable containing the artifact map.

.OUTPUTS
Hashtable containing upload-summary path, manifest path, default-set status, total KB,
and recommended file count.
#>
function New-CollectUploadArtifacts {
  param([hashtable]$State,[hashtable]$Baseline)

  $budget = Get-CollectorUploadBudget
  $artifactMap = $Baseline.ArtifactMap
  $chunkCompanions = New-ProductionUploadSafeChunkCompanions -State $State -ArtifactMap $artifactMap -Budget $budget
  $recommendedPaths = @()

  foreach ($key in @(
    'collection_metadata',
    'collection_notes_and_limitations',
    'security_high_signal_summary',
    'process_inventory',
    'structured_net',
    'defender_status',
    'analyst_follow_up_queue'
  )) {
    if ($artifactMap.ContainsKey($key) -and (Test-Path -LiteralPath $artifactMap[$key])) {
      $recommendedPaths += $artifactMap[$key]
    }
  }

  if ($State.MetadataReportPath -and (Test-Path -LiteralPath $State.MetadataReportPath)) {
    $recommendedPaths = @($State.MetadataReportPath) + $recommendedPaths
  }

  $recommended = New-Object System.Collections.ArrayList
  $safeTotal = 0
  foreach ($path in $recommendedPaths) {
    $sizeKB = Get-FileSizeKB -Path $path
    $safeTotal += $sizeKB
    [void]$recommended.Add([ordered]@{
      path = $path
      relative_path = [string](Resolve-Path -LiteralPath $path | ForEach-Object { $_.Path.Replace($State.RunRoot + '\\', '') })
      size_kb = $sizeKB
      within_safe_per_file = ($sizeKB -le $budget.SafePerFileKB)
      within_hard_per_file = ($sizeKB -le $budget.HardPerFileKB)
    })
  }

  $setStatus = if (($safeTotal -le $budget.SafeTotalKB) -and (@($recommended | Where-Object { -not $_.within_safe_per_file }).Count -eq 0)) {
    'SAFE_DEFAULT_SET'
  } elseif (($safeTotal -le $budget.HardTotalKB) -and (@($recommended | Where-Object { -not $_.within_hard_per_file }).Count -eq 0)) {
    'HARD_LIMIT_ONLY'
  } else {
    'EXCEEDS_ENVIRONMENT_BUDGET'
  }

  $uploadSummaryPath = Join-Path $State.ReportsDir ("DCOIR_UPLOAD_SUMMARY_{0}_{1}.txt" -f $env:COMPUTERNAME, $State.RunId)
  $uploadManifestPath = Join-Path $State.ReportsDir ("DCOIR_ATTACHMENT_BUDGET_MANIFEST_{0}_{1}.json.txt" -f $env:COMPUTERNAME, $State.RunId)
  $chunkManifestPath = $null
  if (@($chunkCompanions).Count -gt 0) {
    $chunkManifestPath = Join-Path $State.ReportsDir ("DCOIR_UPLOAD_SAFE_CHUNK_MANIFEST_{0}_{1}.json.txt" -f $env:COMPUTERNAME, $State.RunId)
    $chunkManifestObj = [ordered]@{
      run_id = $State.RunId
      origin = 'collector_production_upload_safe'
      budget = $budget
      chunked_artifact_count = @($chunkCompanions).Count
      chunked_artifacts = @($chunkCompanions)
    }
    Set-Content -Path $chunkManifestPath -Value (Convert-ToSafeJsonText -InputObject $chunkManifestObj) -Encoding UTF8
    $State.UploadSafeChunkManifestPath = $chunkManifestPath
    $Baseline.ArtifactMap['upload_safe_chunk_manifest'] = $chunkManifestPath
    [void]$Baseline.ArtifactPaths.Add($chunkManifestPath)
    foreach ($chunkRow in @($chunkCompanions)) {
      foreach ($chunkPath in @($chunkRow.chunk_paths)) {
        [void]$Baseline.ArtifactPaths.Add($chunkPath)
      }
    }
  }

  $summaryLines = @(
    "CollectorVersion=$ScriptVersion",
    "RunId=$($State.RunId)",
    "WorkflowPhase=CollectBaseline",
    "UploadModel=ChunkFirst",
    "DoNotAssumeMonolithicBaselineUpload=true",
    "HardPerFileKB=$($budget.HardPerFileKB)",
    "HardTotalKB=$($budget.HardTotalKB)",
    "SafePerFileKB=$($budget.SafePerFileKB)",
    "SafeTotalKB=$($budget.SafeTotalKB)",
    "DefaultSetStatus=$setStatus",
    "RecommendedUploadTotalKB=$safeTotal",
    "",
    "Recommended files for Gemini upload by default:"
  )
  foreach ($row in $recommended) {
    $summaryLines += ('- {0} [{1} KB]' -f $row.path, $row.size_kb)
  }
  $summaryLines += ""
  $summaryLines += "Default guidance:"
  $summaryLines += "- Prefer this upload summary, the metadata report, and the listed representative artifacts."
  $summaryLines += "- Do not assume the large merged baseline report is upload-safe in the office Gemini environment."
  $summaryLines += "- If this set must be trimmed further, keep metadata, follow-up queue, security high-signal summary, and one representative process/network artifact first."
  if (@($chunkCompanions).Count -gt 0) {
    $summaryLines += ""
    $summaryLines += "Upload-safe chunk companions:"
    $summaryLines += ("- UPLOAD_SAFE_CHUNK_MANIFEST_PATH={0}" -f $chunkManifestPath)
    foreach ($chunkRow in @($chunkCompanions)) {
      $summaryLines += ("- SourceKey={0} SourceSizeKB={1} ChunkCount={2} TargetChunkKB={3}" -f $chunkRow.source_artifact_key, $chunkRow.source_size_kb, $chunkRow.chunk_count, $chunkRow.target_chunk_kb)
      foreach ($chunkPath in @($chunkRow.chunk_paths)) {
        $summaryLines += ("  - {0}" -f $chunkPath)
      }
    }
    $summaryLines += "- Upload the high-signal summary first for triage; use full-fidelity chunk companions when the oversized source artifact is needed."
  }

  Set-Content -Path $uploadSummaryPath -Value $summaryLines -Encoding UTF8

  $manifestObj = [ordered]@{
    run_id = $State.RunId
    workflow_phase = 'collect_baseline'
    upload_model = 'chunk_first'
    budget = $budget
    default_set_status = $setStatus
    recommended_upload_total_kb = $safeTotal
    recommended_upload_files = @($recommended)
    upload_safe_chunk_manifest_path = $chunkManifestPath
    upload_safe_chunk_companions = @($chunkCompanions)
    baseline_report_path = $State.BaselineReportPath
    metadata_report_path = $State.MetadataReportPath
    note = 'The merged baseline report may be useful for local analyst review but is no longer the default Gemini-facing upload surface.'
  }
  Set-Content -Path $uploadManifestPath -Value (Convert-ToSafeJsonText -InputObject $manifestObj) -Encoding UTF8

  return @{
    UploadSummaryPath = $uploadSummaryPath
    UploadManifestPath = $uploadManifestPath
    DefaultSetStatus = $setStatus
    RecommendedUploadTotalKB = $safeTotal
    RecommendedUploadCount = @($recommended).Count
    UploadSafeChunkManifestPath = $chunkManifestPath
    UploadSafeChunkCompanionCount = @($chunkCompanions).Count
  }
}

<#
.SYNOPSIS
Runs one Tier 2 registry query through direct reg.exe capture.

.DESCRIPTION
Invokes reg.exe directly for one Tier 2 deep-check registry path, preserves the bounded
captured output, and records a collector error when the query returns a non-zero exit
code so the artifact remains the truth surface instead of failing invisibly.

.FUNCTION NAME
Invoke-Tier2RegistryQueryText

.INPUTS
RegistryPath string, StepName string, and optional FailureLabel string.

.OUTPUTS
String containing the combined direct-process output for the Tier 2 registry query.
#>
function Invoke-Tier2RegistryQueryText {
  param(
    [Parameter(Mandatory=$true)][string]$RegistryPath,
    [Parameter(Mandatory=$true)][string]$StepName,
    [string]$FailureLabel = 'Tier 2 registry query'
  )

  $result = Invoke-ProcessCapture -FilePath 'reg.exe' -Arguments @('query', $RegistryPath, '/s') -StepName $StepName -AllowedExitCodes @(0,1)
  if ($result.ExitCode -ne 0) {
    Add-CollectorError ('{0} returned ExitCode={1} for path [{2}]. Review the artifact for the exact bounded output.' -f $FailureLabel, $result.ExitCode, $RegistryPath)
  }
  return (Get-CombinedProcessOutput -Result $result)
}

<#
.SYNOPSIS
Builds the Tier 2 WMI persistence text surface class by class.

.DESCRIPTION
Queries the root\subscription WMI classes one at a time so one failing class does not
break the whole Tier 2 WMI persistence surface. Each class writes either formatted
results, NO_RESULTS, or one bounded error line that is also added to the collector error
list.

.FUNCTION NAME
Get-Tier2WmiPersistenceText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the combined Tier 2 WMI persistence text surface.
#>
function Get-Tier2WmiPersistenceText {
  $classNames = @(
    '__EventFilter',
    'CommandLineEventConsumer',
    'ActiveScriptEventConsumer',
    'FilterToConsumerBinding'
  )

  $sections = New-Object System.Collections.ArrayList
  foreach ($className in $classNames) {
    [void]$sections.Add(('WMI_CLASS={0}' -f $className))
    [void]$sections.Add('')
    try {
      $instances = @(Get-CimInstance -Namespace 'root\subscription' -ClassName $className -ErrorAction Stop)
      if (@($instances).Count -gt 0) {
        [void]$sections.Add((($instances | Format-List * | Out-String -Width 500).TrimEnd()))
      } else {
        [void]$sections.Add('NO_RESULTS')
      }
    } catch {
      $message = 'ERROR collecting WMI persistence class [{0}]: {1}' -f $className, $_.Exception.Message
      Add-CollectorError $message
      [void]$sections.Add($message)
    }
    [void]$sections.Add('')
    [void]$sections.Add(('—' * 80))
    [void]$sections.Add('')
  }

  return ($sections -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the Tier 2 persistence deep-check text surface.

.DESCRIPTION
Collects Tier 2-only registry, WMI persistence, share, session, and firewall text
artifacts, writes each one to disk, and returns the combined text surface for report
inclusion.

.FUNCTION NAME
Get-Tier2PersistenceText

.INPUTS
Collector state hashtable and ToolMap hashtable.

.OUTPUTS
String containing the combined Tier 2 persistence and deep-check text surface.
#>
function Get-Tier2PersistenceText {
  param([hashtable]$State,[hashtable]$ToolMap)

  $sb = New-Object System.Text.StringBuilder

  $regIfeo = Invoke-Tier2RegistryQueryText -RegistryPath 'HKLM\Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options' -StepName 'TIER2_REG_IFEO' -FailureLabel 'Tier 2 IFEO registry query'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_reg_ifeo.txt' -Text $regIfeo)
  Add-Section -Builder $sb -Name 'TIER2_REG_IFEO' -Text $regIfeo

  $regWinlogon = Invoke-Tier2RegistryQueryText -RegistryPath 'HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon' -StepName 'TIER2_REG_WINLOGON' -FailureLabel 'Tier 2 Winlogon registry query'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_reg_winlogon.txt' -Text $regWinlogon)
  Add-Section -Builder $sb -Name 'TIER2_REG_WINLOGON' -Text $regWinlogon

  $regLsa = Invoke-Tier2RegistryQueryText -RegistryPath 'HKLM\SYSTEM\CurrentControlSet\Control\Lsa' -StepName 'TIER2_REG_LSA' -FailureLabel 'Tier 2 LSA registry query'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_reg_lsa.txt' -Text $regLsa)
  Add-Section -Builder $sb -Name 'TIER2_REG_LSA' -Text $regLsa

  $wmiText = Get-Tier2WmiPersistenceText
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_wmi_persistence.txt' -Text $wmiText)
  Add-Section -Builder $sb -Name 'TIER2_WMI_PERSISTENCE' -Text $wmiText

  $netShare = Get-CmdText -Command 'net share' -StepName 'TIER2_NET_SHARE'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_net_share.txt' -Text $netShare)
  Add-Section -Builder $sb -Name 'TIER2_NET_SHARE' -Text $netShare

  $netSession = Get-CmdText -Command 'net session' -StepName 'TIER2_NET_SESSION' -AllowedExitCodes @(0,2)
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_net_session.txt' -Text $netSession)
  Add-Section -Builder $sb -Name 'TIER2_NET_SESSION' -Text $netSession

  $fw = Get-CmdText -Command 'netsh advfirewall show allprofiles' -StepName 'TIER2_FIREWALL_PROFILES'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_firewall_profiles.txt' -Text $fw)
  Add-Section -Builder $sb -Name 'TIER2_FIREWALL_PROFILES' -Text $fw

  return $sb.ToString()
}

<#
.SYNOPSIS
Builds the baseline report and baseline artifact set.

.DESCRIPTION
Collects the baseline artifact families, writes them to disk, appends them into the
main baseline report, emits analyst follow-up recommendations, and returns the report
builder plus artifact path and map structures.

.FUNCTION NAME
New-BaselineReport

.INPUTS
Collector state hashtable and ToolMap hashtable.

.OUTPUTS
Hashtable containing ReportBuilder, ReportText, ArtifactPaths, and ArtifactMap.
#>
function New-BaselineReport {
  param([hashtable]$State,[hashtable]$ToolMap)

  $artifactPaths = New-Object System.Collections.ArrayList
  $artifactMap = @{}
  $sb = New-Object System.Text.StringBuilder
  $isElevated = Test-CollectorIsElevated

  if (-not $isElevated) {
    Add-CollectorNote 'Collector is running in a non-elevated context. Owner-aware netstat capture and Security log visibility may be restricted on this host.'
  }

  $metaText = @(
    "CollectorVersion=$ScriptVersion"
    "Mode=Collect"
    "Tier=$Tier"
    "Hours=$Hours"
    "Host=$env:COMPUTERNAME"
    "RunId=$($State.RunId)"
    "UserContext=$([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
    "IsElevated=$isElevated"
    "TimeLocal=$(Get-Date -Format o)"
    "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
    "RunRoot=$($State.RunRoot)"
    "ReportsDir=$($State.ReportsDir)"
    "ArtifactsDir=$($State.ArtifactsDir)"
    "EnrichSessionsDir=$($State.EnrichSessionsDir)"
  ) -join [Environment]::NewLine
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_METADATA" -Name "collection_metadata.txt" -Text $metaText
  [void]$artifactPaths.Add($p); $artifactMap['collection_metadata'] = $p
  Add-Section -Builder $sb -Name "COLLECTION_METADATA" -Text $metaText

  $executionContextText = Get-CollectorExecutionContextText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_METADATA" -Name "execution_context.txt" -Text $executionContextText
  [void]$artifactPaths.Add($p); $artifactMap['execution_context'] = $p; $State.ExecutionContextPath = $p; $State.IsElevated = $isElevated

  $script:CollectorAuditPolicyAccessStatus = 'UNKNOWN'
  $auditPolicyText = Get-SecurityAuditPolicyText
  $State.AuditPolicyAccessStatus = if ($script:CollectorAuditPolicyAccessStatus) { [string]$script:CollectorAuditPolicyAccessStatus } else { 'UNKNOWN' }
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_METADATA" -Name "security_audit_policy.txt" -Text $auditPolicyText
  [void]$artifactPaths.Add($p); $artifactMap['security_audit_policy'] = $p; $State.SecurityAuditPolicyPath = $p
  Add-Section -Builder $sb -Name "EXECUTION_CONTEXT_AND_AUDIT_POLICY" -Text (@($executionContextText, '', ('AUDIT_POLICY_ACCESS_STATUS={0}' -f $State.AuditPolicyAccessStatus), '', $auditPolicyText) -join [Environment]::NewLine)

  $limitationLines = @(
    "Offline profile hives were not loaded by design.",
    "Only loaded HKU user Run keys were collected.",
    "Raw EVTX files are not part of baseline collection. Log text is exported for baseline review.",
    "Current run files remain in place until Cleanup runs.",
    "A new Collect run purges prior DCOIR run folders and the prior package zip.",
    "The merged baseline report remains useful for local analyst review, but it is no longer the default Gemini-facing upload surface. Prefer the upload summary and representative artifacts."
  )
  if (@($Global:CollectorNotes).Count -gt 0) {
    $limitationLines += ""
    $limitationLines += "Collection notes:"
    $limitationLines += $Global:CollectorNotes
  }
  if (@($Global:CollectorErrors).Count -gt 0) {
    $limitationLines += ""
    $limitationLines += "Collection errors seen so far:"
    $limitationLines += $Global:CollectorErrors
  }
  $limitationText = ($limitationLines -join [Environment]::NewLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_NOTES_AND_LIMITATIONS" -Name "collection_notes_and_limitations.txt" -Text $limitationText
  [void]$artifactPaths.Add($p); $artifactMap['collection_notes_and_limitations'] = $p
  Add-Section -Builder $sb -Name "COLLECTION_NOTES_AND_LIMITATIONS" -Text $limitationText

  $timeHostText = Get-CmdText -Command 'date /t & time /t & hostname & ver' -StepName "HOST_DATE_TIME_HOSTNAME"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "HOST_BASELINE" -Name "time_host.txt" -Text $timeHostText
  [void]$artifactPaths.Add($p); $artifactMap['time_host'] = $p
  $systemInfoText = Get-CmdText -Command 'systeminfo' -StepName "HOST_SYSTEMINFO"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "HOST_BASELINE" -Name "systeminfo.txt" -Text $systemInfoText
  [void]$artifactPaths.Add($p); $artifactMap['systeminfo'] = $p
  Add-Section -Builder $sb -Name "HOST_BASELINE" -Text (@($timeHostText, "", $systemInfoText) -join [Environment]::NewLine)

  $whoamiText = Get-CmdText -Command 'whoami /all' -StepName "IDENTITY_WHOAMI_ALL"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "whoami_all.txt" -Text $whoamiText
  [void]$artifactPaths.Add($p); $artifactMap['whoami_all'] = $p
  $sessionsText = Get-CmdText -Command 'query user & qwinsta' -StepName "IDENTITY_QUERY_USER_QWINSTA"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "sessions.txt" -Text $sessionsText
  [void]$artifactPaths.Add($p); $artifactMap['sessions'] = $p
  $logonSessionsWmiText = Get-LogonSessionsWmiText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "logon_sessions_wmi.txt" -Text $logonSessionsWmiText
  [void]$artifactPaths.Add($p); $artifactMap['logon_sessions_wmi'] = $p
  Add-Section -Builder $sb -Name "IDENTITY_AND_SESSION_CONTEXT" -Text (@($whoamiText, "", $sessionsText, "", $logonSessionsWmiText) -join [Environment]::NewLine)

  $procInventory = Get-ProcessInventory
  $excludedPids = @([int]$PID)
  try {
    $selfProc = Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId={0}" -f $PID) -ErrorAction Stop
    if ($selfProc.ParentProcessId) { $excludedPids += [int]$selfProc.ParentProcessId }
  } catch { }
  $procInventoryText = Convert-ToTextBlock -InputObject ($procInventory | Select-Object ProcessId, ParentProcessId, Name, Owner, ExecutablePath, CreationTime, CommandLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PROCESS_EXECUTION_CONTEXT" -Name "process_inventory.txt" -Text $procInventoryText
  [void]$artifactPaths.Add($p); $artifactMap['process_inventory'] = $p
  $procParts = @($procInventoryText)
  if ($ToolMap['pslist']) {
    $pslistText = Invoke-ToolToText -ToolPath $ToolMap['pslist'] -Arguments @('-accepteula','-nobanner','-t') -StepName "SYSINTERNALS_PSLIST"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PROCESS_EXECUTION_CONTEXT" -Name "pslist.txt" -Text $pslistText
    [void]$artifactPaths.Add($p); $artifactMap['pslist'] = $p
    $procParts += ""
    $procParts += $pslistText
  }
  Add-Section -Builder $sb -Name "PROCESS_EXECUTION_CONTEXT" -Text ($procParts -join [Environment]::NewLine)

  $ipconfigText = Get-CmdText -Command 'ipconfig /all' -StepName "NETWORK_IPCONFIG"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "ipconfig_all.txt" -Text $ipconfigText
  [void]$artifactPaths.Add($p); $artifactMap['ipconfig_all'] = $p
  $netstatBundle = Get-NetstatCaptureBundle -IsElevated $isElevated
  $netstatText = $netstatBundle.OwnerAwareText
  $State.NetstatOwnerAwareStatus = $netstatBundle.OwnerAwareStatus
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "netstat_abno.txt" -Text $netstatText
  [void]$artifactPaths.Add($p); $artifactMap['netstat_abno'] = $p
  $structuredNetText = Get-BaselineNetText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "structured_net.txt" -Text $structuredNetText
  [void]$artifactPaths.Add($p); $artifactMap['structured_net'] = $p
  $dnsText = Get-CmdText -Command 'ipconfig /displaydns' -StepName "NETWORK_DNS_CACHE"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "dns_cache.txt" -Text $dnsText
  [void]$artifactPaths.Add($p); $artifactMap['dns_cache'] = $p
  $routeText = Get-CmdText -Command 'route print' -StepName "NETWORK_ROUTE_PRINT"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "route_print.txt" -Text $routeText
  [void]$artifactPaths.Add($p); $artifactMap['route_print'] = $p
  $arpText = Get-CmdText -Command 'arp -a' -StepName "NETWORK_ARP_A"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "arp_a.txt" -Text $arpText
  [void]$artifactPaths.Add($p); $artifactMap['arp_a'] = $p
  $networkParts = @($ipconfigText, "", $netstatText, "", $structuredNetText, "", $dnsText, "", $routeText, "", $arpText)
  if ($netstatBundle.PidOnlyText) {
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "netstat_ano_supplemental.txt" -Text $netstatBundle.PidOnlyText
    [void]$artifactPaths.Add($p); $artifactMap['netstat_ano_supplemental'] = $p; $State.NetstatPidOnlyPath = $p
    $networkParts += ""
    $networkParts += $netstatBundle.PidOnlyText
  }
  if ($ToolMap['tcpvcon']) {
    $tcpvconText = Invoke-ToolToText -ToolPath $ToolMap['tcpvcon'] -Arguments @('-accepteula','-nobanner') -StepName "SYSINTERNALS_TCPVCON"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "tcpvcon.txt" -Text $tcpvconText
    [void]$artifactPaths.Add($p); $artifactMap['tcpvcon'] = $p
    $networkParts += ""
    $networkParts += $tcpvconText
  }
  if ($ToolMap['pipelist']) {
    $pipelistText = Invoke-ToolToText -ToolPath $ToolMap['pipelist'] -Arguments @('-accepteula','-nobanner') -StepName "SYSINTERNALS_PIPELIST"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "pipelist.txt" -Text $pipelistText
    [void]$artifactPaths.Add($p); $artifactMap['pipelist'] = $p
    $networkParts += ""
    $networkParts += $pipelistText
  }
  Add-Section -Builder $sb -Name "NETWORK_STATE" -Text ($networkParts -join [Environment]::NewLine)

  $servicesText = Get-CmdText -Command 'sc queryex type= service state= all' -StepName "PERSISTENCE_SERVICES"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "services.txt" -Text $servicesText
  [void]$artifactPaths.Add($p); $artifactMap['services'] = $p
  $tasksText = Get-CmdText -Command 'schtasks /query /fo LIST /v' -StepName "PERSISTENCE_SCHEDULED_TASKS"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "scheduled_tasks.txt" -Text $tasksText
  [void]$artifactPaths.Add($p); $artifactMap['scheduled_tasks'] = $p
  $hklmRunText = Get-RegistryQueryText -RegistryPath 'HKLM\Software\Microsoft\Windows\CurrentVersion\Run' -StepName "PERSISTENCE_HKLM_RUN"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "run_hklm.txt" -Text $hklmRunText
  [void]$artifactPaths.Add($p); $artifactMap['run_hklm'] = $p
  $hkuRunText = Get-LoadedUserRunKeysText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "run_hku_loaded_users.txt" -Text $hkuRunText
  [void]$artifactPaths.Add($p); $artifactMap['run_hku_loaded_users'] = $p
  $persistenceParts = @($servicesText, "", $tasksText, "", $hklmRunText, "", $hkuRunText)
  if ($ToolMap['autorunsc']) {
    $autorunsText = Invoke-ToolToText -ToolPath $ToolMap['autorunsc'] -Arguments @('-accepteula','-nobanner','-a','*','-c','-h','-s','*') -StepName "SYSINTERNALS_AUTORUNSC"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "autorunsc.csv.txt" -Text $autorunsText
    [void]$artifactPaths.Add($p); $artifactMap['autorunsc'] = $p
    $persistenceParts += ""
    $persistenceParts += $autorunsText
  }
  Add-Section -Builder $sb -Name "PERSISTENCE_AND_AUTOSTARTS" -Text ($persistenceParts -join [Environment]::NewLine)

  $defenderText = Get-DefenderStatusText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Name "defender_status.txt" -Text $defenderText
  [void]$artifactPaths.Add($p); $artifactMap['defender_status'] = $p
  $firewallText = Get-CmdText -Command 'netsh advfirewall show allprofiles' -StepName "SECURITY_FIREWALL_PROFILES"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Name "firewall_profiles.txt" -Text $firewallText
  [void]$artifactPaths.Add($p); $artifactMap['firewall_profiles'] = $p
  Add-Section -Builder $sb -Name "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Text (@($defenderText, "", $firewallText) -join [Environment]::NewLine)

  $securityIds = @(4624,4625,4634,4647,4648,4672,4688,4697,4698)
  $securityText = Get-EventText -Channel "Security" -WindowHours $Hours -Ids $securityIds -Take $MaxEvents
  $securityText += Get-TestTextPaddingFromEnvironment -Name 'DCOIR_TEST_SECURITY_FILTERED_OVERSIZE_KB'
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "security_filtered.txt" -Text $securityText
  [void]$artifactPaths.Add($p); $artifactMap['security_filtered'] = $p; $State.SecurityFilteredPath = $p
  $securityHighSignalText = Get-SecurityHighSignalSummaryText -WindowHours $Hours -Take ([Math]::Min($MaxEvents, 200))
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "security_high_signal_summary.txt" -Text $securityHighSignalText
  [void]$artifactPaths.Add($p); $artifactMap['security_high_signal_summary'] = $p; $State.SecurityHighSignalSummaryPath = $p
  $psOpText = Get-EventText -Channel "Microsoft-Windows-PowerShell/Operational" -WindowHours $Hours -Take $MaxEvents
  $psOpText += Get-TestTextPaddingFromEnvironment -Name 'DCOIR_TEST_POWERSHELL_OPERATIONAL_OVERSIZE_KB'
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "powershell_operational_filtered.txt" -Text $psOpText
  [void]$artifactPaths.Add($p); $artifactMap['powershell_operational_filtered'] = $p
  $taskOpText = Get-EventText -Channel "Microsoft-Windows-TaskScheduler/Operational" -WindowHours $Hours -Take $MaxEvents
  $taskOpText += Get-TestTextPaddingFromEnvironment -Name 'DCOIR_TEST_TASKSCHEDULER_OPERATIONAL_OVERSIZE_KB'
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "taskscheduler_operational_filtered.txt" -Text $taskOpText
  [void]$artifactPaths.Add($p); $artifactMap['taskscheduler_operational_filtered'] = $p
  Add-Section -Builder $sb -Name "EVENT_TIMELINE_TEXT_HIGH_SIGNAL" -Text $securityHighSignalText
  Add-Section -Builder $sb -Name "EVENT_TIMELINE_TEXT" -Text (@($securityText, "", $psOpText, "", $taskOpText) -join [Environment]::NewLine)

  if ($Tier -eq "T2") {
    Add-Section -Builder $sb -Name "TIER2_DEEP_CHECKS" -Text (Get-Tier2PersistenceText -State $State -ToolMap $ToolMap)
  }

  $findings = Get-SuspiciousProcessFindings -Processes $procInventory -ExcludedPids $excludedPids
  $collectorCommandBase = Get-CollectorPowerShellCommandBase
  if (@($findings).Count -gt 0) {
    Add-Recommendation 'The following process review candidates were selected by baseline heuristics. Treat them as triage prompts for analyst validation, not proof of malicious activity.'
    foreach ($finding in ($findings | Select-Object -First 10)) {
      Add-Recommendation ("Process review candidate PID {0} ({1}) :: heuristic flags: {2}" -f $finding.ProcessId, $finding.Name, $finding.Reasons)
      if ($finding.ExecutablePath) {
        $safePath = $finding.ExecutablePath
        Add-Recommendation ('Suggested next action if analyst review warrants deeper validation: {0} -Mode Enrich -RunId {1} -Action SigcheckPath -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
        Add-Recommendation ('Suggested next action if analyst review warrants deeper validation: {0} -Mode Enrich -RunId {1} -Action StringsPath -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
        Add-Recommendation ('Suggested next action if analyst review warrants file retrieval: {0} -Mode Enrich -RunId {1} -Action PullSuspiciousFile -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
      }
    }
  } else {
    Add-Recommendation 'No heuristic-driven process review candidates were generated from baseline collection.'
  }

  $followUpText = ($Global:RecommendedActions -join [Environment]::NewLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "ANALYST_FOLLOW_UP_QUEUE" -Name "analyst_follow_up_queue.txt" -Text $followUpText
  [void]$artifactPaths.Add($p); $artifactMap['analyst_follow_up_queue'] = $p
  Add-Section -Builder $sb -Name "ANALYST_FOLLOW_UP_QUEUE" -Text $followUpText

  return @{
    ReportBuilder = $sb
    ReportText = $sb.ToString()
    ArtifactPaths = $artifactPaths
    ArtifactMap = $artifactMap
  }
}

<#
.SYNOPSIS
Builds the metadata report for a collect run.

.DESCRIPTION
Creates the post-collect metadata report with run-summary paths, tool availability,
notes, errors, recommendations, and analyst workflow guidance.

.FUNCTION NAME
New-MetadataReport

.INPUTS
Collector state hashtable and ToolMap hashtable.

.OUTPUTS
String containing the metadata report text.
#>
function New-MetadataReport {
  param([hashtable]$State,[hashtable]$ToolMap)

  $sb = New-Object System.Text.StringBuilder
  Add-Section -Builder $sb -Name "RUN_SUMMARY" -Text (
    @(
      "CollectorVersion=$ScriptVersion"
      "Mode=Collect"
      "Tier=$Tier"
      "Hours=$Hours"
      "Host=$env:COMPUTERNAME"
      "RunId=$($State.RunId)"
      "TimeLocal=$(Get-Date -Format o)"
      "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
      "RunRoot=$($State.RunRoot)"
      "BaselineReport=$($State.BaselineReportPath)"
      "MetadataReport=$($State.MetadataReportPath)"
      "ExecutionContext=$($State.ExecutionContextPath)"
      "SecurityAuditPolicy=$($State.SecurityAuditPolicyPath)"
      "AuditPolicyAccessStatus=$($State.AuditPolicyAccessStatus)"
      "SecurityFiltered=$($State.SecurityFilteredPath)"
      "SecurityHighSignalSummary=$($State.SecurityHighSignalSummaryPath)"
      "NetstatOwnerAwareStatus=$($State.NetstatOwnerAwareStatus)"
      "NetstatPidOnlyPath=$($State.NetstatPidOnlyPath)"
      "CollectBundle=$($State.CollectBundlePath)"
      "UploadSummary=$($State.UploadSummaryPath)"
      "AttachmentBudgetManifest=$($State.UploadBudgetManifestPath)"
      "DefaultGeminiUploadSetStatus=$($State.DefaultGeminiUploadSetStatus)"
    ) -join [Environment]::NewLine
  )

  Add-Section -Builder $sb -Name "TOOL_AVAILABILITY" -Text (Get-CommandAvailabilityTable -ToolMap $ToolMap)

  $notesText = @(
    "Cleanup removes the selected run folder and the package zip.",
    "Artifact retrieval is a separate get-file step.",
    "A new Collect run purges prior DCOIR runs before starting.",
    "Follow-on Enrich sessions do not purge the current run.",
    "For Gemini uploads in the current office environment, prefer the upload summary plus representative artifacts over the monolithic baseline report."
  )
  if (@($Global:CollectorNotes).Count -gt 0) {
    $notesText += ""
    $notesText += "Notes:"
    $notesText += $Global:CollectorNotes
  }
  Add-Section -Builder $sb -Name "NOTES" -Text ($notesText -join [Environment]::NewLine)

  $errorsText = if (@($Global:CollectorErrors).Count -gt 0) { $Global:CollectorErrors -join [Environment]::NewLine } else { "No collection errors were recorded." }
  Add-Section -Builder $sb -Name "ERRORS" -Text $errorsText

  $recsText = if (@($Global:RecommendedActions).Count -gt 0) { $Global:RecommendedActions -join [Environment]::NewLine } else { "No enrichment recommendations were generated." }
  Add-Section -Builder $sb -Name "RECOMMENDED_ENRICHMENT_ACTIONS" -Text $recsText

  $workflowText = @(
    "1. Retrieve the collect bundle with get-file.",
    "2. For Gemini uploads, prefer the upload summary, metadata report, manifest, logs, and representative final_artifacts slices.",
    "3. Review the merged baseline locally when the full monolithic report is needed.",
    "4. Run one enrichment action at a time.",
    "5. Continue the same enrichment session or finalize it for ZIP retrieval.",
    "6. Keep the current run until Cleanup is explicitly run."
  ) -join [Environment]::NewLine
  Add-Section -Builder $sb -Name "WORKFLOW" -Text $workflowText

  return $sb.ToString()
}

<#
.SYNOPSIS
Writes one report file to disk.

.DESCRIPTION
Writes the supplied text to the target report path using UTF-8 encoding.

.FUNCTION NAME
Write-ReportFile

.INPUTS
Path string for the output file and Text string to write.

.OUTPUTS
No direct output. Writes the report file as a side effect.
#>
function Write-ReportFile {
  param([string]$Path,[string]$Text)
  Set-Content -Path $Path -Value $Text -Encoding UTF8
}
# END DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1

# BEGIN DCOIR_Collector.03A_Enrich_Session_State.ps1
<#
.SYNOPSIS
DCOIR collector enrich-session state helpers.

.DESCRIPTION
Maintains enrichment session lookup, creation, reuse, and finalization state for the
DCOIR collector. These helpers keep enrichment work appended to the correct session,
write session metadata and summaries, and package finalized enrichment output into a
bundle that can be retrieved later.

.FILE NAME
DCOIR_Collector.03A_Enrich_Session_State.ps1

.INPUTS
Hashtable state objects, requested session identifiers, and tool-map/runtime context
needed to create or finalize an enrichment session.

.OUTPUTS
Hashtables representing the selected or newly created enrichment session, or the final
bundle path when a session is finalized.
#>

<#
.SYNOPSIS
Returns one enrichment session from collector state by session identifier.

.DESCRIPTION
Searches the in-memory collector state for a session whose SessionId matches the
requested identifier. Returns null when no matching session exists.

.FUNCTION NAME
Get-SessionById

.INPUTS
State hashtable containing EnrichSessions and the session identifier string to match.

.OUTPUTS
Hashtable for the matching enrichment session, or null when the session is absent.
#>
function Get-SessionById {
  param([hashtable]$State,[string]$SessionId)
  foreach ($session in @($State.EnrichSessions)) {
    if ($session.SessionId -eq $SessionId) { return $session }
  }
  return $null
}

<#
.SYNOPSIS
Creates, reuses, or resolves the active enrichment session for the current run.

.DESCRIPTION
Normalizes the collector state for enrichment-session tracking, honors an explicitly
requested session when present, reuses the current open session when appropriate, and
creates a new session directory structure when a fresh session is required. It also
writes the initial session summary header and updates the state fields that track the
open session and last resolution mode.

.FUNCTION NAME
Initialize-EnrichSession

.INPUTS
Collector state hashtable, optional requested session identifier, and an optional
ForceNew switch that suppresses reuse of the currently open session.

.OUTPUTS
Hashtable describing the resolved enrichment session, whether reused or newly created.
#>
function Initialize-EnrichSession {
  param(
    [hashtable]$State,
    [string]$RequestedSessionId,
    [switch]$ForceNew
  )

  if (-not $State.ContainsKey("EnrichSessions") -or $null -eq $State.EnrichSessions) {
    $State.EnrichSessions = @()
  } else {
    $State.EnrichSessions = @($State.EnrichSessions)
  }
  if (-not $State.ContainsKey("EnrichSessionCounter") -or $null -eq $State.EnrichSessionCounter) {
    $State.EnrichSessionCounter = 0
  }

  if (-not $State.ContainsKey('LastSessionResolutionMode')) {
    $State.LastSessionResolutionMode = $null
  }

  if (-not [string]::IsNullOrWhiteSpace($RequestedSessionId)) {
    $existing = Get-SessionById -State $State -SessionId $RequestedSessionId
    if ($existing) {
      if ($existing.Finalized) {
        throw "Requested enrichment session is finalized and cannot be appended: $RequestedSessionId"
      }
      $existing.SessionResolutionMode = 'REUSED_REQUESTED_SESSION'
      $State.LastSessionResolutionMode = 'REUSED_REQUESTED_SESSION'
      return $existing
    }
    throw "Requested enrichment session was not found: $RequestedSessionId"
  }

  if (-not $ForceNew -and -not [string]::IsNullOrWhiteSpace([string]$State.OpenEnrichSessionId)) {
    $open = Get-SessionById -State $State -SessionId ([string]$State.OpenEnrichSessionId)
    if ($open -and -not $open.Finalized) {
      $open.SessionResolutionMode = 'REUSED_OPEN_SESSION'
      $State.LastSessionResolutionMode = 'REUSED_OPEN_SESSION'
      return $open
    }
  }

  $State.EnrichSessionCounter = [int]$State.EnrichSessionCounter + 1
  $sessionNumber = "{0:D3}" -f [int]$State.EnrichSessionCounter
  $sessionStamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $sessionId = "ENRICH_{0}_{1}" -f $sessionNumber, $sessionStamp

  $sessionRoot = Join-Path $State.EnrichSessionsDir $sessionId
  $sessionArtifactsDir = Join-Path $sessionRoot "artifacts"
  $sessionStagedDir = Join-Path $sessionRoot "staged"
  $sessionLogsDir = Join-Path $sessionRoot "logs"
  Ensure-Directory -Path $sessionRoot
  Ensure-Directory -Path $sessionArtifactsDir
  Ensure-Directory -Path $sessionStagedDir
  Ensure-Directory -Path $sessionLogsDir

  $session = @{
    SessionId = $sessionId
    SessionRoot = $sessionRoot
    ArtifactsDir = $sessionArtifactsDir
    StagedDir = $sessionStagedDir
    LogsDir = $sessionLogsDir
    SummaryPath = (Join-Path $sessionRoot ("DCOIR_ENRICH_SUMMARY_{0}_{1}_{2}.txt" -f $sessionId, $env:COMPUTERNAME, $State.RunId))
    ManifestPath = (Join-Path $sessionRoot ("manifest_{0}.json" -f $sessionId))
    BundlePath = $null
    CreatedLocal = (Get-Date).ToString("o")
    Finalized = $false
    ActionCount = 0
    SessionResolutionMode = 'CREATED_NEW_SESSION'
  }

  $State.EnrichSessions = @($State.EnrichSessions) + @($session)
  $State.OpenEnrichSessionId = $sessionId
  $State.LastSessionResolutionMode = 'CREATED_NEW_SESSION'

  $header = @(
    "CollectorVersion=$ScriptVersion"
    "Mode=Enrich"
    "RunId=$($State.RunId)"
    "EnrichSessionId=$sessionId"
    "SessionResolutionMode=CREATED_NEW_SESSION"
    "Host=$env:COMPUTERNAME"
    "SessionCreatedLocal=$(Get-Date -Format o)"
    "SessionRoot=$sessionRoot"
  ) -join [Environment]::NewLine
  Set-Content -Path $session.SummaryPath -Value $header -Encoding UTF8

  return $session
}

<#
.SYNOPSIS
Finalizes an enrichment session and produces its retrievable bundle.

.DESCRIPTION
Builds the per-session manifest, gathers session summary, artifact, staged, and log
files, packages them into the enrich bundle, updates session finalization flags, and
clears the open-session pointer when the finalized session was the active one.

.FUNCTION NAME
Finalize-EnrichSession

.INPUTS
Collector state hashtable, enrichment-session hashtable, and the resolved collector
ToolMap used to write the manifest.

.OUTPUTS
String path to the finalized enrichment bundle ZIP file.
#>
function Finalize-EnrichSession {
  param(
    [hashtable]$State,
    [hashtable]$Session,
    [hashtable]$ToolMap
  )

  $manifest = New-Manifest -ManifestPath $Session.ManifestPath -State $State -ModeName "Enrich" -TierName $Tier -Files (
    @($Session.SummaryPath) +
    @(Get-ChildItem -LiteralPath $Session.ArtifactsDir -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }) +
    @(Get-ChildItem -LiteralPath $Session.StagedDir -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }) +
    @(Get-ChildItem -LiteralPath $Session.LogsDir -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
  ) -ToolMap $ToolMap -Extra @{
    enrich_session_id = $Session.SessionId
    action_count = $Session.ActionCount
    session_resolution_mode = $Session.SessionResolutionMode
    append_model = 'enrich-start creates a new session; enrich-add reuses the current open session unless explicitly overridden; enrich-finalize finalizes the current open session.'
  }

  $bundleInputs = @(
    $Session.SummaryPath,
    $Session.ArtifactsDir,
    $Session.StagedDir,
    $Session.LogsDir,
    $manifest
  )

  $bundlePath = New-BundleZip -BundlesDir $State.BundlesDir -BundleName ("DCOIR_ENRICH_BUNDLE_{0}_{1}_{2}.zip" -f $Session.SessionId, $env:COMPUTERNAME, $State.RunId) -Paths $bundleInputs
  $Session.BundlePath = $bundlePath
  $Session.Finalized = $true
  if ($State.OpenEnrichSessionId -eq $Session.SessionId) {
    $State.OpenEnrichSessionId = $null
  }
  return $bundlePath
}
# END DCOIR_Collector.03A_Enrich_Session_State.ps1

# BEGIN DCOIR_Collector.03B_Enrich_Actions_Review.ps1
<#
.SYNOPSIS
DCOIR collector enrich-mode review action handlers.

.DESCRIPTION
Implements the analyst-review style enrichment actions that operate on already-collected
targets, such as signature review, loaded-module inspection, access review, strings,
alternate data stream inspection, refreshed TCP connection review, and event-log text
export. The file packages the action output into session artifacts and appends the
results to the active enrich-session summary.

.FILE NAME
DCOIR_Collector.03B_Enrich_Actions_Review.ps1

.INPUTS
Collector state, active enrichment session, resolved tool map, and action-specific
parameters such as Path, ServiceName, RegistryPath, LogName, TargetPid, Hours, EventId,
and MaxEvents.

.OUTPUTS
Hashtable containing the enrich summary path, action artifact path, and any staged path
produced by the selected action.
#>

<#
.SYNOPSIS
Runs one enrich-mode review action and writes the result into the active session.

.DESCRIPTION
Selects the requested enrich action, validates required parameters and tool presence,
collects the action output, wraps it in analyst-facing interpretation text, writes the
per-action artifact, appends the result to the session summary, and increments the
session action count. Retrieval-oriented actions are delegated to the retrieval helper
file when the action does not match one of the local review cases.

.FUNCTION NAME
Invoke-EnrichmentAction

.INPUTS
Collector state hashtable, active enrichment-session hashtable, and ToolMap hashtable.
The function also relies on current enrich action parameters already bound in the wider
collector runtime, including Action, Path, ServiceName, RegistryPath, LogName,
TargetPid, Hours, EventId, and MaxEvents.

.OUTPUTS
Hashtable containing ReportPath, ActionArtifactPath, and StagedPath values for the
executed enrich action.
#>
function Invoke-EnrichmentAction {
  param(
    [hashtable]$State,
    [hashtable]$Session,
    [hashtable]$ToolMap
  )

  $sessionArtifactsDir = $Session.ArtifactsDir
  $sessionStagedDir = $Session.StagedDir
  $sessionSummaryPath = $Session.SummaryPath
  $sessionLogsDir = $Session.LogsDir

  $stagedPath = $null
  $reason = $null
  $targetDetails = $null
  $outputText = $null
  $interpretation = $null
  $nextStep = $null

  switch ($Action) {
    "SigcheckPath" {
      if (-not $Path) { throw "SigcheckPath requires -Path" }
      if (-not $ToolMap.sigcheck) { throw "sigcheck tool not found in staged tools directory." }
      $reason = "Signature and hash review for a suspicious path."
      $targetDetails = "Path=$Path"
      $outputText = Invoke-ToolToText -ToolPath $ToolMap.sigcheck -Arguments @("-accepteula","-nobanner","-h",$Path) -StepName "ENRICH_SIGCHECK_PATH"
      $interpretation = "Review signer, hashes, version data, and whether the signer matches the expected vendor."
      $nextStep = "If signer or path looks suspicious, stage the file with PullSuspiciousFile."
    }
    "ListDllsPid" {
      if (-not $TargetPid) { throw "ListDllsPid requires -TargetPid" }
      if (-not $ToolMap.listdlls) { throw "listdlls tool not found in staged tools directory." }
      $reason = "Loaded module review for a suspicious process."
      $targetDetails = "Pid=$TargetPid"
      $outputText = Invoke-ToolToText -ToolPath $ToolMap.listdlls -Arguments @("-accepteula","-nobanner","-v",$TargetPid.ToString()) -StepName "ENRICH_LISTDLLS_PID"
      $interpretation = "Review unexpected DLL paths, unsigned DLLs, and DLLs loaded from user-writable paths."
      $nextStep = "If a suspicious DLL path is present, stage it with PullSuspiciousFile."
    }
    "AccessChkFile" {
      if (-not $Path) { throw "AccessChkFile requires -Path" }
      if (-not $ToolMap.accesschk) { throw "accesschk tool not found in staged tools directory." }
      $reason = "Effective access review for a suspicious file or directory."
      $targetDetails = "Path=$Path"
      $outputText = Invoke-ToolToText -ToolPath $ToolMap.accesschk -Arguments @("-accepteula","-nobanner","-v",$Path) -StepName "ENRICH_ACCESSCHK_FILE"
      $interpretation = "Review whether broad write access or weak ACLs explain persistence or tampering risk."
      $nextStep = "If write access is too broad, document the ACL issue for remediation."
    }
    "AccessChkService" {
      if (-not $ServiceName) { throw "AccessChkService requires -ServiceName" }
      if (-not $ToolMap.accesschk) { throw "accesschk tool not found in staged tools directory." }
      $reason = "Effective access review for a suspicious service."
      $targetDetails = "ServiceName=$ServiceName"
      $outputText = Invoke-ToolToText -ToolPath $ToolMap.accesschk -Arguments @("-accepteula","-nobanner","-c",$ServiceName) -StepName "ENRICH_ACCESSCHK_SERVICE"
      $interpretation = "Review whether low-privilege principals can change or control the service."
      $nextStep = "If service rights are weak, stage the service binary or review the service path."
    }
    "AccessChkReg" {
      if (-not $RegistryPath) { throw "AccessChkReg requires -RegistryPath" }
      if (-not $ToolMap.accesschk) { throw "accesschk tool not found in staged tools directory." }
      $reason = "Effective access review for a suspicious registry location."
      $targetDetails = "RegistryPath=$RegistryPath"
      $outputText = Invoke-ToolToText -ToolPath $ToolMap.accesschk -Arguments @("-accepteula","-nobanner","-k","-u","-v",$RegistryPath) -StepName "ENRICH_ACCESSCHK_REG"
      $interpretation = "Review whether the registry key has weak write permissions."
      $nextStep = "If write access is weak, capture the exact principal and registry path for remediation."
    }
    "StringsPath" {
      if (-not $Path) { throw "StringsPath requires -Path" }
      if (-not $ToolMap.strings) { throw "strings tool not found in staged tools directory." }
      $reason = "Readable string extraction for a suspicious file."
      $targetDetails = "Path=$Path"
      $outputText = Invoke-ToolToText -ToolPath $ToolMap.strings -Arguments @("-accepteula","-nobanner","-n","4",$Path) -StepName "ENRICH_STRINGS_PATH"
      $interpretation = "Review URLs, domains, IPs, command lines, registry keys, mutex names, and suspicious paths."
      $nextStep = "If strings show a second-stage file path or URL, follow that thread next."
    }
    "StreamsPath" {
      if (-not $Path) { throw "StreamsPath requires -Path" }
      if (-not $ToolMap.streams) { throw "streams tool not found in staged tools directory." }
      $reason = "Alternate data stream review for a suspicious path."
      $targetDetails = "Path=$Path"
      $outputText = Invoke-ToolToText -ToolPath $ToolMap.streams -Arguments @("-accepteula",$Path) -StepName "ENRICH_STREAMS_PATH"
      $interpretation = "Review named streams that could hide payloads or mark file-of-origin data."
      $nextStep = "If a suspicious stream is present, stage the parent file for offline review."
    }
    "TcpvconRefresh" {
      if (-not $ToolMap.tcpvcon) { throw "tcpvcon tool not found in staged tools directory." }
      $reason = "Fresh command-line TCPView snapshot for network review."
      $targetDetails = "Action=TcpvconRefresh"
      $outputText = Invoke-ToolToText -ToolPath $ToolMap.tcpvcon -Arguments @("-accepteula","-nobanner") -StepName "ENRICH_TCPVCON_REFRESH"
      $interpretation = "Review owning processes and endpoint pairs against netstat output."
      $nextStep = "If a suspicious owning process is present, inspect that PID next."
    }
    "LogText" {
      if (-not $LogName) { throw "LogText requires -LogName" }
      $reason = "Text export for a Windows event channel."
      $targetDetails = Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId -Take $MaxEvents
      $outputText = Get-EventText -Channel $LogName -WindowHours $Hours -Ids $EventId -Take $MaxEvents
      $interpretation = "Review exact timestamps, Event IDs, process names, accounts, and error details."
      $nextStep = "If text volume is too high or message fidelity is not enough, use LogRaw."
    }
    default {
      return Invoke-EnrichmentAction-Retrieval -State $State -Session $Session -ToolMap $ToolMap
    }
  }

  $targetLabel = $Action
  if ($Path) { $targetLabel = $Path }
  elseif ($ServiceName) { $targetLabel = $ServiceName }
  elseif ($RegistryPath) { $targetLabel = $RegistryPath }
  elseif ($LogName) { $targetLabel = $LogName }
  elseif ($TargetPid) { $targetLabel = "PID_$TargetPid" }

  $actionBuilder = New-Object System.Text.StringBuilder
  Add-Section -Builder $actionBuilder -Name "ENRICHMENT_METADATA" -Text (
    @(
      "CollectorVersion=$ScriptVersion"
      "Mode=Enrich"
      "Action=$Action"
      "Host=$env:COMPUTERNAME"
      "RunId=$($State.RunId)"
      "EnrichSessionId=$($Session.SessionId)"
      "TimeLocal=$(Get-Date -Format o)"
      "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
      "SessionRoot=$($Session.SessionRoot)"
    ) -join [Environment]::NewLine
  )
  Add-Section -Builder $actionBuilder -Name "TRIGGER_REASON" -Text $reason
  Add-Section -Builder $actionBuilder -Name "TARGET_DETAILS" -Text $targetDetails
  Add-Section -Builder $actionBuilder -Name "ACTION_OUTPUT" -Text $outputText
  Add-Section -Builder $actionBuilder -Name "ANALYST_INTERPRETATION_GUIDE" -Text $interpretation
  Add-Section -Builder $actionBuilder -Name "NEXT_BEST_STEP" -Text $nextStep
  if (@($Global:CollectorErrors).Count -gt 0) {
    Add-Section -Builder $actionBuilder -Name "ERRORS" -Text ($Global:CollectorErrors -join [Environment]::NewLine)
  }

  $artifactPath = Write-SessionArtifactText -SessionArtifactsDir $sessionArtifactsDir -ActionName $Action -TargetLabel $targetLabel -Text $actionBuilder.ToString()
  Add-Content -Path $sessionSummaryPath -Value $actionBuilder.ToString() -Encoding UTF8

  $Session.ActionCount = [int]$Session.ActionCount + 1

  return @{
    ReportPath = $sessionSummaryPath
    ActionArtifactPath = $artifactPath
    StagedPath = $stagedPath
  }
}
# END DCOIR_Collector.03B_Enrich_Actions_Review.ps1

# BEGIN DCOIR_Collector.03C_Enrich_Actions_Retrieval.ps1
<#
.SYNOPSIS
DCOIR collector enrich-mode retrieval action handlers.

.DESCRIPTION
Implements the retrieval-oriented enrichment actions that stage files or raw event-log
exports for analyst pickup after baseline collection. These helpers stage the selected
targets, write analyst guidance into the active enrich-session summary, and return the
paths needed for follow-on retrieval.

.FILE NAME
DCOIR_Collector.03C_Enrich_Actions_Retrieval.ps1

.INPUTS
Collector state, active enrichment session, resolved tool map, and action-specific
parameters such as Path, ServiceName, LogName, Hours, EventId, and TargetPid.

.OUTPUTS
Hashtable containing the enrich summary path, action artifact path, and any staged path
produced by the selected retrieval action.
#>

<#
.SYNOPSIS
Runs one retrieval-style enrichment action and stages the requested artifact.

.DESCRIPTION
Selects the requested retrieval action, validates required parameters, stages the target
artifact or EVTX export, builds analyst-facing interpretation guidance, writes the
session artifact, appends the result to the session summary, and increments the session
action count.

.FUNCTION NAME
Invoke-EnrichmentAction-Retrieval

.INPUTS
Collector state hashtable, active enrichment-session hashtable, and ToolMap hashtable.
The function also relies on current enrich action parameters already bound in the wider
collector runtime, including Action, Path, ServiceName, LogName, Hours, and EventId.

.OUTPUTS
Hashtable containing ReportPath, ActionArtifactPath, and StagedPath values for the
executed retrieval action.
#>
function Invoke-EnrichmentAction-Retrieval {
  param(
    [hashtable]$State,
    [hashtable]$Session,
    [hashtable]$ToolMap
  )

  $sessionArtifactsDir = $Session.ArtifactsDir
  $sessionStagedDir = $Session.StagedDir
  $sessionSummaryPath = $Session.SummaryPath
  $sessionLogsDir = $Session.LogsDir

  $stagedPath = $null
  $reason = $null
  $targetDetails = $null
  $outputText = $null
  $interpretation = $null
  $nextStep = $null

  switch ($Action) {
    "LogRaw" {
      if (-not $LogName) { throw "LogRaw requires -LogName" }
      $reason = "Raw EVTX export for analyst workstation review."
      $targetDetails = Get-CollectorEventWindowTargetDetails -LogName $LogName -Hours $Hours -Ids $EventId -Take $MaxEvents
      $safeLogName = ($LogName -replace '[\\/:*?"<>|]','_')
      $stagedPath = Join-Path $sessionStagedDir (New-StageName -Prefix ("STAGED_LogRaw_" + $safeLogName) -Extension ".evtx")
      Export-FilteredEvtx -LogChannel $LogName -WindowHours $Hours -Ids $EventId -OutPath $stagedPath -ScratchDir $sessionLogsDir
      $outputText = "Raw EVTX exported and staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Open the EVTX in Event Viewer on the analyst workstation with Action > Open Saved Log."
      $nextStep = "Retrieve the EVTX with get-file and review it in Event Viewer."
    }
    "PullSuspiciousFile" {
      if (-not $Path) { throw "PullSuspiciousFile requires -Path" }
      $reason = "Stage a suspicious file for analyst retrieval."
      $targetDetails = "Path=$Path"
      $stagedPath = Stage-PathCopy -SourcePath $Path -StagedDir $sessionStagedDir
      $outputText = "Suspicious file staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Retrieve the file with get-file, then review locally with sigcheck and strings or upload to a sandbox if policy allows."
      $nextStep = "After retrieval, run sigcheck and strings on the analyst workstation."
    }
    "PullScriptOrConfig" {
      if (-not $Path) { throw "PullScriptOrConfig requires -Path" }
      $reason = "Stage a script or configuration file for analyst review."
      $targetDetails = "Path=$Path"
      $stagedPath = Stage-PathCopy -SourcePath $Path -StagedDir $sessionStagedDir
      $outputText = "Script or config staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Retrieve the file, open it in a text editor, and upload plain text to the AFRICOM SOC IR AI."
      $nextStep = "If the file references other paths or URLs, follow the next most suspicious reference."
    }
    "PullTaskXml" {
      if (-not $Path) { throw "PullTaskXml requires -Path with the task name, for example \\Microsoft\\Windows\\TaskName" }
      $reason = "Export scheduled task XML for analyst review."
      $targetDetails = "TaskName=$Path"
      $taskXml = Get-TaskXml -TaskName $Path
      $stagedPath = Join-Path $sessionStagedDir (New-StageName -Prefix "STAGED_TASK_XML" -Extension ".xml")
      Set-Content -Path $stagedPath -Value $taskXml -Encoding UTF8
      $outputText = "Task XML exported and staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Review author, principal, triggers, actions, working directory, and command arguments."
      $nextStep = "If the action points to a file path, stage that file next."
    }
    "PullServiceBinary" {
      if (-not $ServiceName) { throw "PullServiceBinary requires -ServiceName" }
      $reason = "Stage the binary referenced by a suspicious service."
      $targetDetails = "ServiceName=$ServiceName"
      $svcPath = Get-ServiceBinaryPath -Name $ServiceName
      if (-not $svcPath) { throw "Unable to resolve service binary path for service [$ServiceName]." }
      $stagedPath = Stage-PathCopy -SourcePath $svcPath -StagedDir $sessionStagedDir
      $outputText = "Service binary staged for retrieval.`r`nSERVICE_BINARY_PATH=$svcPath`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Retrieve the binary, then review locally with sigcheck and strings or upload to a sandbox if policy allows."
      $nextStep = "If the binary is unsigned or suspicious, correlate with service creation or modification events."
    }
    "PullWmiReferencedFile" {
      if (-not $Path) { throw "PullWmiReferencedFile requires -Path" }
      $reason = "Stage a file referenced by suspicious WMI persistence."
      $targetDetails = "Path=$Path"
      $stagedPath = Stage-PathCopy -SourcePath $Path -StagedDir $sessionStagedDir
      $outputText = "WMI-referenced file staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Review the referenced script or binary as a persistence payload."
      $nextStep = "Correlate the file with WMI filter and consumer details in Tier 2 output."
    }
    default {
      throw "Unsupported enrichment action: $Action"
    }
  }

  $targetLabel = $Action
  if ($Path) { $targetLabel = $Path }
  elseif ($ServiceName) { $targetLabel = $ServiceName }
  elseif ($RegistryPath) { $targetLabel = $RegistryPath }
  elseif ($LogName) { $targetLabel = $LogName }
  elseif ($TargetPid) { $targetLabel = "PID_$TargetPid" }

  $actionBuilder = New-Object System.Text.StringBuilder
  Add-Section -Builder $actionBuilder -Name "ENRICHMENT_METADATA" -Text (
    @(
      "CollectorVersion=$ScriptVersion"
      "Mode=Enrich"
      "Action=$Action"
      "Host=$env:COMPUTERNAME"
      "RunId=$($State.RunId)"
      "EnrichSessionId=$($Session.SessionId)"
      "TimeLocal=$(Get-Date -Format o)"
      "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
      "SessionRoot=$($Session.SessionRoot)"
    ) -join [Environment]::NewLine
  )
  Add-Section -Builder $actionBuilder -Name "TRIGGER_REASON" -Text $reason
  Add-Section -Builder $actionBuilder -Name "TARGET_DETAILS" -Text $targetDetails
  Add-Section -Builder $actionBuilder -Name "ACTION_OUTPUT" -Text $outputText
  Add-Section -Builder $actionBuilder -Name "ANALYST_INTERPRETATION_GUIDE" -Text $interpretation
  Add-Section -Builder $actionBuilder -Name "NEXT_BEST_STEP" -Text $nextStep
  if (@($Global:CollectorErrors).Count -gt 0) {
    Add-Section -Builder $actionBuilder -Name "ERRORS" -Text ($Global:CollectorErrors -join [Environment]::NewLine)
  }

  $artifactPath = Write-SessionArtifactText -SessionArtifactsDir $sessionArtifactsDir -ActionName $Action -TargetLabel $targetLabel -Text $actionBuilder.ToString()
  Add-Content -Path $sessionSummaryPath -Value $actionBuilder.ToString() -Encoding UTF8

  $Session.ActionCount = [int]$Session.ActionCount + 1

  return @{
    ReportPath = $sessionSummaryPath
    ActionArtifactPath = $artifactPath
    StagedPath = $stagedPath
  }
}
# END DCOIR_Collector.03C_Enrich_Actions_Retrieval.ps1

# BEGIN DCOIR_Collector.04_Quick_Interface_And_Output.ps1
<#
.SYNOPSIS
DCOIR collector quick-interface, help-text, and cleanup helpers.

.DESCRIPTION
Builds the operator-facing quick-command examples and help text, translates supported
-Quick shortcuts into full collector parameter sets, prints next-step guidance after
major phases, and removes run/package artifacts during cleanup.

.FILE NAME
DCOIR_Collector.04_Quick_Interface_And_Output.ps1

.INPUTS
Collector runtime globals such as Quick, Target, Target2, Hours, and the current state
object passed to cleanup.

.OUTPUTS
Strings for help/usage and next-step guidance, updated collector runtime parameters for
quick shortcuts, and cleanup side effects on package/run paths.
#>

<#
.SYNOPSIS
Builds the short quick-command usage text.

.DESCRIPTION
Returns the operator-facing quick-command examples used by the collector help surface.

.FUNCTION NAME
Get-QuickUsageText

.INPUTS
No direct parameters.

.OUTPUTS
String containing newline-joined quick-command examples.
#>
function Get-QuickUsageText {
  $cmd = Get-CollectorPowerShellCommandBase
  return @(
    "Quick command examples:",
    "  $cmd -Quick collect-t1",
    "  $cmd -Quick collect-t2",
    '  $cmd -Quick collect-targeted-popup -Target "User reported popup around 2026-04-08T09:00Z"',
    '  $cmd -Quick collect-targeted-script -Target "Suspicious script execution follow-up" -Target2 "powershell.exe"',
    "  $cmd -Quick enrich-start-tcp",
    "  $cmd -Quick enrich-add-tcp",
    "  $cmd -Quick enrich-start-logtext -Target Security",
    "  $cmd -Quick enrich-add-logtext -Target Security",
    "  $cmd -Quick enrich-start-lograw -Target Security",
    "  $cmd -Quick enrich-add-lograw -Target Security",
    "  $cmd -Quick enrich-start-sigcheck -Target C:\Windows\System32\notepad.exe",
    "  $cmd -Quick enrich-add-sigcheck -Target C:\Windows\System32\notepad.exe",
    "  $cmd -Quick enrich-start-listdlls -Target 1234",
    "  $cmd -Quick enrich-add-listdlls -Target 1234",
    "  $cmd -Quick enrich-finalize",
    "  $cmd -Quick cleanup",
    "  $cmd -Quick help-collect",
    "  $cmd -Quick help-enrich",
    "  $cmd -Quick help-cleanup",
    "  $cmd -Quick help-targeted",
    "  $cmd -Quick help-version"
  ) -join [Environment]::NewLine
}

<#
.SYNOPSIS
Builds the collector build-identity string.

.DESCRIPTION
Returns the transport/runtime identity string used by version output and validation.

.FUNCTION NAME
Get-CollectorBuildIdentity

.INPUTS
Optional version string.

.OUTPUTS
String build identity.
#>
function Get-CollectorBuildIdentity {
  param([string]$Version = $ScriptVersion)
  return ("DCOIR_Collector.ps1/{0}" -f $Version)
}

<#
.SYNOPSIS
Builds the collector version text block.

.DESCRIPTION
Returns the collector version, build identity, runtime filename, package name, and
script path in key-value form.

.FUNCTION NAME
Get-CollectorVersionText

.INPUTS
No direct parameters.

.OUTPUTS
String containing newline-joined version/build metadata.
#>
function Get-CollectorVersionText {
  $scriptPath = Get-CollectorAbsolutePath
  $resolvedPackageName = if ([string]::IsNullOrWhiteSpace($PackageName)) { "DCOIR_Collector.zip" } else { $PackageName }
  return @(
    ("COLLECTOR_VERSION={0}" -f $ScriptVersion),
    ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity)),
    "COLLECTOR_RUNTIME_FILENAME=DCOIR_Collector.ps1",
    ("EXPECTED_PACKAGE_NAME={0}" -f $resolvedPackageName),
    ("COLLECTOR_SCRIPT_PATH={0}" -f $scriptPath)
  ) -join [Environment]::NewLine
}

<#
.SYNOPSIS
Builds the response-action-safe collector command base.

.DESCRIPTION
Returns the endpoint response-action-safe collector command using the runtime filename.

.FUNCTION NAME
Get-CollectorResponseActionCommandBase

.INPUTS
No direct parameters.

.OUTPUTS
String containing the response-action-safe command base.
#>
function Get-CollectorResponseActionCommandBase {
  return "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """".\DCOIR_Collector.ps1"""""
}

<#
.SYNOPSIS
Builds the delete-script command text.

.DESCRIPTION
Returns the response-action-safe literal-path script-removal command for the uploaded
collector file.

.FUNCTION NAME
Get-CollectorDeleteScriptCommandText

.INPUTS
No direct parameters.

.OUTPUTS
String delete-script command.
#>
function Get-CollectorDeleteScriptCommandText {
  $collectorPath = Get-CollectorAbsolutePath
  return ('execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command Remove-Item -LiteralPath ''{0}'' -Force" --comment "Remove uploaded DCOIR_Collector script"' -f $collectorPath)
}

<#
.SYNOPSIS
Builds contextual collector help for a specific workflow area.

.DESCRIPTION
Returns a narrower help block for collect, enrich, cleanup, targeted, or version guidance
when the operator asks for area-specific help.

.FUNCTION NAME
Get-CollectorContextualHelpText

.INPUTS
Optional topic string.

.OUTPUTS
String containing newline-joined contextual help text.
#>
function Get-CollectorContextualHelpText {
  param([string]$Topic)

  $cmd = Get-CollectorPowerShellCommandBase
  $responseCmd = Get-CollectorResponseActionCommandBase
  $topicKey = if ([string]::IsNullOrWhiteSpace($Topic)) { 'general' } else { $Topic.ToLowerInvariant() }
  $lines = @()

  switch ($topicKey) {
    'collect' {
      $lines += 'DCOIR Collector Contextual Help - Collect'
      $lines += ''
      $lines += 'Use this when you need a baseline collection bundle.'
      $lines += 'Recommended first commands:'
      $lines += "  $cmd -Quick collect-t1"
      $lines += "  $cmd -Quick collect-t2"
      $lines += ''
      $lines += 'Response-action-safe examples:'
      $lines += ('  execute --command "{0} -Quick collect-t1" --comment "Run DCOIR collect T1"' -f $responseCmd)
      $lines += ('  execute --command "{0} -Quick collect-t2" --comment "Run DCOIR collect T2"' -f $responseCmd)
      $lines += ''
      $lines += 'Use T1 when you want the smaller baseline-first path.'
      $lines += 'Use T2 when you need the deeper persistence and investigative path.'
      $lines += 'Run -Version first if you are validating a specific PS1/ZIP pair.'
    }
    'enrich' {
      $lines += 'DCOIR Collector Contextual Help - Enrich'
      $lines += ''
      $lines += 'Use this when you already have a run id and want targeted follow-up collection.'
      $lines += 'Session pattern:'
      $lines += "  $cmd -Quick enrich-start-tcp"
      $lines += "  $cmd -Quick enrich-add-lograw -Target Security"
      $lines += "  $cmd -Quick enrich-finalize"
      $lines += ''
      $lines += 'Response-action-safe examples:'
      $lines += ('  execute --command "{0} -Quick enrich-start-tcp" --comment "Run DCOIR TCP enrichment"' -f $responseCmd)
      $lines += ('  execute --command "{0} -Quick enrich-add-lograw -Target Security" --comment "Add raw Security log enrichment"' -f $responseCmd)
      $lines += ('  execute --command "{0} -Quick enrich-finalize" --comment "Finalize current DCOIR enrichment session"' -f $responseCmd)
      $lines += ''
      $lines += 'Start a session once, add related actions to the same session, then finalize before cleanup.'
    }
    'cleanup' {
      $lines += 'DCOIR Collector Contextual Help - Cleanup'
      $lines += ''
      $lines += 'Cleanup removes the run root and consumed package state.'
      $lines += 'If a collect run failed before state.json was saved, cleanup removes only the latest matching DCOIR_* orphan under the selected OutRoot and reports MISSING_STATE_ORPHAN_CLEANED.'
      $lines += 'Cleanup reports NO_TARGET_FOUND when no state-backed run or bounded orphan cleanup target exists.'
      $lines += 'Cleanup does not remove the uploaded collector script unless you run DELETE_SCRIPT_COMMAND explicitly.'
      $lines += ''
      $lines += 'Response-action-safe example:'
      $lines += ('  execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $responseCmd)
      $lines += ''
      $lines += 'If you plan another collect-style run in the response-action lane, restage the runtime zip first.'
    }
    'targeted' {
      $lines += 'DCOIR Collector Contextual Help - Targeted'
      $lines += ''
      $lines += 'Use targeted mode when the operator has a narrower event window, user report, process, path, or indicator.'
      $lines += 'Examples:'
      $lines += "  $cmd -Quick collect-targeted-popup -Target ""User reported popup around 2026-04-08T09:00Z"""
      $lines += "  $cmd -Quick collect-targeted-script -Target ""Suspicious script execution follow-up"" -Target2 ""powershell.exe"""
      $lines += ''
      $lines += 'Pair targeted mode with WindowStart/WindowEnd and the most specific focus fields you have.'
      $lines += 'Targeted mode narrows guidance and prioritization even when full exact-time filtering is not universal yet.'
    }
    'version' {
      $lines += 'DCOIR Collector Contextual Help - Version'
      $lines += ''
      $lines += 'Use version preflight before collect, enrich, cleanup, or package movement when you need to prove the runtime identity.'
      $lines += 'Examples:'
      $lines += "  $cmd -Version"
      $lines += ('  execute --command "{0} -Version" --comment "Get DCOIR collector version"' -f $responseCmd)
      $lines += ''
      $lines += 'Compare COLLECTOR_VERSION, COLLECTOR_BUILD_IDENTITY, and EXPECTED_PACKAGE_NAME before live validation.'
    }
    default {
      return $null
    }
  }

  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the full collector help text.

.DESCRIPTION
Returns the operator-facing help text including top-level usage, quick shortcuts,
version/build preflight guidance, targeted examples, and lane guidance.

.FUNCTION NAME
Get-CollectorHelpText

.INPUTS
Optional topic string.

.OUTPUTS
String containing newline-joined help text.
#>
function Get-CollectorHelpText {
  param([string]$Topic)

  $contextual = Get-CollectorContextualHelpText -Topic $Topic
  if (-not [string]::IsNullOrWhiteSpace($contextual)) {
    return $contextual
  }

  $cmd = Get-CollectorPowerShellCommandBase
  $responseCmd = Get-CollectorResponseActionCommandBase
  $lines = @()
  $lines += "DCOIR Collector Help"
  $lines += ""
  $lines += "Top-level usage:"
  $lines += "  $cmd -Help"
  $lines += "  $cmd -Version"
  $lines += "  $cmd -Mode Collect -Tier T1"
  $lines += "  $cmd -Mode Collect -Tier T2"
  $lines += "  $cmd -Mode Enrich -Action TcpvconRefresh -NewEnrichSession"
  $lines += "  $cmd -Mode Cleanup"
  $lines += ""
  $lines += "Quick usage:"
  $lines += (Get-QuickUsageText)
  $lines += ""
  $lines += "Contextual help shortcuts:"
  $lines += "  $cmd -Quick help-collect"
  $lines += "  $cmd -Quick help-enrich"
  $lines += "  $cmd -Quick help-cleanup"
  $lines += "  $cmd -Quick help-targeted"
  $lines += "  $cmd -Quick help-version"
  $lines += ""
  $lines += "Accepted top-level modes: Collect, Enrich, Cleanup"
  $lines += "Accepted tiers: T1, T2"
  $lines += "Accepted target profiles: Generic, PopupWindow, ScriptExecution, PersistenceFollowUp, NetworkOnly, ProcessAndPowerShell"
  $lines += ""
  $lines += "Version/build preflight:"
  $lines += "  - Run -Version before collect, enrich, cleanup, package movement, or other stateful test steps."
  $lines += "  - Compare COLLECTOR_VERSION and COLLECTOR_BUILD_IDENTITY to the PS1/ZIP you intended to validate before continuing."
  $lines += ('  - Response-action-safe example: execute --command "{0} -Version" --comment "Get DCOIR collector version"' -f $responseCmd)
  $lines += ""
  $lines += "Targeted usage examples:"
  $lines += '  $cmd -Targeted -TargetProfile PopupWindow -WindowStart "2026-04-08T09:00:00Z" -WindowEnd "2026-04-08T10:00:00Z" -UserReport "User reported popup"'
  $lines += '  $cmd -Targeted -TargetProfile ScriptExecution -WindowStart "2026-04-08T09:00:00Z" -WindowEnd "2026-04-08T10:00:00Z" -UserReport "Suspicious script execution" -FocusProcess "powershell.exe"'
  $lines += '  $cmd -Targeted -TargetProfile NetworkOnly -Hours 6 -FocusIndicator "198.51.100.25" -FocusIndicatorType "ip"'
  $lines += ""
  $lines += "Targeted guidance:"
  $lines += "  - Targeted mode currently narrows guidance, scope intent, artifact prioritization, and next actions."
  $lines += "  - It does not yet rewrite every baseline helper into exact start/end filtering across all artifact families."
  $lines += "  - Use -WindowStart and -WindowEnd to annotate explicit time windows for analyst guidance and follow-up."
  $lines += "  - Use -IncludeArtifactCategory, -FocusProcess, -FocusPath, -FocusIndicator, and -UserReport to make the request narrower and more explainable."
  $lines += ""
  $lines += "Accepted enrich actions:"
  $lines += "  SigcheckPath, ListDllsPid, AccessChkFile, AccessChkService, AccessChkReg, StringsPath, StreamsPath, TcpvconRefresh, LogText, LogRaw, PullSuspiciousFile, PullScriptOrConfig, PullTaskXml, PullServiceBinary, PullWmiReferencedFile"
  $lines += ""
  $lines += "Lane guidance:"
  $lines += "  - Endpoint response-console usage should wrap the PowerShell command in an Elastic response action."
  $lines += "  - Use the response-action-safe runtime pattern with doubled double quotes around .\DCOIR_Collector.ps1 inside the execute --command string."
  $lines += "  - Use the collector-emitted DELETE_SCRIPT_COMMAND literal-path form for script removal in the response-action lane."
  $lines += "  - Local workstation and regression usage should run the PowerShell command directly without the response-action wrapper."
  $lines += "  - Prefer PowerShell 5.1 syntax and the runtime filename DCOIR_Collector.ps1."
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Translates supported quick shortcuts into full collector parameters.

.DESCRIPTION
Maps -Quick values into mode, tier, action, target, and finalize/session settings.

.FUNCTION NAME
Apply-QuickShortcut

.INPUTS
No direct parameters. Uses collector runtime globals.

.OUTPUTS
No direct output. Updates script-scoped collector parameters.
#>
function Apply-QuickShortcut {
  param()

  if ([string]::IsNullOrWhiteSpace($Quick)) { return }
  $q = $Quick.ToLowerInvariant().Replace('_','-')

  <#
  .SYNOPSIS
  Validates that a quick shortcut has a path target.

  .DESCRIPTION
  Throws when -Target is missing for a quick action that requires a file path.

  .FUNCTION NAME
  Require-QuickTargetPath

  .INPUTS
  No direct parameters. Uses -Target and the current quick shortcut name.

  .OUTPUTS
  Returns the validated target path string.
  #>
  function Require-QuickTargetPath {
    if ([string]::IsNullOrWhiteSpace($Target)) { throw ("Quick {0} requires -Target <path>." -f $q) }
    return $Target
  }

  <#
  .SYNOPSIS
  Validates that a quick shortcut has a named target.

  .DESCRIPTION
  Throws when -Target is missing for a quick action that requires a named target such as
  a service name, task path, or registry path.

  .FUNCTION NAME
  Require-QuickTargetName

  .INPUTS
  Label string describing the required target type.

  .OUTPUTS
  Returns the validated target string.
  #>
  function Require-QuickTargetName {
    param([string]$Label)
    if ([string]::IsNullOrWhiteSpace($Target)) { throw ("Quick {0} requires -Target <{1}>." -f $q, $Label) }
    return $Target
  }

  <#
  .SYNOPSIS
  Validates that a quick shortcut has a numeric PID target.

  .DESCRIPTION
  Throws when -Target is missing or non-numeric for a quick action that requires a PID.

  .FUNCTION NAME
  Require-QuickTargetPid

  .INPUTS
  No direct parameters. Uses -Target and the current quick shortcut name.

  .OUTPUTS
  Returns the validated PID integer.
  #>
  function Require-QuickTargetPid {
    if ([string]::IsNullOrWhiteSpace($Target)) { throw ("Quick {0} requires -Target <pid>." -f $q) }
    $tmp = 0
    if (-not [int]::TryParse($Target, [ref]$tmp)) { throw ("Quick {0} requires a numeric -Target <pid>." -f $q) }
    return $tmp
  }

  switch ($q) {
    "collect-t1" { $script:Mode = "Collect"; $script:Tier = "T1"; if ($Hours -eq 24) { $script:Hours = 24 }; return }
    "collect-t2" { $script:Mode = "Collect"; $script:Tier = "T2"; if ($Hours -eq 24) { $script:Hours = 72 }; return }
    "collect-targeted-popup" {
      $script:Mode = "Collect"
      $script:Tier = "T1"
      $script:Targeted = $true
      $script:TargetProfile = "PopupWindow"
      if ($Hours -eq 24) { $script:Hours = 12 }
      if (-not [string]::IsNullOrWhiteSpace($Target)) { $script:UserReport = $Target }
      return
    }
    "collect-targeted-script" {
      $script:Mode = "Collect"
      $script:Tier = "T1"
      $script:Targeted = $true
      $script:TargetProfile = "ScriptExecution"
      if ($Hours -eq 24) { $script:Hours = 12 }
      if (-not [string]::IsNullOrWhiteSpace($Target)) { $script:UserReport = $Target }
      if (-not [string]::IsNullOrWhiteSpace($Target2)) { $script:FocusProcess = $Target2 }
      return
    }
    "enrich-start-tcp" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "TcpvconRefresh"; return }
    "enrich-add-tcp" { $script:Mode = "Enrich"; $script:Action = "TcpvconRefresh"; return }
    "enrich-start-logtext" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "LogText"; $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }; return }
    "enrich-add-logtext" { $script:Mode = "Enrich"; $script:Action = "LogText"; $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }; return }
    "enrich-start-lograw" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "LogRaw"; $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }; return }
    "enrich-add-lograw" { $script:Mode = "Enrich"; $script:Action = "LogRaw"; $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }; return }
    "enrich-start-sigcheck" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "SigcheckPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-sigcheck" { $script:Mode = "Enrich"; $script:Action = "SigcheckPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-listdlls" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "ListDllsPid"; $script:TargetPid = Require-QuickTargetPid; return }
    "enrich-add-listdlls" { $script:Mode = "Enrich"; $script:Action = "ListDllsPid"; $script:TargetPid = Require-QuickTargetPid; return }
    "enrich-start-access-file" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "AccessChkFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-access-file" { $script:Mode = "Enrich"; $script:Action = "AccessChkFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-access-service" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "AccessChkService"; $script:ServiceName = Require-QuickTargetName "service name"; return }
    "enrich-add-access-service" { $script:Mode = "Enrich"; $script:Action = "AccessChkService"; $script:ServiceName = Require-QuickTargetName "service name"; return }
    "enrich-start-access-reg" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "AccessChkReg"; $script:RegistryPath = Require-QuickTargetName "registry path"; return }
    "enrich-add-access-reg" { $script:Mode = "Enrich"; $script:Action = "AccessChkReg"; $script:RegistryPath = Require-QuickTargetName "registry path"; return }
    "enrich-start-strings" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "StringsPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-strings" { $script:Mode = "Enrich"; $script:Action = "StringsPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-streams" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "StreamsPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-streams" { $script:Mode = "Enrich"; $script:Action = "StreamsPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-pull-file" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullSuspiciousFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-pull-file" { $script:Mode = "Enrich"; $script:Action = "PullSuspiciousFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-pull-script" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullScriptOrConfig"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-pull-script" { $script:Mode = "Enrich"; $script:Action = "PullScriptOrConfig"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-pull-task" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullTaskXml"; $script:Path = Require-QuickTargetName "task path"; return }
    "enrich-add-pull-task" { $script:Mode = "Enrich"; $script:Action = "PullTaskXml"; $script:Path = Require-QuickTargetName "task path"; return }
    "enrich-start-pull-service" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullServiceBinary"; $script:ServiceName = Require-QuickTargetName "service name"; return }
    "enrich-add-pull-service" { $script:Mode = "Enrich"; $script:Action = "PullServiceBinary"; $script:ServiceName = Require-QuickTargetName "service name"; return }
    "enrich-start-pull-wmi-file" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullWmiReferencedFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-pull-wmi-file" { $script:Mode = "Enrich"; $script:Action = "PullWmiReferencedFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-finalize" { $script:Mode = "Enrich"; $script:FinalizeEnrichSession = $true; return }
    "cleanup" { $script:Mode = "Cleanup"; return }
    "help" { $script:ShowHelp = $true; $script:ContextualHelpTopic = $null; return }
    "help-collect" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "collect"; return }
    "help-enrich" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "enrich"; return }
    "help-cleanup" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "cleanup"; return }
    "help-targeted" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "targeted"; return }
    "help-version" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "version"; return }
    default { throw ("Unknown -Quick value: {0}`r`n{1}" -f $Quick, (Get-CollectorHelpText)) }
  }
}

<#
.SYNOPSIS
Prints operator next-step quick commands.

.DESCRIPTION
Emits phase-specific follow-up commands and workflow guidance after collect, enrich, and
cleanup phases.

.FUNCTION NAME
Write-QuickNextSteps

.INPUTS
Phase string.

.OUTPUTS
Writes next-step lines to standard output.
#>
function Write-QuickNextSteps {
  param([string]$Phase)

  $responseCmd = Get-CollectorResponseActionCommandBase
  Write-Output "NEXT_QUICK_COMMANDS"
  switch ($Phase) {
    "Collect" {
      Write-Output ('1. execute --command "{0} -Quick enrich-start-tcp" --comment "Run DCOIR TCP enrichment"' -f $responseCmd)
      Write-Output ('2. execute --command "{0} -Quick enrich-start-lograw -Target Security" --comment "Run DCOIR raw Security log enrichment"' -f $responseCmd)
      Write-Output ('3. If Gemini upload is the next step, prefer UPLOAD_SUMMARY_PATH, ATTACHMENT_BUDGET_MANIFEST_PATH, COLLECTION_SCOPE_PATH, and representative final_artifacts slices. No merged baseline report is emitted in this build.' )
      Write-Output ('4. execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $responseCmd)
    }
    "EnrichOpen" {
      Write-Output ('1. execute --command "{0} -Quick enrich-add-logtext -Target Security" --comment "Add Security log text enrichment to current DCOIR session"' -f $responseCmd)
      Write-Output ('2. execute --command "{0} -Quick enrich-finalize" --comment "Finalize current DCOIR enrichment session"' -f $responseCmd)
      Write-Output '3. enrich-add-* should reuse the current open session unless you explicitly request a new one.'
    }
    "EnrichFinalized" {
      Write-Output '1. Review the finalized bundle you already retrieved before recommending another endpoint retrieval of the same path.'
      Write-Output ('2. execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $responseCmd)
    }
    "Cleanup" {
      Write-Output '1. Local script file remains in place by design unless you run the explicit delete command.'
      Write-Output ('2. execute --command "{0} -Quick collect-t1" --comment "Run DCOIR collect T1"' -f $responseCmd)
      Write-Output ('3. execute --command "{0} -Quick collect-targeted-popup -Target ""User reported popup follow-up""" --comment "Run DCOIR targeted popup-style collect"' -f $responseCmd)
    }
  }
}

<#
.SYNOPSIS
Removes run/package artifacts during cleanup.

.DESCRIPTION
Deletes the package path and run root recorded in the supplied collector state object.

.FUNCTION NAME
Invoke-Cleanup

.INPUTS
Collector state object.

.OUTPUTS
No direct output. Removes cleanup targets as a side effect.
#>
function Invoke-Cleanup {
  param($StateObject)
  $targets = @([string]$StateObject.PackagePath,[string]$StateObject.RunRoot) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
  foreach ($target in $targets) {
    Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue
  }
}
# END DCOIR_Collector.04_Quick_Interface_And_Output.ps1

# BEGIN DCOIR_Collector.04B_Feature_Wave_Targeted_Collection.ps1
<#
.SYNOPSIS
DCOIR collector targeted-collection and feature-wave helper functions.

.DESCRIPTION
Builds the targeted-collection scope and analyst plan artifacts, emits the bounded
parallelism assessment, and creates synthetic chunk-validation artifacts used by the
feature-wave collection and upload-surface regression paths.

.FILE NAME
DCOIR_Collector.04B_Feature_Wave_Targeted_Collection.ps1

.INPUTS
Collector state and baseline hashtables, targeted-collection globals such as
WindowStart, WindowEnd, FocusProcess, FocusPath, FocusIndicator, UserReport,
IncludeArtifactCategory, Hours, and validation-specific synthetic chunking settings.

.OUTPUTS
Ordered scope objects, analyst-facing text artifacts, chunk-manifest data, and updates
to the baseline artifact map and report builder.
#>

<#
.SYNOPSIS
Builds the targeted collection scope object.

.DESCRIPTION
Normalizes the current targeted-collection globals into one ordered scope object for
artifact generation and analyst-facing planning.

.FUNCTION NAME
Get-TargetedCollectionScopeObject

.INPUTS
State hashtable.

.OUTPUTS
Ordered hashtable describing the targeted collection scope.
#>
function Get-TargetedCollectionScopeObject {
  param([hashtable]$State)

  $hasWindow = (-not [string]::IsNullOrWhiteSpace($WindowStart)) -or (-not [string]::IsNullOrWhiteSpace($WindowEnd))
  $hasFocus = (-not [string]::IsNullOrWhiteSpace($FocusProcess)) -or (-not [string]::IsNullOrWhiteSpace($FocusPath)) -or (-not [string]::IsNullOrWhiteSpace($FocusIndicator)) -or (-not [string]::IsNullOrWhiteSpace($UserReport))
  $categories = @()
  if ($IncludeArtifactCategory) { $categories = @($IncludeArtifactCategory | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) }

  return [ordered]@{
    targeted_mode_enabled = [bool]$Targeted
    target_profile = $TargetProfile
    has_explicit_time_window = $hasWindow
    window_start = $WindowStart
    window_end = $WindowEnd
    requested_hours = $Hours
    included_artifact_categories = $categories
    focus_process = $FocusProcess
    focus_path = $FocusPath
    focus_indicator = $FocusIndicator
    focus_indicator_type = $FocusIndicatorType
    user_report = $UserReport
    has_focus_context = $hasFocus
    implementation_boundary = "This major-version targeted collection feature currently narrows analyst guidance, collection scope intent, artifact prioritization, and recommended next actions. It does not yet rewrite every baseline collection helper into exact start-end timestamp filtering across all artifact families."
  }
}

<#
.SYNOPSIS
Builds the targeted collection scope text artifact.

.DESCRIPTION
Converts the normalized targeted scope object into an analyst-facing text artifact.

.FUNCTION NAME
Get-TargetedCollectionScopeText

.INPUTS
Scope hashtable.

.OUTPUTS
String targeted collection scope text.
#>
function Get-TargetedCollectionScopeText {
  param([hashtable]$Scope)

  $lines = @()
  $lines += "TARGETED_COLLECTION_SCOPE"
  $lines += ("TARGETED_MODE_ENABLED={0}" -f $Scope.targeted_mode_enabled)
  $lines += ("TARGET_PROFILE={0}" -f $Scope.target_profile)
  $lines += ("HAS_EXPLICIT_TIME_WINDOW={0}" -f $Scope.has_explicit_time_window)
  $lines += ("WINDOW_START={0}" -f $Scope.window_start)
  $lines += ("WINDOW_END={0}" -f $Scope.window_end)
  $lines += ("REQUESTED_HOURS={0}" -f $Scope.requested_hours)
  $lines += ("FOCUS_PROCESS={0}" -f $Scope.focus_process)
  $lines += ("FOCUS_PATH={0}" -f $Scope.focus_path)
  $lines += ("FOCUS_INDICATOR={0}" -f $Scope.focus_indicator)
  $lines += ("FOCUS_INDICATOR_TYPE={0}" -f $Scope.focus_indicator_type)
  $lines += ("USER_REPORT={0}" -f $Scope.user_report)
  $lines += ("INCLUDED_ARTIFACT_CATEGORIES={0}" -f (($Scope.included_artifact_categories | ForEach-Object { $_ }) -join ', '))
  $lines += ""
  $lines += "IMPLEMENTATION_BOUNDARY"
  $lines += $Scope.implementation_boundary
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the targeted collection plan text artifact.

.DESCRIPTION
Returns the analyst-facing plan that prioritizes evidence and review order for the
current targeted profile and focus context.

.FUNCTION NAME
Get-TargetedCollectionPlanText

.INPUTS
Scope hashtable.

.OUTPUTS
String targeted collection plan text.
#>
function Get-TargetedCollectionPlanText {
  param([hashtable]$Scope)

  $lines = @()
  $lines += "TARGETED_COLLECTION_PLAN"
  $lines += ("PROFILE={0}" -f $Scope.target_profile)
  $lines += ""
  $lines += "INTENDED USE"
  $lines += "- This report turns the targeted collection request into explicit analyst-facing scoping guidance."
  $lines += "- It is intended to explain what the collector should emphasize, what the analyst should upload first, and which evidence families should be treated as highest value."
  $lines += "- It is intentionally explicit because narrow incidents such as a user-reported popup, a suspected script execution, or a suspicious process often need a smaller and more explainable collection path than a generic broad baseline."
  $lines += ""
  $lines += "PRIORITIZED EVIDENCE"
  switch ($Scope.target_profile) {
    "PopupWindow" {
      $lines += "1. Security high-signal events around the reported time window."
      $lines += "2. Process inventory and likely user-context process chains."
      $lines += "3. PowerShell operational events and scheduled task activity."
      $lines += "4. Representative artifacts tied to likely GUI-launching processes, startup points, or scripts."
    }
    "ScriptExecution" {
      $lines += "1. PowerShell operational events and Security 4688 process creation records."
      $lines += "2. Process inventory entries with suspicious command lines or user-writable execution paths."
      $lines += "3. Pulled script, config, or suspicious file artifacts if specific paths are known."
      $lines += "4. Strings, streams, or signature enrichment on the focal script or binary path."
    }
    "PersistenceFollowUp" {
      $lines += "1. Services, scheduled tasks, Run keys, and autoruns."
      $lines += "2. WMI persistence text and service binary follow-up."
      $lines += "3. Registry, service ACL, and task XML follow-up actions."
      $lines += "4. Representative retrieved artifacts for persistence evidence."
    }
    "NetworkOnly" {
      $lines += "1. Structured network state, netstat, tcpvcon, dns cache, route, and arp."
      $lines += "2. Security events that establish the launching process or account context."
      $lines += "3. Follow-up TCP refresh enrichment."
      $lines += "4. Representative network-facing process inventory slices."
    }
    "ProcessAndPowerShell" {
      $lines += "1. Process inventory, pslist, Security 4688, and PowerShell operational records."
      $lines += "2. Signature, strings, and stream checks for focal binaries or scripts."
      $lines += "3. Retrieval of suspicious script or config paths when known."
      $lines += "4. Repeatable enrichment of process-centric context in one bounded session."
    }
    default {
      $lines += "1. Metadata, upload summary, analyst follow-up queue, and security high-signal summary."
      $lines += "2. One or more focal process, script, or network artifacts if a likely target is known."
      $lines += "3. Narrow enrichment tied to the strongest current lead."
      $lines += "4. Avoid defaulting to oversized merged review artifacts when smaller decisive artifacts are sufficient."
    }
  }
  $lines += ""
  $lines += "ANALYST NOTES"
  if (-not [string]::IsNullOrWhiteSpace($Scope.user_report)) {
    $lines += ("- User report: {0}" -f $Scope.user_report)
  } else {
    $lines += "- No free-text user report was supplied."
  }
  if ($Scope.has_explicit_time_window) {
    $lines += ("- Explicit time window requested: {0} to {1}" -f $Scope.window_start, $Scope.window_end)
  } else {
    $lines += "- No explicit start-end time window was supplied. The collector remains hour-window based in this version."
  }
  if ($Scope.has_focus_context) {
    $lines += "- Focus context was supplied and should influence the first analyst review pass."
  } else {
    $lines += "- No narrow focal artifact was supplied; use the target profile plus the analyst follow-up queue to choose the first review artifact."
  }
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the bounded parallelism assessment text.

.DESCRIPTION
Returns the analyst-facing explanation of the currently implemented bounded runtime
parallelism posture and its validation expectations.

.FUNCTION NAME
Get-CollectorParallelismAssessmentText

.INPUTS
No direct parameters.

.OUTPUTS
String parallelism assessment text.
#>
function Get-CollectorParallelismAssessmentText {
  $lines = @()
  $lines += "COLLECTOR_PARALLELISM_ASSESSMENT"
  $lines += "STATUS=BOUNDED_RUNTIME_IMPLEMENTED"
  $lines += ""
  $lines += "CURRENT POSITION"
  $lines += "- The collector now performs bounded PowerShell 5.1-safe parallel runtime execution for selected read-only baseline worker groups."
  $lines += "- The implemented worker set is intentionally narrow and preserves deterministic final report assembly."
  $lines += "- The collector still emits a durable parallel execution proof surface so overlap and worker completion can be validated on a real Collect run."
  $lines += ""
  $lines += "IMPLEMENTED WORKER GROUPS"
  $lines += "1. Host baseline worker for time/hostname/version and systeminfo capture."
  $lines += "2. Identity context worker for whoami and interactive session capture."
  $lines += "3. Network light worker for ipconfig, DNS cache, route, and ARP capture."
  $lines += "4. Security posture worker for firewall profile capture."
  $lines += ""
  $lines += "SAFETY GUARDRAILS"
  $lines += "1. Each worker writes its own durable artifact under final_artifacts\\parallel_workers."
  $lines += "2. The parent waits for all workers to finish before continuing deterministic report assembly."
  $lines += "3. Steps not successfully cached by a worker fall back to serial execution when needed."
  $lines += ""
  $lines += "STILL SERIAL"
  $lines += "- Process inventory, event timeline collection, persistence sections, Sysinternals-enriched captures, and bundle/manifest finalization remain serial in this bounded implementation slice."
  $lines += ""
  $lines += "VALIDATION EXPECTATION"
  $lines += "- Use the emitted parallel execution proof artifact and worker files to verify overlapping runtime and deterministic output before claiming the broader issue closed."
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the analyst overview artifact.

.DESCRIPTION
Writes the analyst-first overview artifact that points review toward metadata, upload
summary, high-signal artifacts, and any targeted plan emitted for the run.

.FUNCTION NAME
New-AnalystOverviewArtifact

.INPUTS
State hashtable and Baseline hashtable.

.OUTPUTS
String analyst overview artifact path.
#>
function New-AnalystOverviewArtifact {
  param([hashtable]$State,[hashtable]$Baseline)

  $artifactMap = $Baseline.ArtifactMap
  $overviewPath = Join-Path $State.ReportsDir ("DCOIR_ANALYST_OVERVIEW_{0}_{1}.txt" -f $env:COMPUTERNAME, $State.RunId)
  $lines = New-Object System.Collections.ArrayList

  [void]$lines.Add("DCOIR_ANALYST_OVERVIEW")
  [void]$lines.Add(("CollectorVersion={0}" -f $ScriptVersion))
  [void]$lines.Add(("RunId={0}" -f $State.RunId))
  [void]$lines.Add("WorkflowPhase=CollectBaseline")
  [void]$lines.Add("PrimaryReviewPosture=SmallerSurfaceFirst")
  [void]$lines.Add("DoNotAssumeMonolithicBaselineUpload=true")
  [void]$lines.Add("MergedBaselineReportEmitted=false")
  [void]$lines.Add(("DefaultGeminiUploadSetStatus={0}" -f $State.DefaultGeminiUploadSetStatus))
  [void]$lines.Add(("CollectTier={0}" -f $Tier))
  $collectorErrorCount = @($Global:CollectorErrors).Count
  [void]$lines.Add(("CollectorObservedErrorCount={0}" -f $collectorErrorCount))
  if ($collectorErrorCount -gt 0) {
    [void]$lines.Add('RunHealth=DEGRADED_OR_PARTIAL_REVIEW_REQUIRED')
  } else {
    [void]$lines.Add('RunHealth=NO_DEGRADED_STATE_OBSERVED_DURING_COLLECTION')
  }
  [void]$lines.Add("")
  [void]$lines.Add("WHAT_TO_REVIEW_FIRST")
  [void]$lines.Add("1. Start with this overview, the upload summary, and the metadata report.")
  [void]$lines.Add("2. Use the analyst follow-up queue and security high-signal summary as the first decisive triage surface.")
  [void]$lines.Add("3. Use representative process, network, and defender artifacts before expanding into broader local review.")
  if ($collectorErrorCount -gt 0) {
    [void]$lines.Add("4. This run recorded degraded or partial conditions. Review errors.log and the affected truth surfaces before treating the overview as complete.")
  }
  if ($State.TargetedCollectionPlanPath) {
    [void]$lines.Add("4. A targeted collection plan was emitted for this run; review it first when the incident is narrow.")
  }
  [void]$lines.Add("")
  [void]$lines.Add("REVIEW_FIRST_PATHS")
  foreach ($pair in @(
    @{ Label = 'ANALYST_OVERVIEW_PATH'; Path = $overviewPath },
    @{ Label = 'UPLOAD_SUMMARY_PATH'; Path = $State.UploadSummaryPath },
    @{ Label = 'METADATA_REPORT_PATH'; Path = $State.MetadataReportPath },
    @{ Label = 'ATTACHMENT_BUDGET_MANIFEST_PATH'; Path = $State.UploadBudgetManifestPath },
    @{ Label = 'COLLECTION_SCOPE_PATH'; Path = $State.CollectionScopePath },
    @{ Label = 'TARGETED_COLLECTION_PLAN_PATH'; Path = $State.TargetedCollectionPlanPath },
    @{ Label = 'ANALYST_FOLLOW_UP_QUEUE_PATH'; Path = $artifactMap['analyst_follow_up_queue'] },
    @{ Label = 'SECURITY_HIGH_SIGNAL_SUMMARY_PATH'; Path = $artifactMap['security_high_signal_summary'] },
    @{ Label = 'PROCESS_INVENTORY_PATH'; Path = $artifactMap['process_inventory'] },
    @{ Label = 'STRUCTURED_NET_PATH'; Path = $artifactMap['structured_net'] },
    @{ Label = 'DEFENDER_STATUS_PATH'; Path = $artifactMap['defender_status'] }
  )) {
    if ($pair.Path -and (Test-Path -LiteralPath $pair.Path)) {
      [void]$lines.Add(("{0}={1}" -f $pair.Label, $pair.Path))
    }
  }
  [void]$lines.Add("")
  if ($collectorErrorCount -gt 0) {
    [void]$lines.Add("DEGRADED_REVIEW_NOTE")
    [void]$lines.Add("This run emitted collector errors during collection. Use errors.log plus the specific affected artifacts as the truth surface for degraded lanes.")
    [void]$lines.Add("")
  }
  [void]$lines.Add("NO_MERGED_BASELINE_REPORT")
  [void]$lines.Add("No merged baseline report is emitted in this build. Use metadata plus representative artifacts for broader local review.")

  Set-Content -Path $overviewPath -Value $lines -Encoding UTF8
  return $overviewPath
}

<#
.SYNOPSIS
Reads the synthetic oversized-artifact validation size.

.DESCRIPTION
Returns the requested synthetic oversized artifact size in KB from the process
environment or zero when the override is absent or invalid.

.FUNCTION NAME
Get-ValidationSyntheticOversizeArtifactKB

.INPUTS
No direct parameters.

.OUTPUTS
Integer requested synthetic artifact size in KB.
#>
function Get-ValidationSyntheticOversizeArtifactKB {
  $raw = [Environment]::GetEnvironmentVariable('DCOIR_TEST_SYNTHETIC_OVERSIZE_ARTIFACT_KB', 'Process')
  if ([string]::IsNullOrWhiteSpace($raw)) { return 0 }
  $parsed = 0
  if ([int]::TryParse($raw, [ref]$parsed) -and $parsed -gt 0) { return $parsed }
  return 0
}

<#
.SYNOPSIS
Builds the synthetic oversized artifact text.

.DESCRIPTION
Creates deterministic text content large enough to exceed the requested size for chunking
validation.

.FUNCTION NAME
New-SyntheticOversizeArtifactText

.INPUTS
RequestedKB integer.

.OUTPUTS
String synthetic oversized artifact content.
#>
function New-SyntheticOversizeArtifactText {
  param([int]$RequestedKB)

  $line = 'DCOIR_SYNTHETIC_OVERSIZE_CHUNK_VALIDATION_PAYLOAD|ABCDEFGHIJKLMNOPQRSTUVWXYZ|0123456789|line='
  $targetBytes = $RequestedKB * 1024
  $currentBytes = 0
  $index = 1
  $sb = New-Object System.Text.StringBuilder
  while ($currentBytes -lt $targetBytes) {
    $lineText = ('{0}{1}' -f $line, $index) + [Environment]::NewLine
    [void]$sb.Append($lineText)
    $currentBytes += [System.Text.Encoding]::UTF8.GetByteCount($lineText)
    $index += 1
  }
  return $sb.ToString()
}

<#
.SYNOPSIS
Writes exact UTF-8 text without BOM to an artifact path.

.DESCRIPTION
Builds a deterministic artifact filename and writes the supplied text exactly using
UTF-8 without BOM.

.FUNCTION NAME
Write-ArtifactTextExact

.INPUTS
ArtifactsDir, Section, Name, and Text strings.

.OUTPUTS
String artifact path.
#>
function Write-ArtifactTextExact {
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
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $Text, $utf8NoBom)
  return $path
}

<#
.SYNOPSIS
Splits a validation text artifact into smaller chunks.

.DESCRIPTION
Breaks the supplied source artifact into multiple ordered chunk files sized for upload
budget validation and reconstruction testing.

.FUNCTION NAME
Split-ValidationTextArtifactIntoChunks

.INPUTS
SourcePath, ArtifactsDir, RequestedKB, and TargetChunkKB.

.OUTPUTS
Hashtable describing chunk paths, sizes, and reconstruction metadata.
#>
function Split-ValidationTextArtifactIntoChunks {
  param(
    [string]$SourcePath,
    [string]$ArtifactsDir,
    [int]$RequestedKB,
    [int]$TargetChunkKB
  )

  $chunkPaths = New-Object System.Collections.ArrayList
  $targetBytes = $TargetChunkKB * 1024
  $lines = Get-Content -LiteralPath $SourcePath
  $chunkIndex = 1
  $currentBytes = 0
  $sb = New-Object System.Text.StringBuilder

  foreach ($line in $lines) {
    $lineText = $line + [Environment]::NewLine
    $lineBytes = [System.Text.Encoding]::UTF8.GetByteCount($lineText)
    if (($currentBytes + $lineBytes) -gt $targetBytes -and $currentBytes -gt 0) {
      $chunkPath = Write-ArtifactTextExact -ArtifactsDir $ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_chunk_{1:000}.txt' -f $RequestedKB, $chunkIndex) -Text $sb.ToString()
      [void]$chunkPaths.Add($chunkPath)
      $chunkIndex += 1
      $sb = New-Object System.Text.StringBuilder
      $currentBytes = 0
    }
    [void]$sb.Append($lineText)
    $currentBytes += $lineBytes
  }

  if ($currentBytes -gt 0) {
    $chunkPath = Write-ArtifactTextExact -ArtifactsDir $ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_chunk_{1:000}.txt' -f $RequestedKB, $chunkIndex) -Text $sb.ToString()
    [void]$chunkPaths.Add($chunkPath)
  }

  $chunkSizes = @()
  foreach ($chunkPath in @($chunkPaths)) {
    $chunkSizes += (Get-FileSizeKB -Path $chunkPath)
  }

  return @{
    ChunkPaths = @($chunkPaths)
    ChunkSizesKB = $chunkSizes
    ChunkCount = @($chunkPaths).Count
    TargetChunkKB = $TargetChunkKB
    ReconstructionOrder = 'Concatenate the chunk_paths entries in listed order to reconstruct the original synthetic oversize artifact.'
  }
}

<#
.SYNOPSIS
Builds the synthetic chunk-validation artifacts.

.DESCRIPTION
Creates the synthetic oversized source, chunk files, path list, and manifest, then
registers them into collector state and baseline artifacts.

.FUNCTION NAME
New-SyntheticOversizeChunkValidationArtifacts

.INPUTS
State hashtable, Baseline hashtable, and RequestedKB integer.

.OUTPUTS
No direct output. Updates state and baseline structures.
#>
function New-SyntheticOversizeChunkValidationArtifacts {
  param([hashtable]$State,[hashtable]$Baseline,[int]$RequestedKB)

  $sourceText = New-SyntheticOversizeArtifactText -RequestedKB $RequestedKB
  $sourcePath = Write-ArtifactTextExact -ArtifactsDir $State.ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_source.txt' -f $RequestedKB) -Text $sourceText
  $chunkResult = Split-ValidationTextArtifactIntoChunks -SourcePath $sourcePath -ArtifactsDir $State.ArtifactsDir -RequestedKB $RequestedKB -TargetChunkKB 700
  $pathListPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_chunk_paths.json.txt' -f $RequestedKB) -Text (Convert-ToSafeJsonText -InputObject $chunkResult.ChunkPaths)

  $manifestObj = [ordered]@{
    fixture_origin = 'collector_synthetic_validation'
    source_path = $sourcePath
    source_size_kb = Get-FileSizeKB -Path $sourcePath
    target_chunk_kb = $chunkResult.TargetChunkKB
    chunk_count = $chunkResult.ChunkCount
    chunk_paths = $chunkResult.ChunkPaths
    chunk_file_sizes_kb = $chunkResult.ChunkSizesKB
    reconstruction_order = $chunkResult.ReconstructionOrder
  }
  $manifestPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_chunk_manifest.json.txt' -f $RequestedKB) -Text (Convert-ToSafeJsonText -InputObject $manifestObj)

  $State.SyntheticOversizeSourcePath = $sourcePath
  $State.ChunkManifestPath = $manifestPath
  $Baseline.ArtifactMap['synthetic_oversize_source'] = $sourcePath
  $Baseline.ArtifactMap['synthetic_oversize_chunk_manifest'] = $manifestPath
  $Baseline.ArtifactMap['synthetic_oversize_chunk_paths_json'] = $pathListPath
  [void]$Baseline.ArtifactPaths.Add($sourcePath)
  [void]$Baseline.ArtifactPaths.Add($pathListPath)
  [void]$Baseline.ArtifactPaths.Add($manifestPath)
  foreach ($chunkPath in $chunkResult.ChunkPaths) {
    [void]$Baseline.ArtifactPaths.Add($chunkPath)
  }

  $summaryText = @(
    'VALIDATION_SYNTHETIC_CHUNKING',
    ('REQUESTED_SYNTHETIC_SOURCE_KB={0}' -f $RequestedKB),
    ('SOURCE_PATH={0}' -f $sourcePath),
    ('SOURCE_SIZE_KB={0}' -f (Get-FileSizeKB -Path $sourcePath)),
    ('CHUNK_MANIFEST_PATH={0}' -f $manifestPath),
    ('CHUNK_COUNT={0}' -f $chunkResult.ChunkCount),
    ('TARGET_CHUNK_KB={0}' -f $chunkResult.TargetChunkKB)
  ) -join [Environment]::NewLine
  Add-Section -Builder $Baseline.ReportBuilder -Name 'VALIDATION_SYNTHETIC_CHUNKING' -Text $summaryText
  Add-CollectorNote ('Synthetic oversized validation artifact and chunk set were emitted for collector chunking regression at {0} KB.' -f $RequestedKB)
}

<#
.SYNOPSIS
Applies feature-wave collect enhancements to one baseline run.

.DESCRIPTION
Adds targeted collection artifacts, parallelism assessment, optional targeted planning,
and optional synthetic chunk-validation artifacts into the current baseline result.

.FUNCTION NAME
Apply-FeatureWaveCollectEnhancements

.INPUTS
State hashtable and Baseline hashtable.

.OUTPUTS
No direct output. Updates state, baseline, and collector notes/recommendations.
#>
function Apply-FeatureWaveCollectEnhancements {
  param([hashtable]$State,[hashtable]$Baseline)

  $scope = Get-TargetedCollectionScopeObject -State $State
  $scopeText = Get-TargetedCollectionScopeText -Scope $scope
  $scopePath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TARGETED_COLLECTION" -Name "collection_scope.txt" -Text $scopeText
  $State.CollectionScopePath = $scopePath
  $Baseline.ArtifactMap['collection_scope'] = $scopePath
  [void]$Baseline.ArtifactPaths.Add($scopePath)
  Add-Section -Builder $Baseline.ReportBuilder -Name "TARGETED_COLLECTION_SCOPE" -Text $scopeText

  $parallelText = Get-CollectorParallelismAssessmentText
  $parallelPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TARGETED_COLLECTION" -Name "parallelism_assessment.txt" -Text $parallelText
  $State.ParallelismAssessmentPath = $parallelPath
  $Baseline.ArtifactMap['parallelism_assessment'] = $parallelPath
  [void]$Baseline.ArtifactPaths.Add($parallelPath)
  Add-Section -Builder $Baseline.ReportBuilder -Name "COLLECTOR_PARALLELISM_ASSESSMENT" -Text $parallelText

  if ($Targeted -or $scope.has_focus_context -or $scope.has_explicit_time_window) {
    $planText = Get-TargetedCollectionPlanText -Scope $scope
    $planPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TARGETED_COLLECTION" -Name "targeted_collection_plan.txt" -Text $planText
    $State.TargetedCollectionPlanPath = $planPath
    $Baseline.ArtifactMap['targeted_collection_plan'] = $planPath
    [void]$Baseline.ArtifactPaths.Add($planPath)
    Add-Section -Builder $Baseline.ReportBuilder -Name "TARGETED_COLLECTION_PLAN" -Text $planText

    Add-Recommendation "A targeted collection plan was generated for this run."
    Add-Recommendation "For Gemini uploads, include COLLECTION_SCOPE_PATH and TARGETED_COLLECTION_PLAN_PATH before broader artifact expansion when the case is narrow or user-reported."
  }

  $syntheticKB = Get-ValidationSyntheticOversizeArtifactKB
  if ($syntheticKB -gt 0) {
    New-SyntheticOversizeChunkValidationArtifacts -State $State -Baseline $Baseline -RequestedKB $syntheticKB
  }

  if ($Targeted) {
    Add-CollectorNote ("Targeted collection mode was enabled with profile [{0}]." -f $TargetProfile)
  }
}
# END DCOIR_Collector.04B_Feature_Wave_Targeted_Collection.ps1

# BEGIN DCOIR_Collector.04C_Explicit_Event_Window_Overrides.ps1
<#
.SYNOPSIS
DCOIR collector explicit event-window override helpers.

.DESCRIPTION
Implements explicit event-window parsing, event-filter hashtable construction, event-log
text export, Security high-signal summarization, and raw EVTX export for targeted and
enrichment-driven collection lanes.

.FILE NAME
DCOIR_Collector.04C_Explicit_Event_Window_Overrides.ps1

.INPUTS
Window-hours values, explicit WindowStart and WindowEnd globals, event-log channel
names, optional event IDs, output paths, and scratch directories.

.OUTPUTS
Window hashtables, event-filter hashtables, analyst-facing text summaries, and staged
EVTX exports.
#>

<#
.SYNOPSIS
Resolves the effective event window for the current collector call.

.DESCRIPTION
Combines the current WindowHours value with explicit WindowStart and WindowEnd inputs,
normalizes invalid or partial windows into safe fallback behavior, and returns one
window object that downstream event readers can consume consistently.

.FUNCTION NAME
Get-CollectorEffectiveEventWindow

.INPUTS
WindowHours integer plus the current WindowStart and WindowEnd globals.

.OUTPUTS
Hashtable containing HasExplicitWindow, StartTime, EndTime, and EffectiveHours.
#>
function Get-CollectorEffectiveEventWindow {
  param([int]$WindowHours = 24)

  $effectiveHours = [math]::Abs($WindowHours)
  if ($effectiveHours -le 0) { $effectiveHours = 24 }

  $now = Get-Date
  $parsedStart = $null
  $parsedEnd = $null
  $parseFailed = $false

  if (-not [string]::IsNullOrWhiteSpace($WindowStart)) {
    [datetime]$tmpStart = [datetime]::MinValue
    if ([datetime]::TryParse($WindowStart, [ref]$tmpStart)) {
      $parsedStart = $tmpStart
    } else {
      Add-CollectorError ("Invalid WindowStart value [{0}]; falling back to hour-window behavior." -f $WindowStart)
      $parseFailed = $true
    }
  }

  if (-not [string]::IsNullOrWhiteSpace($WindowEnd)) {
    [datetime]$tmpEnd = [datetime]::MinValue
    if ([datetime]::TryParse($WindowEnd, [ref]$tmpEnd)) {
      $parsedEnd = $tmpEnd
    } else {
      Add-CollectorError ("Invalid WindowEnd value [{0}]; falling back to hour-window behavior." -f $WindowEnd)
      $parseFailed = $true
    }
  }

  if ($parseFailed) {
    $parsedStart = $null
    $parsedEnd = $null
  } elseif ($parsedStart -and $parsedEnd -and $parsedEnd -lt $parsedStart) {
    Add-CollectorError ("WindowEnd [{0}] is earlier than WindowStart [{1}]; falling back to hour-window behavior." -f $WindowEnd, $WindowStart)
    $parsedStart = $null
    $parsedEnd = $null
  }

  if ($parsedStart -and -not $parsedEnd) {
    $parsedEnd = $now
  } elseif ($parsedEnd -and -not $parsedStart) {
    $parsedStart = $parsedEnd.AddHours(-1 * $effectiveHours)
  }

  $hasExplicitWindow = ($parsedStart -ne $null) -or ($parsedEnd -ne $null)
  $startTime = if ($parsedStart) { $parsedStart } else { $now.AddHours(-1 * $effectiveHours) }
  $endTime = if ($parsedEnd) { $parsedEnd } else { $null }

  return @{
    HasExplicitWindow = [bool]$hasExplicitWindow
    StartTime = $startTime
    EndTime = $endTime
    EffectiveHours = $effectiveHours
  }
}

<#
.SYNOPSIS
Builds a Get-WinEvent filter hashtable from a normalized window object.

.DESCRIPTION
Creates the filter hashtable used by event readers, always including LogName and
StartTime and conditionally adding EndTime and Id constraints when present.

.FUNCTION NAME
Get-CollectorEventFilterHashtable

.INPUTS
LogName string, Window hashtable from Get-CollectorEffectiveEventWindow, and optional
integer event IDs.

.OUTPUTS
Hashtable suitable for Get-WinEvent -FilterHashtable.
#>
function Get-CollectorEventFilterHashtable {
  param(
    [Parameter(Mandatory=$true)][string]$LogName,
    [hashtable]$Window,
    [int[]]$Ids
  )

  $fh = @{
    LogName = $LogName
    StartTime = $Window.StartTime
  }

  if ($Window.EndTime) {
    $fh.EndTime = $Window.EndTime
  }

  if ($Ids -and @($Ids).Count -gt 0) {
    $fh.Id = $Ids
  }

  return $fh
}

<#
.SYNOPSIS
Formats event-window metadata for text reports.

.DESCRIPTION
Returns stable key-value lines that make the effective event-window behavior observable in
event text, summaries, and enrichment reports.

.FUNCTION NAME
Get-CollectorEventWindowMetadataLines

.INPUTS
Window hashtable, channel name, optional event IDs, and max-event count.

.OUTPUTS
Array of strings.
#>
function Get-CollectorEventWindowMetadataLines {
  param(
    [hashtable]$Window,
    [string]$Channel,
    [int[]]$Ids,
    [int]$Take
  )

  $lines = New-Object System.Collections.ArrayList
  if (-not [string]::IsNullOrWhiteSpace($Channel)) { [void]$lines.Add(("CHANNEL={0}" -f $Channel)) }
  [void]$lines.Add(("WINDOW_HOURS={0}" -f $Window.EffectiveHours))
  [void]$lines.Add(("HAS_EXPLICIT_TIME_WINDOW={0}" -f $Window.HasExplicitWindow))
  [void]$lines.Add(("WINDOW_START={0}" -f $Window.StartTime.ToString("o")))
  [void]$lines.Add(("WINDOW_END={0}" -f $(if ($Window.EndTime) { $Window.EndTime.ToString("o") } else { "" })))
  if ($Ids -and @($Ids).Count -gt 0) { [void]$lines.Add(("EVENT_IDS={0}" -f ($Ids -join ','))) }
  if ($Take -gt 0) { [void]$lines.Add(("MAX_EVENTS={0}" -f $Take)) }
  return @($lines)
}

<#
.SYNOPSIS
Formats explicit event-window target details for enrich reports.

.DESCRIPTION
Builds one semicolon-delimited target-details string that includes explicit window fields
when they were supplied by the operator.

.FUNCTION NAME
Get-CollectorEventWindowTargetDetails

.INPUTS
LogName string, Hours integer, optional EventIds, and optional MaxEvents.

.OUTPUTS
String suitable for action target-details fields.
#>
function Get-CollectorEventWindowTargetDetails {
  param([string]$LogName,[int]$Hours,[int[]]$Ids,[int]$Take)
  $parts = New-Object System.Collections.ArrayList
  [void]$parts.Add(("LogName={0}" -f $LogName))
  [void]$parts.Add(("Hours={0}" -f $Hours))
  if (-not [string]::IsNullOrWhiteSpace($WindowStart)) { [void]$parts.Add(("WindowStart={0}" -f $WindowStart)) }
  if (-not [string]::IsNullOrWhiteSpace($WindowEnd)) { [void]$parts.Add(("WindowEnd={0}" -f $WindowEnd)) }
  if ($Ids -and @($Ids).Count -gt 0) { [void]$parts.Add(("EventIds={0}" -f ($Ids -join ','))) }
  if ($Take -gt 0) { [void]$parts.Add(("MaxEvents={0}" -f $Take)) }
  return ($parts -join '; ')
}

<#
.SYNOPSIS
Builds a condensed Security high-signal summary for the selected window.

.DESCRIPTION
Queries key Security event IDs, suppresses routine machine/service noise, summarizes the
remaining interesting events, and returns analyst-facing text with explicit window
markers and per-event summaries.

.FUNCTION NAME
Get-SecurityHighSignalSummaryText

.INPUTS
WindowHours integer and Take integer limiting the returned summary volume.

.OUTPUTS
String containing the Security high-signal summary or an explicit error/nothing-found
message.
#>
function Get-SecurityHighSignalSummaryText {
  param(
    [int]$WindowHours = 24,
    [int]$Take = 200
  )

  try {
    $ids = @(4624,4625,4648,4672,4688,4697,4698)
    $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
    $fh = Get-CollectorEventFilterHashtable -LogName "Security" -Window $window -Ids $ids

    $events = @(Get-WinEvent -FilterHashtable $fh -ErrorAction Stop |
      Sort-Object TimeCreated -Descending |
      Select-Object -First ($Take * 4))

    if (@($events).Count -eq 0) {
      Add-CollectorNote "No high-signal Security events were found in the selected window."
      $lines = New-Object System.Collections.ArrayList
      [void]$lines.Add("SECURITY_HIGH_SIGNAL_SUMMARY")
      foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel 'Security' -Ids $ids -Take $Take)) { [void]$lines.Add($metadataLine) }
      [void]$lines.Add("RAW_EVENT_COUNT=0")
      [void]$lines.Add("INTERESTING_EVENT_COUNT=0")
      [void]$lines.Add("SUPPRESSED_EVENT_COUNT=0")
      [void]$lines.Add("")
      [void]$lines.Add("No high-signal Security events were found in the selected window.")
      return ($lines -join [Environment]::NewLine)
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
    foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel 'Security' -Ids $ids -Take $Take)) { [void]$lines.Add($metadataLine) }
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
          $summary = "Successful logon Target={0}\{1} LogonType={2} SourceIp={3} Workstation={4}" -f (Get-EventMapValue -Map $m -Key 'TargetDomainName'), (Get-EventMapValue -Map $m -Key 'TargetUserName'), (Get-EventMapValue -Map $m -Key 'LogonType'), (Get-EventMapValue -Map $m -Key 'IpAddress'), (Get-EventMapValue -Map $m -Key 'WorkstationName')
        }
        4625 {
          $summary = "Failed logon Target={0}\{1} LogonType={2} SourceIp={3} Status={4} SubStatus={5}" -f (Get-EventMapValue -Map $m -Key 'TargetDomainName'), (Get-EventMapValue -Map $m -Key 'TargetUserName'), (Get-EventMapValue -Map $m -Key 'LogonType'), (Get-EventMapValue -Map $m -Key 'IpAddress'), (Get-EventMapValue -Map $m -Key 'Status'), (Get-EventMapValue -Map $m -Key 'SubStatus')
        }
        4648 {
          $summary = "Explicit credentials Subject={0}\{1} TargetServer={2} Process={3} SourceIp={4}" -f (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName'), (Get-EventMapValue -Map $m -Key 'TargetServerName'), (Get-EventMapValue -Map $m -Key 'ProcessName'), (Get-EventMapValue -Map $m -Key 'IpAddress')
        }
        4672 {
          $summary = "Special privileges assigned Subject={0}\{1} Privileges={2}" -f (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName'), (Get-EventMapValue -Map $m -Key 'PrivilegeList')
        }
        4688 {
          $summary = "Process created NewProcess={0} ParentProcess={1} Subject={2}\{3} CommandLine={4}" -f (Get-EventMapValue -Map $m -Key 'NewProcessName'), (Get-EventMapValue -Map $m -Key 'ParentProcessName'), (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName'), (Get-EventMapValue -Map $m -Key 'CommandLine')
        }
        4697 {
          $summary = "Service installed Name={0} File={1} Subject={2}\{3}" -f (Get-EventMapValue -Map $m -Key 'ServiceName'), (Get-EventMapValue -Map $m -Key 'ServiceFileName'), (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName')
        }
        4698 {
          $summary = "Scheduled task created TaskName={0} Subject={1}\{2}" -f (Get-EventMapValue -Map $m -Key 'TaskName'), (Get-EventMapValue -Map $m -Key 'SubjectDomainName'), (Get-EventMapValue -Map $m -Key 'SubjectUserName')
        }
        default {
          $summary = ($ev.Message -replace "`r", "" -replace "`n", " ")
        }
      }

      [void]$lines.Add(("[{0}] Id={1} {2}" -f $ev.TimeCreated.ToString("o"), $ev.Id, $summary.Trim()))
    }

    return ($lines -join [Environment]::NewLine)
  } catch {
    $msg = $_.Exception.Message
    if ($msg -match 'No events were found') {
      $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
      Add-CollectorNote "No high-signal Security events were found in the selected window."
      $lines = New-Object System.Collections.ArrayList
      [void]$lines.Add("SECURITY_HIGH_SIGNAL_SUMMARY")
      foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel 'Security' -Ids $ids -Take $Take)) { [void]$lines.Add($metadataLine) }
      [void]$lines.Add("RAW_EVENT_COUNT=0")
      [void]$lines.Add("INTERESTING_EVENT_COUNT=0")
      [void]$lines.Add("SUPPRESSED_EVENT_COUNT=0")
      [void]$lines.Add("")
      [void]$lines.Add("No high-signal Security events were found in the selected window.")
      return ($lines -join [Environment]::NewLine)
    }
    Add-CollectorError "Failed to collect condensed Security summary: $msg"
    return "ERROR collecting condensed Security summary: $msg"
  }
}

<#
.SYNOPSIS
Exports event-log text for the requested channel and window.

.DESCRIPTION
Resolves the effective event window, queries the requested channel with optional event
IDs, and renders the result into analyst-facing text with explicit window metadata.

.FUNCTION NAME
Get-EventText

.INPUTS
Channel string, WindowHours integer, optional integer event IDs, and Take integer.

.OUTPUTS
String containing event-log text or an explicit nothing-found/error message.
#>
function Get-EventText {
  param(
    [Parameter(Mandatory=$true)][string]$Channel,
    [int]$WindowHours = 24,
    [int[]]$Ids,
    [int]$Take = 500
  )

  try {
    $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
    $fh = Get-CollectorEventFilterHashtable -LogName $Channel -Window $window -Ids $Ids

    $events = Get-WinEvent -FilterHashtable $fh -ErrorAction Stop |
      Sort-Object TimeCreated -Descending |
      Select-Object -First $Take

    if (@($events).Count -eq 0) {
      Add-CollectorNote ("No events were found for channel [{0}] in the selected window." -f $Channel)
      $lines = New-Object System.Collections.ArrayList
      foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel $Channel -Ids $Ids -Take $Take)) { [void]$lines.Add($metadataLine) }
      [void]$lines.Add("EVENT_COUNT=0")
      [void]$lines.Add("")
      [void]$lines.Add(("No events were found for channel [{0}] in the selected window." -f $Channel))
      return ($lines -join [Environment]::NewLine)
    }

    $lines = New-Object System.Collections.ArrayList
    foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel $Channel -Ids $Ids -Take $Take)) { [void]$lines.Add($metadataLine) }
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
      $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
      $lines = New-Object System.Collections.ArrayList
      foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel $Channel -Ids $Ids -Take $Take)) { [void]$lines.Add($metadataLine) }
      [void]$lines.Add("EVENT_COUNT=0")
      [void]$lines.Add("")
      [void]$lines.Add(("No events were found for channel [{0}] in the selected window." -f $Channel))
      return ($lines -join [Environment]::NewLine)
    }
    Add-CollectorError "Failed to collect event log text for [$Channel]: $msg"
    return "ERROR collecting event log text for [$Channel]: $msg"
  }
}

<#
.SYNOPSIS
Exports a filtered EVTX file for the requested channel and window.

.DESCRIPTION
Builds the effective time filter and optional Event ID filter, renders the matching
XPath query, calls wevtutil.exe to export the EVTX file, and verifies that the output
file was created.

.FUNCTION NAME
Export-FilteredEvtx

.INPUTS
LogChannel string, WindowHours integer, optional event IDs, output path, and scratch
directory path.

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

  $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
  if ($window.HasExplicitWindow -and $window.EndTime) {
    $startUtc = $window.StartTime.ToUniversalTime().ToString("o")
    $endUtc = $window.EndTime.ToUniversalTime().ToString("o")
    $systemParts = @("TimeCreated[@SystemTime>='$startUtc' and @SystemTime<='$endUtc']")
  } else {
    $ms = [math]::Abs($window.EffectiveHours) * 3600000
    $systemParts = @("TimeCreated[timediff(@SystemTime) <= $ms]")
  }

  if ($Ids -and @($Ids).Count -gt 0) {
    $idExpr = "(" + (($Ids | ForEach-Object { "EventID=$_"}) -join " or ") + ")"
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
# END DCOIR_Collector.04C_Explicit_Event_Window_Overrides.ps1

# BEGIN DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1
<#
.SYNOPSIS
DCOIR collector bounded parallel runtime helpers.

.DESCRIPTION
Implements the bounded Windows PowerShell 5.1-safe parallel baseline runtime, including
worker definitions, cache initialization, overlap proof generation, and serial fallback
behavior for steps that are not safely satisfied by worker output.

.FILE NAME
DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1

.INPUTS
Collector state hashtable, baseline worker definitions, command strings, step names,
and allowed exit-code lists.

.OUTPUTS
Worker proof artifacts, cached command output text, collector notes/errors, and serial
or cached command text returned to the caller.
#>

$Global:ParallelBaselineCommandCache = @{}
$Global:ParallelBaselineWorkerArtifacts = New-Object System.Collections.ArrayList
$Global:ParallelExecutionProofPath = $null

<#
.SYNOPSIS
Resets all bounded parallel runtime caches and proof paths.

.DESCRIPTION
Clears the worker command cache, worker artifact list, and proof path so a collect run
starts with a clean bounded-parallel-runtime state.

.FUNCTION NAME
Reset-ParallelBaselineCache

.INPUTS
No direct parameters.

.OUTPUTS
No direct output. Resets global parallel-runtime state.
#>
function Reset-ParallelBaselineCache {
  $Global:ParallelBaselineCommandCache = @{}
  $Global:ParallelBaselineWorkerArtifacts = New-Object System.Collections.ArrayList
  $Global:ParallelExecutionProofPath = $null
}

<#
.SYNOPSIS
Runs one command serially and returns its combined text output.

.DESCRIPTION
Calls the standard cmd capture helper for a single step and returns the combined stdout,
stderr, command, and exit-code text surface.

.FUNCTION NAME
Get-SerialCmdText

.INPUTS
Command string, StepName string, and optional allowed exit-code list.

.OUTPUTS
String containing the combined captured process output.
#>
function Get-SerialCmdText {
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
Returns the bounded parallel baseline worker definitions.

.DESCRIPTION
Defines the small, read-only worker groups that can run in parallel during collect mode,
including their step names, command strings, and allowed exit codes.

.FUNCTION NAME
Get-ParallelBaselineWorkerDefinitions

.INPUTS
No direct parameters.

.OUTPUTS
Array of ordered worker-definition hashtables.
#>
function Get-ParallelBaselineWorkerDefinitions {
  return @(
    [ordered]@{
      Name = 'host_baseline'
      Steps = @(
        [ordered]@{ StepName = 'HOST_DATE_TIME_HOSTNAME'; Command = 'date /t & time /t & hostname & ver'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'HOST_SYSTEMINFO'; Command = 'systeminfo'; AllowedExitCodes = @(0) }
      )
    },
    [ordered]@{
      Name = 'identity_context'
      Steps = @(
        [ordered]@{ StepName = 'IDENTITY_WHOAMI_ALL'; Command = 'whoami /all'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'IDENTITY_QUERY_USER_QWINSTA'; Command = 'query user & qwinsta'; AllowedExitCodes = @(0,1) }
      )
    },
    [ordered]@{
      Name = 'network_light'
      Steps = @(
        [ordered]@{ StepName = 'NETWORK_IPCONFIG'; Command = 'ipconfig /all'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'NETWORK_DNS_CACHE'; Command = 'ipconfig /displaydns'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'NETWORK_ROUTE_PRINT'; Command = 'route print'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'NETWORK_ARP_A'; Command = 'arp -a'; AllowedExitCodes = @(0) }
      )
    },
    [ordered]@{
      Name = 'security_posture'
      Steps = @(
        [ordered]@{ StepName = 'SECURITY_FIREWALL_PROFILES'; Command = 'netsh advfirewall show allprofiles'; AllowedExitCodes = @(0) }
      )
    }
  )
}

<#
.SYNOPSIS
Initializes the bounded parallel baseline runtime for a collect run.

.DESCRIPTION
Resets the global cache, starts the bounded worker jobs during collect mode, harvests
successful worker output into the cache, writes the overlap-proof artifact, records
fallback notes for unsuccessful worker steps, and cleans up the background jobs.

.FUNCTION NAME
Initialize-ParallelBaselineCache

.INPUTS
Collector state hashtable used to locate the artifacts directory and store the proof
artifact path.

.OUTPUTS
No direct return value. Updates global cache state, proof artifacts, and collector
notes/errors.
#>
function Initialize-ParallelBaselineCache {
  param([hashtable]$State)

  Reset-ParallelBaselineCache

  if ($Mode -ne 'Collect') { return }

  $workerDefinitions = @(Get-ParallelBaselineWorkerDefinitions)
  if (@($workerDefinitions).Count -lt 2) {
    Add-CollectorNote 'Parallel baseline runtime definitions were insufficient; collector will remain serial for this run.'
    return
  }

  $workerDir = Join-Path $State.ArtifactsDir 'parallel_workers'
  Ensure-Directory -Path $workerDir

  $workerScript = {
    param([hashtable]$WorkerDefinition,[string]$ParallelWorkerDir)

    <#
    .SYNOPSIS
    Captures one bounded-parallel worker step inside the background job.

    .DESCRIPTION
    Starts cmd.exe for the provided worker step definition, captures stdout and stderr,
    evaluates the exit code against the step's allowed list, and returns the normalized
    step-result object that is later written into the worker proof artifact.

    .FUNCTION NAME
    Invoke-WorkerCommandCapture

    .INPUTS
    StepDefinition hashtable containing StepName, Command, and AllowedExitCodes.

    .OUTPUTS
    Ordered hashtable describing the captured step output, exit code, allowed-exit-code
    evaluation, and combined text surface.
    #>
    function Invoke-WorkerCommandCapture {
      param([hashtable]$StepDefinition)

      $psi = New-Object System.Diagnostics.ProcessStartInfo
      $psi.FileName = 'cmd.exe'
      $psi.Arguments = ('/c ' + [string]$StepDefinition.Command)
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

      $allowed = @($StepDefinition.AllowedExitCodes)
      if (@($allowed).Count -eq 0) { $allowed = @(0) }
      $withinAllowed = (@($allowed) -contains [int]$proc.ExitCode)

      $lines = New-Object System.Collections.ArrayList
      [void]$lines.Add(('COMMAND={0}' -f [string]$StepDefinition.Command))
      [void]$lines.Add(('EXIT_CODE={0}' -f [int]$proc.ExitCode))
      [void]$lines.Add('')
      [void]$lines.Add('STDOUT:')
      [void]$lines.Add($stdout)
      [void]$lines.Add('')
      [void]$lines.Add('STDERR:')
      [void]$lines.Add($stderr)

      return [ordered]@{
        step_name = [string]$StepDefinition.StepName
        command = [string]$StepDefinition.Command
        exit_code = [int]$proc.ExitCode
        allowed_exit_codes = @($allowed)
        within_allowed_exit_codes = [bool]$withinAllowed
        text = ($lines -join [Environment]::NewLine)
      }
    }

    $started = Get-Date
    $stepResults = New-Object System.Collections.ArrayList
    foreach ($stepDefinition in @($WorkerDefinition.Steps)) {
      [void]$stepResults.Add((Invoke-WorkerCommandCapture -StepDefinition $stepDefinition))
    }
    $ended = Get-Date

    $status = 'OK'
    if (@($stepResults | Where-Object { -not $_.within_allowed_exit_codes }).Count -gt 0) {
      $status = 'PARTIAL_SUCCESS'
    }

    $workerResult = [ordered]@{
      worker_name = [string]$WorkerDefinition.Name
      status = $status
      start_time_utc = $started.ToUniversalTime().ToString('o')
      end_time_utc = $ended.ToUniversalTime().ToString('o')
      duration_ms = [int][Math]::Round(($ended - $started).TotalMilliseconds)
      worker_pid = $PID
      step_results = @($stepResults)
    }

    $resultPath = Join-Path $ParallelWorkerDir ('parallel_worker_{0}.json.txt' -f [string]$WorkerDefinition.Name)
    Set-Content -Path $resultPath -Value (($workerResult | ConvertTo-Json -Depth 10) + [Environment]::NewLine) -Encoding UTF8
    return $resultPath
  }

  $jobs = @()
  try {
    foreach ($definition in $workerDefinitions) {
      $jobs += Start-Job -Name ('DCOIR_{0}' -f $definition.Name) -ScriptBlock $workerScript -ArgumentList $definition, $workerDir
    }

    if (@($jobs).Count -eq 0) {
      Add-CollectorNote 'Parallel baseline runtime could not start any workers; collector will remain serial for this run.'
      return
    }

    Wait-Job -Job $jobs | Out-Null

    $workerObjects = New-Object System.Collections.ArrayList
    foreach ($job in @($jobs)) {
      try {
        $jobOutput = @(Receive-Job -Job $job -ErrorAction Stop)
        foreach ($resultPath in $jobOutput) {
          if (-not [string]::IsNullOrWhiteSpace([string]$resultPath) -and (Test-Path -LiteralPath $resultPath)) {
            [void]$Global:ParallelBaselineWorkerArtifacts.Add([string]$resultPath)
            $workerObject = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
            [void]$workerObjects.Add($workerObject)
            foreach ($stepResult in @($workerObject.step_results)) {
              if ($stepResult.within_allowed_exit_codes) {
                $Global:ParallelBaselineCommandCache[[string]$stepResult.step_name] = [string]$stepResult.text
              } else {
                Add-CollectorNote ('Parallel worker [{0}] captured step [{1}] with exit code [{2}]; that step will fall back to serial execution when needed.' -f $workerObject.worker_name, $stepResult.step_name, $stepResult.exit_code)
              }
            }
          }
        }
      } catch {
        Add-CollectorError ('Parallel baseline worker job [{0}] failed: {1}' -f $job.Name, $_.Exception.Message)
      }
    }

    $workerResults = @($workerObjects | Sort-Object start_time_utc, worker_name)
    $overlaps = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt @($workerResults).Count; $i++) {
      for ($j = $i + 1; $j -lt @($workerResults).Count; $j++) {
        $left = $workerResults[$i]
        $right = $workerResults[$j]
        $leftStart = [datetime]::Parse([string]$left.start_time_utc)
        $leftEnd = [datetime]::Parse([string]$left.end_time_utc)
        $rightStart = [datetime]::Parse([string]$right.start_time_utc)
        $rightEnd = [datetime]::Parse([string]$right.end_time_utc)
        if (($leftStart -lt $rightEnd) -and ($rightStart -lt $leftEnd)) {
          [void]$overlaps.Add([ordered]@{
            left_worker = [string]$left.worker_name
            right_worker = [string]$right.worker_name
            left_start_utc = [string]$left.start_time_utc
            left_end_utc = [string]$left.end_time_utc
            right_start_utc = [string]$right.start_time_utc
            right_end_utc = [string]$right.end_time_utc
          })
        }
      }
    }

    $proofStatus = if (@($workerResults).Count -ge 2 -and @($overlaps).Count -gt 0) { 'OVERLAP_CONFIRMED' } else { 'NO_OVERLAP_OBSERVED' }
    $proofObject = [ordered]@{
      proof_status = $proofStatus
      implementation_mode = 'bounded_parallel_jobs'
      deterministic_post_processing = 'Parent waits for all parallel worker jobs before baseline report assembly continues.'
      worker_count = @($workerResults).Count
      cached_step_count = @($Global:ParallelBaselineCommandCache.Keys).Count
      worker_artifact_paths = @($Global:ParallelBaselineWorkerArtifacts)
      worker_results = $workerResults
      overlapping_pairs = @($overlaps)
    }

    $proofPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'PARALLEL_EXECUTION' -Name 'parallel_execution_proof.json.txt' -Text (Convert-ToSafeJsonText -InputObject $proofObject)
    $Global:ParallelExecutionProofPath = $proofPath
    $State.ParallelExecutionProofPath = $proofPath

    if ($proofStatus -eq 'OVERLAP_CONFIRMED') {
      Add-CollectorNote ('Bounded parallel baseline workers executed with observed overlap across {0} worker pair(s).' -f @($overlaps).Count)
    } else {
      Add-CollectorNote 'Bounded parallel baseline workers ran, but explicit timing overlap was not observed in this run.'
    }
  } catch {
    Add-CollectorError ('Failed to initialize bounded parallel baseline runtime: {0}' -f $_.Exception.Message)
  } finally {
    foreach ($job in @($jobs)) {
      try { Remove-Job -Job $job -Force -ErrorAction SilentlyContinue } catch { }
    }
  }
}

<#
.SYNOPSIS
Returns cached worker output when available or runs the command serially.

.DESCRIPTION
Looks for the requested step name in the bounded parallel baseline command cache and
returns that cached text when present. If no cached result exists, it falls back to the
standard serial command capture path.

.FUNCTION NAME
Get-CmdText

.INPUTS
Command string, StepName string, and optional allowed exit-code list.

.OUTPUTS
String containing cached worker text or combined serial command output.
#>
function Get-CmdText {
  param(
    [string]$Command,
    [string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )

  if ($Global:ParallelBaselineCommandCache -and $StepName -and $Global:ParallelBaselineCommandCache.ContainsKey($StepName)) {
    return [string]$Global:ParallelBaselineCommandCache[$StepName]
  }

  return (Get-SerialCmdText -Command $Command -StepName $StepName -AllowedExitCodes $AllowedExitCodes)
}
# END DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1

# BEGIN DCOIR_Collector.04E_Diagnostic_Context_Overrides.ps1
<#
.SYNOPSIS
DCOIR collector diagnostic-context override helpers.

.DESCRIPTION
Provides the elevated-context checks and diagnostic-friendly Security/event-log readers
used to classify audit-policy access, explain non-elevated Security visibility limits,
and emit Security text surfaces that preserve explicit-window behavior.

.FILE NAME
DCOIR_Collector.04E_Diagnostic_Context_Overrides.ps1

.INPUTS
Current process security context, WindowHours values, explicit event-window globals,
channel names, optional event IDs, and Security high-signal summary settings.

.OUTPUTS
Boolean elevation state, diagnostic message text, audit-policy text, Security summary
text, and general event-log text.
#>

<#
.SYNOPSIS
Determines whether the current collector context is elevated.

.DESCRIPTION
Queries the current Windows identity and returns true when the current principal is in
the local Administrators role. Returns false on any lookup error.

.FUNCTION NAME
Test-DiagnosticCollectorIsElevated

.INPUTS
No direct parameters.

.OUTPUTS
Boolean indicating whether the current collector context is elevated.
#>
function Test-DiagnosticCollectorIsElevated {
  try {
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch {
    return $false
  }
}

<#
.SYNOPSIS
Returns the standard non-elevated Security visibility explanation.

.DESCRIPTION
Provides one durable message used when Security-event queries return no visible results
in a non-elevated context and the operator should verify the same query from an elevated
shell before concluding the window is truly empty.

.FUNCTION NAME
Get-NonElevatedSecurityVisibilityMessage

.INPUTS
No direct parameters.

.OUTPUTS
String containing the standard non-elevated Security visibility message.
#>
function Get-NonElevatedSecurityVisibilityMessage {
  return 'Security event query returned no matching events in the current non-elevated collection context. Verify the same query in an elevated shell before concluding the window is empty.'
}

<#
.SYNOPSIS
Collects audit-policy text and classifies audit-policy access status.

.DESCRIPTION
Queries the key Security audit subcategories, captures their output, and classifies the
current audit-policy access state as OK, privilege-required in a non-elevated context,
or failed-other for incomplete capture paths.

.FUNCTION NAME
Get-SecurityAuditPolicyText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the combined per-subcategory auditpol command output.
#>
function Get-SecurityAuditPolicyText {
  $subcategories = @('Logon','Logoff','Special Logon','Process Creation')
  $blocks = New-Object System.Collections.ArrayList
  $exitCodes = New-Object System.Collections.ArrayList
  $isElevated = Test-DiagnosticCollectorIsElevated

  foreach ($subcategory in $subcategories) {
    $stepName = ('SECURITY_AUDIT_POLICY_{0}' -f ($subcategory -replace '[^A-Za-z0-9]', '_').ToUpperInvariant())
    $result = Invoke-ProcessCapture -FilePath 'auditpol.exe' -Arguments @('/get', ('/subcategory:{0}' -f $subcategory)) -StepName $stepName -AllowedExitCodes @(0,1314)
    [void]$blocks.Add((Get-CombinedProcessOutput -Result $result))
    [void]$exitCodes.Add([int]$result.ExitCode)
  }

  $allOk = (@($exitCodes).Count -gt 0) -and (@($exitCodes | Where-Object { $_ -ne 0 }).Count -eq 0)
  $allPrivilegeRequired = (@($exitCodes).Count -gt 0) -and (@($exitCodes | Where-Object { $_ -ne 1314 }).Count -eq 0)

  if ($allOk) {
    $script:CollectorAuditPolicyAccessStatus = 'OK'
  } elseif ((-not $isElevated) -and $allPrivilegeRequired) {
    $script:CollectorAuditPolicyAccessStatus = 'PRIVILEGE_REQUIRED_NON_ELEVATED'
    Add-CollectorNote 'Security audit policy access requires elevation in the current non-elevated execution context. Review the recorded auditpol output and re-run from an elevated shell only if that deeper visibility is required.'
  } else {
    $script:CollectorAuditPolicyAccessStatus = 'FAILED_OTHER'
    Add-CollectorError 'Security audit policy capture is incomplete for a reason other than the expected non-elevated privilege boundary. Review the per-subcategory auditpol command outputs in the artifact.'
  }

  return ($blocks -join ([Environment]::NewLine + [Environment]::NewLine))
}

<#
.SYNOPSIS
Builds a diagnostic-friendly Security high-signal summary.

.DESCRIPTION
Uses the effective event window to query key Security events, suppresses routine
service/machine noise and routine Microsoft-managed task/service churn, and returns
analyst-facing summary text while preserving the special non-elevated visibility
message when appropriate.

.FUNCTION NAME
Get-SecurityHighSignalSummaryText

.INPUTS
WindowHours integer and Take integer limiting the returned summary volume.

.OUTPUTS
String containing the Security high-signal summary or an explicit visibility/error
message.
#>
function Get-SecurityHighSignalSummaryText {
  param(
    [int]$WindowHours = 24,
    [int]$Take = 200
  )

  try {
    $ids = @(4624,4625,4648,4672,4688,4697,4698)
    $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
    $fh = @{
      LogName = 'Security'
      StartTime = $window.StartTime
      Id = $ids
    }
    if ($window.HasExplicitWindow -and $window.EndTime) {
      $fh.EndTime = $window.EndTime
    }

    $events = @(Get-WinEvent -FilterHashtable $fh -ErrorAction Stop |
      Sort-Object TimeCreated -Descending |
      Select-Object -First ($Take * 4))

    if (@($events).Count -eq 0) {
      $lines = New-Object System.Collections.ArrayList
      [void]$lines.Add('SECURITY_HIGH_SIGNAL_SUMMARY')
      foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel 'Security' -Ids $ids -Take $Take)) { [void]$lines.Add($metadataLine) }
      [void]$lines.Add('RAW_EVENT_COUNT=0')
      [void]$lines.Add('INTERESTING_EVENT_COUNT=0')
      [void]$lines.Add('SUPPRESSED_EVENT_COUNT=0')
      [void]$lines.Add('')
      if (-not (Test-DiagnosticCollectorIsElevated)) {
        $message = Get-NonElevatedSecurityVisibilityMessage
        Add-CollectorNote $message
        [void]$lines.Add($message)
        return ($lines -join [Environment]::NewLine)
      }
      $message = 'No high-signal Security events were found in the selected window.'
      Add-CollectorNote $message
      [void]$lines.Add($message)
      return ($lines -join [Environment]::NewLine)
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
      $taskName = Get-EventMapValue -Map $m -Key 'TaskName'
      $serviceName = Get-EventMapValue -Map $m -Key 'ServiceName'
      $serviceFileName = Get-EventMapValue -Map $m -Key 'ServiceFileName'

      $subjectIsMachine = ($subjectUser -like '*$')
      $targetIsMachine = ($targetUser -like '*$')
      $subjectIsBuiltinService = $subjectUser -in @('SYSTEM','LOCAL SERVICE','NETWORK SERVICE','ANONYMOUS LOGON')
      $targetIsBuiltinService = $targetUser -in @('SYSTEM','LOCAL SERVICE','NETWORK SERVICE','ANONYMOUS LOGON')
      $isServiceStyleLogon = $logonType -in @('0','5')
      $taskIsMicrosoftManaged = $taskName -like '\Microsoft\Windows\*'
      $taskIsKnownRoutineEnvironmentChurn = $taskName -match '(?i)^\\(UptimeCheck|UptimePopup|Deploy_Sysmon_Production|Cleanup Old PS Transcripts)$'
      $serviceFileIsWindowsManaged = $serviceFileName -match '^(?i)(%systemroot%|[A-Z]:\\Windows\\)'
      $serviceHostStyle = ($serviceFileName -match '(?i)\\svchost\.exe(\s|$)') -or ($serviceFileName -match '(?i)\\services\.exe(\s|$)')
      $serviceNameLooksPerUser = $serviceName -match '(?i)^(CDPUserSvc|OneSyncSvc|UnistoreSvc|UserDataSvc|WpnUserService|BcastDVRUserService|PimIndexMaintenanceSvc|PrintWorkflowUserSvc|UdkUserSvc|CaptureService|ConsentUxUserSvc|CredentialEnrollmentManagerUserSvc|DevicePickerUserSvc|DevicesFlowUserSvc)(_[0-9a-f]+)?$'

      $suppress = $false
      $suppressReason = $null

      switch ([int]$ev.Id) {
        4624 {
          if (($subjectIsMachine -or $targetIsMachine -or $subjectIsBuiltinService -or $targetIsBuiltinService) -and $isServiceStyleLogon) {
            $suppress = $true
            $suppressReason = 'routine successful service or machine logon'
          }
        }
        4672 {
          if ($subjectIsMachine -or $subjectIsBuiltinService) {
            $suppress = $true
            $suppressReason = 'routine special privileges assignment for service or machine account'
          }
        }
        4697 {
          if (($subjectIsMachine -or $subjectIsBuiltinService) -and $serviceFileIsWindowsManaged -and ($serviceHostStyle -or $serviceNameLooksPerUser)) {
            $suppress = $true
            $suppressReason = 'routine Windows-managed service registration or update'
          }
        }
        4698 {
          if (($subjectIsMachine -or $subjectIsBuiltinService) -and ($taskIsMicrosoftManaged -or $taskIsKnownRoutineEnvironmentChurn)) {
            $suppress = $true
            if ($taskIsMicrosoftManaged) {
              $suppressReason = 'routine Microsoft-managed scheduled task registration or update'
            } else {
              $suppressReason = 'routine environment-managed scheduled task registration or update'
            }
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
    [void]$lines.Add('SECURITY_HIGH_SIGNAL_SUMMARY')
    foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel 'Security' -Ids $ids -Take $Take)) { [void]$lines.Add($metadataLine) }
    [void]$lines.Add(("RAW_EVENT_COUNT={0}" -f @($events).Count))
    [void]$lines.Add(("INTERESTING_EVENT_COUNT={0}" -f @($interesting).Count))
    [void]$lines.Add(("SUPPRESSED_EVENT_COUNT={0}" -f @($suppressed).Count))
    [void]$lines.Add('')

    $counts = $interesting | Group-Object { $_.EventRecord.Id } | Sort-Object Name
    [void]$lines.Add('INTERESTING_EVENT_COUNTS')
    if (@($counts).Count -eq 0) {
      [void]$lines.Add('Id=NONE Count=0')
    } else {
      foreach ($g in $counts) {
        [void]$lines.Add(("Id={0} Count={1}" -f $g.Name, $g.Count))
      }
    }

    if (@($suppressed).Count -gt 0) {
      [void]$lines.Add('')
      [void]$lines.Add('SUPPRESSED_EVENT_COUNTS')
      $suppressedCounts = $suppressed | Group-Object Id, Reason | Sort-Object Name
      foreach ($g in $suppressedCounts) {
        [void]$lines.Add(("{0} Count={1}" -f $g.Name, $g.Count))
      }
    }

    if (@($interesting).Count -eq 0) {
      [void]$lines.Add('')
      [void]$lines.Add('EVENT_SUMMARY')
      [void]$lines.Add('No analyst-facing high-signal Security events remained after routine Microsoft-managed task/service suppression in the selected window.')
      return ($lines -join [Environment]::NewLine)
    }

    [void]$lines.Add('')
    [void]$lines.Add('EVENT_SUMMARY')

    foreach ($item in $interesting) {
      $ev = $item.EventRecord
      $m = $item.EventData
      $summary = ''
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
          $summary = ($ev.Message -replace "`r", '' -replace "`n", ' ')
        }
      }

      [void]$lines.Add(("[{0}] Id={1} {2}" -f $ev.TimeCreated.ToString('o'), $ev.Id, $summary.Trim()))
    }

    return ($lines -join [Environment]::NewLine)
  } catch {
    $msg = $_.Exception.Message
    if ($msg -match 'No events were found') {
      $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
      $lines = New-Object System.Collections.ArrayList
      [void]$lines.Add('SECURITY_HIGH_SIGNAL_SUMMARY')
      foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel 'Security' -Ids $ids -Take $Take)) { [void]$lines.Add($metadataLine) }
      [void]$lines.Add('RAW_EVENT_COUNT=0')
      [void]$lines.Add('INTERESTING_EVENT_COUNT=0')
      [void]$lines.Add('SUPPRESSED_EVENT_COUNT=0')
      [void]$lines.Add('')
      if (-not (Test-DiagnosticCollectorIsElevated)) {
        $message = Get-NonElevatedSecurityVisibilityMessage
        Add-CollectorNote $message
        [void]$lines.Add($message)
        return ($lines -join [Environment]::NewLine)
      }
      $message = 'No high-signal Security events were found in the selected window.'
      Add-CollectorNote $message
      [void]$lines.Add($message)
      return ($lines -join [Environment]::NewLine)
    }
    Add-CollectorError ("Failed to collect condensed Security summary: {0}" -f $msg)
    return ("ERROR collecting condensed Security summary: {0}" -f $msg)
  }
}

<#
.SYNOPSIS
Exports diagnostic-friendly event-log text for the requested channel.

.DESCRIPTION
Uses the effective event window to query the requested channel with optional event IDs,
returns analyst-facing text for the matching events, and preserves the special
non-elevated Security visibility explanation when appropriate.

.FUNCTION NAME
Get-EventText

.INPUTS
Channel string, WindowHours integer, optional integer event IDs, and Take integer.

.OUTPUTS
String containing event-log text or an explicit visibility/error message.
#>
function Get-EventText {
  param(
    [Parameter(Mandatory=$true)][string]$Channel,
    [int]$WindowHours = 24,
    [int[]]$Ids,
    [int]$Take = 500
  )

  try {
    $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
    $fh = @{
      LogName = $Channel
      StartTime = $window.StartTime
    }
    if ($window.HasExplicitWindow -and $window.EndTime) {
      $fh.EndTime = $window.EndTime
    }
    if ($Ids -and @($Ids).Count -gt 0) { $fh.Id = $Ids }

    $events = Get-WinEvent -FilterHashtable $fh -ErrorAction Stop |
      Sort-Object TimeCreated -Descending |
      Select-Object -First $Take

    if (@($events).Count -eq 0) {
      $lines = New-Object System.Collections.ArrayList
      foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel $Channel -Ids $Ids -Take $Take)) { [void]$lines.Add($metadataLine) }
      [void]$lines.Add('EVENT_COUNT=0')
      [void]$lines.Add('')
      if (($Channel -eq 'Security') -and (-not (Test-DiagnosticCollectorIsElevated))) {
        $message = Get-NonElevatedSecurityVisibilityMessage
        Add-CollectorNote $message
        [void]$lines.Add($message)
        return ($lines -join [Environment]::NewLine)
      }
      $message = ("No events were found for channel [{0}] in the selected window." -f $Channel)
      Add-CollectorNote $message
      [void]$lines.Add($message)
      return ($lines -join [Environment]::NewLine)
    }

    $lines = New-Object System.Collections.ArrayList
    foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel $Channel -Ids $Ids -Take $Take)) { [void]$lines.Add($metadataLine) }
    [void]$lines.Add(("EVENT_COUNT={0}" -f @($events).Count))
    [void]$lines.Add('')

    foreach ($ev in $events) {
      [void]$lines.Add(("TimeCreated={0}" -f $ev.TimeCreated.ToString('o')))
      [void]$lines.Add(("Id={0}" -f $ev.Id))
      [void]$lines.Add(("Provider={0}" -f $ev.ProviderName))
      [void]$lines.Add(("Level={0}" -f $ev.LevelDisplayName))
      [void]$lines.Add(("RecordId={0}" -f $ev.RecordId))
      [void]$lines.Add(("MachineName={0}" -f $ev.MachineName))
      if ($ev.TaskDisplayName) { [void]$lines.Add(("Task={0}" -f $ev.TaskDisplayName)) }
      if ($ev.UserId) { [void]$lines.Add(("UserId={0}" -f $ev.UserId.Value)) }
      [void]$lines.Add('Message:')
      [void]$lines.Add(($ev.Message -replace "`r", ''))
      [void]$lines.Add('-' * 60)
    }

    return ($lines -join [Environment]::NewLine)
  } catch {
    $msg = $_.Exception.Message
    if ($msg -match 'No events were found') {
      $window = Get-CollectorEffectiveEventWindow -WindowHours $WindowHours
      $lines = New-Object System.Collections.ArrayList
      foreach ($metadataLine in (Get-CollectorEventWindowMetadataLines -Window $window -Channel $Channel -Ids $Ids -Take $Take)) { [void]$lines.Add($metadataLine) }
      [void]$lines.Add('EVENT_COUNT=0')
      [void]$lines.Add('')
      if (($Channel -eq 'Security') -and (-not (Test-DiagnosticCollectorIsElevated))) {
        $message = Get-NonElevatedSecurityVisibilityMessage
        Add-CollectorNote $message
        [void]$lines.Add($message)
        return ($lines -join [Environment]::NewLine)
      }
      $message = ("No events were found for channel [{0}] in the selected window." -f $Channel)
      Add-CollectorNote $message
      [void]$lines.Add($message)
      return ($lines -join [Environment]::NewLine)
    }
    Add-CollectorError (("Failed to collect event log text for [{0}]: {1}" -f $Channel, $msg))
    return (("ERROR collecting event log text for [{0}]: {1}" -f $Channel, $msg))
  }
}
# END DCOIR_Collector.04E_Diagnostic_Context_Overrides.ps1

# BEGIN DCOIR_Collector.04F_PR186_Review_Fixes.ps1
<#
.SYNOPSIS
DCOIR collector PR #186 review-fix overrides.

.DESCRIPTION
Applies narrowly scoped helper overrides for PR #186 review findings before the main
collector entrypoint runs. Keeps custom run-id discovery compatible with collector-created
run roots, normalizes invalid explicit-window state across downstream scope surfaces, and
gates synthetic validation padding behind an explicit harness test-mode flag.

.FILE NAME
DCOIR_Collector.04F_PR186_Review_Fixes.ps1

.INPUTS
Current collector globals, process environment variables, run-root directory names, and
state hashtables.

.OUTPUTS
Replacement helper functions used by the compiled collector runtime.
#>

<#
.SYNOPSIS
Checks whether a directory name matches a collector run-root for the current host.

.DESCRIPTION
Accepts timestamp run IDs and supported custom run IDs produced by Get-RunRoot while
remaining bounded to the current host prefix and a conservative run-id character set.

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
  $hostPrefix = "DCOIR_{0}_" -f [string]$env:COMPUTERNAME
  if (-not $Name.StartsWith($hostPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
  $runIdPart = $Name.Substring($hostPrefix.Length)
  if ([string]::IsNullOrWhiteSpace($runIdPart)) { return $false }
  return [regex]::IsMatch($runIdPart, '^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$')
}

<#
.SYNOPSIS
Checks whether collector validation-only behavior is explicitly enabled.

.DESCRIPTION
Returns true when DCOIR_COLLECTOR_TEST_MODE is set to 1 or when the collector was
spawned by the maintained harness script. Test payload helpers must require this before
mutating runtime artifacts from environment variables.

.FUNCTION NAME
Test-DCOIRCollectorTestModeEnabled

.INPUTS
Process environment variable DCOIR_COLLECTOR_TEST_MODE and parent process command line.

.OUTPUTS
Boolean.
#>
function Test-DCOIRCollectorTestModeEnabled {
  if ([Environment]::GetEnvironmentVariable('DCOIR_COLLECTOR_TEST_MODE', 'Process') -eq '1') { return $true }
  try {
    $current = Get-CimInstance Win32_Process -Filter ("ProcessId = {0}" -f $PID) -ErrorAction Stop
    if ($current -and $current.ParentProcessId) {
      $parent = Get-CimInstance Win32_Process -Filter ("ProcessId = {0}" -f $current.ParentProcessId) -ErrorAction Stop
      if ($parent.CommandLine -match 'run_DCOIR_Tests\.ps1') { return $true }
    }
  } catch {
    return $false
  }
  return $false
}

<#
.SYNOPSIS
Resolves the effective event window for the current collector call.

.DESCRIPTION
Combines WindowHours with explicit WindowStart and WindowEnd inputs. Invalid or inverted
explicit bounds clear the script-level raw window values so later targeted scope and plan
surfaces cannot reuse rejected values after event readers have fallen back.

.FUNCTION NAME
Get-CollectorEffectiveEventWindow

.INPUTS
WindowHours integer plus WindowStart and WindowEnd globals.

.OUTPUTS
Hashtable containing HasExplicitWindow, StartTime, EndTime, and EffectiveHours.
#>
function Get-CollectorEffectiveEventWindow {
  param([int]$WindowHours = 24)

  $effectiveHours = [math]::Abs($WindowHours)
  if ($effectiveHours -le 0) { $effectiveHours = 24 }

  $now = Get-Date
  $parsedStart = $null
  $parsedEnd = $null
  $parseFailed = $false

  if (-not [string]::IsNullOrWhiteSpace($WindowStart)) {
    [datetime]$tmpStart = [datetime]::MinValue
    if ([datetime]::TryParse($WindowStart, [ref]$tmpStart)) {
      $parsedStart = $tmpStart
    } else {
      Add-CollectorError ("Invalid WindowStart value [{0}]; falling back to hour-window behavior." -f $WindowStart)
      $parseFailed = $true
    }
  }

  if (-not [string]::IsNullOrWhiteSpace($WindowEnd)) {
    [datetime]$tmpEnd = [datetime]::MinValue
    if ([datetime]::TryParse($WindowEnd, [ref]$tmpEnd)) {
      $parsedEnd = $tmpEnd
    } else {
      Add-CollectorError ("Invalid WindowEnd value [{0}]; falling back to hour-window behavior." -f $WindowEnd)
      $parseFailed = $true
    }
  }

  if ($parseFailed) {
    $parsedStart = $null
    $parsedEnd = $null
    $script:WindowStart = $null
    $script:WindowEnd = $null
  } elseif ($parsedStart -and $parsedEnd -and $parsedEnd -lt $parsedStart) {
    Add-CollectorError ("WindowEnd [{0}] is earlier than WindowStart [{1}]; falling back to hour-window behavior." -f $WindowEnd, $WindowStart)
    $parsedStart = $null
    $parsedEnd = $null
    $script:WindowStart = $null
    $script:WindowEnd = $null
  }

  if ($parsedStart -and -not $parsedEnd) {
    $parsedEnd = $now
  } elseif ($parsedEnd -and -not $parsedStart) {
    $parsedStart = $parsedEnd.AddHours(-1 * $effectiveHours)
  }

  if ($parsedStart -and $parsedEnd -and $parsedEnd -lt $parsedStart) {
    Add-CollectorError ("Effective WindowEnd [{0}] is earlier than WindowStart [{1}] after partial-window normalization; falling back to hour-window behavior." -f $parsedEnd.ToString('o'), $parsedStart.ToString('o'))
    $parsedStart = $null
    $parsedEnd = $null
    $script:WindowStart = $null
    $script:WindowEnd = $null
  }

  $hasExplicitWindow = ($parsedStart -ne $null) -or ($parsedEnd -ne $null)
  $startTime = if ($parsedStart) { $parsedStart } else { $now.AddHours(-1 * $effectiveHours) }
  $endTime = if ($parsedEnd) { $parsedEnd } else { $null }

  return @{
    HasExplicitWindow = [bool]$hasExplicitWindow
    StartTime = $startTime
    EndTime = $endTime
    EffectiveHours = $effectiveHours
  }
}

<#
.SYNOPSIS
Builds the targeted collection scope object.

.DESCRIPTION
Uses the same effective event-window resolver as event collection metadata so invalid
explicit-window fallback cannot produce contradictory targeted scope output.

.FUNCTION NAME
Get-TargetedCollectionScopeObject

.INPUTS
State hashtable.

.OUTPUTS
Ordered hashtable describing the targeted collection scope.
#>
function Get-TargetedCollectionScopeObject {
  param([hashtable]$State)

  $window = Get-CollectorEffectiveEventWindow -WindowHours $Hours
  $hasWindow = [bool]$window.HasExplicitWindow
  $windowStartText = if ($window.HasExplicitWindow) { $window.StartTime.ToString('o') } else { '' }
  $windowEndText = if ($window.HasExplicitWindow -and $window.EndTime) { $window.EndTime.ToString('o') } else { '' }
  $hasFocus = (-not [string]::IsNullOrWhiteSpace($FocusProcess)) -or (-not [string]::IsNullOrWhiteSpace($FocusPath)) -or (-not [string]::IsNullOrWhiteSpace($FocusIndicator)) -or (-not [string]::IsNullOrWhiteSpace($UserReport))
  $categories = @()
  if ($IncludeArtifactCategory) { $categories = @($IncludeArtifactCategory | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) }

  return [ordered]@{
    targeted_mode_enabled = [bool]$Targeted
    target_profile = $TargetProfile
    has_explicit_time_window = $hasWindow
    window_start = $windowStartText
    window_end = $windowEndText
    requested_hours = $Hours
    included_artifact_categories = $categories
    focus_process = $FocusProcess
    focus_path = $FocusPath
    focus_indicator = $FocusIndicator
    focus_indicator_type = $FocusIndicatorType
    user_report = $UserReport
    has_focus_context = $hasFocus
    implementation_boundary = 'This major-version targeted collection feature currently narrows analyst guidance, collection scope intent, artifact prioritization, and recommended next actions. It does not yet rewrite every baseline collection helper into exact start-end timestamp filtering across all artifact families.'
  }
}

<#
.SYNOPSIS
Reads the synthetic oversized-artifact validation size.

.DESCRIPTION
Returns the requested synthetic oversized artifact size only when collector harness test
mode is explicitly enabled. This prevents stale response-action environment variables
from creating synthetic artifacts in normal collection runs.

.FUNCTION NAME
Get-ValidationSyntheticOversizeArtifactKB

.INPUTS
Process environment variables DCOIR_COLLECTOR_TEST_MODE and DCOIR_TEST_SYNTHETIC_OVERSIZE_ARTIFACT_KB.

.OUTPUTS
Integer requested synthetic artifact size in KB.
#>
function Get-ValidationSyntheticOversizeArtifactKB {
  if (-not (Test-DCOIRCollectorTestModeEnabled)) { return 0 }
  $raw = [Environment]::GetEnvironmentVariable('DCOIR_TEST_SYNTHETIC_OVERSIZE_ARTIFACT_KB', 'Process')
  if ([string]::IsNullOrWhiteSpace($raw)) { return 0 }
  $parsed = 0
  if ([int]::TryParse($raw, [ref]$parsed) -and $parsed -gt 0) { return $parsed }
  return 0
}

<#
.SYNOPSIS
Builds deterministic test padding for a text artifact.

.DESCRIPTION
Returns deterministic chunk-test padding only when collector harness test mode is
explicitly enabled. Normal collection runs ignore stale inherited padding variables.

.FUNCTION NAME
Get-TestTextPaddingFromEnvironment

.INPUTS
Environment variable name plus DCOIR_COLLECTOR_TEST_MODE.

.OUTPUTS
String containing deterministic padding or an empty string.
#>
function Get-TestTextPaddingFromEnvironment {
  param([string]$Name)
  if (-not (Test-DCOIRCollectorTestModeEnabled)) { return '' }
  $raw = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if ([string]::IsNullOrWhiteSpace($raw)) { return '' }
  [int]$requestedKB = 0
  if (-not [int]::TryParse($raw, [ref]$requestedKB) -or $requestedKB -le 0) { return '' }

  $line = 'DCOIR_PRODUCTION_CHUNK_TEST_PAYLOAD|ABCDEFGHIJKLMNOPQRSTUVWXYZ|0123456789|line='
  $sb = New-Object System.Text.StringBuilder
  $index = 0
  while ([System.Text.Encoding]::UTF8.GetByteCount($sb.ToString()) -lt ($requestedKB * 1024)) {
    [void]$sb.AppendLine(('{0}{1:000000}' -f $line, $index))
    $index += 1
  }
  return $sb.ToString()
}

<#
.SYNOPSIS
Formats normalized event-window target details for enrich reports.

.DESCRIPTION
Builds target-details text from the same normalized event-window object used by event
readers so invalid explicit windows do not leave rejected raw bounds in enrich action
metadata.

.FUNCTION NAME
Get-CollectorEventWindowTargetDetails

.INPUTS
LogName string, Hours integer, optional EventIds, and optional MaxEvents.

.OUTPUTS
String suitable for action target-details fields.
#>
function Get-CollectorEventWindowTargetDetails {
  param([string]$LogName,[int]$Hours,[int[]]$Ids,[int]$Take)
  $window = Get-CollectorEffectiveEventWindow -WindowHours $Hours
  $parts = New-Object System.Collections.ArrayList
  [void]$parts.Add(("LogName={0}" -f $LogName))
  [void]$parts.Add(("Hours={0}" -f $Hours))
  if ($window.HasExplicitWindow) {
    [void]$parts.Add(("WindowStart={0}" -f $window.StartTime.ToString('o')))
    if ($window.EndTime) { [void]$parts.Add(("WindowEnd={0}" -f $window.EndTime.ToString('o'))) }
  }
  if ($Ids -and @($Ids).Count -gt 0) { [void]$parts.Add(("EventIds={0}" -f ($Ids -join ','))) }
  if ($Take -gt 0) { [void]$parts.Add(("MaxEvents={0}" -f $Take)) }
  return ($parts -join '; ')
}
# END DCOIR_Collector.04F_PR186_Review_Fixes.ps1

# BEGIN DCOIR_Collector.05_Main_Entry.ps1
Apply-QuickShortcut

if ($ShowVersion) {
  Write-Output (Get-CollectorVersionText)
  return
}

if ($ShowHelp) {
  Write-Output (Get-CollectorHelpText -Topic $script:ContextualHelpTopic)
  return
}

try {
  Ensure-Directory -Path $OutRoot

  switch ($Mode) {
    "Collect" {
      if ([string]::IsNullOrWhiteSpace($RunId)) {
        $RunId = Get-NewRunId
      }

      $resolvedOutRoot = if ([System.IO.Path]::IsPathRooted($OutRoot)) {
        [System.IO.Path]::GetFullPath($OutRoot)
      } else {
        [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutRoot))
      }

      Purge-PreviousRuns -Root $resolvedOutRoot -CurrentPackageName $PackageName
      $dirs = Initialize-RunStructure -Root $resolvedOutRoot -CurrentRunId $RunId
      $Global:CurrentRunId = $RunId
      $Global:ExecutionTxtPath = Join-Path $dirs.LogsDir "collect_execution_log.txt"
      $Global:ExecutionJsonlPath = Join-Path $dirs.LogsDir "collect_execution_log.jsonl"
      $Global:ErrorsLogPath = Join-Path $dirs.LogsDir "errors.log"
      Set-Content -Path $Global:ExecutionTxtPath -Value ("DCOIR Collect Execution Log`r`nRunId={0}" -f $RunId) -Encoding UTF8
      Set-Content -Path $Global:ExecutionJsonlPath -Value "" -Encoding UTF8
      Set-Content -Path $Global:ErrorsLogPath -Value "" -Encoding UTF8

      $packagePath = Move-PackageToOutRoot -Root $resolvedOutRoot -CurrentPackageName $PackageName
      Expand-PackageToTools -PackagePath $packagePath -ToolsDir $dirs.ToolsDir

      $toolMap = Get-ToolMap -ToolsDir $dirs.ToolsDir
      $metadataReportPath = Join-Path $dirs.ReportsDir ("DCOIR_METADATA_{0}_{1}.txt" -f $env:COMPUTERNAME, $RunId)

      $state = @{
        RunId = $RunId
        Host = $env:COMPUTERNAME
        OutRoot = $resolvedOutRoot
        RunRoot = $dirs.RunRoot
        ToolsDir = $dirs.ToolsDir
        ReportsDir = $dirs.ReportsDir
        ArtifactsDir = $dirs.ArtifactsDir
        EnrichSessionsDir = $dirs.EnrichSessionsDir
        LogsDir = $dirs.LogsDir
        BundlesDir = $dirs.BundlesDir
        StatePath = $dirs.StatePath
        PackagePath = $packagePath
        MetadataReportPath = $metadataReportPath
        BaselineReportPath = $null
        UploadSummaryPath = $null
        UploadBudgetManifestPath = $null
        AnalystOverviewPath = $null
        ParallelExecutionProofPath = $null
        ExecutionContextPath = $null
        SecurityAuditPolicyPath = $null
        AuditPolicyAccessStatus = $null
        SecurityFilteredPath = $null
        SecurityHighSignalSummaryPath = $null
        NetstatPidOnlyPath = $null
        NetstatOwnerAwareStatus = $null
        IsElevated = $null
        DefaultGeminiUploadSetStatus = $null
        CollectBundlePath = $null
        CollectionScopePath = $null
        ParallelismAssessmentPath = $null
        TargetedCollectionPlanPath = $null
        SyntheticOversizeSourcePath = $null
        ChunkManifestPath = $null
        UploadSafeChunkManifestPath = $null
        EnrichSessions = @()
        EnrichSessionCounter = 0
        OpenEnrichSessionId = $null
        LastSessionResolutionMode = $null
        CreatedLocal = (Get-Date).ToString("o")
        CreatedUTC = (Get-Date).ToUniversalTime().ToString("o")
        CollectorVersion = $ScriptVersion
      }

      Initialize-ParallelBaselineCache -State $state

      $baseline = New-BaselineReport -State $state -ToolMap $toolMap
      Apply-FeatureWaveCollectEnhancements -State $state -Baseline $baseline

      $metadataText = New-MetadataReport -State $state -ToolMap $toolMap
      Write-ReportFile -Path $metadataReportPath -Text $metadataText

      $uploadArtifacts = New-CollectUploadArtifacts -State $state -Baseline $baseline
      $state.UploadSummaryPath = $uploadArtifacts.UploadSummaryPath
      $state.UploadBudgetManifestPath = $uploadArtifacts.UploadManifestPath
      $state.DefaultGeminiUploadSetStatus = $uploadArtifacts.DefaultSetStatus
      $state.UploadSafeChunkManifestPath = $uploadArtifacts.UploadSafeChunkManifestPath
      $state.AnalystOverviewPath = New-AnalystOverviewArtifact -State $state -Baseline $baseline

      $metadataText = New-MetadataReport -State $state -ToolMap $toolMap
      Write-ReportFile -Path $metadataReportPath -Text $metadataText

      $collectManifest = New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json") -State $state -ModeName "Collect" -TierName $Tier -Files (
        @($metadataReportPath, $state.AnalystOverviewPath, $state.ParallelExecutionProofPath, $state.ExecutionContextPath, $state.SecurityAuditPolicyPath, $state.SecurityFilteredPath, $state.SecurityHighSignalSummaryPath, $state.NetstatPidOnlyPath, $state.UploadSummaryPath, $state.UploadBudgetManifestPath, $state.UploadSafeChunkManifestPath, $state.CollectionScopePath, $state.ParallelismAssessmentPath, $state.TargetedCollectionPlanPath, $Global:ExecutionTxtPath, $Global:ExecutionJsonlPath, $Global:ErrorsLogPath) + $baseline.ArtifactPaths
      ) -ToolMap $toolMap -Extra @{
        collect_bundle = $null
        analyst_overview = $state.AnalystOverviewPath
        parallel_execution_proof = $state.ParallelExecutionProofPath
        execution_context = $state.ExecutionContextPath
        security_audit_policy = $state.SecurityAuditPolicyPath
        audit_policy_access_status = $state.AuditPolicyAccessStatus
        security_filtered = $state.SecurityFilteredPath
        security_high_signal_summary = $state.SecurityHighSignalSummaryPath
        netstat_owner_aware_status = $state.NetstatOwnerAwareStatus
        netstat_pid_only = $state.NetstatPidOnlyPath
        is_elevated = $state.IsElevated
        upload_summary = $state.UploadSummaryPath
        attachment_budget_manifest = $state.UploadBudgetManifestPath
        default_gemini_upload_set_status = $state.DefaultGeminiUploadSetStatus
        collection_scope = $state.CollectionScopePath
        parallelism_assessment = $state.ParallelismAssessmentPath
        targeted_collection_plan = $state.TargetedCollectionPlanPath
        targeted_mode = [bool]$Targeted
        target_profile = $TargetProfile
        synthetic_oversize_source = $state.SyntheticOversizeSourcePath
        chunk_manifest = $state.ChunkManifestPath
        upload_safe_chunk_manifest = $state.UploadSafeChunkManifestPath
      }

      $bundlePath = New-BundleZip -BundlesDir $state.BundlesDir -BundleName ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId) -Paths @(
        $metadataReportPath,
        $state.AnalystOverviewPath,
        $state.ParallelExecutionProofPath,
        $state.ExecutionContextPath,
        $state.SecurityAuditPolicyPath,
        $state.SecurityFilteredPath,
        $state.SecurityHighSignalSummaryPath,
        $state.NetstatPidOnlyPath,
        $state.UploadSummaryPath,
        $state.UploadBudgetManifestPath,
        $state.UploadSafeChunkManifestPath,
        $state.ArtifactsDir,
        $Global:ExecutionTxtPath,
        $Global:ExecutionJsonlPath,
        $Global:ErrorsLogPath,
        $collectManifest
      )

      $state.CollectBundlePath = $bundlePath
      Save-State -State $state

      $metadataText = New-MetadataReport -State $state -ToolMap $toolMap
      Write-ReportFile -Path $metadataReportPath -Text $metadataText
      [void](New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json") -State $state -ModeName "Collect" -TierName $Tier -Files (
        @($metadataReportPath, $state.AnalystOverviewPath, $state.ParallelExecutionProofPath, $state.ExecutionContextPath, $state.SecurityAuditPolicyPath, $state.SecurityFilteredPath, $state.SecurityHighSignalSummaryPath, $state.NetstatPidOnlyPath, $state.UploadSummaryPath, $state.UploadBudgetManifestPath, $state.UploadSafeChunkManifestPath, $state.CollectionScopePath, $state.ParallelismAssessmentPath, $state.TargetedCollectionPlanPath, $Global:ExecutionTxtPath, $Global:ExecutionJsonlPath, $Global:ErrorsLogPath) + $baseline.ArtifactPaths
      ) -ToolMap $toolMap -Extra @{
        collect_bundle = $bundlePath
        analyst_overview = $state.AnalystOverviewPath
        parallel_execution_proof = $state.ParallelExecutionProofPath
        execution_context = $state.ExecutionContextPath
        security_audit_policy = $state.SecurityAuditPolicyPath
        audit_policy_access_status = $state.AuditPolicyAccessStatus
        security_filtered = $state.SecurityFilteredPath
        security_high_signal_summary = $state.SecurityHighSignalSummaryPath
        netstat_owner_aware_status = $state.NetstatOwnerAwareStatus
        netstat_pid_only = $state.NetstatPidOnlyPath
        is_elevated = $state.IsElevated
        upload_summary = $state.UploadSummaryPath
        attachment_budget_manifest = $state.UploadBudgetManifestPath
        default_gemini_upload_set_status = $state.DefaultGeminiUploadSetStatus
        collection_scope = $state.CollectionScopePath
        parallelism_assessment = $state.ParallelismAssessmentPath
        targeted_collection_plan = $state.TargetedCollectionPlanPath
        targeted_mode = [bool]$Targeted
        target_profile = $TargetProfile
        synthetic_oversize_source = $state.SyntheticOversizeSourcePath
        chunk_manifest = $state.ChunkManifestPath
        upload_safe_chunk_manifest = $state.UploadSafeChunkManifestPath
      })

      $status = "SUCCESS"
      if (@($Global:CollectorErrors).Count -gt 0) { $status = "PARTIAL_SUCCESS" }

      $collectorCommandBase = Get-CollectorResponseActionCommandBase
      $deleteScriptCommand = Get-CollectorDeleteScriptCommandText

      Write-Output ("STATUS={0}" -f $status)
      Write-Output ("RUN_ID={0}" -f $RunId)
      Write-Output ("COLLECTOR_VERSION={0}" -f $state.CollectorVersion)
      Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $state.CollectorVersion))
      Write-Output ("METADATA_REPORT_PATH={0}" -f $metadataReportPath)
      Write-Output ("EXECUTION_CONTEXT_PATH={0}" -f $state.ExecutionContextPath)
      Write-Output ("SECURITY_AUDIT_POLICY_PATH={0}" -f $state.SecurityAuditPolicyPath)
      Write-Output ("AUDIT_POLICY_ACCESS_STATUS={0}" -f $state.AuditPolicyAccessStatus)
      Write-Output ("SECURITY_FILTERED_PATH={0}" -f $state.SecurityFilteredPath)
      Write-Output ("SECURITY_HIGH_SIGNAL_SUMMARY_PATH={0}" -f $state.SecurityHighSignalSummaryPath)
      Write-Output ("IS_ELEVATED={0}" -f $state.IsElevated)
      Write-Output ("NETSTAT_OWNER_AWARE_STATUS={0}" -f $state.NetstatOwnerAwareStatus)
      if ($state.NetstatPidOnlyPath) { Write-Output ("NETSTAT_PID_ONLY_PATH={0}" -f $state.NetstatPidOnlyPath) }
      Write-Output ("ANALYST_OVERVIEW_PATH={0}" -f $state.AnalystOverviewPath)
      if ($state.ParallelExecutionProofPath) { Write-Output ("PARALLEL_EXECUTION_PROOF_PATH={0}" -f $state.ParallelExecutionProofPath) }
      Write-Output ("UPLOAD_SUMMARY_PATH={0}" -f $state.UploadSummaryPath)
      Write-Output ("ATTACHMENT_BUDGET_MANIFEST_PATH={0}" -f $state.UploadBudgetManifestPath)
      if ($state.UploadSafeChunkManifestPath) { Write-Output ("UPLOAD_SAFE_CHUNK_MANIFEST_PATH={0}" -f $state.UploadSafeChunkManifestPath) }
      Write-Output ("COLLECTION_SCOPE_PATH={0}" -f $state.CollectionScopePath)
      Write-Output ("PARALLELISM_ASSESSMENT_PATH={0}" -f $state.ParallelismAssessmentPath)
      if ($state.TargetedCollectionPlanPath) { Write-Output ("TARGETED_COLLECTION_PLAN_PATH={0}" -f $state.TargetedCollectionPlanPath) }
      if ($state.SyntheticOversizeSourcePath) { Write-Output ("SYNTHETIC_OVERSIZE_SOURCE_PATH={0}" -f $state.SyntheticOversizeSourcePath) }
      if ($state.ChunkManifestPath) { Write-Output ("CHUNK_MANIFEST_PATH={0}" -f $state.ChunkManifestPath) }
      Write-Output ("DEFAULT_GEMINI_UPLOAD_SET_STATUS={0}" -f $state.DefaultGeminiUploadSetStatus)
      Write-Output ("COLLECT_BUNDLE_PATH={0}" -f $bundlePath)
      Write-Output ('NEXT_GET_FILE=get-file --path "{0}" --comment "Retrieve DCOIR collect bundle"' -f $bundlePath)
      Write-Output ('CLEANUP_COMMAND=execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $collectorCommandBase)
      Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
      Write-Output ('GEMINI_UPLOAD_GUIDANCE=Prefer ANALYST_OVERVIEW_PATH, UPLOAD_SUMMARY_PATH, ATTACHMENT_BUDGET_MANIFEST_PATH, COLLECTION_SCOPE_PATH, PARALLELISM_ASSESSMENT_PATH, and representative final_artifacts slices. If UPLOAD_SAFE_CHUNK_MANIFEST_PATH exists, use it for full-fidelity oversized text artifacts after triage summaries. If TARGETED_COLLECTION_PLAN_PATH exists, include it for narrow incidents.')
      foreach ($collectorError in @($Global:CollectorErrors)) {
        if (-not [string]::IsNullOrWhiteSpace([string]$collectorError)) {
          Write-Output ("COLLECTOR_ERROR={0}" -f $collectorError)
        }
      }
      Write-QuickNextSteps -Phase "Collect"
    }

    "Enrich" {
      $loaded = Load-State -Root $OutRoot -CurrentRunId $RunId
      $state = Convert-StateObjectToHashtable -InputObject $loaded
      $Global:CurrentRunId = [string]$state.RunId

      if (-not $Action -and -not $FinalizeEnrichSession) {
        throw "Enrich mode requires -Action or -FinalizeEnrichSession."
      }

      $session = Initialize-EnrichSession -State $state -RequestedSessionId $EnrichSessionId -ForceNew:$NewEnrichSession

      $logStamp = Get-Date -Format "yyyyMMdd_HHmmss"
      $actionLabel = if ($Action) { $Action } else { "FinalizeSession" }
      $Global:ExecutionTxtPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_execution_log.txt" -f $actionLabel, $logStamp)
      $Global:ExecutionJsonlPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_execution_log.jsonl" -f $actionLabel, $logStamp)
      $Global:ErrorsLogPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_errors.log" -f $actionLabel, $logStamp)
      Set-Content -Path $Global:ExecutionTxtPath -Value ("DCOIR Enrich Execution Log`r`nRunId={0}`r`nEnrichSessionId={1}`r`nAction={2}`r`nSessionResolutionMode={3}" -f $state.RunId, $session.SessionId, $actionLabel, $session.SessionResolutionMode) -Encoding UTF8
      Set-Content -Path $Global:ExecutionJsonlPath -Value "" -Encoding UTF8
      Set-Content -Path $Global:ErrorsLogPath -Value "" -Encoding UTF8

      $toolMap = Get-ToolMap -ToolsDir $state.ToolsDir

      $result = $null
      if ($Action) {
        $result = Invoke-EnrichmentAction -State $state -Session $session -ToolMap $toolMap
      }

      $bundlePath = $null
      $sessionStatus = "OPEN"
      if ($FinalizeEnrichSession) {
        $bundlePath = Finalize-EnrichSession -State $state -Session $session -ToolMap $toolMap
        $sessionStatus = "FINALIZED"
      }

      Save-State -State $state

      $status = "SUCCESS"
      if (@($Global:CollectorErrors).Count -gt 0) { $status = "PARTIAL_SUCCESS" }

      $deleteScriptCommand = Get-CollectorDeleteScriptCommandText

      Write-Output ("STATUS={0}" -f $status)
      Write-Output ("RUN_ID={0}" -f $state.RunId)
      Write-Output ("COLLECTOR_VERSION={0}" -f [string]$state.CollectorVersion)
      Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version ([string]$state.CollectorVersion)))
      Write-Output ("ENRICH_SESSION_ID={0}" -f $session.SessionId)
      Write-Output ("SESSION_RESOLUTION_MODE={0}" -f $session.SessionResolutionMode)
      if ($result) {
        Write-Output ("ENRICH_REPORT_PATH={0}" -f $result.ReportPath)
        Write-Output ("ACTION_ARTIFACT_PATH={0}" -f $result.ActionArtifactPath)
        if ($result.StagedPath) { Write-Output ("STAGED_PATH={0}" -f $result.StagedPath) }
      } else {
        Write-Output ("ENRICH_REPORT_PATH={0}" -f $session.SummaryPath)
      }
      Write-Output ("SESSION_STATUS={0}" -f $sessionStatus)
      if ($bundlePath) {
        Write-Output ("ENRICH_BUNDLE_PATH={0}" -f $bundlePath)
        Write-Output ('NEXT_GET_FILE=get-file --path "{0}" --comment "Retrieve DCOIR enrich bundle"' -f $bundlePath)
      } else {
        Write-Output ("NEXT_OPTIONS=Continue current session with -EnrichSessionId {0} or finalize it with -FinalizeEnrichSession" -f $session.SessionId)
      }
      Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
      if ($sessionStatus -eq "FINALIZED") {
        Write-QuickNextSteps -Phase "EnrichFinalized"
      } else {
        Write-QuickNextSteps -Phase "EnrichOpen"
      }
    }

    "Cleanup" {
      try {
        $loaded = Load-State -Root $OutRoot -CurrentRunId $RunId
        $cleanupCollectorVersion = if (($loaded.PSObject.Properties.Name -contains 'CollectorVersion') -and -not [string]::IsNullOrWhiteSpace([string]$loaded.CollectorVersion)) {
          [string]$loaded.CollectorVersion
        } else {
          $ScriptVersion
        }
        Invoke-Cleanup -StateObject $loaded
        Write-Output ("CLEANUP_STATUS=COMPLETE")
        Write-Output ("RUN_ID={0}" -f $loaded.RunId)
        Write-Output ("COLLECTOR_VERSION={0}" -f $cleanupCollectorVersion)
        Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $cleanupCollectorVersion))
        Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f (Get-CollectorDeleteScriptCommandText))
        Write-QuickNextSteps -Phase "Cleanup"
      } catch {
        $loadError = $_.Exception.Message
        if ($loadError -notmatch 'State file not found|No DCOIR run directories found') { throw }
        $resolvedOutRoot = if ([System.IO.Path]::IsPathRooted($OutRoot)) {
          [System.IO.Path]::GetFullPath($OutRoot)
        } else {
          [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutRoot))
        }
        $cleanupResult = Invoke-NoStateCleanup -Root $resolvedOutRoot -CurrentRunId $RunId -CurrentPackageName $PackageName
        Write-Output ("CLEANUP_STATUS={0}" -f $cleanupResult.Status)
        if ($RunId) { Write-Output ("RUN_ID={0}" -f $RunId) }
        if ($cleanupResult.RunRoot) { Write-Output ("CLEANUP_ORPHAN_RUN_ROOT={0}" -f $cleanupResult.RunRoot) }
        Write-Output ("CLEANUP_TARGET_COUNT={0}" -f $cleanupResult.TargetCount)
        foreach ($target in @($cleanupResult.RemovedTargets)) { Write-Output ("CLEANUP_REMOVED_TARGET={0}" -f $target) }
        foreach ($target in @($cleanupResult.FailedTargets)) { Write-Output ("CLEANUP_FAILED_TARGET={0}" -f $target) }
        Write-Output ("CLEANUP_REASON={0}" -f $loadError)
        Write-Output ("COLLECTOR_VERSION={0}" -f $ScriptVersion)
        Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $ScriptVersion))
        Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f (Get-CollectorDeleteScriptCommandText))
        Write-QuickNextSteps -Phase "Cleanup"
      }
    }
  }
} catch {
  Add-CollectorError $_.Exception.Message
  Write-Output ("STATUS=ERROR")
  Write-Output ("MESSAGE={0}" -f $_.Exception.Message)
  exit 1
}
# END DCOIR_Collector.05_Main_Entry.ps1

# END COMPILED COLLECTOR PARTS
