function Add-CollectorError {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:CollectorErrors.Add($Message)
  if ($Global:ErrorsLogPath) {
    Add-Content -Path $Global:ErrorsLogPath -Value ("[{0}] ERROR {1}" -f ((Get-Date).ToUniversalTime().ToString("o")), $Message) -Encoding UTF8
  }
}

function Add-CollectorNote {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:CollectorNotes.Add($Message)
}

function Add-Recommendation {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:RecommendedActions.Add($Message)
}

function Ensure-Directory {
  param([Parameter(Mandatory=$true)][string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -Path $Path -ItemType Directory -Force | Out-Null
  }
}

function Remove-IfExists {
  param([string]$LiteralPath)
  if (-not [string]::IsNullOrWhiteSpace($LiteralPath) -and (Test-Path -LiteralPath $LiteralPath)) {
    Remove-Item -LiteralPath $LiteralPath -Recurse -Force -ErrorAction SilentlyContinue
  }
}

function Join-ArgString {
  param([string[]]$Arguments)
  if (-not $Arguments) { return "" }
  $parts = foreach ($arg in $Arguments) {
    if ($null -eq $arg) { continue }
    if ($arg -match '[\s"]') {
      '"' + ($arg -replace '"', '\"') + '"'
    } else {
      $arg
    }
  }
  return ($parts -join ' ')
}

function Get-CollectorAbsolutePath {
  if (-not [string]::IsNullOrWhiteSpace($ScriptFilePath)) {
    return [System.IO.Path]::GetFullPath($ScriptFilePath)
  }
  if ($MyInvocation -and $MyInvocation.MyCommand -and $MyInvocation.MyCommand.Path) {
    return [System.IO.Path]::GetFullPath($MyInvocation.MyCommand.Path)
  }
  return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path "DCOIR_Collector.ps1"))
}

function Get-CollectorPowerShellCommandBase {
  $collectorPath = Get-CollectorAbsolutePath
  return ("powershell.exe -NoProfile -ExecutionPolicy Bypass -File '{0}'" -f $collectorPath)
}

function Get-CollectorDeleteScriptCommandText {
  $collectorPath = Get-CollectorAbsolutePath
  return ('execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command Remove-Item -LiteralPath ''{0}'' -Force" --comment "Remove uploaded DCOIR_Collector script"' -f $collectorPath)
}

function Write-StepLog {
  param(
    [string]$StepName,
    [string]$Status,
    [datetime]$StartTime,
    [datetime]$EndTime,
    [int]$ExitCode,
    [string]$Command,
    [string]$ArtifactPath,
    [string]$Message
  )

  $durationMs = [int]([TimeSpan]($EndTime - $StartTime)).TotalMilliseconds
  $txtLine = "[{0}] {1} {2} duration_ms={3} exit_code={4}" -f $EndTime.ToUniversalTime().ToString("o"), $Status, $StepName, $durationMs, $ExitCode
  if ($ArtifactPath) { $txtLine += (" artifact={0}" -f $ArtifactPath) }
  if ($Message) { $txtLine += (" message={0}" -f $Message) }

  if ($Global:ExecutionTxtPath) {
    Add-Content -Path $Global:ExecutionTxtPath -Value $txtLine -Encoding UTF8
    if ($Command) {
      Add-Content -Path $Global:ExecutionTxtPath -Value ("  COMMAND={0}" -f $Command) -Encoding UTF8
    }
  }

  if ($Global:ExecutionJsonlPath) {
    $obj = [ordered]@{
      ts_utc = $EndTime.ToUniversalTime().ToString("o")
      run_id = $Global:CurrentRunId
      step = $StepName
      status = $Status
      duration_ms = $durationMs
      exit_code = $ExitCode
      command = $Command
      artifact_path = $ArtifactPath
      message = $Message
    }
    Add-Content -Path $Global:ExecutionJsonlPath -Value ($obj | ConvertTo-Json -Compress) -Encoding UTF8
  }
}

