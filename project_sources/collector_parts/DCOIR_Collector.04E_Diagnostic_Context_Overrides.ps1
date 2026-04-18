function Test-DiagnosticCollectorIsElevated {
  try {
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch {
    return $false
  }
}

function Get-NonElevatedSecurityVisibilityMessage {
  return 'Security event query returned no matching events in the current non-elevated collection context. Verify the same query in an elevated shell before concluding the window is empty.'
}

function Get-SecurityHighSignalSummaryText {
  param(
    [int]$WindowHours = 24,
    [int]$Take = 200
  )

  try {
    $ids = @(4624,4625,4648,4672,4688,4697,4698)
    $startTime = (Get-Date).AddHours(-1 * [math]::Abs($WindowHours))
    $fh = @{
      LogName = 'Security'
      StartTime = $startTime
      Id = $ids
    }

    $events = @(Get-WinEvent -FilterHashtable $fh -ErrorAction Stop |
      Sort-Object TimeCreated -Descending |
      Select-Object -First ($Take * 4))

    if (@($events).Count -eq 0) {
      if (-not (Test-DiagnosticCollectorIsElevated)) {
        $message = Get-NonElevatedSecurityVisibilityMessage
        Add-CollectorError $message
        return $message
      }
      Add-CollectorNote 'No high-signal Security events were found in the selected window.'
      return 'No high-signal Security events were found in the selected window.'
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
            $suppressReason = 'routine successful service or machine logon'
          }
        }
        4672 {
          if ($subjectIsMachine -or $subjectIsBuiltinService) {
            $suppress = $true
            $suppressReason = 'routine special privileges assignment for service or machine account'
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
    [void]$lines.Add(("WINDOW_HOURS={0}" -f $WindowHours))
    [void]$lines.Add(("RAW_EVENT_COUNT={0}" -f @($events).Count))
    [void]$lines.Add(("INTERESTING_EVENT_COUNT={0}" -f @($interesting).Count))
    [void]$lines.Add(("SUPPRESSED_EVENT_COUNT={0}" -f @($suppressed).Count))
    [void]$lines.Add('')

    $counts = $interesting | Group-Object { $_.EventRecord.Id } | Sort-Object Name
    [void]$lines.Add('INTERESTING_EVENT_COUNTS')
    foreach ($g in $counts) {
      [void]$lines.Add(("Id={0} Count={1}" -f $g.Name, $g.Count))
    }

    if (@($suppressed).Count -gt 0) {
      [void]$lines.Add('')
      [void]$lines.Add('SUPPRESSED_EVENT_COUNTS')
      $suppressedCounts = $suppressed | Group-Object Id, Reason | Sort-Object Name
      foreach ($g in $suppressedCounts) {
        [void]$lines.Add(("{0} Count={1}" -f $g.Name, $g.Count))
      }
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
      if (-not (Test-DiagnosticCollectorIsElevated)) {
        $message = Get-NonElevatedSecurityVisibilityMessage
        Add-CollectorError $message
        return $message
      }
      Add-CollectorNote 'No high-signal Security events were found in the selected window.'
      return 'No high-signal Security events were found in the selected window.'
    }
    Add-CollectorError ("Failed to collect condensed Security summary: {0}" -f $msg)
    return ("ERROR collecting condensed Security summary: {0}" -f $msg)
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
      if (($Channel -eq 'Security') -and (-not (Test-DiagnosticCollectorIsElevated))) {
        $message = Get-NonElevatedSecurityVisibilityMessage
        Add-CollectorNote $message
        return $message
      }
      Add-CollectorNote (("No events were found for channel [{0}] in the selected window." -f $Channel))
      return (("No events were found for channel [{0}] in the selected window." -f $Channel))
    }

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add(("CHANNEL={0}" -f $Channel))
    [void]$lines.Add(("WINDOW_HOURS={0}" -f $WindowHours))
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
      if (($Channel -eq 'Security') -and (-not (Test-DiagnosticCollectorIsElevated))) {
        $message = Get-NonElevatedSecurityVisibilityMessage
        Add-CollectorNote $message
        return $message
      }
      Add-CollectorNote (("No events were found for channel [{0}] in the selected window." -f $Channel))
      return (("No events were found for channel [{0}] in the selected window." -f $Channel))
    }
    Add-CollectorError (("Failed to collect event log text for [{0}]: {1}" -f $Channel, $msg))
    return (("ERROR collecting event log text for [{0}]: {1}" -f $Channel, $msg))
  }
}
