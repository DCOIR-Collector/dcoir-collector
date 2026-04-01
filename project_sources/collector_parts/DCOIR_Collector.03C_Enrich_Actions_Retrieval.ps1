function Invoke-EnrichmentAction-Retrieval {
  param(
    [hashtable]$State,
    [hashtable]$Session,
    [hashtable]$ToolMap
  )

  $sessionArtifactsDir = $Session.ArtifactsDir
  $sessionStagedDir = $Session.StagedDir
  $sessionSummaryPath = $Session.SummaryPath
  $sessionLogsDir = $Session.LogsDir

  $stagedPath = $null
  $reason = $null
  $targetDetails = $null
  $outputText = $null
  $interpretation = $null
  $nextStep = $null

  switch ($Action) {
    "LogRaw" {
      if (-not $LogName) { throw "LogRaw requires -LogName" }
      $reason = "Raw EVTX export for analyst workstation review."
      $targetDetails = "LogName=$LogName; Hours=$Hours; EventIds=$($EventId -join ',')"
      $safeLogName = ($LogName -replace '[\\/:*?"<>|]','_')
      $stagedPath = Join-Path $sessionStagedDir (New-StageName -Prefix ("STAGED_LogRaw_" + $safeLogName) -Extension ".evtx")
      Export-FilteredEvtx -LogChannel $LogName -WindowHours $Hours -Ids $EventId -OutPath $stagedPath -ScratchDir $sessionLogsDir
      $outputText = "Raw EVTX exported and staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Open the EVTX in Event Viewer on the analyst workstation with Action > Open Saved Log."
      $nextStep = "Retrieve the EVTX with get-file and review it in Event Viewer."
    }
    "PullSuspiciousFile" {
      if (-not $Path) { throw "PullSuspiciousFile requires -Path" }
      $reason = "Stage a suspicious file for analyst retrieval."
      $targetDetails = "Path=$Path"
      $stagedPath = Stage-PathCopy -SourcePath $Path -StagedDir $sessionStagedDir
      $outputText = "Suspicious file staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Retrieve the file with get-file, then review locally with sigcheck and strings or upload to a sandbox if policy allows."
      $nextStep = "After retrieval, run sigcheck and strings on the analyst workstation."
    }
    "PullScriptOrConfig" {
      if (-not $Path) { throw "PullScriptOrConfig requires -Path" }
      $reason = "Stage a script or configuration file for analyst review."
      $targetDetails = "Path=$Path"
      $stagedPath = Stage-PathCopy -SourcePath $Path -StagedDir $sessionStagedDir
      $outputText = "Script or config staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Retrieve the file, open it in a text editor, and upload plain text to the AFRICOM SOC IR AI."
      $nextStep = "If the file references other paths or URLs, follow the next most suspicious reference."
    }
    "PullTaskXml" {
      if (-not $Path) { throw "PullTaskXml requires -Path with the task name, for example \\Microsoft\\Windows\\TaskName" }
      $reason = "Export scheduled task XML for analyst review."
      $targetDetails = "TaskName=$Path"
      $taskXml = Get-TaskXml -TaskName $Path
      $stagedPath = Join-Path $sessionStagedDir (New-StageName -Prefix "STAGED_TASK_XML" -Extension ".xml")
      Set-Content -Path $stagedPath -Value $taskXml -Encoding UTF8
      $outputText = "Task XML exported and staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Review author, principal, triggers, actions, working directory, and command arguments."
      $nextStep = "If the action points to a file path, stage that file next."
    }
    "PullServiceBinary" {
      if (-not $ServiceName) { throw "PullServiceBinary requires -ServiceName" }
      $reason = "Stage the binary referenced by a suspicious service."
      $targetDetails = "ServiceName=$ServiceName"
      $svcPath = Get-ServiceBinaryPath -Name $ServiceName
      if (-not $svcPath) { throw "Unable to resolve service binary path for service [$ServiceName]." }
      $stagedPath = Stage-PathCopy -SourcePath $svcPath -StagedDir $sessionStagedDir
      $outputText = "Service binary staged for retrieval.`r`nSERVICE_BINARY_PATH=$svcPath`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Retrieve the binary, then review locally with sigcheck and strings or upload to a sandbox if policy allows."
      $nextStep = "If the binary is unsigned or suspicious, correlate with service creation or modification events."
    }
    "PullWmiReferencedFile" {
      if (-not $Path) { throw "PullWmiReferencedFile requires -Path" }
      $reason = "Stage a file referenced by suspicious WMI persistence."
      $targetDetails = "Path=$Path"
      $stagedPath = Stage-PathCopy -SourcePath $Path -StagedDir $sessionStagedDir
      $outputText = "WMI-referenced file staged for retrieval.`r`nSTAGED_PATH=$stagedPath"
      $interpretation = "Review the referenced script or binary as a persistence payload."
      $nextStep = "Correlate the file with WMI filter and consumer details in Tier 2 output."
    }
    default {
      throw "Unsupported enrichment action: $Action"
    }
  }

  $targetLabel = $Action
  if ($Path) { $targetLabel = $Path }
  elseif ($ServiceName) { $targetLabel = $ServiceName }
  elseif ($RegistryPath) { $targetLabel = $RegistryPath }
  elseif ($LogName) { $targetLabel = $LogName }
  elseif ($TargetPid) { $targetLabel = "PID_$TargetPid" }

  $actionBuilder = New-Object System.Text.StringBuilder
  Add-Section -Builder $actionBuilder -Name "ENRICHMENT_METADATA" -Text (
    @(
      "CollectorVersion=$ScriptVersion"
      "Mode=Enrich"
      "Action=$Action"
      "Host=$env:COMPUTERNAME"
      "RunId=$($State.RunId)"
      "EnrichSessionId=$($Session.SessionId)"
      "TimeLocal=$(Get-Date -Format o)"
      "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
      "SessionRoot=$($Session.SessionRoot)"
    ) -join [Environment]::NewLine
  )
  Add-Section -Builder $actionBuilder -Name "TRIGGER_REASON" -Text $reason
  Add-Section -Builder $actionBuilder -Name "TARGET_DETAILS" -Text $targetDetails
  Add-Section -Builder $actionBuilder -Name "ACTION_OUTPUT" -Text $outputText
  Add-Section -Builder $actionBuilder -Name "ANALYST_INTERPRETATION_GUIDE" -Text $interpretation
  Add-Section -Builder $actionBuilder -Name "NEXT_BEST_STEP" -Text $nextStep
  if (@($Global:CollectorErrors).Count -gt 0) {
    Add-Section -Builder $actionBuilder -Name "ERRORS" -Text ($Global:CollectorErrors -join [Environment]::NewLine)
  }

  $artifactPath = Write-SessionArtifactText -SessionArtifactsDir $sessionArtifactsDir -ActionName $Action -TargetLabel $targetLabel -Text $actionBuilder.ToString()
  Add-Content -Path $sessionSummaryPath -Value $actionBuilder.ToString() -Encoding UTF8

  $Session.ActionCount = [int]$Session.ActionCount + 1

  return @{
    ReportPath = $sessionSummaryPath
    ActionArtifactPath = $artifactPath
    StagedPath = $stagedPath
  }
}
