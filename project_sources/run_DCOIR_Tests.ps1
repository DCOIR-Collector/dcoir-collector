param(
  [ValidateSet("Core","Retrieval","QuickAliases","SessionBehavior","TargetedCollection","ChunkingOversizeArtifact","ChunkingReconstructionMetadata","MajorVersion","FullRegression","FailureGates")]
  [string]$Suite = "Core",

  [string]$CollectorPath = ".\DCOIR_Collector.ps1",

  [string]$OutputRoot = ".\TestResults",

  [string]$MasterZipPath = ".\assets\DCOIR_Collector.zip",

  [switch]$LiveResponseMode,

  [int]$SafePerFileKB = 900,

  [int]$HardPerFileKB = 1000,

  [int]$SafePerPromptKB = 1800,

  [int]$HardPerPromptKB = 2000,

  [switch]$ContinueOnError,

  [switch]$SkipCleanup
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

if ($LiveResponseMode) {
  if ($CollectorPath -eq ".\DCOIR_Collector.ps1") { $CollectorPath = "C:\Temp\DCOIR_Collector.ps1" }
  if ($OutputRoot -eq ".\TestResults") { $OutputRoot = "C:\Temp\DCOIR_TestResults" }
  if ($MasterZipPath -eq ".\assets\DCOIR_Collector.zip") { $MasterZipPath = "C:\Temp\assets\DCOIR_Collector.zip" }
}

$ProjectRoot = Split-Path -Parent (Resolve-Path -LiteralPath $CollectorPath)
$CollectorFullPath = (Resolve-Path -LiteralPath $CollectorPath).Path
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputRootFullPath = if ([System.IO.Path]::IsPathRooted($OutputRoot)) {
  [System.IO.Path]::GetFullPath($OutputRoot)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $OutputRoot))
}
$RunOutputRoot = Join-Path $OutputRootFullPath ("DCOIR_TestRun_{0}" -f $Timestamp)
$LogsDir = Join-Path $RunOutputRoot "logs"
$WorkingZipPath = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot "DCOIR_Collector.zip"))
$MasterZipFullPath = if ([System.IO.Path]::IsPathRooted($MasterZipPath)) {
  [System.IO.Path]::GetFullPath($MasterZipPath)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot $MasterZipPath))
}

$script:CollectorRunId = $null
$script:CollectorSessionId = $null
$script:Results = New-Object System.Collections.ArrayList

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

function Write-HarnessLog {
  param([string]$StepName,[string[]]$Lines)
  Ensure-Directory -Path $LogsDir
  $logPath = Join-Path $LogsDir ("{0}.txt" -f $StepName)
  Set-Content -Path $logPath -Value $Lines -Encoding UTF8
  return $logPath
}

function Add-Result {
  param(
    [string]$StepName,
    [string]$Status,
    [int]$ExitCode,
    [string]$RunId,
    [string]$EnrichSessionId,
    [string]$CollectorReportedStatus,
    [string]$LogPath,
    [datetime]$Start,
    [datetime]$End
  )
  [void]$script:Results.Add([pscustomobject]@{
    StepName = $StepName
    Status = $Status
    ExitCode = $ExitCode
    RunId = $RunId
    EnrichSessionId = $EnrichSessionId
    CollectorReportedStatus = $CollectorReportedStatus
    LogPath = $LogPath
    Start = $Start.ToString("o")
    End = $End.ToString("o")
    DurationMs = [int][Math]::Round(($End - $Start).TotalMilliseconds)
  })
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
  param([string[]]$Args)
  $parts = New-Object System.Collections.ArrayList
  foreach ($a in $Args) {
    [void]$parts.Add((Quote-Arg -Value $a))
  }
  return ($parts -join ' ')
}

function Restore-WorkingZip {
  param([string]$Reason)
  $stepName = "ZZ_RestoreWorkingZip_{0}" -f ($Reason -replace '[^A-Za-z0-9_-]','_')
  $start = Get-Date
  if (-not (Test-Path -LiteralPath $MasterZipFullPath)) {
    $end = Get-Date
    $logPath = Write-HarnessLog -StepName $stepName -Lines @("STEP=$stepName","STATUS=FAIL","MESSAGE=Master zip not found.","MASTER_ZIP=$MasterZipFullPath","WORKING_ZIP=$WorkingZipPath")
    Add-Result -StepName $stepName -Status "FAIL" -ExitCode 1 -RunId $null -EnrichSessionId $null -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
    throw ("Master zip not found: {0}" -f $MasterZipFullPath)
  }
  Copy-Item -LiteralPath $MasterZipFullPath -Destination $WorkingZipPath -Force
  $status = "PASS"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $stepName -Lines @("STEP=$stepName","STATUS=$status","MASTER_ZIP=$MasterZipFullPath","WORKING_ZIP=$WorkingZipPath")
  Add-Result -StepName $stepName -Status $status -ExitCode 0 -RunId $null -EnrichSessionId $null -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
}

function Resolve-CollectorStepStatus {
  param([int]$ExitCode,[string]$CollectorReportedStatus)
  if ($ExitCode -ne 0) { return "FAIL" }
  if ($CollectorReportedStatus -eq "PARTIAL_SUCCESS") { return "PARTIAL_SUCCESS" }
  return "PASS"
}

