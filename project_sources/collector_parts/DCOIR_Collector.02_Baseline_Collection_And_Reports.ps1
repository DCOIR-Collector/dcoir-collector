function Get-CollectorUploadBudget {
  return @{
    HardPerFileKB = 1000
    HardTotalKB = 2000
    SafePerFileKB = 900
    SafeTotalKB = 1800
  }
}

function Get-FileSizeKB {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) { return 0 }
  return [int][Math]::Ceiling(((Get-Item -LiteralPath $Path).Length) / 1KB)
}

function Convert-ToSafeJsonText {
  param([object]$InputObject)
  return (($InputObject | ConvertTo-Json -Depth 12) + [Environment]::NewLine)
}

function New-CollectUploadArtifacts {
  param([hashtable]$State,[hashtable]$Baseline)

  $budget = Get-CollectorUploadBudget
  $artifactMap = $Baseline.ArtifactMap
  $recommendedPaths = @()

  foreach ($key in @(
    'collection_metadata',
    'collection_notes_and_limitations',
    'security_high_signal_summary',
    'process_inventory',
    'structured_net',
    'defender_status',
    'analyst_follow_up_queue'
  )) {
    if ($artifactMap.ContainsKey($key) -and (Test-Path -LiteralPath $artifactMap[$key])) {
      $recommendedPaths += $artifactMap[$key]
    }
  }

  if ($State.MetadataReportPath -and (Test-Path -LiteralPath $State.MetadataReportPath)) {
    $recommendedPaths = @($State.MetadataReportPath) + $recommendedPaths
  }

  $recommended = New-Object System.Collections.ArrayList
  $safeTotal = 0
  foreach ($path in $recommendedPaths) {
    $sizeKB = Get-FileSizeKB -Path $path
    $safeTotal += $sizeKB
    [void]$recommended.Add([ordered]@{
      path = $path
      relative_path = [string](Resolve-Path -LiteralPath $path | ForEach-Object { $_.Path.Replace($State.RunRoot + '\\', '') })
      size_kb = $sizeKB
      within_safe_per_file = ($sizeKB -le $budget.SafePerFileKB)
      within_hard_per_file = ($sizeKB -le $budget.HardPerFileKB)
    })
  }

  $setStatus = if (($safeTotal -le $budget.SafeTotalKB) -and (@($recommended | Where-Object { -not $_.within_safe_per_file }).Count -eq 0)) {
    'SAFE_DEFAULT_SET'
  } elseif (($safeTotal -le $budget.HardTotalKB) -and (@($recommended | Where-Object { -not $_.within_hard_per_file }).Count -eq 0)) {
    'HARD_LIMIT_ONLY'
  } else {
    'EXCEEDS_ENVIRONMENT_BUDGET'
  }

  $uploadSummaryPath = Join-Path $State.ReportsDir ("DCOIR_UPLOAD_SUMMARY_{0}_{1}.txt" -f $env:COMPUTERNAME, $State.RunId)
  $uploadManifestPath = Join-Path $State.ReportsDir ("DCOIR_ATTACHMENT_BUDGET_MANIFEST_{0}_{1}.json.txt" -f $env:COMPUTERNAME, $State.RunId)

  $summaryLines = @(
    "CollectorVersion=$ScriptVersion",
    "RunId=$($State.RunId)",
    "WorkflowPhase=CollectBaseline",
    "UploadModel=ChunkFirst",
    "DoNotAssumeMonolithicBaselineUpload=true",
    "HardPerFileKB=$($budget.HardPerFileKB)",
    "HardTotalKB=$($budget.HardTotalKB)",
    "SafePerFileKB=$($budget.SafePerFileKB)",
    "SafeTotalKB=$($budget.SafeTotalKB)",
    "DefaultSetStatus=$setStatus",
    "RecommendedUploadTotalKB=$safeTotal",
    "",
    "Recommended files for Gemini upload by default:"
  )
  foreach ($row in $recommended) {
    $summaryLines += ('- {0} [{1} KB]' -f $row.path, $row.size_kb)
  }
  $summaryLines += ""
  $summaryLines += "Default guidance:"
  $summaryLines += "- Prefer this upload summary, the metadata report, and the listed representative artifacts."
  $summaryLines += "- Do not assume the large merged baseline report is upload-safe in the office Gemini environment."
  $summaryLines += "- If this set must be trimmed further, keep metadata, follow-up queue, security high-signal summary, and one representative process/network artifact first."

  Set-Content -Path $uploadSummaryPath -Value $summaryLines -Encoding UTF8

  $manifestObj = [ordered]@{
    run_id = $State.RunId
    workflow_phase = 'collect_baseline'
    upload_model = 'chunk_first'
    budget = $budget
    default_set_status = $setStatus
    recommended_upload_total_kb = $safeTotal
    recommended_upload_files = @($recommended)
    baseline_report_path = $State.BaselineReportPath
    metadata_report_path = $State.MetadataReportPath
    note = 'The merged baseline report may be useful for local analyst review but is no longer the default Gemini-facing upload surface.'
  }
  Set-Content -Path $uploadManifestPath -Value (Convert-ToSafeJsonText -InputObject $manifestObj) -Encoding UTF8

  return @{
    UploadSummaryPath = $uploadSummaryPath
    UploadManifestPath = $uploadManifestPath
    DefaultSetStatus = $setStatus
    RecommendedUploadTotalKB = $safeTotal
    RecommendedUploadCount = @($recommended).Count
  }
}

