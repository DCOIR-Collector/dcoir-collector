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
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_METADATA" -Name "collection_metadata.txt" -Text $metaText))
  Add-Section -Builder $sb -Name "COLLECTION_METADATA" -Text $metaText

  $limitationLines = @(
    "Offline profile hives were not loaded by design."
    "Only loaded HKU user Run keys were collected."
    "Raw EVTX files are not part of baseline collection. Log text is exported for baseline review."
    "Current run files remain in place until Cleanup runs."
    "A new Collect run purges prior DCOIR run folders and the prior package zip."
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
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_NOTES_AND_LIMITATIONS" -Name "collection_notes_and_limitations.txt" -Text $limitationText))
  Add-Section -Builder $sb -Name "COLLECTION_NOTES_AND_LIMITATIONS" -Text $limitationText

  $timeHostText = Get-CmdText -Command 'date /t & time /t & hostname & ver' -StepName "HOST_DATE_TIME_HOSTNAME"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "HOST_BASELINE" -Name "time_host.txt" -Text $timeHostText))
  $systemInfoText = Get-CmdText -Command 'systeminfo' -StepName "HOST_SYSTEMINFO"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "HOST_BASELINE" -Name "systeminfo.txt" -Text $systemInfoText))
  Add-Section -Builder $sb -Name "HOST_BASELINE" -Text (@($timeHostText, "", $systemInfoText) -join [Environment]::NewLine)

  $whoamiText = Get-CmdText -Command 'whoami /all' -StepName "IDENTITY_WHOAMI_ALL"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "whoami_all.txt" -Text $whoamiText))
  $sessionsText = Get-CmdText -Command 'query user & qwinsta' -StepName "IDENTITY_QUERY_USER_QWINSTA"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "sessions.txt" -Text $sessionsText))
  $logonSessionsWmiText = Get-LogonSessionsWmiText
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "logon_sessions_wmi.txt" -Text $logonSessionsWmiText))
  Add-Section -Builder $sb -Name "IDENTITY_AND_SESSION_CONTEXT" -Text (@($whoamiText, "", $sessionsText, "", $logonSessionsWmiText) -join [Environment]::NewLine)

  $procInventory = Get-ProcessInventory
  $excludedPids = @([int]$PID)
  try {
    $selfProc = Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId={0}" -f $PID) -ErrorAction Stop
    if ($selfProc.ParentProcessId) { $excludedPids += [int]$selfProc.ParentProcessId }
  } catch { }
  $procInventoryText = Convert-ToTextBlock -InputObject ($procInventory | Select-Object ProcessId, ParentProcessId, Name, Owner, ExecutablePath, CreationTime, CommandLine)
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PROCESS_EXECUTION_CONTEXT" -Name "process_inventory.txt" -Text $procInventoryText))
  $procParts = @($procInventoryText)
  if ($ToolMap["pslist"]) {
    $pslistText = Invoke-ToolToText -ToolPath $ToolMap["pslist"] -Arguments @("-accepteula","-nobanner","-t") -StepName "SYSINTERNALS_PSLIST"
    [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PROCESS_EXECUTION_CONTEXT" -Name "pslist.txt" -Text $pslistText))
    $procParts += ""
    $procParts += $pslistText
  }
  Add-Section -Builder $sb -Name "PROCESS_EXECUTION_CONTEXT" -Text ($procParts -join [Environment]::NewLine)

  $ipconfigText = Get-CmdText -Command 'ipconfig /all' -StepName "NETWORK_IPCONFIG"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "ipconfig_all.txt" -Text $ipconfigText))
  $netstatText = Get-CmdText -Command 'netstat -abno' -StepName "NETWORK_NETSTAT"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "netstat_abno.txt" -Text $netstatText))
  $structuredNetText = Get-BaselineNetText
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "structured_net.txt" -Text $structuredNetText))
  $dnsText = Get-CmdText -Command 'ipconfig /displaydns' -StepName "NETWORK_DNS_CACHE"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "dns_cache.txt" -Text $dnsText))
  $routeText = Get-CmdText -Command 'route print' -StepName "NETWORK_ROUTE_PRINT"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "route_print.txt" -Text $routeText))
  $arpText = Get-CmdText -Command 'arp -a' -StepName "NETWORK_ARP_A"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "arp_a.txt" -Text $arpText))
  $networkParts = @($ipconfigText, "", $netstatText, "", $structuredNetText, "", $dnsText, "", $routeText, "", $arpText)

  if ($ToolMap["tcpvcon"]) {
    $tcpvconText = Invoke-ToolToText -ToolPath $ToolMap["tcpvcon"] -Arguments @("-accepteula","-nobanner") -StepName "SYSINTERNALS_TCPVCON"
    [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "tcpvcon.txt" -Text $tcpvconText))
    $networkParts += ""
    $networkParts += $tcpvconText
  }
  if ($ToolMap["pipelist"]) {
    $pipelistText = Invoke-ToolToText -ToolPath $ToolMap["pipelist"] -Arguments @("-accepteula","-nobanner") -StepName "SYSINTERNALS_PIPELIST"
    [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "pipelist.txt" -Text $pipelistText))
    $networkParts += ""
    $networkParts += $pipelistText
  }
  Add-Section -Builder $sb -Name "NETWORK_STATE" -Text ($networkParts -join [Environment]::NewLine)

  $servicesText = Get-CmdText -Command 'sc queryex type= service state= all' -StepName "PERSISTENCE_SERVICES"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "services.txt" -Text $servicesText))
  $tasksText = Get-CmdText -Command 'schtasks /query /fo LIST /v' -StepName "PERSISTENCE_SCHEDULED_TASKS"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "scheduled_tasks.txt" -Text $tasksText))
  $hklmRunText = Get-RegistryQueryText -RegistryPath 'HKLM\Software\Microsoft\Windows\CurrentVersion\Run' -StepName "PERSISTENCE_HKLM_RUN"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "run_hklm.txt" -Text $hklmRunText))
  $hkuRunText = Get-LoadedUserRunKeysText
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "run_hku_loaded_users.txt" -Text $hkuRunText))
  $persistenceParts = @($servicesText, "", $tasksText, "", $hklmRunText, "", $hkuRunText)
  if ($ToolMap["autorunsc"]) {
    $autorunsText = Invoke-ToolToText -ToolPath $ToolMap["autorunsc"] -Arguments @("-accepteula","-nobanner","-a","*","-c","-h","-s","*") -StepName "SYSINTERNALS_AUTORUNSC"
    [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "autorunsc.csv.txt" -Text $autorunsText))
    $persistenceParts += ""
    $persistenceParts += $autorunsText
  }
  Add-Section -Builder $sb -Name "PERSISTENCE_AND_AUTOSTARTS" -Text ($persistenceParts -join [Environment]::NewLine)

  $defenderText = Get-DefenderStatusText
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Name "defender_status.txt" -Text $defenderText))
  $firewallText = Get-CmdText -Command 'netsh advfirewall show allprofiles' -StepName "SECURITY_FIREWALL_PROFILES"
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Name "firewall_profiles.txt" -Text $firewallText))
  Add-Section -Builder $sb -Name "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Text (@($defenderText, "", $firewallText) -join [Environment]::NewLine)

  $securityIds = @(4624,4625,4634,4647,4648,4672,4688,4697,4698)
  $securityText = Get-EventText -Channel "Security" -WindowHours $Hours -Ids $securityIds -Take $MaxEvents
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "security_filtered.txt" -Text $securityText))
  $securityHighSignalText = Get-SecurityHighSignalSummaryText -WindowHours $Hours -Take ([Math]::Min($MaxEvents, 200))
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "security_high_signal_summary.txt" -Text $securityHighSignalText))
  $psOpText = Get-EventText -Channel "Microsoft-Windows-PowerShell/Operational" -WindowHours $Hours -Take $MaxEvents
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "powershell_operational_filtered.txt" -Text $psOpText))
  $taskOpText = Get-EventText -Channel "Microsoft-Windows-TaskScheduler/Operational" -WindowHours $Hours -Take $MaxEvents
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "taskscheduler_operational_filtered.txt" -Text $taskOpText))
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
  [void]$artifactPaths.Add((Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "ANALYST_FOLLOW_UP_QUEUE" -Name "analyst_follow_up_queue.txt" -Text $followUpText))
  Add-Section -Builder $sb -Name "ANALYST_FOLLOW_UP_QUEUE" -Text $followUpText

  return @{
    ReportText = $sb.ToString()
    ArtifactPaths = @($artifactPaths)
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
    ) -join [Environment]::NewLine
  )

  Add-Section -Builder $sb -Name "TOOL_AVAILABILITY" -Text (Get-CommandAvailabilityTable -ToolMap $ToolMap)

  $notesText = @(
    "Cleanup removes the selected run folder and the package zip."
    "Artifact retrieval is a separate get-file step."
    "A new Collect run purges prior DCOIR runs before starting."
    "Follow-on Enrich sessions do not purge the current run."
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
    "1. Retrieve the baseline collect bundle with get-file."
    "2. Review the merged baseline and the flat final_artifacts folder."
    "3. Run one enrichment action at a time."
    "4. Continue the same enrichment session or finalize it for ZIP retrieval."
    "5. Keep the current run until Cleanup is explicitly run."
  ) -join [Environment]::NewLine
  Add-Section -Builder $sb -Name "WORKFLOW" -Text $workflowText

  return $sb.ToString()
}

function Write-ReportFile {
  param([string]$Path,[string]$Text)
  Set-Content -Path $Path -Value $Text -Encoding UTF8
}
