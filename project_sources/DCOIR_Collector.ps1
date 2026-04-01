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
  [string]$Target2
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Continue"
$ScriptFilePath = $MyInvocation.MyCommand.Path
$ScriptVersion = "3.1.5"

$Global:CollectorErrors = New-Object System.Collections.ArrayList
$Global:CollectorNotes = New-Object System.Collections.ArrayList
$Global:RecommendedActions = New-Object System.Collections.ArrayList
$Global:ExecutionTxtPath = $null
$Global:ExecutionJsonlPath = $null
$Global:ErrorsLogPath = $null
$Global:CurrentRunId = $null

$collectorPartsRoot = Join-Path (Split-Path -Parent $ScriptFilePath) "collector_parts"
$collectorPartFiles = @(
  "DCOIR_Collector.01_Core_State_And_Utilities.ps1",
  "DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1",
  "DCOIR_Collector.03A_Enrich_Session_State.ps1",
  "DCOIR_Collector.03B_Enrich_Actions_Review.ps1",
  "DCOIR_Collector.03C_Enrich_Actions_Retrieval.ps1",
  "DCOIR_Collector.04_Quick_Interface_And_Output.ps1",
  "DCOIR_Collector.05_Main_Entry.ps1"
)

foreach ($partFile in $collectorPartFiles) {
  $partPath = Join-Path $collectorPartsRoot $partFile
  if (-not (Test-Path -LiteralPath $partPath)) {
    throw "Required collector part file missing: $partPath"
  }
  . $partPath
}
