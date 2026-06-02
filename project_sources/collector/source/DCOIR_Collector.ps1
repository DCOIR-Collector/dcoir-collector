<#
.SYNOPSIS
DCOIR collector source wrapper.

.DESCRIPTION
Loads the maintained collector source parts in deterministic order for source-mode
execution. The runtime package builder compiles these same parts into the delivery
runtime.
#>

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

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

function Resolve-DCOIRRuntimePath {
  foreach ($candidate in @($PSCommandPath, $MyInvocation.PSCommandPath, $MyInvocation.MyCommand.Path)) {
    if (Test-DCOIRRuntimePathCandidate -Path $candidate) {
      return [System.IO.Path]::GetFullPath($candidate)
    }
  }

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

$collectorPartsRoot = Join-Path (Split-Path -Parent $ScriptFilePath) "parts"
$collectorPartFiles = @(
  "DCOIR_Collector.01_Core_State_And_Utilities.ps1",
  "DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1",
  "DCOIR_Collector.03A_Enrich_Session_State.ps1",
  "DCOIR_Collector.03B_Enrich_Actions_Review.ps1",
  "DCOIR_Collector.03C_Enrich_Actions_Retrieval.ps1",
  "DCOIR_Collector.04_Quick_Interface_And_Output.ps1",
  "DCOIR_Collector.04B_Feature_Wave_Targeted_Collection.ps1",
  "DCOIR_Collector.04C_Explicit_Event_Window_Overrides.ps1",
  "DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1",
  "DCOIR_Collector.04E_Diagnostic_Context_Overrides.ps1",
  "DCOIR_Collector.04F_PR186_Review_Fixes.ps1",
  "DCOIR_Collector.04G_PR186_External_Review_Fixes.ps1",
  "DCOIR_Collector.05_Main_Entry.ps1"
)

foreach ($partFile in $collectorPartFiles) {
  $partPath = Join-Path $collectorPartsRoot $partFile
  if (-not (Test-Path -LiteralPath $partPath)) {
    throw "Required collector part file missing: $partPath"
  }
  . $partPath
}