function Invoke-ProcessCapture {
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$Arguments,
    [Parameter(Mandatory=$true)][string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )

  $startTime = Get-Date
  $commandText = $FilePath
  if ($Arguments) {
    $commandText = "$FilePath $(Join-ArgString -Arguments $Arguments)"
  }

  try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = (Join-ArgString -Arguments $Arguments)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    $endTime = Get-Date
    $status = "OK"
    $message = ""
    if (@($AllowedExitCodes) -notcontains [int]$proc.ExitCode) {
      $status = "ERROR"
      $message = ("ExitCode={0}" -f $proc.ExitCode)
      Add-CollectorError ("Step [{0}] failed. {1}. Command: {2}" -f $StepName, $message, $commandText)
    }

    Write-StepLog -StepName $StepName -Status $status -StartTime $startTime -EndTime $endTime -ExitCode $proc.ExitCode -Command $commandText -ArtifactPath "" -Message $message

    return [pscustomobject]@{
      StdOut = $stdout
      StdErr = $stderr
      ExitCode = [int]$proc.ExitCode
      Command = $commandText
      Status = $status
    }
  } catch {
    $endTime = Get-Date
    $message = $_.Exception.Message
    Add-CollectorError ("Step [{0}] raised an exception. {1}. Command: {2}" -f $StepName, $message, $commandText)
    Write-StepLog -StepName $StepName -Status "EXCEPTION" -StartTime $startTime -EndTime $endTime -ExitCode -1 -Command $commandText -ArtifactPath "" -Message $message
    return [pscustomobject]@{
      StdOut = ""
      StdErr = $message
      ExitCode = -1
      Command = $commandText
      Status = "EXCEPTION"
    }
  }
}