function Get-Tier2PersistenceText {
  param([hashtable]$State,[hashtable]$ToolMap)

  $sb = New-Object System.Text.StringBuilder
  $regIfeo = Get-CmdText -Command 'reg query "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options" /s' -StepName "TIER2_REG_IFEO"
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TIER2_DEEP_CHECKS" -Name "tier2_reg_ifeo.txt" -Text $regIfeo)
  Add-Section -Builder $sb -Name "TIER2_REG_IFEO" -Text $regIfeo

  $regWinlogon = Get-CmdText -Command 'reg query "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /s' -StepName "TIER2_REG_WINLOGON"
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TIER2_DEEP_CHECKS" -Name "tier2_reg_winlogon.txt" -Text $regWinlogon)
  Add-Section -Builder $sb -Name "TIER2_REG_WINLOGON" -Text $regWinlogon

  $regLsa = Get-CmdText -Command 'reg query "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /s' -StepName "TIER2_REG_LSA"
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TIER2_DEEP_CHECKS" -Name "tier2_reg_lsa.txt" -Text $regLsa)
  Add-Section -Builder $sb -Name "TIER2_REG_LSA" -Text $regLsa

  try {
    $wmiText = Get-CimInstance -Namespace root\subscription -ClassName __EventFilter,CommandLineEventConsumer,ActiveScriptEventConsumer,FilterToConsumerBinding -ErrorAction Stop |
      Format-List * | Out-String -Width 500
  } catch {
    $wmiText = "ERROR collecting WMI persistence data: $($_.Exception.Message)"
    Add-CollectorError $wmiText
  }
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TIER2_DEEP_CHECKS" -Name "tier2_wmi_persistence.txt" -Text $wmiText)
  Add-Section -Builder $sb -Name "TIER2_WMI_PERSISTENCE" -Text $wmiText

  $netShare = Get-CmdText -Command 'net share' -StepName "TIER2_NET_SHARE"
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TIER2_DEEP_CHECKS" -Name "tier2_net_share.txt" -Text $netShare)
  Add-Section -Builder $sb -Name "TIER2_NET_SHARE" -Text $netShare

  $netSession = Get-CmdText -Command 'net session' -StepName "TIER2_NET_SESSION" -AllowedExitCodes @(0,2)
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TIER2_DEEP_CHECKS" -Name "tier2_net_session.txt" -Text $netSession)
  Add-Section -Builder $sb -Name "TIER2_NET_SESSION" -Text $netSession

  $fw = Get-CmdText -Command 'netsh advfirewall show allprofiles' -StepName "TIER2_FIREWALL_PROFILES"
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TIER2_DEEP_CHECKS" -Name "tier2_firewall_profiles.txt" -Text $fw)
  Add-Section -Builder $sb -Name "TIER2_FIREWALL_PROFILES" -Text $fw

  return $sb.ToString()
}

