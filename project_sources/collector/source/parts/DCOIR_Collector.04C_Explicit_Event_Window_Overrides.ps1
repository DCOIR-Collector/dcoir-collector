<#
.SYNOPSIS
DCOIR collector explicit event-window helpers.

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
