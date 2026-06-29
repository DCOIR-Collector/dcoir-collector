<#
.SYNOPSIS
DCOIR collector collect-mode entry helper.

.DESCRIPTION
Runs the collect-mode package preparation, run-structure initialization, baseline collection, upload guidance artifact creation, manifest finalization, bundle creation, and collect-mode status output.

.FILE NAME
DCOIR_Collector.05A_Main_Entry.ps1

.INPUTS
Collector runtime parameters such as OutRoot, PackageName, RunId, Tier, targeted-collection flags, and WhatIf/ShouldProcess context.

.OUTPUTS
Collect-mode status key-value lines, output artifact paths, quick next-step guidance, and persisted run state.
#>

<#
.SYNOPSIS
Runs collect mode.

.DESCRIPTION
Contains the collect branch previously held in the main switch dispatcher. Keeping it as a function makes the source connector-sized while preserving the compiled runtime behavior and output contract.

.FUNCTION NAME
Invoke-DCOIRCollectMode

.INPUTS
Collector runtime parameters and script-scoped state resolved by the main entry dispatcher.

.OUTPUTS
Collect-mode status key-value lines and artifact paths.
#>
function Invoke-DCOIRCollectMode {
$resolvedOutRoot = if ([System.IO.Path]::IsPathRooted($OutRoot)) {
  [System.IO.Path]::GetFullPath($OutRoot)
} else {
  [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutRoot))
}

$purgeCompleted = Purge-PreviousRuns -Root $resolvedOutRoot -CurrentPackageName $PackageName
if (-not $purgeCompleted) {
  $prepSkipReason = if ($script:CollectPrepSkipReason) { [string]$script:CollectPrepSkipReason } else { 'PACKAGE_PURGE_SKIPPED' }
  $Global:CurrentRunId = $RunId
  $collectorCommandBase = Get-CollectorResponseActionCommandBase
  $deleteScriptCommand = Get-CollectorDeleteScriptCommandText
  Write-Output "STATUS=SKIPPED"
  Write-Output "COLLECT_PREP_STATUS=SKIPPED"
  if ($prepSkipReason -eq 'CUSTOM_RUN_PURGE_SKIPPED') {
    Write-Output "CUSTOM_RUN_PURGE_STATUS=SKIPPED"
  } else {
    Write-Output "PACKAGE_PURGE_STATUS=SKIPPED"
  }
  Write-Output ("COLLECT_PREP_SKIP_REASON={0}" -f $prepSkipReason)
  Write-Output ("RUN_ID={0}" -f $RunId)
  Write-Output ("COLLECTOR_VERSION={0}" -f $ScriptVersion)
  Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $ScriptVersion))
  Write-Output "NEXT_OPTIONS=Re-run without -WhatIf and confirm previous package cleanup to continue collect mode."
  Write-Output ('CLEANUP_COMMAND=execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $collectorCommandBase)
  Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
  return
}

$packagePath = Move-PackageToOutRoot -Root $resolvedOutRoot -CurrentPackageName $PackageName
if (-not $packagePath) {
  $Global:CurrentRunId = $RunId
  $collectorCommandBase = Get-CollectorResponseActionCommandBase
  $deleteScriptCommand = Get-CollectorDeleteScriptCommandText
  Write-Output "STATUS=SKIPPED"
  Write-Output "COLLECT_PREP_STATUS=SKIPPED"
  Write-Output "COLLECT_PACKAGE_STATUS=SKIPPED"
  Write-Output ("RUN_ID={0}" -f $RunId)
  Write-Output ("COLLECTOR_VERSION={0}" -f $ScriptVersion)
  Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $ScriptVersion))
  Write-Output "NEXT_OPTIONS=Re-run without -WhatIf and confirm package preparation to continue collect mode."
  Write-Output ('CLEANUP_COMMAND=execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $collectorCommandBase)
  Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
  return
}