function Invoke-CollectorStep {
  param(
    [Parameter(Mandatory=$true)][string]$StepName,
    [Parameter(Mandatory=$true)][string[]]$CollectorArgs
  )
  Ensure-Directory -Path $LogsDir
  $invokeArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$CollectorFullPath) + $CollectorArgs
  $displayArgs = Build-ArgumentString -Args $invokeArgs
  $start = Get-Date
  $allOutput = & powershell.exe @invokeArgs 2>&1
  $exitCode = $LASTEXITCODE
  $end = Get-Date
  $stdout = ($allOutput | ForEach-Object { if ($null -eq $_) { "" } else { $_.ToString() } }) -join [Environment]::NewLine
  $collectorReportedStatus = Parse-OutputValue -Text $stdout -Key "STATUS"
  $logLines = New-Object System.Collections.ArrayList
  [void]$logLines.Add("STEP=$StepName")
  [void]$logLines.Add("START=$($start.ToString('o'))")
  [void]$logLines.Add("END=$($end.ToString('o'))")
  [void]$logLines.Add(("DURATION_MS={0}" -f [int][Math]::Round(($end - $start).TotalMilliseconds)))
  [void]$logLines.Add("EXIT_CODE=$exitCode")
  if ($collectorReportedStatus) { [void]$logLines.Add("COLLECTOR_STATUS=$collectorReportedStatus") }
  [void]$logLines.Add(("COMMAND=powershell.exe {0}" -f $displayArgs))
  [void]$logLines.Add("")
  [void]$logLines.Add("STDOUT:")
  [void]$logLines.Add($stdout)
  $logPath = Write-HarnessLog -StepName $StepName -Lines $logLines
  $status = Resolve-CollectorStepStatus -ExitCode $exitCode -CollectorReportedStatus $collectorReportedStatus
  $runId = Parse-OutputValue -Text $stdout -Key "RUN_ID"
  $sessionId = Parse-OutputValue -Text $stdout -Key "ENRICH_SESSION_ID"
  if ($runId) { $script:CollectorRunId = $runId }
  if ($sessionId) { $script:CollectorSessionId = $sessionId }
  Add-Result -StepName $StepName -Status $status -ExitCode $exitCode -RunId $runId -EnrichSessionId $sessionId -CollectorReportedStatus $collectorReportedStatus -LogPath $logPath -Start $start -End $end
  return [pscustomobject]@{
    StepName = $StepName
    Status = $status
    ExitCode = $exitCode
    RunId = $runId
    EnrichSessionId = $sessionId
    CollectorReportedStatus = $collectorReportedStatus
    StdOut = $stdout
    LogPath = $logPath
    BaselineReportPath = Parse-OutputValue -Text $stdout -Key "BASELINE_REPORT_PATH"
    MetadataReportPath = Parse-OutputValue -Text $stdout -Key "METADATA_REPORT_PATH"
    UploadSummaryPath = Parse-OutputValue -Text $stdout -Key "UPLOAD_SUMMARY_PATH"
    AttachmentBudgetManifestPath = Parse-OutputValue -Text $stdout -Key "ATTACHMENT_BUDGET_MANIFEST_PATH"
    CollectionScopePath = Parse-OutputValue -Text $stdout -Key "COLLECTION_SCOPE_PATH"
    ParallelismAssessmentPath = Parse-OutputValue -Text $stdout -Key "PARALLELISM_ASSESSMENT_PATH"
    TargetedCollectionPlanPath = Parse-OutputValue -Text $stdout -Key "TARGETED_COLLECTION_PLAN_PATH"
    SyntheticOversizeSourcePath = Parse-OutputValue -Text $stdout -Key "SYNTHETIC_OVERSIZE_SOURCE_PATH"
    ChunkManifestPath = Parse-OutputValue -Text $stdout -Key "CHUNK_MANIFEST_PATH"
    DefaultGeminiUploadSetStatus = Parse-OutputValue -Text $stdout -Key "DEFAULT_GEMINI_UPLOAD_SET_STATUS"
    CollectBundlePath = Parse-OutputValue -Text $stdout -Key "COLLECT_BUNDLE_PATH"
    EnrichBundlePath = Parse-OutputValue -Text $stdout -Key "ENRICH_BUNDLE_PATH"
    SessionResolutionMode = Parse-OutputValue -Text $stdout -Key "SESSION_RESOLUTION_MODE"
    SessionStatus = Parse-OutputValue -Text $stdout -Key "SESSION_STATUS"
    NextGetFile = Parse-OutputValue -Text $stdout -Key "NEXT_GET_FILE"
    NextOptions = Parse-OutputValue -Text $stdout -Key "NEXT_OPTIONS"
    CleanupCommand = Parse-OutputValue -Text $stdout -Key "CLEANUP_COMMAND"
    DeleteScriptCommand = Parse-OutputValue -Text $stdout -Key "DELETE_SCRIPT_COMMAND"
    GeminiUploadGuidance = Parse-OutputValue -Text $stdout -Key "GEMINI_UPLOAD_GUIDANCE"
    CleanupStatus = Parse-OutputValue -Text $stdout -Key "CLEANUP_STATUS"
    HasQuickCommands = [regex]::IsMatch($stdout, '(?m)^NEXT_QUICK_COMMANDS$')
  }
}

function Invoke-CollectorStepWithEnvOverride {
  param(
    [Parameter(Mandatory=$true)][string]$StepName,
    [Parameter(Mandatory=$true)][string[]]$CollectorArgs,
    [Parameter(Mandatory=$true)][hashtable]$EnvOverrides
  )

  $previous = @{}
  try {
    foreach ($name in $EnvOverrides.Keys) {
      $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
      [Environment]::SetEnvironmentVariable($name, [string]$EnvOverrides[$name], 'Process')
    }
    return Invoke-CollectorStep -StepName $StepName -CollectorArgs $CollectorArgs
  } finally {
    foreach ($name in $EnvOverrides.Keys) {
      [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process')
    }
  }
}

function Invoke-ExpectedFailureStep {
  param(
    [Parameter(Mandatory=$true)][string]$StepName,
    [Parameter(Mandatory=$true)][string[]]$CollectorArgs,
    [Parameter(Mandatory=$true)][ValidateSet('BIND_REJECT','RUNTIME_ERROR')][string]$ExpectedOutcome,
    [string[]]$ExpectedPatterns
  )

  Ensure-Directory -Path $LogsDir
  $invokeArgs = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$CollectorFullPath) + $CollectorArgs
  $displayArgs = Build-ArgumentString -Args $invokeArgs
  $start = Get-Date

  $process = New-Object System.Diagnostics.Process
  $process.StartInfo = New-Object System.Diagnostics.ProcessStartInfo
  $process.StartInfo.FileName = 'powershell.exe'
  $process.StartInfo.UseShellExecute = $false
  $process.StartInfo.RedirectStandardOutput = $true
  $process.StartInfo.RedirectStandardError = $true
  $process.StartInfo.CreateNoWindow = $true
  foreach ($invokeArg in $invokeArgs) {
    [void]$process.StartInfo.ArgumentList.Add($invokeArg)
  }
  [void]$process.Start()
  $stdoutTask = $process.StandardOutput.ReadToEndAsync()
  $stderrTask = $process.StandardError.ReadToEndAsync()
  $process.WaitForExit()
  $stdoutText = $stdoutTask.GetAwaiter().GetResult()
  $stderrText = $stderrTask.GetAwaiter().GetResult()
  $exitCode = $process.ExitCode
  $end = Get-Date

  $stdout = @($stdoutText, $stderrText | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) -join [Environment]::NewLine
  $collectorReportedStatus = Parse-OutputValue -Text $stdout -Key "STATUS"

  $missingPatterns = New-Object System.Collections.ArrayList
  foreach ($pattern in @($ExpectedPatterns)) {
    if (-not [string]::IsNullOrWhiteSpace($pattern) -and -not [regex]::IsMatch($stdout, [regex]::Escape($pattern))) {
      [void]$missingPatterns.Add($pattern)
    }
  }

  $status = 'FAIL'
  $message = ''
  switch ($ExpectedOutcome) {
    'BIND_REJECT' {
      if ($exitCode -ne 0 -and [string]::IsNullOrWhiteSpace($collectorReportedStatus) -and @($missingPatterns).Count -eq 0) {
        $status = 'PASS'
        $message = 'Observed expected bind-reject behavior.'
      } else {
        $message = 'Expected bind-reject behavior was not observed.'
      }
    }
    'RUNTIME_ERROR' {
      if ($exitCode -ne 0 -and $collectorReportedStatus -eq 'ERROR' -and @($missingPatterns).Count -eq 0) {
        $status = 'PASS'
        $message = 'Observed expected runtime-error behavior.'
      } else {
        $message = 'Expected runtime-error behavior was not observed.'
      }
    }
  }

  if (@($missingPatterns).Count -gt 0) {
    $message = ($message + ' Missing patterns: ' + (@($missingPatterns) -join '; ')).Trim()
  }

  $logLines = New-Object System.Collections.ArrayList
  [void]$logLines.Add("STEP=$StepName")
  [void]$logLines.Add("START=$($start.ToString('o'))")
  [void]$logLines.Add("END=$($end.ToString('o'))")
  [void]$logLines.Add(("DURATION_MS={0}" -f [int][Math]::Round(($end - $start).TotalMilliseconds)))
  [void]$logLines.Add("EXPECTED_OUTCOME=$ExpectedOutcome")
  [void]$logLines.Add("EXIT_CODE=$exitCode")
  if ($collectorReportedStatus) { [void]$logLines.Add("COLLECTOR_STATUS=$collectorReportedStatus") }
  [void]$logLines.Add("STATUS=$status")
  if ($message) { [void]$logLines.Add("MESSAGE=$message") }
  [void]$logLines.Add(("COMMAND=powershell.exe {0}" -f $displayArgs))
  [void]$logLines.Add("")
  [void]$logLines.Add("STDOUT:")
  [void]$logLines.Add($stdoutText)
  [void]$logLines.Add("")
  [void]$logLines.Add("STDERR:")
  [void]$logLines.Add($stderrText)
  $logPath = Write-HarnessLog -StepName $StepName -Lines $logLines
  Add-Result -StepName $StepName -Status $status -ExitCode $exitCode -RunId $null -EnrichSessionId $null -CollectorReportedStatus $collectorReportedStatus -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
  return [pscustomobject]@{
    StepName = $StepName
    Status = $status
    ExitCode = $exitCode
    CollectorReportedStatus = $collectorReportedStatus
    StdOut = $stdout
    LogPath = $logPath
  }
}

