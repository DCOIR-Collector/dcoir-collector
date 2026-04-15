function Get-CollectorEffectiveEventWindow {
  param([int]$WindowHours = 24)

  $effectiveHours = [math]::Abs($WindowHours)
  if ($effectiveHours -le 0) { $effectiveHours = 24 }

  $now = Get-Date
  $parsedStart = $null
  $parsedEnd = $null

  if (-not [string]::IsNullOrWhiteSpace($WindowStart)) {
    [datetime]$tmpStart = [datetime]::MinValue
    if ([datetime]::TryParse($WindowStart, [ref]$tmpStart)) {
      $parsedStart = $tmpStart
    } else {
      Add-CollectorError ("Invalid WindowStart value [{0}]; falling back to hour-window behavior." -f $WindowStart)
    }
  }

  if (-not [string]::IsNullOrWhiteSpace($WindowEnd)) {
    [datetime]$tmpEnd = [datetime]::MinValue
    if ([datetime]::TryParse($WindowEnd, [ref]$tmpEnd)) {
      $parsedEnd = $tmpEnd
    } else {
      Add-CollectorError ("Invalid WindowEnd value [{0}]; falling back to hour-window behavior." -f $WindowEnd)
    }
  }

  if ($parsedStart -and $parsedEnd -and $parsedEnd -lt $parsedStart) {
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
    [void]$lines.Add(("WINDOW_HOURS={0}" -f $window.EffectiveHours))
    [void]$lines.Add(("HAS_EXPLICIT_TIME_WINDOW={0}" -f $window.HasExplicitWindow))
    [void]$lines.Add(("WINDOW_START={0}" -f $window.StartTime.ToString("o")))
    [void]$lines.Add(("WINDOW_END={0}" -f $(if ($window.EndTime) { $window.EndTime.ToString("o") } else { "" })))
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
    Add-CollectorError "Failed to collect condensed Security summary: $($_.Exception.Message)"
    return "ERROR collecting condensed Security summary: $($_.Exception.Message)"
  }
}

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
      return ("No events were found for channel [{0}] in the selected window." -f $Channel)
    }

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add(("CHANNEL={0}" -f $Channel))
    [void]$lines.Add(("WINDOW_HOURS={0}" -f $window.EffectiveHours))
    [void]$lines.Add(("HAS_EXPLICIT_TIME_WINDOW={0}" -f $window.HasExplicitWindow))
    [void]$lines.Add(("WINDOW_START={0}" -f $window.StartTime.ToString("o")))
    [void]$lines.Add(("WINDOW_END={0}" -f $(if ($window.EndTime) { $window.EndTime.ToString("o") } else { "" })))
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
