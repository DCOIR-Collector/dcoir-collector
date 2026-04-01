param(
  [ValidateSet("Core","Retrieval","QuickAliases","FullRegression")]
  [string]$Suite = "Core",

  [string]$CollectorPath = ".\DCOIR_Collector.ps1",

  [string]$OutputRoot = ".\TestResults",

  [string]$MasterZipPath = ".\assets\DCOIR_Collector.zip",

  [switch]$ContinueOnError,

  [switch]$SkipCleanup
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

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

function Get-FileSha256 {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
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
    $logPath = Write-HarnessLog -StepName $stepName -Lines @(
      "STEP=$stepName",
      "STATUS=FAIL",
      "MESSAGE=Master zip not found.",
      "MASTER_ZIP=$MasterZipFullPath",
      "WORKING_ZIP=$WorkingZipPath"
    )
    Add-Result -StepName $stepName -Status "FAIL" -ExitCode 1 -RunId $null -EnrichSessionId $null -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end
    throw ("Master zip not found: {0}" -f $MasterZipFullPath)
  }

  Copy-Item -LiteralPath $MasterZipFullPath -Destination $WorkingZipPath -Force
  $masterHash = Get-FileSha256 -Path $MasterZipFullPath
  $workingHash = Get-FileSha256 -Path $WorkingZipPath
  $status = if ($masterHash -and $workingHash -and $masterHash -eq $workingHash) { "PASS" } else { "FAIL" }
  $end = Get-Date

  $logPath = Write-HarnessLog -StepName $stepName -Lines @(
    "STEP=$stepName",
    "STATUS=$status",
    "MASTER_ZIP=$MasterZipFullPath",
    "WORKING_ZIP=$WorkingZipPath",
    "MASTER_SHA256=$masterHash",
    "WORKING_SHA256=$workingHash"
  )
  Add-Result -StepName $stepName -Status $status -ExitCode ($(if($status -eq "PASS"){0}else{1})) -RunId $null -EnrichSessionId $null -CollectorReportedStatus $null -LogPath $logPath -Start $start -End $end

  Write-Host ""
  Write-Host ("[{0}] {1}" -f $status, $stepName)
  Write-Host ("Log: {0}" -f $logPath)
  Write-Host ("MASTER_ZIP={0}" -f $MasterZipFullPath)
  Write-Host ("WORKING_ZIP={0}" -f $WorkingZipPath)

  if ($status -ne "PASS" -and -not $ContinueOnError) {
    throw ("Failed to restage working zip for {0}" -f $Reason)
  }
}

function Resolve-CollectorStepStatus {
  param(
    [int]$ExitCode,
    [string]$CollectorReportedStatus
  )

  if ($ExitCode -ne 0) {
    return "FAIL"
  }

  if ($CollectorReportedStatus -eq "PARTIAL_SUCCESS") {
    return "PARTIAL_SUCCESS"
  }

  return "PASS"
}