function Assert-CollectorStepSucceeded {
  param(
    [string]$StepName,
    [object]$CollectorStep
  )

  if ($CollectorStep.ExitCode -eq 0 -and ($CollectorStep.Status -eq 'PASS' -or $CollectorStep.Status -eq 'PARTIAL_SUCCESS')) {
    return
  }

  $message = @(
    ("Collector step failed before downstream verification: {0}" -f $StepName),
    ("Collector harness status: {0}" -f $CollectorStep.Status),
    ("Collector reported status: {0}" -f $CollectorStep.CollectorReportedStatus),
    ("Collector step log: {0}" -f $CollectorStep.LogPath),
    "Collector stdout follows:",
    $CollectorStep.StdOut
  ) -join [Environment]::NewLine

  throw $message
}

function Assert-CollectorStepDegradedPartial {
  param(
    [string]$StepName,
    [object]$CollectorStep,
    [string[]]$ExpectedPatterns
  )

  $missingPatterns = New-Object System.Collections.ArrayList
  foreach ($pattern in @($ExpectedPatterns)) {
    if (-not [string]::IsNullOrWhiteSpace($pattern) -and -not [regex]::IsMatch($CollectorStep.StdOut, [regex]::Escape($pattern))) {
      [void]$missingPatterns.Add($pattern)
    }
  }

  if ($CollectorStep.ExitCode -eq 0 -and $CollectorStep.CollectorReportedStatus -eq 'PARTIAL_SUCCESS' -and @($missingPatterns).Count -eq 0) {
    return
  }

  $message = @(
    ("Collector step did not show the expected degraded partial behavior: {0}" -f $StepName),
    ("Collector harness status: {0}" -f $CollectorStep.Status),
    ("Collector reported status: {0}" -f $CollectorStep.CollectorReportedStatus),
    ("Collector step log: {0}" -f $CollectorStep.LogPath),
    ("Missing patterns: {0}" -f (@($missingPatterns) -join '; ')),
    "Collector stdout follows:",
    $CollectorStep.StdOut
  ) -join [Environment]::NewLine

  throw $message
}