if ($WhatIfPreference) {
  $Global:CurrentRunId = $RunId
  $collectorCommandBase = Get-CollectorResponseActionCommandBase
  $deleteScriptCommand = Get-CollectorDeleteScriptCommandText
  Write-Output "STATUS=SKIPPED"
  Write-Output "COLLECT_PREP_STATUS=SKIPPED"
  Write-Output "COLLECT_SETUP_STATUS=SKIPPED"
  Write-Output ("RUN_ID={0}" -f $RunId)
  Write-Output ("COLLECTOR_VERSION={0}" -f $ScriptVersion)
  Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $ScriptVersion))
  Write-Output "NEXT_OPTIONS=Re-run without -WhatIf to create the collect run structure and continue collect mode."
  Write-Output ('CLEANUP_COMMAND=execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $collectorCommandBase)
  Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
  return
}

$dirs = Initialize-RunStructure -Root $resolvedOutRoot -CurrentRunId $RunId
$Global:CurrentRunId = $RunId
$Global:ExecutionTxtPath = Join-Path $dirs.LogsDir "collect_execution_log.txt"
$Global:ExecutionJsonlPath = Join-Path $dirs.LogsDir "collect_execution_log.jsonl"
$Global:ErrorsLogPath = Join-Path $dirs.LogsDir "errors.log"
Set-Content -Path $Global:ExecutionTxtPath -Value ("DCOIR Collect Execution Log`r`nRunId={0}" -f $RunId) -Encoding UTF8 -ErrorAction Stop
Set-Content -Path $Global:ExecutionJsonlPath -Value "" -Encoding UTF8 -ErrorAction Stop
Set-Content -Path $Global:ErrorsLogPath -Value "" -Encoding UTF8 -ErrorAction Stop

$toolsExpanded = Expand-PackageToTools -PackagePath $packagePath -ToolsDir $dirs.ToolsDir
if (-not $toolsExpanded) {
  $collectorCommandBase = Get-CollectorResponseActionCommandBase
  $deleteScriptCommand = Get-CollectorDeleteScriptCommandText
  Write-Output "STATUS=SKIPPED"
  Write-Output "COLLECT_PREP_STATUS=SKIPPED"
  Write-Output "TOOL_EXPANSION_STATUS=SKIPPED"
  Write-Output ("RUN_ID={0}" -f $RunId)
  Write-Output ("COLLECTOR_VERSION={0}" -f $ScriptVersion)
  Write-Output ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity -Version $ScriptVersion))
  Write-Output "NEXT_OPTIONS=Re-run without -WhatIf and confirm tool expansion to continue collect mode."
  Write-Output ('CLEANUP_COMMAND=execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $collectorCommandBase)
  Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
  return
}

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
$targetedPlanExpected = [bool]($Targeted -or (-not [string]::IsNullOrWhiteSpace($FocusProcess)) -or (-not [string]::IsNullOrWhiteSpace($FocusPath)) -or (-not [string]::IsNullOrWhiteSpace($FocusIndicator)) -or (-not [string]::IsNullOrWhiteSpace($UserReport)) -or (-not [string]::IsNullOrWhiteSpace($WindowStart)) -or (-not [string]::IsNullOrWhiteSpace($WindowEnd)))

$uploadArtifacts = New-CollectUploadArtifactsWithLateMetadataReport -State $state -Baseline $baseline
$state.UploadSummaryPath = $uploadArtifacts.UploadSummaryPath
$state.UploadBudgetManifestPath = $uploadArtifacts.UploadManifestPath
$state.DefaultGeminiUploadSetStatus = $uploadArtifacts.DefaultSetStatus
$state.UploadSafeChunkManifestPath = $uploadArtifacts.UploadSafeChunkManifestPath
$state.AnalystOverviewPath = New-AnalystOverviewArtifactWithLateMetadataReport -State $state -Baseline $baseline