function New-BaselineReport {
  param([hashtable]$State,[hashtable]$ToolMap)

  $artifactPaths = New-Object System.Collections.ArrayList
  $artifactMap = @{}
  $sb = New-Object System.Text.StringBuilder

  $metaText = @(
    "CollectorVersion=$ScriptVersion"
    "Mode=Collect"
    "Tier=$Tier"
    "Hours=$Hours"
    "Host=$env:COMPUTERNAME"
    "RunId=$($State.RunId)"
    "UserContext=$([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
    "TimeLocal=$(Get-Date -Format o)"
    "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
    "RunRoot=$($State.RunRoot)"
    "ReportsDir=$($State.ReportsDir)"
    "ArtifactsDir=$($State.ArtifactsDir)"
    "EnrichSessionsDir=$($State.EnrichSessionsDir)"
  ) -join [Environment]::NewLine
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_METADATA" -Name "collection_metadata.txt" -Text $metaText
  [void]$artifactPaths.Add($p); $artifactMap['collection_metadata'] = $p
  Add-Section -Builder $sb -Name "COLLECTION_METADATA" -Text $metaText

  $limitationLines = @(
    "Offline profile hives were not loaded by design.",
    "Only loaded HKU user Run keys were collected.",
    "Raw EVTX files are not part of baseline collection. Log text is exported for baseline review.",
    "Current run files remain in place until Cleanup runs.",
    "A new Collect run purges prior DCOIR run folders and the prior package zip.",
    "The merged baseline report remains useful for local analyst review, but it is no longer the default Gemini-facing upload surface. Prefer the upload summary and representative artifacts."
  )
  if (@($Global:CollectorNotes).Count -gt 0) {
    $limitationLines += ""
    $limitationLines += "Collection notes:"
    $limitationLines += $Global:CollectorNotes
  }
  if (@($Global:CollectorErrors).Count -gt 0) {
    $limitationLines += ""
    $limitationLines += "Collection errors seen so far:"
    $limitationLines += $Global:CollectorErrors
  }
  $limitationText = ($limitationLines -join [Environment]::NewLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_NOTES_AND_LIMITATIONS" -Name "collection_notes_and_limitations.txt" -Text $limitationText
  [void]$artifactPaths.Add($p); $artifactMap['collection_notes_and_limitations'] = $p
  Add-Section -Builder $sb -Name "COLLECTION_NOTES_AND_LIMITATIONS" -Text $limitationText

  $timeHostText = Get-CmdText -Command 'date /t & time /t & hostname & ver' -StepName "HOST_DATE_TIME_HOSTNAME"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "HOST_BASELINE" -Name "time_host.txt" -Text $timeHostText
  [void]$artifactPaths.Add($p); $artifactMap['time_host'] = $p
  $systemInfoText = Get-CmdText -Command 'systeminfo' -StepName "HOST_SYSTEMINFO"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "HOST_BASELINE" -Name "systeminfo.txt" -Text $systemInfoText
  [void]$artifactPaths.Add($p); $artifactMap['systeminfo'] = $p
  Add-Section -Builder $sb -Name "HOST_BASELINE" -Text (@($timeHostText, "", $systemInfoText) -join [Environment]::NewLine)

  $whoamiText = Get-CmdText -Command 'whoami /all' -StepName "IDENTITY_WHOAMI_ALL"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "whoami_all.txt" -Text $whoamiText
  [void]$artifactPaths.Add($p); $artifactMap['whoami_all'] = $p
  $sessionsText = Get-CmdText -Command 'query user & qwinsta' -StepName "IDENTITY_QUERY_USER_QWINSTA"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "sessions.txt" -Text $sessionsText
  [void]$artifactPaths.Add($p); $artifactMap['sessions'] = $p
  $logonSessionsWmiText = Get-LogonSessionsWmiText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "logon_sessions_wmi.txt" -Text $logonSessionsWmiText
  [void]$artifactPaths.Add($p); $artifactMap['logon_sessions_wmi'] = $p
  Add-Section -Builder $sb -Name "IDENTITY_AND_SESSION_CONTEXT" -Text (@($whoamiText, "", $sessionsText, "", $logonSessionsWmiText) -join [Environment]::NewLine)

  $procInventory = Get-ProcessInventory
  $excludedPids = @([int]$PID)
  try {
    $selfProc = Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId={0}" -f $PID) -ErrorAction Stop
    if ($selfProc.ParentProcessId) { $excludedPids += [int]$selfProc.ParentProcessId }
  } catch { }
  $procInventoryText = Convert-ToTextBlock -InputObject ($procInventory | Select-Object ProcessId, ParentProcessId, Name, Owner, ExecutablePath, CreationTime, CommandLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PROCESS_EXECUTION_CONTEXT" -Name "process_inventory.txt" -Text $procInventoryText
  [void]$artifactPaths.Add($p); $artifactMap['process_inventory'] = $p
  $procParts = @($procInventoryText)
  if ($ToolMap['pslist']) {
    $pslistText = Invoke-ToolToText -ToolPath $ToolMap['pslist'] -Arguments @('-accepteula','-nobanner','-t') -StepName "SYSINTERNALS_PSLIST"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PROCESS_EXECUTION_CONTEXT" -Name "pslist.txt" -Text $pslistText
    [void]$artifactPaths.Add($p); $artifactMap['pslist'] = $p
    $procParts += ""
    $procParts += $pslistText
  }
  Add-Section -Builder $sb -Name "PROCESS_EXECUTION_CONTEXT" -Text ($procParts -join [Environment]::NewLine)

  $ipconfigText = Get-CmdText -Command 'ipconfig /all' -StepName "NETWORK_IPCONFIG"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "ipconfig_all.txt" -Text $ipconfigText
  [void]$artifactPaths.Add($p); $artifactMap['ipconfig_all'] = $p
  $netstatText = Get-CmdText -Command 'netstat -abno' -StepName "NETWORK_NETSTAT"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "netstat_abno.txt" -Text $netstatText
  [void]$artifactPaths.Add($p); $artifactMap['netstat_abno'] = $p
  $structuredNetText = Get-BaselineNetText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "structured_net.txt" -Text $structuredNetText
  [void]$artifactPaths.Add($p); $artifactMap['structured_net'] = $p
  $dnsText = Get-CmdText -Command 'ipconfig /displaydns' -StepName "NETWORK_DNS_CACHE"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "dns_cache.txt" -Text $dnsText
  [void]$artifactPaths.Add($p); $artifactMap['dns_cache'] = $p
  $routeText = Get-CmdText -Command 'route print' -StepName "NETWORK_ROUTE_PRINT"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "route_print.txt" -Text $routeText
  [void]$artifactPaths.Add($p); $artifactMap['route_print'] = $p
  $arpText = Get-CmdText -Command 'arp -a' -StepName "NETWORK_ARP_A"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "arp_a.txt" -Text $arpText
  [void]$artifactPaths.Add($p); $artifactMap['arp_a'] = $p
  $networkParts = @($ipconfigText, "", $netstatText, "", $structuredNetText, "", $dnsText, "", $routeText, "", $arpText)
  if ($ToolMap['tcpvcon']) {
    $tcpvconText = Invoke-ToolToText -ToolPath $ToolMap['tcpvcon'] -Arguments @('-accepteula','-nobanner') -StepName "SYSINTERNALS_TCPVCON"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "tcpvcon.txt" -Text $tcpvconText
    [void]$artifactPaths.Add($p); $artifactMap['tcpvcon'] = $p
    $networkParts += ""
    $networkParts += $tcpvconText
  }
  if ($ToolMap['pipelist']) {
    $pipelistText = Invoke-ToolToText -ToolPath $ToolMap['pipelist'] -Arguments @('-accepteula','-nobanner') -StepName "SYSINTERNALS_PIPELIST"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "pipelist.txt" -Text $pipelistText
    [void]$artifactPaths.Add($p); $artifactMap['pipelist'] = $p
    $networkParts += ""
    $networkParts += $pipelistText
  }
  Add-Section -Builder $sb -Name "NETWORK_STATE" -Text ($networkParts -join [Environment]::NewLine)

  $servicesText = Get-CmdText -Command 'sc queryex type= service state= all' -StepName "PERSISTENCE_SERVICES"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "services.txt" -Text $servicesText
  [void]$artifactPaths.Add($p); $artifactMap['services'] = $p
  $tasksText = Get-CmdText -Command 'schtasks /query /fo LIST /v' -StepName "PERSISTENCE_SCHEDULED_TASKS"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "scheduled_tasks.txt" -Text $tasksText
  [void]$artifactPaths.Add($p); $artifactMap['scheduled_tasks'] = $p
  $hklmRunText = Get-RegistryQueryText -RegistryPath 'HKLM\Software\Microsoft\Windows\CurrentVersion\Run' -StepName "PERSISTENCE_HKLM_RUN"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "run_hklm.txt" -Text $hklmRunText
  [void]$artifactPaths.Add($p); $artifactMap['run_hklm'] = $p
  $hkuRunText = Get-LoadedUserRunKeysText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "run_hku_loaded_users.txt" -Text $hkuRunText
  [void]$artifactPaths.Add($p); $artifactMap['run_hku_loaded_users'] = $p
  $persistenceParts = @($servicesText, "", $tasksText, "", $hklmRunText, "", $hkuRunText)
  if ($ToolMap['autorunsc']) {
    $autorunsText = Invoke-ToolToText -ToolPath $ToolMap['autorunsc'] -Arguments @('-accepteula','-nobanner','-a','*','-c','-h','-s','*') -StepName "SYSINTERNALS_AUTORUNSC"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "autorunsc.csv.txt" -Text $autorunsText
    [void]$artifactPaths.Add($p); $artifactMap['autorunsc'] = $p
    $persistenceParts += ""
    $persistenceParts += $autorunsText
  }
  Add-Section -Builder $sb -Name "PERSISTENCE_AND_AUTOSTARTS" -Text ($persistenceParts -join [Environment]::NewLine)

  $defenderText = Get-DefenderStatusText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Name "defender_status.txt" -Text $defenderText
  [void]$artifactPaths.Add($p); $artifactMap['defender_status'] = $p
  $firewallText = Get-CmdText -Command 'netsh advfirewall show allprofiles' -StepName "SECURITY_FIREWALL_PROFILES"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Name "firewall_profiles.txt" -Text $firewallText
  [void]$artifactPaths.Add($p); $artifactMap['firewall_profiles'] = $p
  Add-Section -Builder $sb -Name "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Text (@($defenderText, "", $firewallText) -join [Environment]::NewLine)

  $securityIds = @(4624,4625,4634,4647,4648,4672,4688,4697,4698)
  $securityText = Get-EventText -Channel "Security" -WindowHours $Hours -Ids $securityIds -Take $MaxEvents
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "security_filtered.txt" -Text $securityText
  [void]$artifactPaths.Add($p); $artifactMap['security_filtered'] = $p
  $securityHighSignalText = Get-SecurityHighSignalSummaryText -WindowHours $Hours -Take ([Math]::Min($MaxEvents, 200))
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "security_high_signal_summary.txt" -Text $securityHighSignalText
  [void]$artifactPaths.Add($p); $artifactMap['security_high_signal_summary'] = $p
  $psOpText = Get-EventText -Channel "Microsoft-Windows-PowerShell/Operational" -WindowHours $Hours -Take $MaxEvents
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "powershell_operational_filtered.txt" -Text $psOpText
  [void]$artifactPaths.Add($p); $artifactMap['powershell_operational_filtered'] = $p
  $taskOpText = Get-EventText -Channel "Microsoft-Windows-TaskScheduler/Operational" -WindowHours $Hours -Take $MaxEvents
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "taskscheduler_operational_filtered.txt" -Text $taskOpText
  [void]$artifactPaths.Add($p); $artifactMap['taskscheduler_operational_filtered'] = $p
  Add-Section -Builder $sb -Name "EVENT_TIMELINE_TEXT_HIGH_SIGNAL" -Text $securityHighSignalText
  Add-Section -Builder $sb -Name "EVENT_TIMELINE_TEXT" -Text (@($securityText, "", $psOpText, "", $taskOpText) -join [Environment]::NewLine)

  if ($Tier -eq "T2") {
    Add-Section -Builder $sb -Name "TIER2_DEEP_CHECKS" -Text (Get-Tier2PersistenceText -State $State -ToolMap $ToolMap)
  }

  $findings = Get-SuspiciousProcessFindings -Processes $procInventory -ExcludedPids $excludedPids
  $collectorCommandBase = Get-CollectorPowerShellCommandBase
  if (@($findings).Count -gt 0) {
    foreach ($finding in ($findings | Select-Object -First 10)) {
      Add-Recommendation ("Suspicious process PID {0} ({1}) :: {2}" -f $finding.ProcessId, $finding.Name, $finding.Reasons)
      if ($finding.ExecutablePath) {
        $safePath = $finding.ExecutablePath
        Add-Recommendation ('Suggested next action: {0} -Mode Enrich -RunId {1} -Action SigcheckPath -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
        Add-Recommendation ('Suggested next action: {0} -Mode Enrich -RunId {1} -Action StringsPath -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
        Add-Recommendation ('Suggested next action: {0} -Mode Enrich -RunId {1} -Action PullSuspiciousFile -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
      }
    }
  } else {
    Add-Recommendation "No obvious suspicious process heuristics were triggered in baseline collection."
  }

  $followUpText = ($Global:RecommendedActions -join [Environment]::NewLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "ANALYST_FOLLOW_UP_QUEUE" -Name "analyst_follow_up_queue.txt" -Text $followUpText
  [void]$artifactPaths.Add($p); $artifactMap['analyst_follow_up_queue'] = $p
  Add-Section -Builder $sb -Name "ANALYST_FOLLOW_UP_QUEUE" -Text $followUpText

  return @{
    ReportBuilder = $sb
    ReportText = $sb.ToString()
    ArtifactPaths = $artifactPaths
    ArtifactMap = $artifactMap
  }
}

function New-MetadataReport {
  param([hashtable]$State,[hashtable]$ToolMap)

  $sb = New-Object System.Text.StringBuilder
  Add-Section -Builder $sb -Name "RUN_SUMMARY" -Text (
    @(
      "CollectorVersion=$ScriptVersion"
      "Mode=Collect"
      "Tier=$Tier"
      "Hours=$Hours"
      "Host=$env:COMPUTERNAME"
      "RunId=$($State.RunId)"
      "TimeLocal=$(Get-Date -Format o)"
      "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
      "RunRoot=$($State.RunRoot)"
      "BaselineReport=$($State.BaselineReportPath)"
      "MetadataReport=$($State.MetadataReportPath)"
      "CollectBundle=$($State.CollectBundlePath)"
      "UploadSummary=$($State.UploadSummaryPath)"
      "AttachmentBudgetManifest=$($State.UploadBudgetManifestPath)"
      "DefaultGeminiUploadSetStatus=$($State.DefaultGeminiUploadSetStatus)"
    ) -join [Environment]::NewLine
  )

  Add-Section -Builder $sb -Name "TOOL_AVAILABILITY" -Text (Get-CommandAvailabilityTable -ToolMap $ToolMap)

  $notesText = @(
    "Cleanup removes the selected run folder and the package zip.",
    "Artifact retrieval is a separate get-file step.",
    "A new Collect run purges prior DCOIR runs before starting.",
    "Follow-on Enrich sessions do not purge the current run.",
    "For Gemini uploads in the current office environment, prefer the upload summary plus representative artifacts over the monolithic baseline report."
  )
  if (@($Global:CollectorNotes).Count -gt 0) {
    $notesText += ""
    $notesText += "Notes:"
    $notesText += $Global:CollectorNotes
  }
  Add-Section -Builder $sb -Name "NOTES" -Text ($notesText -join [Environment]::NewLine)

  $errorsText = if (@($Global:CollectorErrors).Count -gt 0) { $Global:CollectorErrors -join [Environment]::NewLine } else { "No collection errors were recorded." }
  Add-Section -Builder $sb -Name "ERRORS" -Text $errorsText

  $recsText = if (@($Global:RecommendedActions).Count -gt 0) { $Global:RecommendedActions -join [Environment]::NewLine } else { "No enrichment recommendations were generated." }
  Add-Section -Builder $sb -Name "RECOMMENDED_ENRICHMENT_ACTIONS" -Text $recsText

  $workflowText = @(
    "1. Retrieve the collect bundle with get-file.",
    "2. For Gemini uploads, prefer the upload summary, metadata report, manifest, logs, and representative final_artifacts slices.",
    "3. Review the merged baseline locally when the full monolithic report is needed.",
    "4. Run one enrichment action at a time.",
    "5. Continue the same enrichment session or finalize it for ZIP retrieval.",
    "6. Keep the current run until Cleanup is explicitly run."
  ) -join [Environment]::NewLine
  Add-Section -Builder $sb -Name "WORKFLOW" -Text $workflowText

  return $sb.ToString()
}

function Write-ReportFile {
  param([string]$Path,[string]$Text)
  Set-Content -Path $Path -Value $Text -Encoding UTF8
}