function Invoke-CmdCapture {
  param(
    [Parameter(Mandatory=$true)][string]$Command,
    [Parameter(Mandatory=$true)][string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  return (Invoke-ProcessCapture -FilePath "cmd.exe" -Arguments @("/c", $Command) -StepName $StepName -AllowedExitCodes $AllowedExitCodes)
}

function Get-CombinedProcessOutput {
  param($Result)
  $lines = New-Object System.Collections.ArrayList
  [void]$lines.Add(("COMMAND={0}" -f $Result.Command))
  [void]$lines.Add(("EXIT_CODE={0}" -f $Result.ExitCode))
  [void]$lines.Add("")
  [void]$lines.Add("STDOUT:")
  [void]$lines.Add(($Result.StdOut))
  [void]$lines.Add("")
  [void]$lines.Add("STDERR:")
  [void]$lines.Add(($Result.StdErr))
  return ($lines -join [Environment]::NewLine)
}

function Get-NewRunId {
  return (Get-Date -Format "yyyyMMdd_HHmmss")
}

function Get-RunRoot {
  param([string]$Root,[string]$CurrentRunId)
  return (Join-Path $Root ("DCOIR_{0}_{1}" -f $env:COMPUTERNAME, $CurrentRunId))
}

function Get-StatePath {
  param([string]$Root,[string]$CurrentRunId)
  return (Join-Path (Get-RunRoot -Root $Root -CurrentRunId $CurrentRunId) "state.json")
}

function Save-State {
  param([Parameter(Mandatory=$true)][hashtable]$State)
  $json = $State | ConvertTo-Json -Depth 12
  Set-Content -Path $State.StatePath -Value $json -Encoding UTF8
}

function Load-State {
  param([string]$Root,[string]$CurrentRunId)

  if ([string]::IsNullOrWhiteSpace($CurrentRunId)) {
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -like "DCOIR_*" } |
      Sort-Object LastWriteTime -Descending
    if (-not $dirs) {
      throw "No DCOIR run directories found under $Root"
    }
    $selected = $dirs | Select-Object -First 1
    $statePath = Join-Path $selected.FullName "state.json"
    if (-not (Test-Path -LiteralPath $statePath)) {
      throw "State file not found: $statePath"
    }
    return (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
  }

  $statePath = Get-StatePath -Root $Root -CurrentRunId $CurrentRunId
  if (-not (Test-Path -LiteralPath $statePath)) {
    throw "State file not found: $statePath"
  }

  return (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
}

function Convert-StateObjectToHashtable {
  param([object]$InputObject)

  if ($null -eq $InputObject) { return $null }

  if ($InputObject -is [System.Collections.IDictionary]) {
    $hash = @{}
    foreach ($key in $InputObject.Keys) {
      $hash[$key] = Convert-StateObjectToHashtable -InputObject $InputObject[$key]
    }
    return $hash
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
    $list = @()
    foreach ($item in $InputObject) {
      $list += ,(Convert-StateObjectToHashtable -InputObject $item)
    }
    return $list
  }

  $psProps = @()
  try { $psProps = @($InputObject.PSObject.Properties) } catch { $psProps = @() }
  if (@($psProps).Count -gt 0 -and -not ($InputObject -is [string])) {
    $hash = @{}
    foreach ($prop in $psProps) {
      $hash[$prop.Name] = Convert-StateObjectToHashtable -InputObject $prop.Value
    }
    return $hash
  }

  return $InputObject
}

function Convert-ToArrayList {
  param([object]$InputObject)

  $list = New-Object System.Collections.ArrayList

  if ($null -eq $InputObject) {
    return $list
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string]) -and -not ($InputObject -is [System.Collections.IDictionary])) {
    foreach ($item in $InputObject) {
      [void]$list.Add($item)
    }
    return $list
  }

  [void]$list.Add($InputObject)
  return $list
}

function Get-ScriptDirectory {
  if (-not [string]::IsNullOrWhiteSpace($ScriptFilePath)) {
    return (Split-Path -Parent $ScriptFilePath)
  }
  if ($PSScriptRoot) {
    return $PSScriptRoot
  }
  return (Get-Location).Path
}

function Resolve-Tool {
  param([string]$ToolsDir,[string]$BaseName)

  $candidates = @(
    (Join-Path $ToolsDir ("{0}64.exe" -f $BaseName)),
    (Join-Path $ToolsDir ("{0}.exe" -f $BaseName))
  )

  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) { return $candidate }
  }
  return $null
}

function New-SectionHeader {
  param([string]$Name)
  return @(
    ""
    ("=" * 80)
    $Name
    ("=" * 80)
    ""
  )
}

function Add-Section {
  param(
    [System.Text.StringBuilder]$Builder,
    [string]$Name,
    [string]$Text
  )
  foreach ($line in (New-SectionHeader -Name $Name)) {
    [void]$Builder.AppendLine($line)
  }
  [void]$Builder.AppendLine(($Text | Out-String))
}

function Convert-ToTextBlock {
  param([object]$InputObject)
  if ($null -eq $InputObject) { return "" }
  return ($InputObject | Out-String -Width 500)
}

function Initialize-RunStructure {
  param([string]$Root,[string]$CurrentRunId)

  $runRoot = Get-RunRoot -Root $Root -CurrentRunId $CurrentRunId
  $toolsDir = Join-Path $runRoot "tools"
  $reportsDir = Join-Path $runRoot "reports"
  $artifactsDir = Join-Path $runRoot "final_artifacts"
  $enrichSessionsDir = Join-Path $runRoot "enrich_sessions"
  $logsDir = Join-Path $runRoot "logs"
  $bundlesDir = Join-Path $runRoot "bundles"

  Ensure-Directory -Path $Root
  Ensure-Directory -Path $runRoot
  Ensure-Directory -Path $toolsDir
  Ensure-Directory -Path $reportsDir
  Ensure-Directory -Path $artifactsDir
  Ensure-Directory -Path $enrichSessionsDir
  Ensure-Directory -Path $logsDir
  Ensure-Directory -Path $bundlesDir

  return @{
    RunRoot = $runRoot
    ToolsDir = $toolsDir
    ReportsDir = $reportsDir
    ArtifactsDir = $artifactsDir
    EnrichSessionsDir = $enrichSessionsDir
    LogsDir = $logsDir
    BundlesDir = $bundlesDir
    StatePath = (Join-Path $runRoot "state.json")
  }
}

