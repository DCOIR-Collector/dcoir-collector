<#
.SYNOPSIS
Runs a focused regression check for default no-flags collector execution.

.DESCRIPTION
Invokes the collector with no explicit arguments, verifies that the collect output
contract is emitted, and optionally runs cleanup to confirm the default lane leaves a
normal cleanup path behind.
#>

param(
  [string]$CollectorPath = ".\DCOIR_Collector.ps1",
  [string]$OutputRoot = ".\TestResults",
  [switch]$SkipCleanup,
  [ValidateSet("Auto","PowerShellFile","Executable")]
  [string]$CollectorInvocationMode = "Auto"
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Resolve-Path -LiteralPath $CollectorPath)
$CollectorFullPath = (Resolve-Path -LiteralPath $CollectorPath).Path
$ResolvedInvocationMode = $CollectorInvocationMode
if ($ResolvedInvocationMode -eq "Auto") {
  if ([System.IO.Path]::GetExtension($CollectorFullPath) -ieq ".exe") {
    $ResolvedInvocationMode = "Executable"
  } else {
    $ResolvedInvocationMode = "PowerShellFile"
  }
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputRootFullPath = if ([System.IO.Path]::IsPathRooted($OutputRoot)) {
  [System.IO.Path]::GetFullPath($OutputRoot)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $OutputRoot))
}
$RunOutputRoot = Join-Path $OutputRootFullPath ("DCOIR_DefaultNoFlagsRegression_{0}" -f $Timestamp)
$LogPath = Join-Path $RunOutputRoot "default_no_flags_regression.log"
$SummaryPath = Join-Path $RunOutputRoot "default_no_flags_regression_summary.txt"

function Ensure-Directory {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -Path $Path -ItemType Directory -Force | Out-Null
  }
}

function Parse-OutputValue {
  param([string]$Text,[string]$Key)
  $pattern = '(?m)^{0}=(.+)$' -f [regex]::Escape($Key)
  $m = [regex]::Match($Text, $pattern)
  if ($m.Success) { return $m.Groups[1].Value.Trim() }
  return $null
}

function Quote-Arg {
  param([string]$Value)
  if ($null -eq $Value) { return '""' }
  if ($Value -match '[\s"]') {
    return '"' + ($Value -replace '"','\"') + '"'
  }
  return $Value
}

function Build-ArgumentString {
  param([string[]]$ArgumentValues)
  $parts = New-Object System.Collections.ArrayList
  foreach ($a in $ArgumentValues) {
    [void]$parts.Add((Quote-Arg -Value $a))
  }
  return ($parts -join ' ')
}

function New-CollectorInvocation {
  param([string[]]$CollectorArgs)
  if ($ResolvedInvocationMode -eq "Executable") {
    return [pscustomobject]@{
      FileName = $CollectorFullPath
      Arguments = @($CollectorArgs)
      DisplayCommand = ("{0} {1}" -f (Quote-Arg -Value $CollectorFullPath), (Build-ArgumentString -ArgumentValues $CollectorArgs)).Trim()
    }
  }

  $invokeArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$CollectorFullPath) + $CollectorArgs
  return [pscustomobject]@{
    FileName = "powershell.exe"
    Arguments = $invokeArgs
    DisplayCommand = ("powershell.exe {0}" -f (Build-ArgumentString -ArgumentValues $invokeArgs)).Trim()
  }
}

function Invoke-Collector {
  param([string[]]$CollectorArgs)
  $invocation = New-CollectorInvocation -CollectorArgs $CollectorArgs
  $process = New-Object System.Diagnostics.Process
  $process.StartInfo = New-Object System.Diagnostics.ProcessStartInfo
  $process.StartInfo.FileName = $invocation.FileName
  $process.StartInfo.UseShellExecute = $false
  $process.StartInfo.RedirectStandardOutput = $true
  $process.StartInfo.RedirectStandardError = $true
  $process.StartInfo.CreateNoWindow = $true
  $process.StartInfo.Arguments = Build-ArgumentString -ArgumentValues @($invocation.Arguments)
  [void]$process.Start()
  $stdoutTask = $process.StandardOutput.ReadToEndAsync()
  $stderrTask = $process.StandardError.ReadToEndAsync()
  $process.WaitForExit()
  $stdoutText = $stdoutTask.GetAwaiter().GetResult()
  $stderrText = $stderrTask.GetAwaiter().GetResult()
  $stdout = @($stdoutText, $stderrText | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) -join [Environment]::NewLine
  return [pscustomobject]@{
    ExitCode = $process.ExitCode
    StdOut = $stdout
    DisplayCommand = $invocation.DisplayCommand
    CollectorReportedStatus = Parse-OutputValue -Text $stdout -Key "STATUS"
    RunId = Parse-OutputValue -Text $stdout -Key "RUN_ID"
    NextGetFile = Parse-OutputValue -Text $stdout -Key "NEXT_GET_FILE"
    CleanupCommand = Parse-OutputValue -Text $stdout -Key "CLEANUP_COMMAND"
    DeleteScriptCommand = Parse-OutputValue -Text $stdout -Key "DELETE_SCRIPT_COMMAND"
    GeminiUploadGuidance = Parse-OutputValue -Text $stdout -Key "GEMINI_UPLOAD_GUIDANCE"
    CollectionScopePath = Parse-OutputValue -Text $stdout -Key "COLLECTION_SCOPE_PATH"
  }
}

