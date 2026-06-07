<#
.SYNOPSIS
DCOIR collector core logging, runtime-path, and process-capture helpers.

.DESCRIPTION
Provides the core logging, filesystem, runtime-path, command-capture, and process-capture
helpers used across collect, enrich, cleanup, validation, and bundle-generation paths.

.FILE NAME
DCOIR_Collector.01A_Core_Logging_And_Process_Capture.ps1

.INPUTS
Collector runtime globals, filesystem paths, command details, process details, and
runtime-location candidates.

.OUTPUTS
Collector notes/errors/recommendations, command-capture objects and text, runtime paths,
and supporting helper return values.
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
  [CmdletBinding()]
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:CollectorErrors.Add($Message)
  if ($Global:ErrorsLogPath) {
    try {
      Add-Content -Path $Global:ErrorsLogPath -Value ("[{0}] ERROR {1}" -f ((Get-Date).ToUniversalTime().ToString("o")), $Message) -Encoding UTF8 -ErrorAction Stop
    } catch {
      [void]$Global:CollectorNotes.Add(("Failed to append collector error log: {0}" -f $_.Exception.Message))
    }
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
    New-Item -Path $Path -ItemType Directory -Force -ErrorAction Stop | Out-Null
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
  [CmdletBinding(SupportsShouldProcess=$true)]
  param([string]$LiteralPath)
  if (-not [string]::IsNullOrWhiteSpace($LiteralPath) -and (Test-Path -LiteralPath $LiteralPath)) {
    if ($PSCmdlet.ShouldProcess($LiteralPath, 'Remove item recursively')) {
      Remove-Item -LiteralPath $LiteralPath -Recurse -Force -ErrorAction SilentlyContinue
    }
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
  [CmdletBinding()]
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
    Add-Content -Path $Global:ExecutionTxtPath -Value $txtLine -Encoding UTF8 -ErrorAction Stop
    if ($Command) {
      Add-Content -Path $Global:ExecutionTxtPath -Value ("  COMMAND={0}" -f $Command) -Encoding UTF8 -ErrorAction Stop
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
    Add-Content -Path $Global:ExecutionJsonlPath -Value (Convert-ToCollectorJsonText -InputObject $obj -Compress -Label 'execution step JSONL') -Encoding UTF8 -ErrorAction Stop
  }
}

<#
.SYNOPSIS
Returns the timeout used for external process capture.

.DESCRIPTION
Uses an explicit per-call timeout when provided, then an optional in-memory collector
override, and finally the conservative default. This is intentionally not an
environment variable so collector runtime behavior does not depend on undeclared host
configuration.

.FUNCTION NAME
Get-CollectorProcessCaptureTimeoutSeconds

.INPUTS
Optional timeout value in seconds.

.OUTPUTS
Positive integer timeout in seconds.
#>
function Get-CollectorProcessCaptureTimeoutSeconds {
  param([int]$TimeoutSeconds = 0)

  $defaultTimeoutSeconds = 600
  try {
    if ($TimeoutSeconds -gt 0) {
      return [int][Math]::Min($TimeoutSeconds, 86400)
    }

    $override = Get-Variable -Name CollectorProcessCaptureTimeoutSeconds -Scope Global -ErrorAction SilentlyContinue
    if ($override -and $null -ne $override.Value) {
      $overrideValue = [int]$override.Value
      if ($overrideValue -gt 0) {
        return [int][Math]::Min($overrideValue, 86400)
      }
    }
  } catch { }

  return $defaultTimeoutSeconds
}

<#
.SYNOPSIS
Stops one timed-out process and its child process tree when possible.

.DESCRIPTION
Attempts a Windows taskkill process-tree stop first, then falls back to the .NET process
kill method. Failure to stop is recorded as a collector error rather than hidden.

.FUNCTION NAME
Stop-CollectorProcessTree

.INPUTS
Process object and display command text.

.OUTPUTS
No direct output. Stops the process as a side effect when possible.
#>
function Stop-CollectorProcessTree {
  param(
    [System.Diagnostics.Process]$Process,
    [string]$CommandText
  )

  if ($null -eq $Process) { return }
  try {
    if ($Process.HasExited) { return }
  } catch { }

  $stopped = $false
  $taskkillTempPaths = @()
  try {
    $taskkillPath = 'taskkill.exe'
    if (-not [string]::IsNullOrWhiteSpace($env:SystemRoot)) {
      $candidate = Join-Path $env:SystemRoot 'System32\taskkill.exe'
      if (Test-Path -LiteralPath $candidate) {
        $taskkillPath = $candidate
      }
    }

    $taskkillStdoutPath = [System.IO.Path]::GetTempFileName()
    $taskkillTempPaths += $taskkillStdoutPath
    $taskkillStderrPath = [System.IO.Path]::GetTempFileName()
    $taskkillTempPaths += $taskkillStderrPath
    try {
      $killProcess = Start-Process -FilePath $taskkillPath -ArgumentList @('/PID', [string]$Process.Id, '/T', '/F') -Wait -NoNewWindow -PassThru -RedirectStandardOutput $taskkillStdoutPath -RedirectStandardError $taskkillStderrPath -ErrorAction Stop
      if ($killProcess.ExitCode -eq 0) {
        $stopped = $true
      }
    } finally {
      foreach ($taskkillTempPath in @($taskkillTempPaths)) {
        if (-not [string]::IsNullOrWhiteSpace($taskkillTempPath)) {
          Remove-Item -LiteralPath $taskkillTempPath -Force -ErrorAction SilentlyContinue
        }
      }
    }
  } catch { }

  try {
    if (-not $Process.HasExited -and -not $stopped) {
      $Process.Kill()
      $stopped = $true
    }
  } catch {
    Add-CollectorError ("Failed to stop timed-out process [{0}] for command [{1}]: {2}" -f $Process.Id, $CommandText, $_.Exception.Message)
  }
}

<#
.SYNOPSIS
Reads one asynchronous process-output task with a bounded wait.

.DESCRIPTION
Returns captured stream text when the async read task completes, or a visible warning
string when the stream cannot be harvested after the process has exited or been stopped.

.FUNCTION NAME
Get-CollectorProcessOutputTaskText

.INPUTS
Async task, stream name, and bounded wait in milliseconds.

.OUTPUTS
Captured stream text or a warning string.
#>
function Get-CollectorProcessOutputTaskText {
  param(
    [System.Threading.Tasks.Task]$Task,
    [string]$StreamName,
    [int]$WaitMilliseconds = 10000
  )

  if ($null -eq $Task) { return "" }
  try {
    if (-not $Task.Wait($WaitMilliseconds)) {
      return ("[DCOIR_CAPTURE_WARNING] {0} capture did not complete within {1}ms after process exit." -f $StreamName, $WaitMilliseconds)
    }
    return [string]$Task.Result
  } catch {
    return ("[DCOIR_CAPTURE_WARNING] {0} capture failed: {1}" -f $StreamName, $_.Exception.Message)
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
Mandatory FilePath and StepName, optional argument array, optional allowed exit-code
list, and optional timeout seconds.

.OUTPUTS
PSCustomObject containing StdOut, StdErr, ExitCode, Command, Status, TimedOut, and
TimeoutSeconds.
#>
function Invoke-ProcessCapture {
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$Arguments,
    [Parameter(Mandatory=$true)][string]$StepName,
    [int[]]$AllowedExitCodes = @(0),
    [int]$TimeoutSeconds = 0
  )

  $startTime = Get-Date
  $commandText = $FilePath
  if ($Arguments) {
    $commandText = "$FilePath $(Join-ArgString -Arguments $Arguments)"
  }

  $effectiveTimeoutSeconds = Get-CollectorProcessCaptureTimeoutSeconds -TimeoutSeconds $TimeoutSeconds
  $timeoutMilliseconds = [int][Math]::Min(([double]$effectiveTimeoutSeconds * 1000), [double][int]::MaxValue)
  $proc = $null
  $timedOut = $false

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
    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()

    $timedOut = -not $proc.WaitForExit($timeoutMilliseconds)
    if ($timedOut) {
      Stop-CollectorProcessTree -Process $proc -CommandText $commandText
      try { [void]$proc.WaitForExit(5000) } catch { }
    } else {
      [void]$proc.WaitForExit()
    }

    $stdout = Get-CollectorProcessOutputTaskText -Task $stdoutTask -StreamName 'stdout'
    $stderr = Get-CollectorProcessOutputTaskText -Task $stderrTask -StreamName 'stderr'

    $endTime = Get-Date
    $status = "OK"
    $message = ""
    $exitCode = -1
    if (-not $timedOut) {
      $exitCode = [int]$proc.ExitCode
    }

    if ($timedOut) {
      $status = "TIMEOUT"
      $message = ("TimedOut=True TimeoutSeconds={0}" -f $effectiveTimeoutSeconds)
      Add-CollectorError ("Step [{0}] timed out after {1} seconds. Command: {2}" -f $StepName, $effectiveTimeoutSeconds, $commandText)
    } elseif (@($AllowedExitCodes) -notcontains $exitCode) {
      $status = "ERROR"
      $message = ("ExitCode={0}" -f $exitCode)
      Add-CollectorError ("Step [{0}] failed. {1}. Command: {2}" -f $StepName, $message, $commandText)
    }

    Write-StepLog -StepName $StepName -Status $status -StartTime $startTime -EndTime $endTime -ExitCode $exitCode -Command $commandText -ArtifactPath "" -Message $message

    return [pscustomobject]@{
      StdOut = $stdout
      StdErr = $stderr
      ExitCode = $exitCode
      Command = $commandText
      Status = $status
      TimedOut = [bool]$timedOut
      TimeoutSeconds = [int]$effectiveTimeoutSeconds
    }
  } catch {
    $endTime = Get-Date
    $message = $_.Exception.Message
    Add-CollectorError ("Step [{0}] raised an exception. {1}. Command: {2}" -f $StepName, $message, $commandText)
    $status = if ($timedOut) { "TIMEOUT" } else { "EXCEPTION" }
    Write-StepLog -StepName $StepName -Status $status -StartTime $startTime -EndTime $endTime -ExitCode -1 -Command $commandText -ArtifactPath "" -Message $message
    return [pscustomobject]@{
      StdOut = ""
      StdErr = $message
      ExitCode = -1
      Command = $commandText
      Status = $status
      TimedOut = [bool]$timedOut
      TimeoutSeconds = [int]$effectiveTimeoutSeconds
    }
  } finally {
    if ($null -ne $proc) {
      try { $proc.Dispose() } catch { }
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
Mandatory Command and StepName, optional allowed exit-code list, and optional timeout
seconds.

.OUTPUTS
PSCustomObject containing the captured cmd.exe result.
#>
function Invoke-CmdCapture {
  param(
    [Parameter(Mandatory=$true)][string]$Command,
    [Parameter(Mandatory=$true)][string]$StepName,
    [int[]]$AllowedExitCodes = @(0),
    [int]$TimeoutSeconds = 0
  )
  return (Invoke-ProcessCapture -FilePath "cmd.exe" -Arguments @("/c", $Command) -StepName $StepName -AllowedExitCodes $AllowedExitCodes -TimeoutSeconds $TimeoutSeconds)
}
