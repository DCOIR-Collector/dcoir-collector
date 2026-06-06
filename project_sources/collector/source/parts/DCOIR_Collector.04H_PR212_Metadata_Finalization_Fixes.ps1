<#
.SYNOPSIS
DCOIR collector metadata finalization helpers for issue #212.

.DESCRIPTION
Provides collect-mode guidance builders that can reference the final metadata report path
before the report content is written, without snapshotting an empty placeholder file.

.FILE NAME
DCOIR_Collector.04H_PR212_Metadata_Finalization_Fixes.ps1

.INPUTS
Collector state and baseline hashtables.

.OUTPUTS
Upload guidance artifacts and analyst overview artifacts that reference late-bound
metadata deterministically.
#>

<#
.SYNOPSIS
Creates collect upload guidance while treating metadata as a late-bound final report.

.DESCRIPTION
Builds the upload summary and attachment-budget manifest before final metadata content is
written. The metadata report path is included deterministically, but when the file is not
yet present this helper records it as late-bound instead of resolving, sizing, hashing, or
budgeting a placeholder artifact.

.FUNCTION NAME
New-CollectUploadArtifactsWithLateMetadataReport

.INPUTS
Collector state hashtable and baseline result hashtable containing the artifact map.

.OUTPUTS
Hashtable containing upload-summary path, manifest path, default-set status, total KB,
and recommended file count.
#>
function New-CollectUploadArtifactsWithLateMetadataReport {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param([hashtable]$State,[hashtable]$Baseline)

  $budget = Get-CollectorUploadBudget
  $artifactMap = $Baseline.ArtifactMap
  $chunkCompanions = New-ProductionUploadSafeChunkCompanions -State $State -ArtifactMap $artifactMap -Budget $budget
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
    $candidatePath = if ($artifactMap.ContainsKey($key)) { [string]$artifactMap[$key] } else { $null }
    if (-not [string]::IsNullOrWhiteSpace($candidatePath) -and (Test-Path -LiteralPath $candidatePath)) {
      $recommendedPaths += $candidatePath
    }
  }

  $metadataReportPath = [string]$State.MetadataReportPath
  if ($metadataReportPath) {
    $recommendedPaths = @($metadataReportPath) + $recommendedPaths
  }

  $recommended = New-Object System.Collections.ArrayList
  $safeTotal = 0
  foreach ($path in $recommendedPaths) {
    $pathText = [string]$path
    $pathExists = (Test-Path -LiteralPath $pathText)
    $isLateBoundMetadata = ($metadataReportPath -and ($pathText -eq $metadataReportPath) -and -not $pathExists)
    $sizeKB = if ($isLateBoundMetadata) { $null } else { Get-FileSizeKB -Path $pathText }
    if (-not $isLateBoundMetadata) { $safeTotal += $sizeKB }

    $resolvedPath = if ($pathExists) {
      [string](Resolve-Path -LiteralPath $pathText | Select-Object -First 1 | ForEach-Object { $_.Path })
    } else {
      $pathText
    }
    $relativePath = $resolvedPath
    if ($State.RunRoot -and $resolvedPath.StartsWith($State.RunRoot + '\')) {
      $relativePath = $resolvedPath.Replace($State.RunRoot + '\', '')
    }

    [void]$recommended.Add([ordered]@{
      path = $pathText
      relative_path = $relativePath
      size_kb = $sizeKB
      late_bound_after_upload_artifacts = [bool]$isLateBoundMetadata
      within_safe_per_file = ($isLateBoundMetadata -or ($sizeKB -le $budget.SafePerFileKB))
      within_hard_per_file = ($isLateBoundMetadata -or ($sizeKB -le $budget.HardPerFileKB))
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
  $chunkManifestPath = $null
  if (@($chunkCompanions).Count -gt 0) {
    $plannedChunkManifestPath = Join-Path $State.ReportsDir ("DCOIR_UPLOAD_SAFE_CHUNK_MANIFEST_{0}_{1}.json.txt" -f $env:COMPUTERNAME, $State.RunId)
    $chunkManifestObj = [ordered]@{
      run_id = $State.RunId
      origin = 'collector_production_upload_safe'
      budget = $budget
      chunked_artifact_count = @($chunkCompanions).Count
      chunked_artifacts = @($chunkCompanions)
    }
    if ($PSCmdlet.ShouldProcess($plannedChunkManifestPath, 'Write upload-safe chunk manifest')) {
      Set-Content -Path $plannedChunkManifestPath -Value (Convert-ToSafeJsonText -InputObject $chunkManifestObj) -Encoding UTF8 -ErrorAction Stop
      $chunkManifestPath = $plannedChunkManifestPath
      $State.UploadSafeChunkManifestPath = $chunkManifestPath
      $Baseline.ArtifactMap['upload_safe_chunk_manifest'] = $chunkManifestPath
      [void]$Baseline.ArtifactPaths.Add($chunkManifestPath)
      foreach ($chunkRow in @($chunkCompanions)) {
        foreach ($chunkPath in @($chunkRow.chunk_paths)) {
          [void]$Baseline.ArtifactPaths.Add($chunkPath)
        }
      }
    }
  }

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
    "LateBoundMetadataReport=true",
    "",
    "Recommended files for Gemini upload by default:"
  )
  foreach ($row in $recommended) {
    $sizeLabel = if ($row.late_bound_after_upload_artifacts) { 'late-bound final metadata' } else { ("{0} KB" -f $row.size_kb) }
    $summaryLines += ('- {0} [{1}]' -f $row.path, $sizeLabel)
  }
  $summaryLines += ""
  $summaryLines += "Default guidance:"
  $summaryLines += "- Prefer this upload summary, the metadata report, and the listed representative artifacts."
  $summaryLines += "- The metadata report is written after this upload guidance so late-bound run fields are final before packaging."
  $summaryLines += "- Do not assume the large merged baseline report is upload-safe in the office Gemini environment."
  $summaryLines += "- If this set must be trimmed further, keep metadata, follow-up queue, security high-signal summary, and one representative process/network artifact first."
  if (@($chunkCompanions).Count -gt 0) {
    $summaryLines += ""
    $summaryLines += "Upload-safe chunk companions:"
    if ($chunkManifestPath) {
      $summaryLines += ("- UPLOAD_SAFE_CHUNK_MANIFEST_PATH={0}" -f $chunkManifestPath)
    }
    foreach ($chunkRow in @($chunkCompanions)) {
      $summaryLines += ("- SourceKey={0} SourceSizeKB={1} ChunkCount={2} TargetChunkKB={3}" -f $chunkRow.source_artifact_key, $chunkRow.source_size_kb, $chunkRow.chunk_count, $chunkRow.target_chunk_kb)
      foreach ($chunkPath in @($chunkRow.chunk_paths)) {
        $summaryLines += ("  - {0}" -f $chunkPath)
      }
    }
    $summaryLines += "- Upload the high-signal summary first for triage; use full-fidelity chunk companions when the oversized source artifact is needed."
  }

  $uploadSummaryResultPath = $null
  if ($PSCmdlet.ShouldProcess($uploadSummaryPath, 'Write collect upload summary')) {
    Set-Content -Path $uploadSummaryPath -Value $summaryLines -Encoding UTF8 -ErrorAction Stop
    $uploadSummaryResultPath = $uploadSummaryPath
  }

  $manifestObj = [ordered]@{
    run_id = $State.RunId
    workflow_phase = 'collect_baseline'
    upload_model = 'chunk_first'
    budget = $budget
    default_set_status = $setStatus
    recommended_upload_total_kb = $safeTotal
    recommended_upload_files = @($recommended)
    metadata_report_late_bound_after_upload_artifacts = $true
    upload_safe_chunk_manifest_path = $chunkManifestPath
    upload_safe_chunk_companions = @($chunkCompanions)
    baseline_report_path = $State.BaselineReportPath
    metadata_report_path = $State.MetadataReportPath
    note = 'The merged baseline report may be useful for local analyst review but is no longer the default Gemini-facing upload surface.'
  }
  $uploadManifestResultPath = $null
  if ($PSCmdlet.ShouldProcess($uploadManifestPath, 'Write attachment budget manifest')) {
    Set-Content -Path $uploadManifestPath -Value (Convert-ToSafeJsonText -InputObject $manifestObj) -Encoding UTF8 -ErrorAction Stop
    $uploadManifestResultPath = $uploadManifestPath
  }

  return @{
    UploadSummaryPath = $uploadSummaryResultPath
    UploadManifestPath = $uploadManifestResultPath
    DefaultSetStatus = $setStatus
    RecommendedUploadTotalKB = $safeTotal
    RecommendedUploadCount = @($recommended).Count
    UploadSafeChunkManifestPath = $chunkManifestPath
    UploadSafeChunkCompanionCount = @($chunkCompanions).Count
  }
}

<#
.SYNOPSIS
Builds the analyst overview while allowing the metadata report path to be late-bound.

.DESCRIPTION
Writes the analyst-first overview artifact and includes METADATA_REPORT_PATH even when
final metadata content has not yet been written, because collect finalization writes that
report immediately after upload and overview paths are populated.

.FUNCTION NAME
New-AnalystOverviewArtifactWithLateMetadataReport

.INPUTS
State hashtable and Baseline hashtable.

.OUTPUTS
String analyst overview artifact path.
#>
function New-AnalystOverviewArtifactWithLateMetadataReport {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param([hashtable]$State,[hashtable]$Baseline)

  $artifactMap = $Baseline.ArtifactMap
  $overviewPath = Join-Path $State.ReportsDir ("DCOIR_ANALYST_OVERVIEW_{0}_{1}.txt" -f $env:COMPUTERNAME, $State.RunId)
  $lines = New-Object System.Collections.ArrayList

  [void]$lines.Add("DCOIR_ANALYST_OVERVIEW")
  [void]$lines.Add(("CollectorVersion={0}" -f $ScriptVersion))
  [void]$lines.Add(("RunId={0}" -f $State.RunId))
  [void]$lines.Add("WorkflowPhase=CollectBaseline")
  [void]$lines.Add("PrimaryReviewPosture=SmallerSurfaceFirst")
  [void]$lines.Add("DoNotAssumeMonolithicBaselineUpload=true")
  [void]$lines.Add("MergedBaselineReportEmitted=false")
  [void]$lines.Add(("DefaultGeminiUploadSetStatus={0}" -f $State.DefaultGeminiUploadSetStatus))
  [void]$lines.Add(("CollectTier={0}" -f $Tier))
  $collectorErrorCount = @($Global:CollectorErrors).Count
  [void]$lines.Add(("CollectorObservedErrorCount={0}" -f $collectorErrorCount))
  if ($collectorErrorCount -gt 0) {
    [void]$lines.Add('RunHealth=DEGRADED_OR_PARTIAL_REVIEW_REQUIRED')
  } else {
    [void]$lines.Add('RunHealth=NO_DEGRADED_STATE_OBSERVED_DURING_COLLECTION')
  }
  [void]$lines.Add("")
  [void]$lines.Add("WHAT_TO_REVIEW_FIRST")
  [void]$lines.Add("1. Start with this overview, the upload summary, and the metadata report.")
  [void]$lines.Add("2. Use the analyst follow-up queue and security high-signal summary as the first decisive triage surface.")
  [void]$lines.Add("3. Use representative process, network, and defender artifacts before expanding into broader local review.")
  if ($collectorErrorCount -gt 0) {
    [void]$lines.Add("4. This run recorded degraded or partial conditions. Review errors.log and the affected truth surfaces before treating the overview as complete.")
  }
  if ($State.TargetedCollectionPlanPath) {
    [void]$lines.Add("4. A targeted collection plan was emitted for this run; review it first when the incident is narrow.")
  }
  [void]$lines.Add("")
  [void]$lines.Add("REVIEW_FIRST_PATHS")
  foreach ($pair in @(
    @{ Label = 'ANALYST_OVERVIEW_PATH'; Path = $overviewPath },
    @{ Label = 'UPLOAD_SUMMARY_PATH'; Path = $State.UploadSummaryPath },
    @{ Label = 'METADATA_REPORT_PATH'; Path = $State.MetadataReportPath },
    @{ Label = 'ATTACHMENT_BUDGET_MANIFEST_PATH'; Path = $State.UploadBudgetManifestPath },
    @{ Label = 'COLLECTION_SCOPE_PATH'; Path = $State.CollectionScopePath },
    @{ Label = 'TARGETED_COLLECTION_PLAN_PATH'; Path = $State.TargetedCollectionPlanPath },
    @{ Label = 'ANALYST_FOLLOW_UP_QUEUE_PATH'; Path = $artifactMap['analyst_follow_up_queue'] },
    @{ Label = 'SECURITY_HIGH_SIGNAL_SUMMARY_PATH'; Path = $artifactMap['security_high_signal_summary'] },
    @{ Label = 'PROCESS_INVENTORY_PATH'; Path = $artifactMap['process_inventory'] },
    @{ Label = 'STRUCTURED_NET_PATH'; Path = $artifactMap['structured_net'] },
    @{ Label = 'DEFENDER_STATUS_PATH'; Path = $artifactMap['defender_status'] }
  )) {
    $includePath = $false
    if ($pair.Path) {
      $includePath = (($pair.Label -eq 'METADATA_REPORT_PATH') -or (Test-Path -LiteralPath $pair.Path))
    }
    if ($includePath) {
      [void]$lines.Add(("{0}={1}" -f $pair.Label, $pair.Path))
    }
  }
  [void]$lines.Add("")
  if ($collectorErrorCount -gt 0) {
    [void]$lines.Add("DEGRADED_REVIEW_NOTE")
    [void]$lines.Add("This run emitted collector errors during collection. Use errors.log plus the specific affected artifacts as the truth surface for degraded lanes.")
    [void]$lines.Add("")
  }
  [void]$lines.Add("NO_MERGED_BASELINE_REPORT")
  [void]$lines.Add("No merged baseline report is emitted in this build. Use metadata plus representative artifacts for broader local review.")

  if ($PSCmdlet.ShouldProcess($overviewPath, 'Write analyst overview artifact')) {
    Set-Content -Path $overviewPath -Value $lines -Encoding UTF8 -ErrorAction Stop
    return $overviewPath
  }
  return $null
}