function Invoke-CollectorStep {
  param(
    [Parameter(Mandatory=$true)][string]$StepName,
    [Parameter(Mandatory=$true)][string[]]$CollectorArgs
  )

  Ensure-Directory -Path $LogsDir

  $invokeArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $CollectorFullPath
  ) + $CollectorArgs

  $displayArgs = Build-ArgumentString -Args $invokeArgs

  $start = Get-Date
  $allOutput = & powershell.exe @invokeArgs 2>&1
  $exitCode = $LASTEXITCODE
  $end = Get-Date

  $stdout = ($allOutput | ForEach-Object {
    if ($null -eq $_) { "" } else { $_.ToString() }
  }) -join [Environment]::NewLine
  $stderr = ""
  $collectorReportedStatus = Parse-OutputValue -Text $stdout -Key "STATUS"

  $logLines = New-Object System.Collections.ArrayList
  [void]$logLines.Add("STEP=$StepName")
  [void]$logLines.Add("START=$($start.ToString('o'))")
  [void]$logLines.Add("END=$($end.ToString('o'))")
  [void]$logLines.Add(("DURATION_MS={0}" -f [int][Math]::Round(($end - $start).TotalMilliseconds)))
  [void]$logLines.Add("EXIT_CODE=$exitCode")
  if ($collectorReportedStatus) {
    [void]$logLines.Add("COLLECTOR_STATUS=$collectorReportedStatus")
  }
  [void]$logLines.Add(("COMMAND=powershell.exe {0}" -f $displayArgs))
  [void]$logLines.Add("")
  [void]$logLines.Add("STDOUT:")
  [void]$logLines.Add($stdout)
  [void]$logLines.Add("")
  [void]$logLines.Add("STDERR:")
  [void]$logLines.Add($stderr)
  $logPath = Write-HarnessLog -StepName $StepName -Lines $logLines

  $status = Resolve-CollectorStepStatus -ExitCode $exitCode -CollectorReportedStatus $collectorReportedStatus
  $runId = Parse-OutputValue -Text $stdout -Key "RUN_ID"
  $sessionId = Parse-OutputValue -Text $stdout -Key "ENRICH_SESSION_ID"

  if ($runId) { $script:CollectorRunId = $runId }
  if ($sessionId) { $script:CollectorSessionId = $sessionId }

  Add-Result -StepName $StepName -Status $status -ExitCode $exitCode -RunId $runId -EnrichSessionId $sessionId -CollectorReportedStatus $collectorReportedStatus -LogPath $logPath -Start $start -End $end

  Write-Host ""
  Write-Host ("[{0}] {1}" -f $status, $StepName)
  Write-Host ("Log: {0}" -f $logPath)
  if ($runId) { Write-Host ("RUN_ID={0}" -f $runId) }
  if ($sessionId) { Write-Host ("ENRICH_SESSION_ID={0}" -f $sessionId) }
  if ($collectorReportedStatus) { Write-Host ("COLLECTOR_STATUS={0}" -f $collectorReportedStatus) }
  Write-Host $stdout

  if ($exitCode -ne 0 -and -not $ContinueOnError) {
    throw ("Step failed: {0}" -f $StepName)
  }
}

function Save-Summary {
  Ensure-Directory -Path $RunOutputRoot
  $summaryTxtPath = Join-Path $RunOutputRoot "summary.txt"
  $summaryJsonPath = Join-Path $RunOutputRoot "summary.json"

  $lines = @()
  $lines += ("SUITE={0}" -f $Suite)
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

  Write-Host ""
  Write-Host ("SUMMARY_TXT={0}" -f $summaryTxtPath)
  Write-Host ("SUMMARY_JSON={0}" -f $summaryJsonPath)
}

function Run-CoreSuite {
  Restore-WorkingZip -Reason "Core"
  Invoke-CollectorStep -StepName "01_CollectT1" -CollectorArgs @("-Quick","collect-t1")
  Invoke-CollectorStep -StepName "02_EnrichStartTcp" -CollectorArgs @("-Quick","enrich-start-tcp")
  Invoke-CollectorStep -StepName "03_EnrichAddLogTextSecurity" -CollectorArgs @("-Quick","enrich-add-logtext","-Target","Security")
  Invoke-CollectorStep -StepName "04_EnrichFinalize" -CollectorArgs @("-Quick","enrich-finalize")
  if (-not $SkipCleanup) {
    Invoke-CollectorStep -StepName "05_Cleanup" -CollectorArgs @("-Quick","cleanup")
  }
}

function Run-RetrievalSuite {
  Restore-WorkingZip -Reason "Retrieval"
  Invoke-CollectorStep -StepName "11_CollectT1" -CollectorArgs @("-Quick","collect-t1")
  Invoke-CollectorStep -StepName "12_EnrichStartLogRawSecurity" -CollectorArgs @("-Quick","enrich-start-lograw","-Target","Security")
  Invoke-CollectorStep -StepName "13_EnrichFinalize" -CollectorArgs @("-Quick","enrich-finalize")
  if (-not $SkipCleanup) {
    Invoke-CollectorStep -StepName "14_Cleanup" -CollectorArgs @("-Quick","cleanup")
  }
}