$uploadSafeChunkCompanionSkipped = [bool]($state.ContainsKey('UploadSafeChunkCompanionSkipped') -and [bool]$state.UploadSafeChunkCompanionSkipped)
$uploadSafeChunkManifestExpected = [bool](($uploadArtifacts.ContainsKey('UploadSafeChunkCompanionCount') -and ([int]$uploadArtifacts.UploadSafeChunkCompanionCount -gt 0)) -or $uploadSafeChunkCompanionSkipped)
$uploadSummarySkipped = -not $state.UploadSummaryPath
$attachmentBudgetManifestSkipped = -not $state.UploadBudgetManifestPath
$uploadSafeChunkManifestSkipped = [bool]($uploadSafeChunkManifestExpected -and -not $state.UploadSafeChunkManifestPath)
$analystOverviewSkipped = -not $state.AnalystOverviewPath
$collectionScopeSkipped = -not $state.CollectionScopePath
$parallelismAssessmentSkipped = -not $state.ParallelismAssessmentPath
$targetedCollectionPlanSkipped = [bool]($targetedPlanExpected -and -not $state.TargetedCollectionPlanPath)
$collectGuidanceSkipped = [bool]($uploadSummarySkipped -or $attachmentBudgetManifestSkipped -or $uploadSafeChunkManifestSkipped -or $analystOverviewSkipped -or $collectionScopeSkipped -or $parallelismAssessmentSkipped -or $targetedCollectionPlanSkipped)

$bundleName = ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId)
$bundlePath = Join-Path $state.BundlesDir $bundleName
$state.CollectBundlePath = $bundlePath
$bundleCreationApproved = $PSCmdlet.ShouldProcess($bundlePath, 'Create collector ZIP bundle')
$collectManifestSkipped = -not $bundleCreationApproved
$collectManifestFinalized = $false
$metadataReportSkipped = -not $bundleCreationApproved
$collectManifest = $null