function Invoke-CollectOutputContractVerification {
  param([string]$StepName,[object]$CollectStep)
  $start = Get-Date
  $status = 'FAIL'
  $message = ''
  $lines = @(
    "STEP=$StepName",
    "RUN_ID=$($CollectStep.RunId)",
    "NEXT_GET_FILE=$($CollectStep.NextGetFile)",
    "CLEANUP_COMMAND=$($CollectStep.CleanupCommand)",
    "DELETE_SCRIPT_COMMAND=$($CollectStep.DeleteScriptCommand)",
    "GEMINI_UPLOAD_GUIDANCE=$($CollectStep.GeminiUploadGuidance)",
    "HAS_QUICK_COMMANDS=$($CollectStep.HasQuickCommands)"
  )

  $missing = New-Object System.Collections.ArrayList
  if ([string]::IsNullOrWhiteSpace($CollectStep.RunId)) { [void]$missing.Add('RUN_ID missing') }
  if ([string]::IsNullOrWhiteSpace($CollectStep.NextGetFile)) { [void]$missing.Add('NEXT_GET_FILE missing') }
  if ([string]::IsNullOrWhiteSpace($CollectStep.CleanupCommand)) { [void]$missing.Add('CLEANUP_COMMAND missing') }
  if ([string]::IsNullOrWhiteSpace($CollectStep.DeleteScriptCommand)) { [void]$missing.Add('DELETE_SCRIPT_COMMAND missing') }
  if ([string]::IsNullOrWhiteSpace($CollectStep.GeminiUploadGuidance)) { [void]$missing.Add('GEMINI_UPLOAD_GUIDANCE missing') }

  if (@($missing).Count -eq 0) {
    $status = 'PASS'
    $message = 'Collect output contract fields were emitted.'
  } else {
    $message = (@($missing) -join '; ')
  }

  $lines += "STATUS=$status"
  $lines += "MESSAGE=$message"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $CollectStep.RunId -EnrichSessionId $CollectStep.EnrichSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Invoke-EnrichOpenOutputContractVerification {
  param([string]$StepName,[object]$EnrichStep)
  $start = Get-Date
  $status = 'FAIL'
  $message = ''
  $lines = @(
    "STEP=$StepName",
    "RUN_ID=$($EnrichStep.RunId)",
    "ENRICH_SESSION_ID=$($EnrichStep.EnrichSessionId)",
    "NEXT_OPTIONS=$($EnrichStep.NextOptions)",
    "DELETE_SCRIPT_COMMAND=$($EnrichStep.DeleteScriptCommand)",
    "HAS_QUICK_COMMANDS=$($EnrichStep.HasQuickCommands)"
  )

  $missing = New-Object System.Collections.ArrayList
  if ([string]::IsNullOrWhiteSpace($EnrichStep.RunId)) { [void]$missing.Add('RUN_ID missing') }
  if ([string]::IsNullOrWhiteSpace($EnrichStep.EnrichSessionId)) { [void]$missing.Add('ENRICH_SESSION_ID missing') }
  if ([string]::IsNullOrWhiteSpace($EnrichStep.NextOptions)) { [void]$missing.Add('NEXT_OPTIONS missing') }
  if ([string]::IsNullOrWhiteSpace($EnrichStep.DeleteScriptCommand)) { [void]$missing.Add('DELETE_SCRIPT_COMMAND missing') }

  if (@($missing).Count -eq 0) {
    $status = 'PASS'
    $message = 'Open enrich-session output contract fields were emitted.'
  } else {
    $message = (@($missing) -join '; ')
  }

  $lines += "STATUS=$status"
  $lines += "MESSAGE=$message"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $EnrichStep.RunId -EnrichSessionId $EnrichStep.EnrichSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Invoke-EnrichFinalizedOutputContractVerification {
  param([string]$StepName,[object]$EnrichStep)
  $start = Get-Date
  $status = 'FAIL'
  $message = ''
  $lines = @(
    "STEP=$StepName",
    "RUN_ID=$($EnrichStep.RunId)",
    "ENRICH_SESSION_ID=$($EnrichStep.EnrichSessionId)",
    "NEXT_GET_FILE=$($EnrichStep.NextGetFile)",
    "DELETE_SCRIPT_COMMAND=$($EnrichStep.DeleteScriptCommand)",
    "HAS_QUICK_COMMANDS=$($EnrichStep.HasQuickCommands)"
  )

  $missing = New-Object System.Collections.ArrayList
  if ([string]::IsNullOrWhiteSpace($EnrichStep.RunId)) { [void]$missing.Add('RUN_ID missing') }
  if ([string]::IsNullOrWhiteSpace($EnrichStep.EnrichSessionId)) { [void]$missing.Add('ENRICH_SESSION_ID missing') }
  if ([string]::IsNullOrWhiteSpace($EnrichStep.NextGetFile)) { [void]$missing.Add('NEXT_GET_FILE missing') }
  if ([string]::IsNullOrWhiteSpace($EnrichStep.DeleteScriptCommand)) { [void]$missing.Add('DELETE_SCRIPT_COMMAND missing') }

  if (@($missing).Count -eq 0) {
    $status = 'PASS'
    $message = 'Finalized enrich-session output contract fields were emitted.'
  } else {
    $message = (@($missing) -join '; ')
  }

  $lines += "STATUS=$status"
  $lines += "MESSAGE=$message"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $EnrichStep.RunId -EnrichSessionId $EnrichStep.EnrichSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Invoke-CleanupOutputContractVerification {
  param([string]$StepName,[object]$CleanupStep)
  $start = Get-Date
  $status = 'FAIL'
  $message = ''
  $lines = @(
    "STEP=$StepName",
    "RUN_ID=$($CleanupStep.RunId)",
    "CLEANUP_STATUS=$($CleanupStep.CleanupStatus)",
    "DELETE_SCRIPT_COMMAND=$($CleanupStep.DeleteScriptCommand)",
    "HAS_QUICK_COMMANDS=$($CleanupStep.HasQuickCommands)"
  )

  $missing = New-Object System.Collections.ArrayList
  if ([string]::IsNullOrWhiteSpace($CleanupStep.RunId)) { [void]$missing.Add('RUN_ID missing') }
  if ($CleanupStep.CleanupStatus -ne 'COMPLETE') { [void]$missing.Add('CLEANUP_STATUS missing or not COMPLETE') }
  if ([string]::IsNullOrWhiteSpace($CleanupStep.DeleteScriptCommand)) { [void]$missing.Add('DELETE_SCRIPT_COMMAND missing') }

  if (@($missing).Count -eq 0) {
    $status = 'PASS'
    $message = 'Cleanup output contract fields were emitted.'
  } else {
    $message = (@($missing) -join '; ')
  }

  $lines += "STATUS=$status"
  $lines += "MESSAGE=$message"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $CleanupStep.RunId -EnrichSessionId $CleanupStep.EnrichSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Invoke-AttachmentBudgetVerification {
  param([string]$StepName,[string]$ManifestPath)
  $start = Get-Date
  $status = 'FAIL'
  $message = ''
  $lines = @("STEP=$StepName","MANIFEST_PATH=$ManifestPath","SAFE_PER_FILE_KB=$SafePerFileKB","HARD_PER_FILE_KB=$HardPerFileKB","SAFE_PER_PROMPT_KB=$SafePerPromptKB","HARD_PER_PROMPT_KB=$HardPerPromptKB")
  if (-not (Test-Path -LiteralPath $ManifestPath)) {
    $message = 'Attachment budget manifest missing.'
    $lines += "STATUS=FAIL"
    $lines += "MESSAGE=$message"
  } else {
    $obj = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    $rows = @($obj.recommended_upload_files)
    $total = 0
    $violations = New-Object System.Collections.ArrayList
    foreach ($row in $rows) {
      $total += [int]$row.size_kb
      $lines += ('FILE={0} SIZE_KB={1}' -f $row.path, $row.size_kb)
      if ([int]$row.size_kb -gt $SafePerFileKB) { [void]$violations.Add(('safe per-file exceeded: {0}' -f $row.path)) }
      if ([int]$row.size_kb -gt $HardPerFileKB) { [void]$violations.Add(('hard per-file exceeded: {0}' -f $row.path)) }
    }
    $lines += "TOTAL_RECOMMENDED_KB=$total"
    if ($total -gt $SafePerPromptKB) { [void]$violations.Add('safe total exceeded') }
    if ($total -gt $HardPerPromptKB) { [void]$violations.Add('hard total exceeded') }
    if (@($violations).Count -eq 0) {
      $status = 'PASS'
      $message = 'Recommended upload set is within the configured safe budget.'
    } else {
      $status = 'FAIL'
      $message = ($violations -join '; ')
    }
    $lines += "STATUS=$status"
    $lines += "MESSAGE=$message"
  }
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $script:CollectorRunId -EnrichSessionId $script:CollectorSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Invoke-SessionBehaviorVerification {
  param([string]$StepName,[string]$StartSessionId,[string]$AddSessionId,[string]$StartMode,[string]$AddMode)
  $start = Get-Date
  $status = 'FAIL'
  $message = ''
  $lines = @("STEP=$StepName","START_SESSION_ID=$StartSessionId","ADD_SESSION_ID=$AddSessionId","START_MODE=$StartMode","ADD_MODE=$AddMode")
  if ($StartSessionId -and $AddSessionId -and ($StartSessionId -eq $AddSessionId) -and ($StartMode -eq 'CREATED_NEW_SESSION') -and ($AddMode -like 'REUSED_*')) {
    $status = 'PASS'
    $message = 'enrich-add reused the existing open session as expected.'
  } else {
    $message = 'Session reuse behavior did not match the expected start/add model.'
  }
  $lines += "STATUS=$status"
  $lines += "MESSAGE=$message"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $script:CollectorRunId -EnrichSessionId $script:CollectorSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Invoke-TargetedCollectionVerification {
  param([string]$StepName,[object]$CollectStep)
  $start = Get-Date
  $status = "FAIL"
  $message = ""
  $lines = @(
    "STEP=$StepName",
    "COLLECTION_SCOPE_PATH=$($CollectStep.CollectionScopePath)",
    "PARALLELISM_ASSESSMENT_PATH=$($CollectStep.ParallelismAssessmentPath)",
    "TARGETED_COLLECTION_PLAN_PATH=$($CollectStep.TargetedCollectionPlanPath)"
  )

  $required = @(
    @{ Label = "COLLECTION_SCOPE_PATH"; Path = $CollectStep.CollectionScopePath },
    @{ Label = "PARALLELISM_ASSESSMENT_PATH"; Path = $CollectStep.ParallelismAssessmentPath },
    @{ Label = "TARGETED_COLLECTION_PLAN_PATH"; Path = $CollectStep.TargetedCollectionPlanPath }
  )

  $missing = New-Object System.Collections.ArrayList
  foreach ($row in $required) {
    $candidate = [string]$row.Path
    if ([string]::IsNullOrWhiteSpace($candidate)) {
      [void]$missing.Add(("{0} was not emitted by the collector response." -f $row.Label))
      continue
    }
    if (-not (Test-Path -LiteralPath $candidate)) {
      [void]$missing.Add(("{0} path does not exist: {1}" -f $row.Label, $candidate))
    }
  }

  if (@($missing).Count -eq 0) {
    $scopeText = Get-Content -LiteralPath $CollectStep.CollectionScopePath -Raw
    $planText = Get-Content -LiteralPath $CollectStep.TargetedCollectionPlanPath -Raw
    if (($scopeText -match 'TARGETED_COLLECTION_SCOPE') -and ($planText -match 'TARGETED_COLLECTION_PLAN')) {
      $status = "PASS"
      $message = "Targeted collection artifacts were produced and contained the expected markers."
    } else {
      $message = "Targeted collection artifact markers were missing."
    }
  } else {
    $message = ($missing -join '; ')
  }

  $lines += "STATUS=$status"
  $lines += "MESSAGE=$message"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $script:CollectorRunId -EnrichSessionId $script:CollectorSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Invoke-ChunkingOversizeVerification {
  param([string]$StepName,[object]$CollectStep)
  $start = Get-Date
  $status = 'FAIL'
  $message = ''
  $lines = @(
    "STEP=$StepName",
    "SYNTHETIC_OVERSIZE_SOURCE_PATH=$($CollectStep.SyntheticOversizeSourcePath)",
    "CHUNK_MANIFEST_PATH=$($CollectStep.ChunkManifestPath)"
  )

  if ([string]::IsNullOrWhiteSpace([string]$CollectStep.SyntheticOversizeSourcePath) -or -not (Test-Path -LiteralPath $CollectStep.SyntheticOversizeSourcePath)) {
    $message = 'Synthetic oversize source artifact was not emitted by the collector.'
  } elseif ([string]::IsNullOrWhiteSpace([string]$CollectStep.ChunkManifestPath) -or -not (Test-Path -LiteralPath $CollectStep.ChunkManifestPath)) {
    $message = 'Chunk manifest path was not emitted by the collector.'
  } else {
    $manifest = Get-Content -LiteralPath $CollectStep.ChunkManifestPath -Raw | ConvertFrom-Json
    $chunkPaths = @($manifest.chunk_paths)
    $sourceSizeKB = [int]$manifest.source_size_kb
    $chunkCount = [int]$manifest.chunk_count
    $violations = New-Object System.Collections.ArrayList
    if ($sourceSizeKB -le $HardPerFileKB) { [void]$violations.Add('Synthetic source artifact did not exceed the hard per-file budget.') }
    if ($chunkCount -lt 2) { [void]$violations.Add('Chunk count was less than 2 for the oversized artifact.') }
    foreach ($chunkPath in $chunkPaths) {
      if (-not (Test-Path -LiteralPath $chunkPath)) {
        [void]$violations.Add(('Missing chunk path: {0}' -f $chunkPath))
        continue
      }
      $chunkSizeKB = [int][Math]::Ceiling(((Get-Item -LiteralPath $chunkPath).Length) / 1KB)
      $lines += ('CHUNK={0} SIZE_KB={1}' -f $chunkPath, $chunkSizeKB)
      if ($chunkSizeKB -gt $SafePerFileKB) {
        [void]$violations.Add(('Chunk exceeded safe per-file budget: {0}' -f $chunkPath))
      }
    }
    if (@($violations).Count -eq 0) {
      $status = 'PASS'
      $message = 'Synthetic oversized artifact was chunked into multiple smaller files within the safe per-file budget.'
    } else {
      $message = ($violations -join '; ')
    }
  }

  $lines += "STATUS=$status"
  $lines += "MESSAGE=$message"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $script:CollectorRunId -EnrichSessionId $script:CollectorSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Invoke-ChunkingReconstructionVerification {
  param([string]$StepName,[object]$CollectStep)
  $start = Get-Date
  $status = 'FAIL'
  $message = ''
  $lines = @(
    "STEP=$StepName",
    "SYNTHETIC_OVERSIZE_SOURCE_PATH=$($CollectStep.SyntheticOversizeSourcePath)",
    "CHUNK_MANIFEST_PATH=$($CollectStep.ChunkManifestPath)"
  )

  if ([string]::IsNullOrWhiteSpace([string]$CollectStep.SyntheticOversizeSourcePath) -or -not (Test-Path -LiteralPath $CollectStep.SyntheticOversizeSourcePath)) {
    $message = 'Synthetic oversize source artifact was not emitted by the collector.'
  } elseif ([string]::IsNullOrWhiteSpace([string]$CollectStep.ChunkManifestPath) -or -not (Test-Path -LiteralPath $CollectStep.ChunkManifestPath)) {
    $message = 'Chunk manifest path was not emitted by the collector.'
  } else {
    $manifest = Get-Content -LiteralPath $CollectStep.ChunkManifestPath -Raw | ConvertFrom-Json
    $chunkPaths = @($manifest.chunk_paths)
    $violations = New-Object System.Collections.ArrayList
    if (-not $manifest.reconstruction_order) {
      [void]$violations.Add('Chunk manifest does not describe reconstruction order.')
    }
    if ([int]$manifest.chunk_count -ne @($chunkPaths).Count) {
      [void]$violations.Add('Chunk count in manifest does not match listed chunk paths.')
    }
    $rebuilt = New-Object System.Text.StringBuilder
    foreach ($chunkPath in $chunkPaths) {
      if (-not (Test-Path -LiteralPath $chunkPath)) {
        [void]$violations.Add(('Missing chunk path: {0}' -f $chunkPath))
        continue
      }
      $lines += ('RECONSTRUCT_CHUNK={0}' -f $chunkPath)
      [void]$rebuilt.Append((Get-Content -LiteralPath $chunkPath -Raw))
    }
    if (@($violations).Count -eq 0) {
      $sourceText = Get-Content -LiteralPath $CollectStep.SyntheticOversizeSourcePath -Raw
      if ($rebuilt.ToString() -eq $sourceText) {
        $status = 'PASS'
        $message = 'Chunk reconstruction metadata and chunk ordering were sufficient to rebuild the synthetic oversize artifact exactly.'
      } else {
        $message = 'Chunk reconstruction did not match the original synthetic source artifact.'
      }
    } else {
      $message = ($violations -join '; ')
    }
  }

  $lines += "STATUS=$status"
  $lines += "MESSAGE=$message"
  $end = Get-Date
  $logPath = Write-HarnessLog -StepName $StepName -Lines $lines
  Add-Result -StepName $StepName -Status $status -ExitCode ($(if($status -eq 'PASS'){0}else{1})) -RunId $script:CollectorRunId -EnrichSessionId $script:CollectorSessionId -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
  if ($status -ne 'PASS' -and -not $ContinueOnError) { throw $message }
}

function Save-Summary {
  Ensure-Directory -Path $RunOutputRoot
  $summaryTxtPath = Join-Path $RunOutputRoot "summary.txt"
  $summaryJsonPath = Join-Path $RunOutputRoot "summary.json"
  $lines = @()
  $lines += ("SUITE={0}" -f $Suite)
  $lines += ("LIVE_RESPONSE_MODE={0}" -f $LiveResponseMode)
  $lines += ("PROJECT_ROOT={0}" -f $ProjectRoot)
  $lines += ("COLLECTOR_PATH={0}" -f $CollectorFullPath)
  $lines += ("MASTER_ZIP={0}" -f $MasterZipFullPath)
  $lines += ("WORKING_ZIP={0}" -f $WorkingZipPath)
  $lines += ("TEST_RUN_OUTPUT={0}" -f $RunOutputRoot)
  $lines += ("LATEST_RUN_ID={0}" -f $script:CollectorRunId)
  $lines += ("LATEST_ENRICH_SESSION_ID={0}" -f $script:CollectorSessionId)
  $lines += ""
  foreach ($r in $script:Results) {
    if ($r.CollectorReportedStatus) {
      $lines += ("STEP={0} STATUS={1} EXIT_CODE={2} COLLECTOR_STATUS={3} LOG={4}" -f $r.StepName, $r.Status, $r.ExitCode, $r.CollectorReportedStatus, $r.LogPath)
    } else {
      $lines += ("STEP={0} STATUS={1} EXIT_CODE={2} LOG={3}" -f $r.StepName, $r.Status, $r.ExitCode, $r.LogPath)
    }
  }
  Set-Content -Path $summaryTxtPath -Value $lines -Encoding UTF8
  $summaryObj = [pscustomobject]@{
    Suite = $Suite
    LiveResponseMode = [bool]$LiveResponseMode
    ProjectRoot = $ProjectRoot
    CollectorPath = $CollectorFullPath
    MasterZip = $MasterZipFullPath
    WorkingZip = $WorkingZipPath
    TestRunOutput = $RunOutputRoot
    LatestRunId = $script:CollectorRunId
    LatestEnrichSessionId = $script:CollectorSessionId
    Results = @($script:Results)
  }
  $summaryObj | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryJsonPath -Encoding UTF8
}

function Run-CoreSuite {
  Restore-WorkingZip -Reason "Core"
  $collect = Invoke-CollectorStep -StepName "01_CollectT1" -CollectorArgs @("-Quick","collect-t1")
  Assert-CollectorStepSucceeded -StepName "01_CollectT1" -CollectorStep $collect
  Invoke-CollectOutputContractVerification -StepName "ZZ_CollectOutputContract" -CollectStep $collect
  if ($collect.AttachmentBudgetManifestPath) { Invoke-AttachmentBudgetVerification -StepName "ZZ_AttachmentBudget_Collect" -ManifestPath $collect.AttachmentBudgetManifestPath }
  [void](Invoke-CollectorStep -StepName "02_EnrichStartTcp" -CollectorArgs @("-Quick","enrich-start-tcp"))
  [void](Invoke-CollectorStep -StepName "03_EnrichAddLogTextSecurity" -CollectorArgs @("-Quick","enrich-add-logtext","-Target","Security"))
  $finalize = Invoke-CollectorStep -StepName "04_EnrichFinalize" -CollectorArgs @("-Quick","enrich-finalize")
  Assert-CollectorStepSucceeded -StepName "04_EnrichFinalize" -CollectorStep $finalize
  Invoke-EnrichFinalizedOutputContractVerification -StepName "ZZ_EnrichFinalizedOutputContract" -EnrichStep $finalize
  if (-not $SkipCleanup) {
    $cleanup = Invoke-CollectorStep -StepName "05_Cleanup" -CollectorArgs @("-Quick","cleanup")
    Assert-CollectorStepSucceeded -StepName "05_Cleanup" -CollectorStep $cleanup
    Invoke-CleanupOutputContractVerification -StepName "ZZ_CleanupOutputContract" -CleanupStep $cleanup
  }
}

function Run-RetrievalSuite {
  Restore-WorkingZip -Reason "Retrieval"
  $collect = Invoke-CollectorStep -StepName "11_CollectT1" -CollectorArgs @("-Quick","collect-t1")
  Assert-CollectorStepSucceeded -StepName "11_CollectT1" -CollectorStep $collect
  if ($collect.AttachmentBudgetManifestPath) { Invoke-AttachmentBudgetVerification -StepName "ZZ_AttachmentBudget_RetrievalCollect" -ManifestPath $collect.AttachmentBudgetManifestPath }
  [void](Invoke-CollectorStep -StepName "12_EnrichStartLogRawSecurity" -CollectorArgs @("-Quick","enrich-start-lograw"))
  [void](Invoke-CollectorStep -StepName "13_EnrichFinalize" -CollectorArgs @("-Quick","enrich-finalize"))
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "14_Cleanup" -CollectorArgs @("-Quick","cleanup")) }
}

function Run-QuickAliasesSuite {
  $sampleScriptPath = $CollectorFullPath
  $sampleBinaryPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
  $sampleService = "EventLog"
  $sampleRegistry = "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
  $sampleTask = "\Microsoft\Windows\Defrag\ScheduledDefrag"
  Restore-WorkingZip -Reason "QuickAliases"
  $collect = Invoke-CollectorStep -StepName "21_CollectT1" -CollectorArgs @("-Quick","collect-t1")
  Assert-CollectorStepSucceeded -StepName "21_CollectT1" -CollectorStep $collect
  if ($collect.AttachmentBudgetManifestPath) { Invoke-AttachmentBudgetVerification -StepName "ZZ_AttachmentBudget_QuickAliasesCollect" -ManifestPath $collect.AttachmentBudgetManifestPath }
  [void](Invoke-CollectorStep -StepName "22_EnrichStartSigcheck" -CollectorArgs @("-Quick","enrich-start-sigcheck","-Target",$sampleBinaryPath))
  [void](Invoke-CollectorStep -StepName "23_EnrichFinalize_Sigcheck" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "24_EnrichStartStrings" -CollectorArgs @("-Quick","enrich-start-strings","-Target",$sampleBinaryPath))
  [void](Invoke-CollectorStep -StepName "25_EnrichFinalize_Strings" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "26_EnrichStartStreams" -CollectorArgs @("-Quick","enrich-start-streams","-Target",$sampleScriptPath))
  [void](Invoke-CollectorStep -StepName "27_EnrichFinalize_Streams" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "28_EnrichStartListDlls" -CollectorArgs @("-Quick","enrich-start-listdlls","-Target",$PID.ToString()))
  [void](Invoke-CollectorStep -StepName "29_EnrichFinalize_ListDlls" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "30_EnrichStartAccessFile" -CollectorArgs @("-Quick","enrich-start-access-file","-Target",$sampleBinaryPath))
  [void](Invoke-CollectorStep -StepName "31_EnrichFinalize_AccessFile" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "32_EnrichStartAccessService" -CollectorArgs @("-Quick","enrich-start-access-service","-Target",$sampleService))
  [void](Invoke-CollectorStep -StepName "33_EnrichFinalize_AccessService" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "34_EnrichStartAccessReg" -CollectorArgs @("-Quick","enrich-start-access-reg","-Target",$sampleRegistry))
  [void](Invoke-CollectorStep -StepName "35_EnrichFinalize_AccessReg" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "36_EnrichStartPullFile" -CollectorArgs @("-Quick","enrich-start-pull-file","-Target",$sampleBinaryPath))
  [void](Invoke-CollectorStep -StepName "37_EnrichFinalize_PullFile" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "38_EnrichStartPullScript" -CollectorArgs @("-Quick","enrich-start-pull-script","-Target",$sampleScriptPath))
  [void](Invoke-CollectorStep -StepName "39_EnrichFinalize_PullScript" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "40_EnrichStartPullTask" -CollectorArgs @("-Quick","enrich-start-pull-task","-Target",$sampleTask))
  [void](Invoke-CollectorStep -StepName "41_EnrichFinalize_PullTask" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "42_EnrichStartPullService" -CollectorArgs @("-Quick","enrich-start-pull-service","-Target",$sampleService))
  [void](Invoke-CollectorStep -StepName "43_EnrichFinalize_PullService" -CollectorArgs @("-Quick","enrich-finalize"))
  [void](Invoke-CollectorStep -StepName "44_EnrichStartPullWmiFile" -CollectorArgs @("-Quick","enrich-start-pull-wmi-file","-Target",$sampleScriptPath))
  [void](Invoke-CollectorStep -StepName "45_EnrichFinalize_PullWmiFile" -CollectorArgs @("-Quick","enrich-finalize"))
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "46_Cleanup" -CollectorArgs @("-Quick","cleanup")) }
}

function Run-SessionBehaviorSuite {
  Restore-WorkingZip -Reason "SessionBehavior"
  $collect = Invoke-CollectorStep -StepName "51_CollectT1" -CollectorArgs @("-Quick","collect-t1")
  Assert-CollectorStepSucceeded -StepName "51_CollectT1" -CollectorStep $collect
  if ($collect.AttachmentBudgetManifestPath) { Invoke-AttachmentBudgetVerification -StepName "ZZ_AttachmentBudget_SessionBehaviorCollect" -ManifestPath $collect.AttachmentBudgetManifestPath }
  $startStep = Invoke-CollectorStep -StepName "52_EnrichStartTcp" -CollectorArgs @("-Quick","enrich-start-tcp")
  Assert-CollectorStepSucceeded -StepName "52_EnrichStartTcp" -CollectorStep $startStep
  Invoke-EnrichOpenOutputContractVerification -StepName "ZZ_EnrichOpenOutputContract" -EnrichStep $startStep
  $addStep = Invoke-CollectorStep -StepName "53_EnrichAddLogTextSecurity" -CollectorArgs @("-Quick","enrich-add-logtext","-Target","Security")
  Invoke-SessionBehaviorVerification -StepName "ZZ_SessionReuseValidation" -StartSessionId $startStep.EnrichSessionId -AddSessionId $addStep.EnrichSessionId -StartMode $startStep.SessionResolutionMode -AddMode $addStep.SessionResolutionMode
  [void](Invoke-CollectorStep -StepName "54_EnrichFinalize" -CollectorArgs @("-Quick","enrich-finalize"))
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "55_Cleanup" -CollectorArgs @("-Quick","cleanup")) }
}

function Run-TargetedCollectionSuite {
  Restore-WorkingZip -Reason "TargetedCollection"
  $collect = Invoke-CollectorStep -StepName "61_CollectTargetedPopup" -CollectorArgs @("-Quick","collect-targeted-popup","-Target","User reported popup around 2026-04-08T09:00Z","-WindowStart","2026-04-08T08:45:00Z","-WindowEnd","2026-04-08T09:15:00Z")
  Assert-CollectorStepSucceeded -StepName "61_CollectTargetedPopup" -CollectorStep $collect
  if ($collect.AttachmentBudgetManifestPath) { Invoke-AttachmentBudgetVerification -StepName "ZZ_AttachmentBudget_TargetedCollect" -ManifestPath $collect.AttachmentBudgetManifestPath }
  Invoke-TargetedCollectionVerification -StepName "ZZ_TargetedCollectionValidation" -CollectStep $collect
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "62_Cleanup" -CollectorArgs @("-Quick","cleanup")) }
}

