<#
.SYNOPSIS
DCOIR collector process, event, and baseline utility helpers.

.DESCRIPTION
Provides loaded-user Run-key collection, logon-session formatting, process inventory,
suspicious-process heuristics, event-data mapping, baseline network text, Defender status,
and registry query helpers.

.FILE NAME
DCOIR_Collector.01D_Process_Event_And_Baseline_Utilities.ps1

.INPUTS
Process objects, event records, registry paths, event data maps, and collector runtime
state used by process and baseline collection surfaces.

.OUTPUTS
Process inventory rows, suspicious-process findings, event-data maps, baseline text, and
registry or Defender status text.
#>

<#
.SYNOPSIS
Collects loaded-user HKU Run-key text.

.DESCRIPTION
Enumerates loaded HKU SID hives, collects each loaded Run key, and returns the combined
text surface. Returns a bounded explanatory message when no loaded user Run keys exist.

.FUNCTION NAME
Get-LoadedUserRunKeysText

.INPUTS
No direct parameters.

.OUTPUTS
String containing loaded-user HKU Run-key text or an explanatory/error message.
#>
function Get-LoadedUserRunKeysText {
  try {
    $lines = New-Object System.Collections.ArrayList
    $sidPattern = '^S-1-5-21-\d+-\d+-\d+-\d+$'
    $hku = Get-ChildItem -Path Registry::HKEY_USERS -ErrorAction SilentlyContinue
    foreach ($key in $hku) {
      if ($key.PSChildName -notmatch $sidPattern) { continue }
      $runPath = "Registry::HKEY_USERS\$($key.PSChildName)\Software\Microsoft\Windows\CurrentVersion\Run"
      if (Test-Path -LiteralPath $runPath) {
        [void]$lines.Add(("SID={0}" -f $key.PSChildName))
        [void]$lines.Add((Get-ItemProperty -LiteralPath $runPath | Format-List * | Out-String -Width 500))
      }
    }
    if (@($lines).Count -eq 0) {
      return "No loaded user HKU Run keys were found. Offline profile hives were not loaded by design."
    }
    return ($lines -join [Environment]::NewLine)
  } catch {
    Add-CollectorError "Failed to enumerate loaded user HKU Run keys: $($_.Exception.Message)"
    return "ERROR: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Returns the human-readable name for one Windows logon type.

.DESCRIPTION
Maps known numeric logon-type values to analyst-friendly names.

.FUNCTION NAME
Get-LogonTypeName

.INPUTS
LogonType integer.

.OUTPUTS
String logon-type name.
#>
function Get-LogonTypeName {
  param([int]$LogonType)
  switch ($LogonType) {
    0 { "System" }
    2 { "Interactive" }
    3 { "Network" }
    4 { "Batch" }
    5 { "Service" }
    7 { "Unlock" }
    8 { "NetworkCleartext" }
    9 { "NewCredentials" }
    10 { "RemoteInteractive" }
    11 { "CachedInteractive" }
    default { "Unknown" }
  }
}

<#
.SYNOPSIS
Builds the WMI logon-session text surface.

.DESCRIPTION
Collects Win32_LogonSession and Win32_LoggedOnUser association data, correlates account
rows to logon sessions, and returns an analyst-friendly text surface.

.FUNCTION NAME
Get-LogonSessionsWmiText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the WMI logon-session text surface or an error message.
#>
function Get-LogonSessionsWmiText {
  try {
    $sb = New-Object System.Text.StringBuilder
    $sessionsRaw = @(Get-CimInstance -ClassName Win32_LogonSession -ErrorAction Stop)
    $sessions = $sessionsRaw | Select-Object LogonId, LogonType, AuthenticationPackage, StartTime

    $assocRows = New-Object System.Collections.ArrayList
    $seen = @{}

    foreach ($sess in $sessionsRaw) {
      try {
        $accounts = @(Get-CimAssociatedInstance -InputObject $sess -Association Win32_LoggedOnUser -ResultClassName Win32_Account -ErrorAction Stop)
        foreach ($acct in $accounts) {
          $row = [pscustomobject]@{
            LogonId = [string]$sess.LogonId
            Domain = [string]$acct.Domain
            User = [string]$acct.Name
            SID = [string]$acct.SID
            Source = "AssociatedInstance"
          }
          $key = "{0}|{1}|{2}|{3}" -f $row.LogonId, $row.Domain, $row.User, $row.SID
          if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            [void]$assocRows.Add($row)
          }
        }
      } catch { }
    }

    $assocs = @(Get-CimInstance -ClassName Win32_LoggedOnUser -ErrorAction SilentlyContinue)
    foreach ($assoc in $assocs) {
      $ante = [string]$assoc.Antecedent
      $dep = [string]$assoc.Dependent

      $domain = ""
      $user = ""
      $sid = ""
      $logonId = ""

      if ($ante -match 'Domain="([^"]+)",Name="([^"]+)"') {
        $domain = $matches[1]
        $user = $matches[2]
      }
      if ($ante -match 'SID="([^"]+)"') {
        $sid = $matches[1]
      }
      if ($dep -match 'LogonId="?([^",]+)"?') {
        $logonId = $matches[1]
      }

      $row = [pscustomobject]@{
        LogonId = $logonId
        Domain = $domain
        User = $user
        SID = $sid
        Source = "ParsedAssociation"
      }
      $key = "{0}|{1}|{2}|{3}" -f $row.LogonId, $row.Domain, $row.User, $row.SID
      if (-not $seen.ContainsKey($key)) {
        $seen[$key] = $true
        [void]$assocRows.Add($row)
      }
    }

    [void]$sb.AppendLine("WIN32_LOGONSESSION")
    foreach ($sess in ($sessions | Sort-Object LogonId)) {
      $typeName = Get-LogonTypeName -LogonType ([int]$sess.LogonType)
      [void]$sb.AppendLine(("LogonId={0}" -f $sess.LogonId))
      [void]$sb.AppendLine(("LogonType={0} ({1})" -f $sess.LogonType, $typeName))
      [void]$sb.AppendLine(("AuthenticationPackage={0}" -f $sess.AuthenticationPackage))
      [void]$sb.AppendLine(("StartTime={0}" -f $sess.StartTime))
      $matchesForSession = @($assocRows | Where-Object { $_.LogonId -eq ([string]$sess.LogonId) })
      if (@($matchesForSession).Count -gt 0) {
        [void]$sb.AppendLine("Accounts:")
        foreach ($m in $matchesForSession | Sort-Object Domain, User, SID) {
          if ($m.SID) {
            [void]$sb.AppendLine(("  {0}\{1} SID={2} Source={3}" -f $m.Domain, $m.User, $m.SID, $m.Source))
          } else {
            [void]$sb.AppendLine(("  {0}\{1} Source={2}" -f $m.Domain, $m.User, $m.Source))
          }
        }
      }
      [void]$sb.AppendLine("-" * 60)
    }

    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("WIN32_LOGGEDONUSER_ASSOCIATIONS")
    [void]$sb.AppendLine((Convert-ToTextBlock -InputObject ($assocRows | Sort-Object LogonId, Domain, User, SID)))

    return $sb.ToString().TrimEnd()
  } catch {
    Add-CollectorError "Failed to collect WMI logon sessions: $($_.Exception.Message)"
    return "ERROR collecting WMI logon sessions: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Converts one Win32_Process object into the normalized process-inventory row.

.DESCRIPTION
Resolves owner, parent-process name, and creation time details for one process and
returns the normalized PSCustomObject used by the process inventory.

.FUNCTION NAME
Convert-ProcessObjectToText

.INPUTS
Proc object, StartTimeMap hashtable, and ProcessNameById hashtable.

.OUTPUTS
PSCustomObject containing normalized process-inventory fields.
#>
function Convert-ProcessObjectToText {
  param(
    [object]$Proc,
    [hashtable]$StartTimeMap,
    [hashtable]$ProcessNameById
  )

  $owner = ""
  try {
    $ownerInfo = Invoke-CimMethod -InputObject $Proc -MethodName GetOwner -ErrorAction Stop
    if ($ownerInfo.ReturnValue -eq 0) {
      $owner = "{0}\{1}" -f $ownerInfo.Domain, $ownerInfo.User
    }
  } catch { }

  $created = $null
  try {
    $procId = [int]$Proc.ProcessId
    if ($StartTimeMap -and $StartTimeMap.ContainsKey($procId)) {
      $created = $StartTimeMap[$procId]
    } elseif ($Proc.CreationDate) {
      $created = [System.Management.ManagementDateTimeConverter]::ToDateTime($Proc.CreationDate)
    }
  } catch { }

  $parentProcessId = $null
  try {
    if ($null -ne $Proc.ParentProcessId) {
      $parentProcessId = [int]$Proc.ParentProcessId
    }
  } catch { }

  $parentName = ""
  try {
    if ($null -ne $parentProcessId -and $ProcessNameById -and $ProcessNameById.ContainsKey($parentProcessId)) {
      $parentName = [string]$ProcessNameById[$parentProcessId]
    }
  } catch { }

  return [pscustomobject]@{
    ProcessId         = $Proc.ProcessId
    ParentProcessId   = $parentProcessId
    ParentProcessName = $parentName
    Name              = $Proc.Name
    ExecutablePath    = $Proc.ExecutablePath
    CommandLine       = $Proc.CommandLine
    Owner             = $owner
    CreationTime      = $created
  }
}

<#
.SYNOPSIS
Builds the normalized Win32_Process inventory.

.DESCRIPTION
Collects current process start times, queries Win32_Process, builds a parent-name lookup,
converts each row into the normalized process-inventory form, and returns the sorted
process list.

.FUNCTION NAME
Get-ProcessInventory

.INPUTS
No direct parameters.

.OUTPUTS
Array of normalized process-inventory rows.
#>
function Get-ProcessInventory {
  try {
    $startTimeMap = @{}
    try {
      foreach ($gp in @(Get-Process -ErrorAction SilentlyContinue)) {
        try {
          $startTimeMap[[int]$gp.Id] = $gp.StartTime
        } catch { }
      }
    } catch { }

    $raw = @(Get-CimInstance -ClassName Win32_Process -ErrorAction Stop)
    $processNameById = @{}
    foreach ($p in $raw) {
      try {
        if ($null -ne $p.ProcessId -and -not [string]::IsNullOrWhiteSpace([string]$p.Name)) {
          $processNameById[[int]$p.ProcessId] = [string]$p.Name
        }
      } catch { }
    }
    $items = foreach ($p in $raw) {
      Convert-ProcessObjectToText -Proc $p -StartTimeMap $startTimeMap -ProcessNameById $processNameById
    }
    return $items | Sort-Object ProcessId
  } catch {
    Add-CollectorError "Failed to collect Win32_Process inventory: $($_.Exception.Message)"
    return @()
  }
}

<#
.SYNOPSIS
Builds a key-value map from one event record’s EventData section.

.DESCRIPTION
Parses the event record XML and returns a hashtable containing EventData values keyed
by name or synthetic DataN names when the event field is unnamed.

.FUNCTION NAME
Get-EventDataMap

.INPUTS
EventRecord object.

.OUTPUTS
Hashtable of event-data values.
#>
function Get-EventDataMap {
  param([object]$EventRecord)

  $map = @{}
  try {
    $xml = [xml]$EventRecord.ToXml()
    if ($xml -and $xml.Event -and $xml.Event.EventData) {
      $index = 0
      foreach ($node in @($xml.Event.EventData.Data)) {
        $index += 1
        $name = [string]$node.Name
        if ([string]::IsNullOrWhiteSpace($name)) {
          $name = "Data{0}" -f $index
        }
        $value = [string]$node.'#text'
        $map[$name] = $value
      }
    }
  } catch { }
  return $map
}

<#
.SYNOPSIS
Returns one value from an event-data map.

.DESCRIPTION
Safely returns the named value from the supplied event-data map or an empty string when
no such key exists.

.FUNCTION NAME
Get-EventMapValue

.INPUTS
Map hashtable and Key string.

.OUTPUTS
String event-data value or empty string.
#>
function Get-EventMapValue {
  param(
    [hashtable]$Map,
    [string]$Key
  )
  if ($null -eq $Map) { return "" }
  if ([string]::IsNullOrWhiteSpace($Key)) { return "" }
  if ($Map.ContainsKey($Key)) {
    return [string]$Map[$Key]
  }
  return ""
}

<#
.SYNOPSIS
Returns suspicious-process heuristic findings from the process inventory.

.DESCRIPTION
Applies command-line, path, and LOLBin heuristics to the process inventory while using
parent-process context to reduce low-confidence name-only LOLBin noise. Suspicious
command-line and path indicators still produce findings.

.FUNCTION NAME
Get-SuspiciousProcessFindings

.INPUTS
Processes array and ExcludedPids integer array.

.OUTPUTS
ArrayList of suspicious process finding objects.
#>
function Get-SuspiciousProcessFindings {
  param([object[]]$Processes,[int[]]$ExcludedPids)

  $findings = New-Object System.Collections.ArrayList
  foreach ($proc in $Processes) {
    if (@($ExcludedPids) -contains [int]$proc.ProcessId) { continue }

    $reasons = New-Object System.Collections.ArrayList
    $cmd = [string]$proc.CommandLine
    $pathValue = [string]$proc.ExecutablePath
    $nameValue = [string]$proc.Name
    $parentNameValue = [string]$proc.ParentProcessName
    $nameOnlyLolbinPattern = '^(powershell|pwsh|rundll32|regsvr32|mshta|wscript|cscript|cmd|certutil|bitsadmin|wmic|psexec)(\.exe)?$'
    $benignNameOnlyLolbinPattern = '^(powershell|pwsh|cmd|wmic)(\.exe)?$'
    $knownBenignLolbinParentPattern = '^(svchost|services|trustedinstaller|tiworker|wuauclt|msiexec)(\.exe)?$'
    $isKnownBenignNameOnlyLolbin = ($nameValue -match $benignNameOnlyLolbinPattern) -and ($parentNameValue -match $knownBenignLolbinParentPattern)

    $isCollectorSelfRun = ($cmd -match '(?i)DCOIR_Collector\.ps1') -and ($nameValue -match '^(powershell|pwsh|cmd)(\.exe)?$')
    $isDefenderDlpUserAgent = ($nameValue -match '^(DlpUserAgent)(\.exe)?$') -and ($pathValue -match '(?i)\\ProgramData\\Microsoft\\Windows Defender\\Platform\\[^\\]+\\DlpUserAgent\.exe$')
    if ($isCollectorSelfRun -or $isDefenderDlpUserAgent) { continue }

    if ($cmd -match '(?i)(-enc\b|-encodedcommand\b|downloadstring|frombase64string|iex\b|invoke-expression\b|-w\s+hidden|-nop\b|-noni\b)') {
      [void]$reasons.Add("suspicious PowerShell style command line")
    }
    if ($cmd -match '(?i)(mshta\.exe.*http|regsvr32\.exe.*(http|scrobj)|rundll32\.exe.*(appdata|temp|programdata)|wscript\.exe|cscript\.exe)') {
      [void]$reasons.Add("suspicious LOLBin usage")
    }
    if ($pathValue -match '(?i)\\AppData\\|\\Temp\\|\\ProgramData\\') {
      [void]$reasons.Add("process running from high-risk path")
    }
    if ($nameValue -match $nameOnlyLolbinPattern) {
      if (-not $isKnownBenignNameOnlyLolbin -or @($reasons).Count -gt 0) {
        [void]$reasons.Add("living-off-the-land process")
      }
    }

    if (@($reasons).Count -gt 0) {
      [void]$findings.Add([pscustomobject]@{
        ProcessId = $proc.ProcessId
        ParentProcessId = $proc.ParentProcessId
        ParentProcessName = $proc.ParentProcessName
        Name = $proc.Name
        ExecutablePath = $proc.ExecutablePath
        CommandLine = $proc.CommandLine
        Reasons = ($reasons -join '; ')
      })
    }
  }
  return $findings
}

<#
.SYNOPSIS
Builds the structured TCP and UDP baseline text surface.

.DESCRIPTION
Queries Get-NetTCPConnection and Get-NetUDPEndpoint, formats both views, and returns the
combined text block.

.FUNCTION NAME
Get-BaselineNetText

.INPUTS
No direct parameters.

.OUTPUTS
String containing structured TCP and UDP text or an error message.
#>
function Get-BaselineNetText {
  try {
    $tcp = Get-NetTCPConnection -ErrorAction Stop |
      Sort-Object State, OwningProcess, LocalAddress, LocalPort |
      Select-Object State, LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess
    $udp = Get-NetUDPEndpoint -ErrorAction Stop |
      Sort-Object OwningProcess, LocalAddress, LocalPort |
      Select-Object LocalAddress, LocalPort, OwningProcess
    $text = @()
    $text += "TCP CONNECTIONS"
    $text += ($tcp | Format-Table -AutoSize | Out-String -Width 500)
    $text += ""
    $text += "UDP ENDPOINTS"
    $text += ($udp | Format-Table -AutoSize | Out-String -Width 500)
    return ($text -join [Environment]::NewLine)
  } catch {
    Add-CollectorError "Failed to collect structured TCP/UDP data: $($_.Exception.Message)"
    return "ERROR: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Collects Microsoft Defender status text.

.DESCRIPTION
Uses Get-MpComputerStatus when available and returns a formatted Defender status block,
or a bounded explanatory/error message when unavailable.

.FUNCTION NAME
Get-DefenderStatusText

.INPUTS
No direct parameters.

.OUTPUTS
String containing Defender status text or an explanatory/error message.
#>
function Get-DefenderStatusText {
  try {
    if (Get-Command Get-MpComputerStatus -ErrorAction SilentlyContinue) {
      return ((Get-MpComputerStatus | Format-List * | Out-String -Width 500).TrimEnd())
    }
    return "Get-MpComputerStatus is not available on this endpoint."
  } catch {
    Add-CollectorError "Failed to collect Defender status: $($_.Exception.Message)"
    return "ERROR: $($_.Exception.Message)"
  }
}

<#
.SYNOPSIS
Collects registry-query text with bounded absent-key handling.

.DESCRIPTION
Runs reg query for the requested registry path, returns a bounded absent-key text block
for exit code 1, and otherwise returns the combined command output text.

.FUNCTION NAME
Get-RegistryQueryText

.INPUTS
RegistryPath string and StepName string.

.OUTPUTS
String containing registry-query output or a bounded absent-key explanation.
#>
function Get-RegistryQueryText {
  param([string]$RegistryPath,[string]$StepName)

  $cmd = ('reg query "{0}"' -f $RegistryPath)
  $result = Invoke-CmdCapture -Command $cmd -StepName $StepName -AllowedExitCodes @(0,1)
  if ($result.ExitCode -eq 1) {
    $message = "Registry key absent or not readable: $RegistryPath"
    Add-CollectorNote $message
    return (@(
      "COMMAND=reg query `"$RegistryPath`""
      "EXIT_CODE=1"
      ""
      "STDOUT:"
      ""
      ""
      "STDERR:"
      $message
    ) -join [Environment]::NewLine)
  }
  return (Get-CombinedProcessOutput -Result $result)
}