function Purge-PreviousRuns {
  param([string]$Root,[string]$CurrentPackageName)

  try {
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -like "DCOIR_*" }
    foreach ($dir in $dirs) {
      Remove-Item -LiteralPath $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
  } catch {
    Add-CollectorError "Failed to purge previous DCOIR directories: $($_.Exception.Message)"
  }

  try {
    $pkg = Join-Path $Root $CurrentPackageName
    if (Test-Path -LiteralPath $pkg) {
      Remove-Item -LiteralPath $pkg -Force -ErrorAction SilentlyContinue
    }
  } catch {
    Add-CollectorError "Failed to purge previous package file: $($_.Exception.Message)"
  }
}

function Move-PackageToOutRoot {
  param([string]$Root,[string]$CurrentPackageName)

  $scriptDir = Get-ScriptDirectory
  $sourcePath = Join-Path $scriptDir $CurrentPackageName
  $destPath = Join-Path $Root $CurrentPackageName

  if (Test-Path -LiteralPath $sourcePath) {
    if ($sourcePath -ne $destPath) {
      Move-Item -LiteralPath $sourcePath -Destination $destPath -Force
    }
    return $destPath
  }

  if (Test-Path -LiteralPath $destPath) {
    return $destPath
  }

  throw "Package not found in script directory or OutRoot: $CurrentPackageName"
}

function Expand-PackageToTools {
  param([string]$PackagePath,[string]$ToolsDir)

  try {
    Remove-IfExists -LiteralPath $ToolsDir
    Ensure-Directory -Path $ToolsDir
    Expand-Archive -LiteralPath $PackagePath -DestinationPath $ToolsDir -Force
  } catch {
    throw "Failed to expand package [$PackagePath] to [$ToolsDir]: $($_.Exception.Message)"
  }
}

function Get-BaselineArtifactPrefix {
  param([string]$Name)
  switch ($Name.ToLowerInvariant()) {
    "collection_metadata.txt" { "01" }
    "collection_notes_and_limitations.txt" { "02" }
    "time_host.txt" { "03" }
    "systeminfo.txt" { "04" }
    "whoami_all.txt" { "05" }
    "sessions.txt" { "06" }
    "logon_sessions_wmi.txt" { "07" }
    "process_inventory.txt" { "08" }
    "pslist.txt" { "09" }
    "ipconfig_all.txt" { "10" }
    "netstat_abno.txt" { "11" }
    "structured_net.txt" { "12" }
    "dns_cache.txt" { "13" }
    "route_print.txt" { "14" }
    "arp_a.txt" { "15" }
    "tcpvcon.txt" { "16" }
    "pipelist.txt" { "17" }
    "services.txt" { "18" }
    "scheduled_tasks.txt" { "19" }
    "run_hklm.txt" { "20" }
    "run_hku_loaded_users.txt" { "21" }
    "autorunsc.csv.txt" { "22" }
    "defender_status.txt" { "23" }
    "firewall_profiles.txt" { "24" }
    "security_filtered.txt" { "25" }
    "security_high_signal_summary.txt" { "25A" }
    "powershell_operational_filtered.txt" { "26" }
    "taskscheduler_operational_filtered.txt" { "27" }
    "tier2_reg_ifeo.txt" { "28" }
    "tier2_reg_winlogon.txt" { "29" }
    "tier2_reg_lsa.txt" { "30" }
    "tier2_wmi_persistence.txt" { "31" }
    "tier2_net_share.txt" { "32" }
    "tier2_net_session.txt" { "33" }
    "tier2_firewall_profiles.txt" { "34" }
    "analyst_follow_up_queue.txt" { "35" }
    default { "99" }
  }
}