function Run-ChunkingOversizeArtifactSuite {
  Restore-WorkingZip -Reason "ChunkingOversizeArtifact"
  $collect = Invoke-CollectorStepWithEnvOverride -StepName "71_CollectT1_SyntheticOversize" -CollectorArgs @("-Quick","collect-t1") -EnvOverrides @{ 'DCOIR_TEST_SYNTHETIC_OVERSIZE_ARTIFACT_KB' = '2600' }
  Assert-CollectorStepSucceeded -StepName "71_CollectT1_SyntheticOversize" -CollectorStep $collect
  Invoke-ChunkingOversizeVerification -StepName "ZZ_ChunkingOversizeValidation" -CollectStep $collect
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "72_Cleanup" -CollectorArgs @("-Quick","cleanup")) }
}

function Run-ChunkingReconstructionMetadataSuite {
  Restore-WorkingZip -Reason "ChunkingReconstructionMetadata"
  $collect = Invoke-CollectorStepWithEnvOverride -StepName "81_CollectT1_SyntheticOversizeReconstruction" -CollectorArgs @("-Quick","collect-t1") -EnvOverrides @{ 'DCOIR_TEST_SYNTHETIC_OVERSIZE_ARTIFACT_KB' = '2600' }
  Assert-CollectorStepSucceeded -StepName "81_CollectT1_SyntheticOversizeReconstruction" -CollectorStep $collect
  Invoke-ChunkingReconstructionVerification -StepName "ZZ_ChunkingReconstructionValidation" -CollectStep $collect
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "82_Cleanup" -CollectorArgs @("-Quick","cleanup")) }
}

