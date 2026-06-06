Apply-QuickShortcut

if ($ShowVersion) {
  Write-Output (Get-CollectorVersionText)
  return
}

if ($ShowHelp) {
  Write-Output (Get-CollectorHelpText -Topic $script:ContextualHelpTopic)
  return
}

try {
  Ensure-Directory -Path $OutRoot

  switch ($Mode) {
    "Collect" {
      if ([string]::IsNullOrWhiteSpace($RunId)) {
        $RunId = Get-NewRunId
      }

      $resolvedOutRoot = if ([System.IO.Path]::IsPathRooted($OutRoot)) {
        [System.IO.Path]::GetFullPath($OutRoot)
      } else {
        [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutRoot))
      }

      Purge-PreviousRuns -Root $resolvedOutRoot -CurrentPackageName $PackageName
      $dirs = Initialize-RunStructure -Root $resolvedOutRoot -CurrentRunId $RunId
      $Global:CurrentRunId = $RunId
      $Global:ExecutionTxtPath = Join-Path $dirs.LogsDir "collect_execution_log.txt"
      $Global:ExecutionJsonlPath = Join-Path $dirs.LogsDir "collect_execution_log.jsonl"
      $Global:ErrorsLogPath = Join-Path $dirs.LogsDir "errors.log"
      Set-Content -Path $Global:ExecutionTxtPath -Value ("DCOIR Collect Execution Log`r`nRunId={0}" -f $RunId) -Encoding UTF8 -ErrorAction Stop
      Set-Content -Path $Global:ExecutionJsonlPath -Value "" -Encoding UTF8 -ErrorAction Stop
      Set-Content -Path $Global:ErrorsLogPath -Value "" -Encoding UTF8 -ErrorAction Stop

      $packagePath = Move-PackageToOutRoot -Root $resolvedOutRoot -CurrentPackageName $PackageName
      Expand-PackageToTools -PackagePath $packagePath -ToolsDir $dirs.ToolsDir

      $toolMap = Get-ToolMap -ToolsDir $dirs.ToolsDir
      $metadataReportPath = Join-Path $dirs.ReportsDir ("DCOIR_METADATA_{0}_{1}.txt" -f $env:COMPUTERNAME, $RunId)

      $state = @{
        RunId = $RunId
        Host = $env:COMPUTERNAME
        OutRoot = $resolvedOutRoot
        RunRoot = $dirs.RunRoot
        ToolsDir = $dirs.ToolsDir
        ReportsDir = $dirs.ReportsDir
        ArtifactsDir = $dirs.ArtifactsDir
        EnrichSessionsDir = $dirs.EnrichSessionsDir
        LogsDir = $dirs.LogsDir
        BundlesDir = $dirs.BundlesDir
        StatePath = $dirs.StatePath
        PackagePath = $packagePath
        MetadataReportPath = $metadataReportPath
        BaselineReportPath = $null
        UploadSummaryPath = $null
        UploadBudgetManifestPath = $null
        AnalystOverviewPath = $null
        ParallelExecutionProofPath = $null
        ExecutionContextPath = $null
        SecurityAuditPolicyPath = $null
        AuditPolicyAccessStatus = $null
        SecurityFilteredPath = $null
        SecurityHighSignalSummaryPath = $null
        NetstatPidOnlyPath = $null
        NetstatOwnerAwareStatus = $null
        IsElevated = $null
        DefaultGeminiUploadSetStatus = $null
        CollectBundlePath = $null
        CollectionScopePath = $null
        ParallelismAssessmentPath = $null
        TargetedCollectionPlanPath = $null
        SyntheticOversizeSourcePath = $null
        ChunkManifestPath = $null
        UploadSafeChunkManifestPath = $null
        EnrichSessions = @()
        EnrichSessionCounter = 0
        OpenEnrichSessionId = $null
        LastSessionResolutionMode = $null
        CreatedLocal = (Get-Date).ToString("o")
        CreatedUTC = (Get-Date).ToUniversalTime().ToString("o")
        CollectorVersion = $ScriptVersion
      }

      Initialize-ParallelBaselineCache -State $state

      $baseline = New-BaselineReport -State $state -ToolMap $toolMap
      Apply-FeatureWaveCollectEnhancements -State $state -Baseline $baseline

      $uploadArtifacts = New-CollectUploadArtifactsWithLateMetadataReport -State $state -Baseline $baseline
      $state.UploadSummaryPath = $uploadArtifacts.UploadSummaryPath
      $state.UploadBudgetManifestPath = $uploadArtifacts.UploadManifestPath
      $state.DefaultGeminiUploadSetStatus = $uploadArtifacts.DefaultSetStatus
      $state.UploadSafeChunkManifestPath = $uploadArtifacts.UploadSafeChunkManifestPath
      $state.AnalystOverviewPath = New-AnalystOverviewArtifactWithLateMetadataReport -State $state -Baseline $baseline

      $bundleName = ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId)
      $bundlePath = $null

      # Write metadata once after late-bound collect fields are populated and before manifest/bundle packaging.
      $metadataText = New-MetadataReport -State $state -ToolMap $toolMap
      $metadataReportPath = Write-ReportFile -Path $metadataReportPath -Text $metadataText
      $state.MetadataReportPath = $metadataReportPath

      $collectManifestPath = Join-Path $state.RunRoot "manifest_collect.json"
      $collectManifestFiles = @($metadataReportPath, $state.AnalystOverviewPath, $state.ParallelExecutionProofPath, $state.ExecutionContextPath, $state.SecurityAuditPolicyPath, $state.SecurityFilteredPath, $state.SecurityHighSignalSummaryPath, $state.NetstatPidOnlyPath, $state.UploadSummaryPath, $state.UploadBudgetManifestPath, $state.UploadSafeChunkManifestPath, $state.CollectionScopePath, $state.ParallelismAssessmentPath, $state.TargetedCollectionPlanPath, $Global:ExecutionTxtPath, $Global:ExecutionJsonlPath, $Global:ErrorsLogPath) + $baseline.ArtifactPaths
      $collectManifestExtra = @{
        collect_bundle = $state.CollectBundlePath
        analyst_overview = $state.AnalystOverviewPath
        parallel_execution_proof = $state.ParallelExecutionProofPath
        execution_context = $state.ExecutionContextPath
        security_audit_policy = $state.SecurityAuditPolicyPath
        audit_policy_access_status = $state.AuditPolicyAccessStatus
        security_filtered = $state.SecurityFilteredPath
        security_high_signal_summary = $state.SecurityHighSignalSummaryPath
        netstat_owner_aware_status = $state.NetstatOwnerAwareStatus
        netstat_pid_only = $state.NetstatPidOnlyPath
        is_elevated = $state.IsElevated
        upload_summary = $state.UploadSummaryPath
        attachment_budget_manifest = $state.UploadBudgetManifestPath
        default_gemini_upload_set_status = $state.DefaultGeminiUploadSetStatus
        collection_scope = $state.CollectionScopePath
        parallelism_assessment = $state.ParallelismAssessmentPath
        targeted_collection_plan = $state.TargetedCollectionPlanPath
        targeted_mode = [bool]$Targeted
        target_profile = $TargetProfile
        synthetic_oversize_source = $state.SyntheticOversizeSourcePath
        chunk_manifest = $state.ChunkManifestPath
        upload_safe_chunk_manifest = $state.UploadSafeChunkManifestPath
      }
      $collectManifest = New-Manifest -ManifestPath $collectManifestPath -State $state -ModeName "Collect" -TierName $Tier -Files $collectManifestFiles -ToolMap $toolMap -Extra $collectManifestExtra

      $bundlePath = New-BundleZip -BundlesDir $state.BundlesDir -BundleName $bundleName -Paths @(
        $metadataReportPath,
        $state.AnalystOverviewPath,
        $state.ParallelExecutionProofPath,
        $state.ExecutionContextPath,
        $state.SecurityAuditPolicyPath,
        $state.SecurityFilteredPath,
        $state.SecurityHighSignalSummaryPath,
        $state.NetstatPidOnlyPath,
        $state.UploadSummaryPath,
        $state.UploadBudgetManifestPath,
        $state.UploadSafeChunkManifestPath,
        $state.ArtifactsDir,
        $Global:ExecutionTxtPath,
        $Global:ExecutionJsonlPath,
        $Global:ErrorsLogPath,
        $collectManifest
      )
      $state.CollectBundlePath = $bundlePath
      if ($bundlePath -and $collectManifest) {
        $collectManifestExtra.collect_bundle = $state.CollectBundlePath
        $collectManifest = New-Manifest -ManifestPath $collectManifestPath -State $state -ModeName "Collect" -TierName $Tier -Files $collectManifestFiles -ToolMap $toolMap -Extra $collectManifestExtra
      }

      Save-State -State $state

      $status = "SUCCESS"
      if (@($Global:CollectorErrors).Count -gt 0) { $status = "PARTIAL_SUCCESS" }

      $collectorCommandBase = Get-CollectorResponseActionCommandBase
      $deleteScriptCommand = Get-CollectorDeleteScriptCommandText

      Write-Output ("STATUS={0}" -f $status)
      Write-Output ("RUN_ID={0}" -f $RunId)
      Write-Output ("COLLECTOR_VERSION={0}" -f $state.CollectorVersion)
      Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $state.CollectorVersion))
      if ($metadataReportPath) { Write-Output ("METADATA_REPORT_PATH={0}" -f $metadataReportPath) }
      if ($state.ExecutionContextPath) { Write-Output ("EXECUTION_CONTEXT_PATH={0}" -f $state.ExecutionContextPath) }
      if ($state.SecurityAuditPolicyPath) { Write-Output ("SECURITY_AUDIT_POLICY_PATH={0}" -f $state.SecurityAuditPolicyPath) }
      Write-Output ("AUDIT_POLICY_ACCESS_STATUS={0}" -f $state.AuditPolicyAccessStatus)
      if ($state.SecurityFilteredPath) { Write-Output ("SECURITY_FILTERED_PATH={0}" -f $state.SecurityFilteredPath) }
      if ($state.SecurityHighSignalSummaryPath) { Write-Output ("SECURITY_HIGH_SIGNAL_SUMMARY_PATH={0}" -f $state.SecurityHighSignalSummaryPath) }
      Write-Output ("IS_ELEVATED={0}" -f $state.IsElevated)
      Write-Output ("NETSTAT_OWNER_AWARE_STATUS={0}" -f $state.NetstatOwnerAwareStatus)
      if ($state.NetstatPidOnlyPath) { Write-Output ("NETSTAT_PID_ONLY_PATH={0}" -f $state.NetstatPidOnlyPath) }
      if ($state.AnalystOverviewPath) { Write-Output ("ANALYST_OVERVIEW_PATH={0}" -f $state.AnalystOverviewPath) }
      if ($state.ParallelExecutionProofPath) { Write-Output ("PARALLEL_EXECUTION_PROOF_PATH={0}" -f $state.ParallelExecutionProofPath) }
      if ($state.UploadSummaryPath) { Write-Output ("UPLOAD_SUMMARY_PATH={0}" -f $state.UploadSummaryPath) }
      if ($state.UploadBudgetManifestPath) { Write-Output ("ATTACHMENT_BUDGET_MANIFEST_PATH={0}" -f $state.UploadBudgetManifestPath) }
      if ($state.UploadSafeChunkManifestPath) { Write-Output ("UPLOAD_SAFE_CHUNK_MANIFEST_PATH={0}" -f $state.UploadSafeChunkManifestPath) }
      if ($state.CollectionScopePath) { Write-Output ("COLLECTION_SCOPE_PATH={0}" -f $state.CollectionScopePath) }
      if ($state.ParallelismAssessmentPath) { Write-Output ("PARALLELISM_ASSESSMENT_PATH={0}" -f $state.ParallelismAssessmentPath) }
      if ($state.TargetedCollectionPlanPath) { Write-Output ("TARGETED_COLLECTION_PLAN_PATH={0}" -f $state.TargetedCollectionPlanPath) }
      if ($state.SyntheticOversizeSourcePath) { Write-Output ("SYNTHETIC_OVERSIZE_SOURCE_PATH={0}" -f $state.SyntheticOversizeSourcePath) }
      if ($state.ChunkManifestPath) { Write-Output ("CHUNK_MANIFEST_PATH={0}" -f $state.ChunkManifestPath) }
      Write-Output ("DEFAULT_GEMINI_UPLOAD_SET_STATUS={0}" -f $state.DefaultGeminiUploadSetStatus)
      if ($bundlePath) {
        Write-Output ("COLLECT_BUNDLE_PATH={0}" -f $bundlePath)
        Write-Output ('NEXT_GET_FILE=get-file --path "{0}" --comment "Retrieve DCOIR collect bundle"' -f $bundlePath)
      }
      Write-Output ('CLEANUP_COMMAND=execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $collectorCommandBase)
      Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
      Write-Output ('GEMINI_UPLOAD_GUIDANCE=Prefer ANALYST_OVERVIEW_PATH, UPLOAD_SUMMARY_PATH, ATTACHMENT_BUDGET_MANIFEST_PATH, COLLECTION_SCOPE_PATH, PARALLELISM_ASSESSMENT_PATH, and representative final_artifacts slices. If UPLOAD_SAFE_CHUNK_MANIFEST_PATH exists, use it for full-fidelity oversized text artifacts after triage summaries. If TARGETED_COLLECTION_PLAN_PATH exists, include it for narrow incidents.')
      foreach ($collectorError in @($Global:CollectorErrors)) {
        if (-not [string]::IsNullOrWhiteSpace([string]$collectorError)) {
          Write-Output ("COLLECTOR_ERROR={0}" -f $collectorError)
        }
      }
      Write-QuickNextSteps -Phase "Collect"
    }

    "Enrich" {
      $loaded = Load-State -Root $OutRoot -CurrentRunId $RunId
      $state = Convert-StateObjectToHashtable -InputObject $loaded
      $Global:CurrentRunId = [string]$state.RunId

      if (-not $Action -and -not $FinalizeEnrichSession) {
        throw "Enrich mode requires -Action or -FinalizeEnrichSession."
      }

      $requireOpenSessionForFinalize = [bool]($FinalizeEnrichSession -and -not $Action -and [string]::IsNullOrWhiteSpace($EnrichSessionId))
      $session = Initialize-EnrichSession -State $state -RequestedSessionId $EnrichSessionId -ForceNew:$NewEnrichSession -RequireExistingOpenSession:$requireOpenSessionForFinalize
      if ($session -and $session.ContainsKey('CreationSkipped') -and [bool]$session.CreationSkipped) {
        $deleteScriptCommand = Get-CollectorDeleteScriptCommandText
        Write-Output "STATUS=SKIPPED"
        Write-Output ("RUN_ID={0}" -f $state.RunId)
        Write-Output ("COLLECTOR_VERSION={0}" -f [string]$state.CollectorVersion)
        Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version ([string]$state.CollectorVersion)))
        Write-Output ("PLANNED_ENRICH_SESSION_ID={0}" -f $session.SessionId)
        Write-Output ("SESSION_RESOLUTION_MODE={0}" -f $session.SessionResolutionMode)
        Write-Output "SESSION_STATUS=CREATE_SKIPPED"
        Write-Output "NEXT_OPTIONS=Re-run without -WhatIf to create the enrich session, or provide an existing -EnrichSessionId."
        Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
        return
      }

      $logStamp = Get-Date -Format "yyyyMMdd_HHmmss"
      $actionLabel = if ($Action) { $Action } else { "FinalizeSession" }
      $Global:ExecutionTxtPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_execution_log.txt" -f $actionLabel, $logStamp)
      $Global:ExecutionJsonlPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_execution_log.jsonl" -f $actionLabel, $logStamp)
      $Global:ErrorsLogPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_errors.log" -f $actionLabel, $logStamp)
      Set-Content -Path $Global:ExecutionTxtPath -Value ("DCOIR Enrich Execution Log`r`nRunId={0}`r`nEnrichSessionId={1}`r`nAction={2}`r`nSessionResolutionMode={3}" -f $state.RunId, $session.SessionId, $actionLabel, $session.SessionResolutionMode) -Encoding UTF8 -ErrorAction Stop
      Set-Content -Path $Global:ExecutionJsonlPath -Value "" -Encoding UTF8 -ErrorAction Stop
      Set-Content -Path $Global:ErrorsLogPath -Value "" -Encoding UTF8 -ErrorAction Stop

      $toolMap = Get-ToolMap -ToolsDir $state.ToolsDir

      $result = $null
      if ($Action) {
        $result = Invoke-EnrichmentAction -State $state -Session $session -ToolMap $toolMap
      }
      $resultIsDictionary = ($result -is [System.Collections.IDictionary])
      $actionSkipped = [bool]($resultIsDictionary -and $result.ContainsKey('ActionSkipped') -and [bool]$result.ActionSkipped)

      $bundlePath = $null
      $sessionStatus = "OPEN"
      if ($FinalizeEnrichSession) {
        $bundlePath = Finalize-EnrichSession -State $state -Session $session -ToolMap $toolMap
        $sessionStatus = if ($bundlePath) { "FINALIZED" } else { "FINALIZE_SKIPPED" }
      }

      Save-State -State $state

      $status = if ($actionSkipped) { "SKIPPED" } else { "SUCCESS" }
      if (-not $actionSkipped -and @($Global:CollectorErrors).Count -gt 0) { $status = "PARTIAL_SUCCESS" }

      $deleteScriptCommand = Get-CollectorDeleteScriptCommandText

      Write-Output ("STATUS={0}" -f $status)
      Write-Output ("RUN_ID={0}" -f $state.RunId)
      Write-Output ("COLLECTOR_VERSION={0}" -f [string]$state.CollectorVersion)
      Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version ([string]$state.CollectorVersion)))
      Write-Output ("ENRICH_SESSION_ID={0}" -f $session.SessionId)
      Write-Output ("SESSION_RESOLUTION_MODE={0}" -f $session.SessionResolutionMode)
      if ($result) {
        if ($resultIsDictionary -and $result.ContainsKey('ActionStatus') -and $result.ActionStatus) { Write-Output ("ACTION_STATUS={0}" -f $result.ActionStatus) }
        if ($result.ReportPath) { Write-Output ("ENRICH_REPORT_PATH={0}" -f $result.ReportPath) }
        if ($result.ActionArtifactPath) { Write-Output ("ACTION_ARTIFACT_PATH={0}" -f $result.ActionArtifactPath) }
        if ($result.StagedPath) { Write-Output ("STAGED_PATH={0}" -f $result.StagedPath) }
      } else {
        if ($session.SummaryPath -and (Test-Path -LiteralPath $session.SummaryPath)) { Write-Output ("ENRICH_REPORT_PATH={0}" -f $session.SummaryPath) }
      }
      Write-Output ("SESSION_STATUS={0}" -f $sessionStatus)
      if ($bundlePath) {
        Write-Output ("ENRICH_BUNDLE_PATH={0}" -f $bundlePath)
        Write-Output ('NEXT_GET_FILE=get-file --path "{0}" --comment "Retrieve DCOIR enrich bundle"' -f $bundlePath)
      } elseif ($actionSkipped) {
        Write-Output "NEXT_OPTIONS=Re-run without -WhatIf and confirm the enrich action writes to persist the action."
      } else {
        Write-Output ("NEXT_OPTIONS=Continue current session with -EnrichSessionId {0} or finalize it with -FinalizeEnrichSession" -f $session.SessionId)
      }
      Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
      if ($sessionStatus -eq "FINALIZED") {
        Write-QuickNextSteps -Phase "EnrichFinalized"
      } else {
        Write-QuickNextSteps -Phase "EnrichOpen"
      }
    }

    "Cleanup" {
      try {
        $loaded = Load-State -Root $OutRoot -CurrentRunId $RunId
        $cleanupCollectorVersion = if (($loaded.PSObject.Properties.Name -contains 'CollectorVersion') -and -not [string]::IsNullOrWhiteSpace([string]$loaded.CollectorVersion)) {
          [string]$loaded.CollectorVersion
        } else {
          $ScriptVersion
        }
        $cleanupResult = Invoke-Cleanup -StateObject $loaded
        Write-Output ("CLEANUP_STATUS={0}" -f $cleanupResult.Status)
        Write-Output ("RUN_ID={0}" -f $loaded.RunId)
        Write-Output ("CLEANUP_TARGET_COUNT={0}" -f $cleanupResult.TargetCount)
        Write-Output ("CLEANUP_REMOVED_COUNT={0}" -f $cleanupResult.RemovedCount)
        Write-Output ("CLEANUP_SKIPPED_COUNT={0}" -f $cleanupResult.SkippedCount)
        Write-Output ("CLEANUP_FAILED_COUNT={0}" -f $cleanupResult.FailedCount)
        foreach ($target in @($cleanupResult.RemovedTargets)) { Write-Output ("CLEANUP_REMOVED_TARGET={0}" -f $target) }
        foreach ($target in @($cleanupResult.SkippedTargets)) { Write-Output ("CLEANUP_SKIPPED_TARGET={0}" -f $target) }
        foreach ($target in @($cleanupResult.FailedTargets)) { Write-Output ("CLEANUP_FAILED_TARGET={0}" -f $target) }
        Write-Output ("COLLECTOR_VERSION={0}" -f $cleanupCollectorVersion)
        Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $cleanupCollectorVersion))
        Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f (Get-CollectorDeleteScriptCommandText))
        Write-QuickNextSteps -Phase "Cleanup"
      } catch {
        $loadError = $_.Exception.Message
        if ($loadError -notmatch 'State file not found|No DCOIR run directories found') { throw }
        $resolvedOutRoot = if ([System.IO.Path]::IsPathRooted($OutRoot)) {
          [System.IO.Path]::GetFullPath($OutRoot)
        } else {
          [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutRoot))
        }
        $cleanupResult = Invoke-NoStateCleanup -Root $resolvedOutRoot -CurrentRunId $RunId -CurrentPackageName $PackageName
        Write-Output ("CLEANUP_STATUS={0}" -f $cleanupResult.Status)
        if ($RunId) { Write-Output ("RUN_ID={0}" -f $RunId) }
        if ($cleanupResult.RunRoot) { Write-Output ("CLEANUP_ORPHAN_RUN_ROOT={0}" -f $cleanupResult.RunRoot) }
        Write-Output ("CLEANUP_TARGET_COUNT={0}" -f $cleanupResult.TargetCount)
        Write-Output ("CLEANUP_REMOVED_COUNT={0}" -f $cleanupResult.RemovedCount)
        Write-Output ("CLEANUP_SKIPPED_COUNT={0}" -f $cleanupResult.SkippedCount)
        Write-Output ("CLEANUP_FAILED_COUNT={0}" -f $cleanupResult.FailedCount)
        foreach ($target in @($cleanupResult.RemovedTargets)) { Write-Output ("CLEANUP_REMOVED_TARGET={0}" -f $target) }
        foreach ($target in @($cleanupResult.SkippedTargets)) { Write-Output ("CLEANUP_SKIPPED_TARGET={0}" -f $target) }
        foreach ($target in @($cleanupResult.FailedTargets)) { Write-Output ("CLEANUP_FAILED_TARGET={0}" -f $target) }
        Write-Output ("CLEANUP_REASON={0}" -f $loadError)
        Write-Output ("COLLECTOR_VERSION={0}" -f $ScriptVersion)
        Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $ScriptVersion))
        Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f (Get-CollectorDeleteScriptCommandText))
        Write-QuickNextSteps -Phase "Cleanup"
      }
    }
  }
} catch {
  Add-CollectorError $_.Exception.Message
  Write-Output ("STATUS=ERROR")
  Write-Output ("MESSAGE={0}" -f $_.Exception.Message)
  exit 1
}