Ensure-Directory -Path $RunOutputRoot

$collect = Invoke-Collector -CollectorArgs @()
$missing = New-Object System.Collections.ArrayList
if ($collect.ExitCode -ne 0) { [void]$missing.Add(("Exit code was {0}" -f $collect.ExitCode)) }
if ([string]::IsNullOrWhiteSpace($collect.RunId)) { [void]$missing.Add("RUN_ID missing") }
if ([string]::IsNullOrWhiteSpace($collect.NextGetFile)) { [void]$missing.Add("NEXT_GET_FILE missing") }
if ([string]::IsNullOrWhiteSpace($collect.CleanupCommand)) { [void]$missing.Add("CLEANUP_COMMAND missing") }
if ([string]::IsNullOrWhiteSpace($collect.DeleteScriptCommand)) { [void]$missing.Add("DELETE_SCRIPT_COMMAND missing") }
if ([string]::IsNullOrWhiteSpace($collect.GeminiUploadGuidance)) { [void]$missing.Add("GEMINI_UPLOAD_GUIDANCE missing") }
if ([string]::IsNullOrWhiteSpace($collect.CollectionScopePath)) { [void]$missing.Add("COLLECTION_SCOPE_PATH missing") }
if ($collect.CollectorReportedStatus -notin @("SUCCESS","PARTIAL_SUCCESS")) {
  [void]$missing.Add(("Unexpected STATUS value [{0}]" -f $collect.CollectorReportedStatus))
}

$logLines = @(
  ("COMMAND={0}" -f $collect.DisplayCommand),
  ("EXIT_CODE={0}" -f $collect.ExitCode),
  ("STATUS={0}" -f $collect.CollectorReportedStatus),
  ("RUN_ID={0}" -f $collect.RunId),
  ("NEXT_GET_FILE={0}" -f $collect.NextGetFile),
  ("CLEANUP_COMMAND={0}" -f $collect.CleanupCommand),
  ("DELETE_SCRIPT_COMMAND={0}" -f $collect.DeleteScriptCommand),
  ("GEMINI_UPLOAD_GUIDANCE={0}" -f $collect.GeminiUploadGuidance),
  ("COLLECTION_SCOPE_PATH={0}" -f $collect.CollectionScopePath),
  "",
  "STDOUT:",
  $collect.StdOut
)
Set-Content -Path $LogPath -Value $logLines -Encoding UTF8

if (@($missing).Count -gt 0) {
  $summary = @(
    "STATUS=FAIL",
    ("MESSAGE={0}" -f (@($missing) -join '; ')),
    ("LOG_PATH={0}" -f $LogPath)
  )
  Set-Content -Path $SummaryPath -Value $summary -Encoding UTF8
  throw (@($missing) -join '; ')
}

$cleanupSummary = "SKIPPED"
if (-not $SkipCleanup) {
  $cleanup = Invoke-Collector -CollectorArgs @("-Quick","cleanup")
  if ($cleanup.ExitCode -ne 0 -or $cleanup.CollectorReportedStatus -notin @("SUCCESS","PARTIAL_SUCCESS")) {
    $summary = @(
      "STATUS=FAIL",
      ("MESSAGE=Cleanup failed after default no-flags collect. ExitCode={0}; STATUS={1}" -f $cleanup.ExitCode, $cleanup.CollectorReportedStatus),
      ("LOG_PATH={0}" -f $LogPath)
    )
    Set-Content -Path $SummaryPath -Value $summary -Encoding UTF8
    throw ("Cleanup failed after default no-flags collect. ExitCode={0}; STATUS={1}" -f $cleanup.ExitCode, $cleanup.CollectorReportedStatus)
  }
  $cleanupSummary = $cleanup.CollectorReportedStatus
}

$summary = @(
  "STATUS=PASS",
  "MESSAGE=Default no-flags collector execution emitted the expected collect contract.",
  ("RUN_OUTPUT_ROOT={0}" -f $RunOutputRoot),
  ("LOG_PATH={0}" -f $LogPath),
  ("COLLECT_STATUS={0}" -f $collect.CollectorReportedStatus),
  ("CLEANUP_STATUS={0}" -f $cleanupSummary),
  ("RUN_ID={0}" -f $collect.RunId),
  ("COLLECTION_SCOPE_PATH={0}" -f $collect.CollectionScopePath)
)
Set-Content -Path $SummaryPath -Value $summary -Encoding UTF8
Write-Output ("STATUS=PASS")
Write-Output ("SUMMARY_PATH={0}" -f $SummaryPath)