function Run-FailureGatesSuite {
  Restore-WorkingZip -Reason "FailureGates"

  [void](Invoke-ExpectedFailureStep -StepName "91_InvalidMode" -CollectorArgs @("-Mode","Bogus") -ExpectedOutcome 'BIND_REJECT' -ExpectedPatterns @("Mode","Bogus"))
  [void](Invoke-ExpectedFailureStep -StepName "92_InvalidTier" -CollectorArgs @("-Tier","Bogus") -ExpectedOutcome 'BIND_REJECT' -ExpectedPatterns @("Tier","Bogus"))
  [void](Invoke-ExpectedFailureStep -StepName "93_InvalidAction" -CollectorArgs @("-Mode","Enrich","-Action","Bogus") -ExpectedOutcome 'BIND_REJECT' -ExpectedPatterns @("Action","Bogus"))
  [void](Invoke-ExpectedFailureStep -StepName "94_InvalidTargetProfile" -CollectorArgs @("-TargetProfile","Bogus") -ExpectedOutcome 'BIND_REJECT' -ExpectedPatterns @("TargetProfile","Bogus"))

  [void](Invoke-ExpectedFailureStep -StepName "95_QuickHelp" -CollectorArgs @("-Quick","help") -ExpectedOutcome 'BIND_REJECT' -ExpectedPatterns @("Quick command examples:"))
  [void](Invoke-ExpectedFailureStep -StepName "96_QuickUnknown" -CollectorArgs @("-Quick","unknown-value") -ExpectedOutcome 'BIND_REJECT' -ExpectedPatterns @("Unknown -Quick value","Quick command examples:"))
  [void](Invoke-ExpectedFailureStep -StepName "97_QuickSigcheckMissingTarget" -CollectorArgs @("-Quick","enrich-start-sigcheck") -ExpectedOutcome 'BIND_REJECT' -ExpectedPatterns @("requires -Target <path>"))
  [void](Invoke-ExpectedFailureStep -StepName "98_QuickListDllsBadPid" -CollectorArgs @("-Quick","enrich-start-listdlls","-Target","abc") -ExpectedOutcome 'BIND_REJECT' -ExpectedPatterns @("requires a numeric -Target <pid>"))

  $invalidStart = Invoke-CollectorStep -StepName "99_TargetedInvalidWindowStart" -CollectorArgs @("-Quick","collect-targeted-popup","-Target","User reported popup around 2026-04-08T09:00Z","-WindowStart","not-a-date","-WindowEnd","2026-04-08T09:15:00Z")
  Assert-CollectorStepDegradedPartial -StepName "99_TargetedInvalidWindowStart" -CollectorStep $invalidStart -ExpectedPatterns @("Invalid WindowStart value [not-a-date]; falling back to hour-window behavior.")
  Invoke-TargetedCollectionVerification -StepName "ZZ_TargetedInvalidWindowStartValidation" -CollectStep $invalidStart
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "99_CleanupAfterInvalidWindowStart" -CollectorArgs @("-Quick","cleanup")) }

  $invalidEnd = Invoke-CollectorStep -StepName "100_TargetedInvalidWindowEnd" -CollectorArgs @("-Quick","collect-targeted-popup","-Target","User reported popup around 2026-04-08T09:00Z","-WindowStart","2026-04-08T08:45:00Z","-WindowEnd","not-a-date")
  Assert-CollectorStepDegradedPartial -StepName "100_TargetedInvalidWindowEnd" -CollectorStep $invalidEnd -ExpectedPatterns @("Invalid WindowEnd value [not-a-date]; falling back to hour-window behavior.")
  Invoke-TargetedCollectionVerification -StepName "ZZ_TargetedInvalidWindowEndValidation" -CollectStep $invalidEnd
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "100_CleanupAfterInvalidWindowEnd" -CollectorArgs @("-Quick","cleanup")) }

  $invertedWindow = Invoke-CollectorStep -StepName "101_TargetedInvertedWindow" -CollectorArgs @("-Quick","collect-targeted-popup","-Target","User reported popup around 2026-04-08T09:00Z","-WindowStart","2026-04-08T09:15:00Z","-WindowEnd","2026-04-08T08:45:00Z")
  Assert-CollectorStepDegradedPartial -StepName "101_TargetedInvertedWindow" -CollectorStep $invertedWindow -ExpectedPatterns @("is earlier than WindowStart")
  Invoke-TargetedCollectionVerification -StepName "ZZ_TargetedInvertedWindowValidation" -CollectStep $invertedWindow
  if (-not $SkipCleanup) { [void](Invoke-CollectorStep -StepName "101_CleanupAfterInvertedWindow" -CollectorArgs @("-Quick","cleanup")) }
}

