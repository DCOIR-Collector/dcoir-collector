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