function Write-ArtifactText {
  param(
    [string]$ArtifactsDir,
    [string]$Section,
    [string]$Name,
    [string]$Text
  )
  Ensure-Directory -Path $ArtifactsDir
  $prefix = Get-BaselineArtifactPrefix -Name $Name
  $safeSection = ($Section -replace '[\\/:*?"<>| ]','_')
  $safeName = ($Name -replace '[\\/:*?"<>| ]','_')
  $path = Join-Path $ArtifactsDir ("{0}_{1}_{2}" -f $prefix, $safeSection, $safeName)
  Set-Content -Path $path -Value $Text -Encoding UTF8
  return $path
}

function Get-SessionActionSequence {
  param([string]$SessionArtifactsDir)
  $count = @(Get-ChildItem -LiteralPath $SessionArtifactsDir -File -Filter "*.txt" -ErrorAction SilentlyContinue).Count
  return ($count + 1)
}

function Write-SessionArtifactText {
  param(
    [string]$SessionArtifactsDir,
    [string]$ActionName,
    [string]$TargetLabel,
    [string]$Text
  )
  Ensure-Directory -Path $SessionArtifactsDir
  $seq = Get-SessionActionSequence -SessionArtifactsDir $SessionArtifactsDir
  $safeAction = ($ActionName -replace '[\\/:*?"<>| ]','_')
  $safeTarget = ($TargetLabel -replace '[\\/:*?"<>| ]','_')
  if ([string]::IsNullOrWhiteSpace($safeTarget)) { $safeTarget = "artifact" }
  if ($safeTarget.Length -gt 80) { $safeTarget = $safeTarget.Substring(0,80) }
  $path = Join-Path $SessionArtifactsDir ("{0:D2}_ENRICH_{1}_{2}.txt" -f $seq, $safeAction, $safeTarget)
  Set-Content -Path $path -Value $Text -Encoding UTF8
  return $path
}

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

function Convert-ProcessObjectToText {
  param(
    [object]$Proc,
    [hashtable]$StartTimeMap
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

  return [pscustomobject]@{
    ProcessId       = $Proc.ProcessId
    ParentProcessId = $Proc.ParentProcessId
    Name            = $Proc.Name
    ExecutablePath  = $Proc.ExecutablePath
    CommandLine     = $Proc.CommandLine
    Owner           = $owner
    CreationTime    = $created
  }
}

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

    $raw = Get-CimInstance -ClassName Win32_Process -ErrorAction Stop
    $items = foreach ($p in $raw) {
      Convert-ProcessObjectToText -Proc $p -StartTimeMap $startTimeMap
    }
    return $items | Sort-Object ProcessId
  } catch {
    Add-CollectorError "Failed to collect Win32_Process inventory: $($_.Exception.Message)"
    return @()
  }
}

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