function Run-MajorVersionSuite {
  Run-CoreSuite
  Run-QuickAliasesSuite
  Run-SessionBehaviorSuite
  Run-TargetedCollectionSuite
  Run-ChunkingOversizeArtifactSuite
  Run-ChunkingReconstructionMetadataSuite
}

Ensure-Directory -Path $RunOutputRoot
Ensure-Directory -Path $LogsDir

try {
  switch ($Suite) {
    "Core" { Run-CoreSuite }
    "Retrieval" { Run-RetrievalSuite }
    "QuickAliases" { Run-QuickAliasesSuite }
    "SessionBehavior" { Run-SessionBehaviorSuite }
    "TargetedCollection" { Run-TargetedCollectionSuite }
    "ChunkingOversizeArtifact" { Run-ChunkingOversizeArtifactSuite }
    "ChunkingReconstructionMetadata" { Run-ChunkingReconstructionMetadataSuite }
    "MajorVersion" { Run-MajorVersionSuite }
    "FailureGates" { Run-FailureGatesSuite }
    "FullRegression" {
      Run-CoreSuite
      Run-RetrievalSuite
      Run-QuickAliasesSuite
      Run-SessionBehaviorSuite
      Run-TargetedCollectionSuite
      Run-ChunkingOversizeArtifactSuite
      Run-ChunkingReconstructionMetadataSuite
      Run-FailureGatesSuite
    }
  }
  Save-Summary
} catch {
  Save-Summary
  Write-Error $_.Exception.Message
  exit 1
}