function Run-QuickAliasesSuite {
  $sampleScriptPath = $CollectorFullPath
  $sampleBinaryPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
  $sampleService = "EventLog"
  $sampleRegistry = "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
  $sampleTask = "\Microsoft\Windows\Defrag\ScheduledDefrag"

  Restore-WorkingZip -Reason "QuickAliases"
  Invoke-CollectorStep -StepName "21_CollectT1" -CollectorArgs @("-Quick","collect-t1")
  Invoke-CollectorStep -StepName "22_EnrichStartSigcheck" -CollectorArgs @("-Quick","enrich-start-sigcheck","-Target",$sampleBinaryPath)
  Invoke-CollectorStep -StepName "23_EnrichFinalize_Sigcheck" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "24_EnrichStartStrings" -CollectorArgs @("-Quick","enrich-start-strings","-Target",$sampleBinaryPath)
  Invoke-CollectorStep -StepName "25_EnrichFinalize_Strings" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "26_EnrichStartStreams" -CollectorArgs @("-Quick","enrich-start-streams","-Target",$sampleScriptPath)
  Invoke-CollectorStep -StepName "27_EnrichFinalize_Streams" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "28_EnrichStartListDlls" -CollectorArgs @("-Quick","enrich-start-listdlls","-Target",$PID.ToString())
  Invoke-CollectorStep -StepName "29_EnrichFinalize_ListDlls" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "30_EnrichStartAccessFile" -CollectorArgs @("-Quick","enrich-start-access-file","-Target",$sampleBinaryPath)
  Invoke-CollectorStep -StepName "31_EnrichFinalize_AccessFile" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "32_EnrichStartAccessService" -CollectorArgs @("-Quick","enrich-start-access-service","-Target",$sampleService)
  Invoke-CollectorStep -StepName "33_EnrichFinalize_AccessService" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "34_EnrichStartAccessReg" -CollectorArgs @("-Quick","enrich-start-access-reg","-Target",$sampleRegistry)
  Invoke-CollectorStep -StepName "35_EnrichFinalize_AccessReg" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "36_EnrichStartPullFile" -CollectorArgs @("-Quick","enrich-start-pull-file","-Target",$sampleBinaryPath)
  Invoke-CollectorStep -StepName "37_EnrichFinalize_PullFile" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "38_EnrichStartPullScript" -CollectorArgs @("-Quick","enrich-start-pull-script","-Target",$sampleScriptPath)
  Invoke-CollectorStep -StepName "39_EnrichFinalize_PullScript" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "40_EnrichStartPullTask" -CollectorArgs @("-Quick","enrich-start-pull-task","-Target",$sampleTask)
  Invoke-CollectorStep -StepName "41_EnrichFinalize_PullTask" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "42_EnrichStartPullService" -CollectorArgs @("-Quick","enrich-start-pull-service","-Target",$sampleService)
  Invoke-CollectorStep -StepName "43_EnrichFinalize_PullService" -CollectorArgs @("-Quick","enrich-finalize")
  Invoke-CollectorStep -StepName "44_EnrichStartPullWmiFile" -CollectorArgs @("-Quick","enrich-start-pull-wmi-file","-Target",$sampleScriptPath)
  Invoke-CollectorStep -StepName "45_EnrichFinalize_PullWmiFile" -CollectorArgs @("-Quick","enrich-finalize")
  if (-not $SkipCleanup) {
    Invoke-CollectorStep -StepName "46_Cleanup" -CollectorArgs @("-Quick","cleanup")
  }
}

Ensure-Directory -Path $RunOutputRoot
Ensure-Directory -Path $LogsDir

try {
  switch ($Suite) {
    "Core" { Run-CoreSuite }
    "Retrieval" { Run-RetrievalSuite }
    "QuickAliases" { Run-QuickAliasesSuite }
    "FullRegression" {
      Run-CoreSuite
      Run-RetrievalSuite
      Run-QuickAliasesSuite
    }
  }
  Save-Summary
} catch {
  Save-Summary
  Write-Error $_.Exception.Message
  exit 1
}