function Get-SecurityHighSignalSummaryText {
  param(
    [int]$WindowHours = 24,
    [int]$Take = 200
  )

  try {
    $ids = @(4624,4625,4648,4672,4688,4697,4698)
    $startTime = (Get-Date).AddHours(-1 * [math]::Abs($WindowHours))
    $fh = @{
      LogName = "Security"
      StartTime = $startTime
      Id = $ids
    }

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
    [void]$lines.Add(("WINDOW_HOURS={0}" -f $WindowHours))
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

function Get-SuspiciousProcessFindings {
  param([object[]]$Processes,[int[]]$ExcludedPids)

  $findings = New-Object System.Collections.ArrayList
  foreach ($proc in $Processes) {
    if (@($ExcludedPids) -contains [int]$proc.ProcessId) { continue }

    $reasons = New-Object System.Collections.ArrayList
    $cmd = [string]$proc.CommandLine
    $pathValue = [string]$proc.ExecutablePath
    $nameValue = [string]$proc.Name

    if ($cmd -match '(?i)(-enc\b|-encodedcommand\b|downloadstring|frombase64string|iex\b|invoke-expression\b|-w\s+hidden|-nop\b|-noni\b)') {
      [void]$reasons.Add("suspicious PowerShell style command line")
    }
    if ($cmd -match '(?i)(mshta\.exe.*http|regsvr32\.exe.*(http|scrobj)|rundll32\.exe.*(appdata|temp|programdata)|wscript\.exe|cscript\.exe)') {
      [void]$reasons.Add("suspicious LOLBin usage")
    }
    if ($pathValue -match '(?i)\\AppData\\|\\Temp\\|\\ProgramData\\') {
      [void]$reasons.Add("process running from high-risk path")
    }
    if ($nameValue -match '^(powershell|pwsh|rundll32|regsvr32|mshta|wscript|cscript|cmd|certutil|bitsadmin|wmic|psexec)(\.exe)?$') {
      [void]$reasons.Add("living-off-the-land process")
    }

    if (@($reasons).Count -gt 0) {
      [void]$findings.Add([pscustomobject]@{
        ProcessId = $proc.ProcessId
        Name = $proc.Name
        ExecutablePath = $proc.ExecutablePath
        CommandLine = $proc.CommandLine
        Reasons = ($reasons -join '; ')
      })
    }
  }
  return $findings
}

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
      Add-CollectorNote ("No events were found for channel [{0}] in the selected window." -f $Channel)
      return ("No events were found for channel [{0}] in the selected window." -f $Channel)
    }

    $lines = New-Object System.Collections.ArrayList
    [void]$lines.Add(("CHANNEL={0}" -f $Channel))
    [void]$lines.Add(("WINDOW_HOURS={0}" -f $WindowHours))
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

function Get-CmdText {
  param(
    [string]$Command,
    [string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  $result = Invoke-CmdCapture -Command $Command -StepName $StepName -AllowedExitCodes $AllowedExitCodes
  return (Get-CombinedProcessOutput -Result $result)
}

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

function Invoke-ToolToText {
  param(
    [string]$ToolPath,
    [string[]]$Arguments,
    [string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  $result = Invoke-ProcessCapture -FilePath $ToolPath -Arguments $Arguments -StepName $StepName -AllowedExitCodes $AllowedExitCodes
  return (Get-CombinedProcessOutput -Result $result)
}

function New-StageName {
  param([string]$Prefix,[string]$Extension)
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  $guid = ([guid]::NewGuid().ToString("N")).Substring(0,8)
  return ("{0}_{1}_{2}_{3}{4}" -f $Prefix, $env:COMPUTERNAME, $ts, $guid, $Extension)
}

function Get-ServiceBinaryPath {
  param([string]$Name)
  try {
    $svc = Get-CimInstance -ClassName Win32_Service -Filter ("Name='{0}'" -f ($Name -replace "'", "''")) -ErrorAction Stop
    if (-not $svc) { return $null }
    $pn = [string]$svc.PathName
    if ([string]::IsNullOrWhiteSpace($pn)) { return $null }
    if ($pn.StartsWith('"')) {
      return ($pn -replace '^"([^"]+)".*$', '$1')
    }
    return ($pn -replace '^([^\s]+).*$', '$1')
  } catch {
    Add-CollectorError "Failed to resolve service binary for [$Name]: $($_.Exception.Message)"
    return $null
  }
}

function Stage-PathCopy {
  param([string]$SourcePath,[string]$StagedDir)
  if (-not (Test-Path -LiteralPath $SourcePath)) {
    throw "Path not found: $SourcePath"
  }
  Ensure-Directory -Path $StagedDir
  $leaf = Split-Path -Leaf $SourcePath
  $dest = Join-Path $StagedDir (New-StageName -Prefix ("STAGED_" + $leaf) -Extension "")
  Copy-Item -LiteralPath $SourcePath -Destination $dest -Force
  return $dest
}

function Get-TaskXml {
  param([string]$TaskName)
  try {
    $result = Invoke-ProcessCapture -FilePath "schtasks.exe" -Arguments @("/query","/tn",$TaskName,"/xml") -StepName "ENRICH_PULL_TASK_XML"
    return (Get-CombinedProcessOutput -Result $result)
  } catch {
    Add-CollectorError "Failed to export task XML for [$TaskName]: $($_.Exception.Message)"
    return "ERROR exporting task XML: $($_.Exception.Message)"
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

  $ms = [math]::Abs($WindowHours) * 3600000
  $systemParts = @("TimeCreated[timediff(@SystemTime) <= $ms]")
  if ($Ids -and @($Ids).Count -gt 0) {
    $idExpr = "(" + (($Ids | ForEach-Object { "EventID=$_"} ) -join " or ") + ")"
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

function Get-ToolMap {
  param([string]$ToolsDir)
  return @{
    accesschk = Resolve-Tool -ToolsDir $ToolsDir -BaseName "accesschk"
    autorunsc = Resolve-Tool -ToolsDir $ToolsDir -BaseName "autorunsc"
    listdlls = Resolve-Tool -ToolsDir $ToolsDir -BaseName "listdlls"
    pipelist = Resolve-Tool -ToolsDir $ToolsDir -BaseName "pipelist"
    pslist = Resolve-Tool -ToolsDir $ToolsDir -BaseName "pslist"
    sigcheck = Resolve-Tool -ToolsDir $ToolsDir -BaseName "sigcheck"
    streams = Resolve-Tool -ToolsDir $ToolsDir -BaseName "streams"
    strings = Resolve-Tool -ToolsDir $ToolsDir -BaseName "strings"
    tcpvcon = Resolve-Tool -ToolsDir $ToolsDir -BaseName "tcpvcon"
  }
}

function Get-CommandAvailabilityTable {
  param([hashtable]$ToolMap)
  $rows = foreach ($key in ($ToolMap.Keys | Sort-Object)) {
    [pscustomobject]@{
      Tool = $key
      Present = [bool]($ToolMap[$key])
      Path = $ToolMap[$key]
    }
  }
  return ($rows | Format-Table -AutoSize | Out-String -Width 500)
}

function New-Manifest {
  param(
    [string]$ManifestPath,
    [hashtable]$State,
    [string]$ModeName,
    [string]$TierName,
    [string[]]$Files,
    [hashtable]$ToolMap,
    [hashtable]$Extra
  )

  $manifest = [ordered]@{
    host = $env:COMPUTERNAME
    run_id = $State.RunId
    mode = $ModeName
    tier = $TierName
    script_version = $ScriptVersion
    created_local = (Get-Date).ToString("o")
    created_utc = (Get-Date).ToUniversalTime().ToString("o")
    files = @($Files)
    notes = @($Global:CollectorNotes)
    errors = @($Global:CollectorErrors)
    recommendations = @($Global:RecommendedActions)
    tool_map = $ToolMap
    extra = $Extra
  }
  Set-Content -Path $ManifestPath -Value ($manifest | ConvertTo-Json -Depth 12) -Encoding UTF8
  return $ManifestPath
}

function New-BundleZip {
  param(
    [string]$BundlesDir,
    [string]$BundleName,
    [string[]]$Paths
  )

  Ensure-Directory -Path $BundlesDir
  $bundlePath = Join-Path $BundlesDir $BundleName
  if (Test-Path -LiteralPath $bundlePath) {
    Remove-Item -LiteralPath $bundlePath -Force -ErrorAction SilentlyContinue
  }
  $existing = @($Paths | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
  if (@($existing).Count -eq 0) {
    throw "No bundle inputs were found."
  }
  Compress-Archive -LiteralPath $existing -DestinationPath $bundlePath -CompressionLevel Optimal -Force
  return $bundlePath
}