if ($bundleCreationApproved) {
  # Write metadata once after late-bound collect fields are populated and before manifest/bundle packaging.
  $metadataText = New-MetadataReport -State $state -ToolMap $toolMap
  $metadataReportPath = Write-ReportFile -Path $metadataReportPath -Text $metadataText
  $metadataReportSkipped = -not $metadataReportPath
  $state.MetadataReportPath = $metadataReportPath

  if ($metadataReportPath) {
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
    $collectManifest = New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json") -State $state -ModeName "Collect" -TierName $Tier -Files $collectManifestFiles -ToolMap $toolMap -Extra $collectManifestExtra
    $collectManifestSkipped = -not $collectManifest
    $collectManifestFinalized = [bool]$collectManifest
  }

  if ($collectManifest) {
    $bundlePath = New-BundleZip -BundlesDir $state.BundlesDir -BundleName $bundleName -Confirm:$false -Paths @(
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
  } else {
    $bundlePath = $null
  }

  if ($bundlePath) {
    $state.CollectBundlePath = $bundlePath
  } else {
    $state.CollectBundlePath = $null
    $metadataReportPath = $null
    $state.MetadataReportPath = $null
    $metadataReportSkipped = $true
    $state.UploadSummaryPath = $null
    $state.UploadBudgetManifestPath = $null
    $state.UploadSafeChunkManifestPath = $null
    $state.AnalystOverviewPath = $null
    $state.CollectionScopePath = $null
    $state.ParallelismAssessmentPath = $null
    $state.TargetedCollectionPlanPath = $null
    $uploadSummarySkipped = $true
    $attachmentBudgetManifestSkipped = $true
    $uploadSafeChunkManifestSkipped = [bool]$uploadSafeChunkManifestExpected
    $analystOverviewSkipped = $true
    $collectionScopeSkipped = $true
    $parallelismAssessmentSkipped = $true
    $targetedCollectionPlanSkipped = [bool]$targetedPlanExpected
    $collectGuidanceSkipped = $true
  }
} else {
  $metadataReportPath = $null
  $state.MetadataReportPath = $null
  $state.CollectBundlePath = $null
  $state.UploadSummaryPath = $null
  $state.UploadBudgetManifestPath = $null
  $state.UploadSafeChunkManifestPath = $null
  $state.AnalystOverviewPath = $null
  $state.CollectionScopePath = $null
  $state.ParallelismAssessmentPath = $null
  $state.TargetedCollectionPlanPath = $null
  $bundlePath = $null
  $uploadSummarySkipped = $true
  $attachmentBudgetManifestSkipped = $true
  $uploadSafeChunkManifestSkipped = [bool]$uploadSafeChunkManifestExpected
  $analystOverviewSkipped = $true
  $collectionScopeSkipped = $true
  $parallelismAssessmentSkipped = $true
  $targetedCollectionPlanSkipped = [bool]$targetedPlanExpected
  $collectGuidanceSkipped = $true
}

$stateSavePath = Save-State -State $state
$collectPackageSkipped = -not $bundlePath
$collectManifestFinalizationSkipped = -not $collectManifestFinalized
$stateSaveSkipped = -not $stateSavePath

$status = "SUCCESS"
if ($collectPackageSkipped -or $collectManifestFinalizationSkipped -or $metadataReportSkipped -or $stateSaveSkipped -or $collectGuidanceSkipped) { $status = "PARTIAL_SUCCESS" }
if ($status -eq "SUCCESS" -and @($Global:CollectorErrors).Count -gt 0) { $status = "PARTIAL_SUCCESS" }

$collectorCommandBase = Get-CollectorResponseActionCommandBase
$deleteScriptCommand = Get-CollectorDeleteScriptCommandText

Write-Output ("STATUS={0}" -f $status)
if ($collectPackageSkipped) {
  Write-Output "COLLECT_PACKAGE_STATUS=SKIPPED"
  Write-Output "COLLECT_BUNDLE_STATUS=SKIPPED"
} elseif ($bundlePath) {
  Write-Output "COLLECT_PACKAGE_STATUS=CREATED"
  Write-Output "COLLECT_BUNDLE_STATUS=CREATED"
}
if ($collectManifestSkipped) { Write-Output "COLLECT_MANIFEST_STATUS=SKIPPED" }
elif ($collectManifestFinalizationSkipped) { Write-Output "COLLECT_MANIFEST_STATUS=PARTIAL" }
if ($metadataReportSkipped) { Write-Output "METADATA_REPORT_STATUS=SKIPPED" }
if ($stateSaveSkipped) { Write-Output "STATE_SAVE_STATUS=SKIPPED" }
if ($uploadSummarySkipped) { Write-Output "UPLOAD_SUMMARY_STATUS=SKIPPED" }
if ($attachmentBudgetManifestSkipped) { Write-Output "ATTACHMENT_BUDGET_MANIFEST_STATUS=SKIPPED" }
if ($uploadSafeChunkManifestSkipped) { Write-Output "UPLOAD_SAFE_CHUNK_MANIFEST_STATUS=SKIPPED" }
if ($analystOverviewSkipped) { Write-Output "ANALYST_OVERVIEW_STATUS=SKIPPED" }
if ($collectionScopeSkipped) { Write-Output "COLLECTION_SCOPE_STATUS=SKIPPED" }
if ($parallelismAssessmentSkipped) { Write-Output "PARALLELISM_ASSESSMENT_STATUS=SKIPPED" }
if ($targetedCollectionPlanSkipped) { Write-Output "TARGETED_COLLECTION_PLAN_STATUS=SKIPPED" }
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
if (-not $collectGuidanceSkipped -and -not $metadataReportSkipped) {
  Write-Output ('GEMINI_UPLOAD_GUIDANCE=Prefer ANALYST_OVERVIEW_PATH, UPLOAD_SUMMARY_PATH, ATTACHMENT_BUDGET_MANIFEST_PATH, COLLECTION_SCOPE_PATH, PARALLELISM_ASSESSMENT_PATH, and representative final_artifacts slices. If UPLOAD_SAFE_CHUNK_MANIFEST_PATH exists, use it for full-fidelity oversized text artifacts after triage summaries. If TARGETED_COLLECTION_PLAN_PATH exists, include it for narrow incidents.')
} else {
  Write-Output "GEMINI_UPLOAD_GUIDANCE_STATUS=SKIPPED"
}
foreach ($collectorError in @($Global:CollectorErrors)) {
  if (-not [string]::IsNullOrWhiteSpace([string]$collectorError)) {
    Write-Output ("COLLECTOR_ERROR={0}" -f $collectorError)
  }
}
Write-QuickNextSteps -Phase "Collect"
}
