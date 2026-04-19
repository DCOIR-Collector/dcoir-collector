<#
.SYNOPSIS
DCOIR collector targeted-collection and feature-wave helper functions.

.DESCRIPTION
Builds the targeted-collection scope and analyst plan artifacts, emits the bounded
parallelism assessment, and creates synthetic chunk-validation artifacts used by the
feature-wave collection and upload-surface regression paths.

.FILE NAME
DCOIR_Collector.04B_Feature_Wave_Targeted_Collection.ps1

.INPUTS
Collector state and baseline hashtables, targeted-collection globals such as
WindowStart, WindowEnd, FocusProcess, FocusPath, FocusIndicator, UserReport,
IncludeArtifactCategory, Hours, and validation-specific synthetic chunking settings.

.OUTPUTS
Ordered scope objects, analyst-facing text artifacts, chunk-manifest data, and updates
to the baseline artifact map and report builder.
#>

<#
.SYNOPSIS
Builds the targeted-collection scope object for the current run.

.DESCRIPTION
Normalizes the current targeted-collection inputs into one ordered object that records
whether targeted mode is enabled, whether an explicit time window or focus context was
supplied, which artifact categories were requested, and the current implementation
boundary for the feature.

.FUNCTION NAME
Get-TargetedCollectionScopeObject

.INPUTS
Collector state hashtable plus targeted-collection globals already bound in the current
collector runtime.

.OUTPUTS
Ordered hashtable describing the targeted-collection scope for the current run.
#>
function Get-TargetedCollectionScopeObject {
  param([hashtable]$State)

  $hasWindow = (-not [string]::IsNullOrWhiteSpace($WindowStart)) -or (-not [string]::IsNullOrWhiteSpace($WindowEnd))
  $hasFocus = (-not [string]::IsNullOrWhiteSpace($FocusProcess)) -or (-not [string]::IsNullOrWhiteSpace($FocusPath)) -or (-not [string]::IsNullOrWhiteSpace($FocusIndicator)) -or (-not [string]::IsNullOrWhiteSpace($UserReport))
  $categories = @()
  if ($IncludeArtifactCategory) { $categories = @($IncludeArtifactCategory | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) }

  return [ordered]@{
    targeted_mode_enabled = [bool]$Targeted
    target_profile = $TargetProfile
    has_explicit_time_window = $hasWindow
    window_start = $WindowStart
    window_end = $WindowEnd
    requested_hours = $Hours
    included_artifact_categories = $categories
    focus_process = $FocusProcess
    focus_path = $FocusPath
    focus_indicator = $FocusIndicator
    focus_indicator_type = $FocusIndicatorType
    user_report = $UserReport
    has_focus_context = $hasFocus
    implementation_boundary = "This major-version targeted collection feature currently narrows analyst guidance, collection scope intent, artifact prioritization, and recommended next actions. It does not yet rewrite every baseline collection helper into exact start-end timestamp filtering across all artifact families."
  }
}

<#
.SYNOPSIS
Renders the targeted-collection scope object into analyst-facing text.

.DESCRIPTION
Transforms the normalized scope object into a durable text artifact that records the
requested time window, focus indicators, included artifact categories, and current
implementation boundary for targeted collection.

.FUNCTION NAME
Get-TargetedCollectionScopeText

.INPUTS
Scope hashtable previously returned by Get-TargetedCollectionScopeObject.

.OUTPUTS
String containing the targeted-collection scope text artifact.
#>
function Get-TargetedCollectionScopeText {
  param([hashtable]$Scope)

  $lines = @()
  $lines += "TARGETED_COLLECTION_SCOPE"
  $lines += ("TARGETED_MODE_ENABLED={0}" -f $Scope.targeted_mode_enabled)
  $lines += ("TARGET_PROFILE={0}" -f $Scope.target_profile)
  $lines += ("HAS_EXPLICIT_TIME_WINDOW={0}" -f $Scope.has_explicit_time_window)
  $lines += ("WINDOW_START={0}" -f $Scope.window_start)
  $lines += ("WINDOW_END={0}" -f $Scope.window_end)
  $lines += ("REQUESTED_HOURS={0}" -f $Scope.requested_hours)
  $lines += ("FOCUS_PROCESS={0}" -f $Scope.focus_process)
  $lines += ("FOCUS_PATH={0}" -f $Scope.focus_path)
  $lines += ("FOCUS_INDICATOR={0}" -f $Scope.focus_indicator)
  $lines += ("FOCUS_INDICATOR_TYPE={0}" -f $Scope.focus_indicator_type)
  $lines += ("USER_REPORT={0}" -f $Scope.user_report)
  $lines += ("INCLUDED_ARTIFACT_CATEGORIES={0}" -f (($Scope.included_artifact_categories | ForEach-Object { $_ }) -join ', '))
  $lines += ""
  $lines += "IMPLEMENTATION_BOUNDARY"
  $lines += $Scope.implementation_boundary
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the analyst-facing targeted-collection plan text.

.DESCRIPTION
Turns the current target profile, time-window context, and focus inputs into explicit
prioritized-evidence guidance and analyst notes so a narrow incident can be reviewed
without defaulting immediately to the full monolithic baseline report.

.FUNCTION NAME
Get-TargetedCollectionPlanText

.INPUTS
Scope hashtable previously returned by Get-TargetedCollectionScopeObject.

.OUTPUTS
String containing the targeted-collection plan text artifact.
#>
function Get-TargetedCollectionPlanText {
  param([hashtable]$Scope)

  $lines = @()
  $lines += "TARGETED_COLLECTION_PLAN"
  $lines += ("PROFILE={0}" -f $Scope.target_profile)
  $lines += ""
  $lines += "INTENDED USE"
  $lines += "- This report turns the targeted collection request into explicit analyst-facing scoping guidance."
  $lines += "- It is intended to explain what the collector should emphasize, what the analyst should upload first, and which evidence families should be treated as highest value."
  $lines += "- It is intentionally explicit because narrow incidents such as a user-reported popup, a suspected script execution, or a suspicious process often need a smaller and more explainable collection path than a generic broad baseline."
  $lines += ""
  $lines += "PRIORITIZED EVIDENCE"
  switch ($Scope.target_profile) {
    "PopupWindow" {
      $lines += "1. Security high-signal events around the reported time window."
      $lines += "2. Process inventory and likely user-context process chains."
      $lines += "3. PowerShell operational events and scheduled task activity."
      $lines += "4. Representative artifacts tied to likely GUI-launching processes, startup points, or scripts."
    }
    "ScriptExecution" {
      $lines += "1. PowerShell operational events and Security 4688 process creation records."
      $lines += "2. Process inventory entries with suspicious command lines or user-writable execution paths."
      $lines += "3. Pulled script, config, or suspicious file artifacts if specific paths are known."
      $lines += "4. Strings, streams, or signature enrichment on the focal script or binary path."
    }
    "PersistenceFollowUp" {
      $lines += "1. Services, scheduled tasks, Run keys, and autoruns."
      $lines += "2. WMI persistence text and service binary follow-up."
      $lines += "3. Registry, service ACL, and task XML follow-up actions."
      $lines += "4. Representative retrieved artifacts for persistence evidence."
    }
    "NetworkOnly" {
      $lines += "1. Structured network state, netstat, tcpvcon, dns cache, route, and arp."
      $lines += "2. Security events that establish the launching process or account context."
      $lines += "3. Follow-up TCP refresh enrichment."
      $lines += "4. Representative network-facing process inventory slices."
    }
    "ProcessAndPowerShell" {
      $lines += "1. Process inventory, pslist, Security 4688, and PowerShell operational records."
      $lines += "2. Signature, strings, and stream checks for focal binaries or scripts."
      $lines += "3. Retrieval of suspicious script or config paths when known."
      $lines += "4. Repeatable enrichment of process-centric context in one bounded session."
    }
    default {
      $lines += "1. Metadata, upload summary, analyst follow-up queue, and security high-signal summary."
      $lines += "2. One or more focal process, script, or network artifacts if a likely target is known."
      $lines += "3. Narrow enrichment tied to the strongest current lead."
      $lines += "4. Avoid defaulting to the full monolithic baseline report when smaller decisive artifacts are sufficient."
    }
  }
  $lines += ""
  $lines += "ANALYST NOTES"
  if (-not [string]::IsNullOrWhiteSpace($Scope.user_report)) {
    $lines += ("- User report: {0}" -f $Scope.user_report)
  } else {
    $lines += "- No free-text user report was supplied."
  }
  if ($Scope.has_explicit_time_window) {
    $lines += ("- Explicit time window requested: {0} to {1}" -f $Scope.window_start, $Scope.window_end)
  } else {
    $lines += "- No explicit start-end time window was supplied. The collector remains hour-window based in this version."
  }
  if ($Scope.has_focus_context) {
    $lines += "- Focus context was supplied and should influence the first analyst review pass."
  } else {
    $lines += "- No narrow focal artifact was supplied; use the target profile plus the analyst follow-up queue to choose the first review artifact."
  }
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Returns the current bounded-parallel-runtime assessment text.

.DESCRIPTION
Builds a durable analyst-facing summary of the current parallel runtime implementation,
including implemented worker groups, safety guardrails, still-serial areas, and the
expected validation posture for proving overlap and deterministic output.

.FUNCTION NAME
Get-CollectorParallelismAssessmentText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the current collector parallelism assessment text.
#>
function Get-CollectorParallelismAssessmentText {
  $lines = @()
  $lines += "COLLECTOR_PARALLELISM_ASSESSMENT"
  $lines += "STATUS=BOUNDED_RUNTIME_IMPLEMENTED"
  $lines += ""
  $lines += "CURRENT POSITION"
  $lines += "- The collector now performs bounded PowerShell 5.1-safe parallel runtime execution for selected read-only baseline worker groups."
  $lines += "- The implemented worker set is intentionally narrow and preserves deterministic final report assembly."
  $lines += "- The collector still emits a durable parallel execution proof surface so overlap and worker completion can be validated on a real Collect run."
  $lines += ""
  $lines += "IMPLEMENTED WORKER GROUPS"
  $lines += "1. Host baseline worker for time/hostname/version and systeminfo capture."
  $lines += "2. Identity context worker for whoami and interactive session capture."
  $lines += "3. Network light worker for ipconfig, DNS cache, route, and ARP capture."
  $lines += "4. Security posture worker for firewall profile capture."
  $lines += ""
  $lines += "SAFETY GUARDRAILS"
  $lines += "1. Each worker writes its own durable artifact under final_artifacts\\parallel_workers."
  $lines += "2. The parent waits for all workers to finish before continuing deterministic report assembly."
  $lines += "3. Steps not successfully cached by a worker fall back to serial execution when needed."
  $lines += ""
  $lines += "STILL SERIAL"
  $lines += "- Process inventory, event timeline collection, persistence sections, Sysinternals-enriched captures, and bundle/manifest finalization remain serial in this bounded implementation slice."
  $lines += ""
  $lines += "VALIDATION EXPECTATION"
  $lines += "- Use the emitted parallel execution proof artifact and worker files to verify overlapping runtime and deterministic output before claiming the broader issue closed."
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the analyst-overview artifact for a collect run.

.DESCRIPTION
Creates a compact analyst-first overview that points reviewers to the upload summary,
metadata, follow-up queue, high-signal summaries, and other review-first artifacts so
local or Gemini-facing triage can start with the smaller surface before the full merged
baseline report.

.FUNCTION NAME
New-AnalystOverviewArtifact

.INPUTS
Collector state hashtable and the baseline result hashtable that contains ArtifactMap.

.OUTPUTS
String path to the written analyst-overview artifact.
#>
function New-AnalystOverviewArtifact {
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
  [void]$lines.Add(("DefaultGeminiUploadSetStatus={0}" -f $State.DefaultGeminiUploadSetStatus))
  [void]$lines.Add("")
  [void]$lines.Add("WHAT_TO_REVIEW_FIRST")
  [void]$lines.Add("1. Start with this overview, the upload summary, and the metadata report.")
  [void]$lines.Add("2. Use the analyst follow-up queue and security high-signal summary as the first decisive triage surface.")
  [void]$lines.Add("3. Use representative process, network, and defender artifacts before opening the full merged baseline report.")
  if ($State.TargetedCollectionPlanPath) {
    [void]$lines.Add("4. A targeted collection plan was emitted for this run; review it before the monolithic baseline when the incident is narrow.")
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
    if ($pair.Path -and (Test-Path -LiteralPath $pair.Path)) {
      [void]$lines.Add(("{0}={1}" -f $pair.Label, $pair.Path))
    }
  }
  [void]$lines.Add("")
  [void]$lines.Add("LOCAL_DEEP_REVIEW_ONLY")
  [void]$lines.Add(("BASELINE_REPORT_PATH={0}" -f $State.BaselineReportPath))
  [void]$lines.Add("Use the full merged baseline report only when the smaller analyst-first surface is insufficient or when a broader local review is explicitly needed.")

  Set-Content -Path $overviewPath -Value $lines -Encoding UTF8
  return $overviewPath
}

<#
.SYNOPSIS
Reads the synthetic oversize-artifact size requested for validation.

.DESCRIPTION
Looks for the process-scoped validation environment variable and returns a positive
integer size in KB when present. Returns zero when no valid request exists.

.FUNCTION NAME
Get-ValidationSyntheticOversizeArtifactKB

.INPUTS
No direct parameters. Uses the process environment variable
DCOIR_TEST_SYNTHETIC_OVERSIZE_ARTIFACT_KB.

.OUTPUTS
Integer number of KB requested for the synthetic oversize validation artifact.
#>
function Get-ValidationSyntheticOversizeArtifactKB {
  $raw = [Environment]::GetEnvironmentVariable('DCOIR_TEST_SYNTHETIC_OVERSIZE_ARTIFACT_KB', 'Process')
  if ([string]::IsNullOrWhiteSpace($raw)) { return 0 }
  $parsed = 0
  if ([int]::TryParse($raw, [ref]$parsed) -and $parsed -gt 0) { return $parsed }
  return 0
}

<#
.SYNOPSIS
Builds the synthetic oversize validation payload text.

.DESCRIPTION
Creates a deterministic multiline payload that grows until it reaches or exceeds the
requested size so chunking and reconstruction metadata can be validated repeatably.

.FUNCTION NAME
New-SyntheticOversizeArtifactText

.INPUTS
RequestedKB integer describing the desired source artifact size.

.OUTPUTS
String containing the synthetic oversize payload text.
#>
function New-SyntheticOversizeArtifactText {
  param([int]$RequestedKB)

  $line = 'DCOIR_SYNTHETIC_OVERSIZE_CHUNK_VALIDATION_PAYLOAD|ABCDEFGHIJKLMNOPQRSTUVWXYZ|0123456789|line='
  $targetBytes = $RequestedKB * 1024
  $currentBytes = 0
  $index = 1
  $sb = New-Object System.Text.StringBuilder
  while ($currentBytes -lt $targetBytes) {
    $lineText = ('{0}{1}' -f $line, $index) + [Environment]::NewLine
    [void]$sb.Append($lineText)
    $currentBytes += [System.Text.Encoding]::UTF8.GetByteCount($lineText)
    $index += 1
  }
  return $sb.ToString()
}

<#
.SYNOPSIS
Writes an artifact without altering the provided text bytes through section rendering.

.DESCRIPTION
Creates the target artifact filename using the baseline prefix and safe section/name
rules, then writes the exact UTF-8-no-BOM text payload to disk.

.FUNCTION NAME
Write-ArtifactTextExact

.INPUTS
ArtifactsDir, Section, Name, and the exact text payload to write.

.OUTPUTS
String path to the written artifact.
#>
function Write-ArtifactTextExact {
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
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $Text, $utf8NoBom)
  return $path
}

<#
.SYNOPSIS
Splits a synthetic validation text artifact into deterministic chunks.

.DESCRIPTION
Reads the source text artifact, writes sequential chunk files that stay near the target
chunk size, and returns the chunk paths, sizes, count, and reconstruction guidance.

.FUNCTION NAME
Split-ValidationTextArtifactIntoChunks

.INPUTS
SourcePath for the source artifact, ArtifactsDir for output, RequestedKB for naming,
and TargetChunkKB for the desired chunk size.

.OUTPUTS
Hashtable containing chunk paths, sizes, count, target chunk size, and reconstruction
order text.
#>
function Split-ValidationTextArtifactIntoChunks {
  param(
    [string]$SourcePath,
    [string]$ArtifactsDir,
    [int]$RequestedKB,
    [int]$TargetChunkKB
  )

  $chunkPaths = New-Object System.Collections.ArrayList
  $targetBytes = $TargetChunkKB * 1024
  $lines = Get-Content -LiteralPath $SourcePath
  $chunkIndex = 1
  $currentBytes = 0
  $sb = New-Object System.Text.StringBuilder

  foreach ($line in $lines) {
    $lineText = $line + [Environment]::NewLine
    $lineBytes = [System.Text.Encoding]::UTF8.GetByteCount($lineText)
    if (($currentBytes + $lineBytes) -gt $targetBytes -and $currentBytes -gt 0) {
      $chunkPath = Write-ArtifactTextExact -ArtifactsDir $ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_chunk_{1:000}.txt' -f $RequestedKB, $chunkIndex) -Text $sb.ToString()
      [void]$chunkPaths.Add($chunkPath)
      $chunkIndex += 1
      $sb = New-Object System.Text.StringBuilder
      $currentBytes = 0
    }
    [void]$sb.Append($lineText)
    $currentBytes += $lineBytes
  }

  if ($currentBytes -gt 0) {
    $chunkPath = Write-ArtifactTextExact -ArtifactsDir $ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_chunk_{1:000}.txt' -f $RequestedKB, $chunkIndex) -Text $sb.ToString()
    [void]$chunkPaths.Add($chunkPath)
  }

  $chunkSizes = @()
  foreach ($chunkPath in @($chunkPaths)) {
    $chunkSizes += (Get-FileSizeKB -Path $chunkPath)
  }

  return @{
    ChunkPaths = @($chunkPaths)
    ChunkSizesKB = $chunkSizes
    ChunkCount = @($chunkPaths).Count
    TargetChunkKB = $TargetChunkKB
    ReconstructionOrder = 'Concatenate the chunk_paths entries in listed order to reconstruct the original synthetic oversize artifact.'
  }
}

<#
.SYNOPSIS
Creates the synthetic oversize validation artifacts and manifest set.

.DESCRIPTION
Writes the synthetic source artifact, splits it into chunk files, writes the chunk-path
and chunk-manifest JSON artifacts, updates the collector state and baseline artifact
maps, and appends a validation summary to the baseline report.

.FUNCTION NAME
New-SyntheticOversizeChunkValidationArtifacts

.INPUTS
Collector state hashtable, baseline result hashtable, and RequestedKB integer.

.OUTPUTS
No direct return value. Updates state, baseline artifact maps, and report content.
#>
function New-SyntheticOversizeChunkValidationArtifacts {
  param([hashtable]$State,[hashtable]$Baseline,[int]$RequestedKB)

  $sourceText = New-SyntheticOversizeArtifactText -RequestedKB $RequestedKB
  $sourcePath = Write-ArtifactTextExact -ArtifactsDir $State.ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_source.txt' -f $RequestedKB) -Text $sourceText
  $chunkResult = Split-ValidationTextArtifactIntoChunks -SourcePath $sourcePath -ArtifactsDir $State.ArtifactsDir -RequestedKB $RequestedKB -TargetChunkKB 700
  $pathListPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_chunk_paths.json.txt' -f $RequestedKB) -Text (Convert-ToSafeJsonText -InputObject $chunkResult.ChunkPaths)

  $manifestObj = [ordered]@{
    fixture_origin = 'collector_synthetic_validation'
    source_path = $sourcePath
    source_size_kb = Get-FileSizeKB -Path $sourcePath
    target_chunk_kb = $chunkResult.TargetChunkKB
    chunk_count = $chunkResult.ChunkCount
    chunk_paths = $chunkResult.ChunkPaths
    chunk_file_sizes_kb = $chunkResult.ChunkSizesKB
    reconstruction_order = $chunkResult.ReconstructionOrder
  }
  $manifestPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'VALIDATION_CHUNKING' -Name ('synthetic_oversize_{0}KB_chunk_manifest.json.txt' -f $RequestedKB) -Text (Convert-ToSafeJsonText -InputObject $manifestObj)

  $State.SyntheticOversizeSourcePath = $sourcePath
  $State.ChunkManifestPath = $manifestPath
  $Baseline.ArtifactMap['synthetic_oversize_source'] = $sourcePath
  $Baseline.ArtifactMap['synthetic_oversize_chunk_manifest'] = $manifestPath
  $Baseline.ArtifactMap['synthetic_oversize_chunk_paths_json'] = $pathListPath
  [void]$Baseline.ArtifactPaths.Add($sourcePath)
  [void]$Baseline.ArtifactPaths.Add($pathListPath)
  [void]$Baseline.ArtifactPaths.Add($manifestPath)
  foreach ($chunkPath in $chunkResult.ChunkPaths) {
    [void]$Baseline.ArtifactPaths.Add($chunkPath)
  }

  $summaryText = @(
    'VALIDATION_SYNTHETIC_CHUNKING',
    ('REQUESTED_SYNTHETIC_SOURCE_KB={0}' -f $RequestedKB),
    ('SOURCE_PATH={0}' -f $sourcePath),
    ('SOURCE_SIZE_KB={0}' -f (Get-FileSizeKB -Path $sourcePath)),
    ('CHUNK_MANIFEST_PATH={0}' -f $manifestPath),
    ('CHUNK_COUNT={0}' -f $chunkResult.ChunkCount),
    ('TARGET_CHUNK_KB={0}' -f $chunkResult.TargetChunkKB)
  ) -join [Environment]::NewLine
  Add-Section -Builder $Baseline.ReportBuilder -Name 'VALIDATION_SYNTHETIC_CHUNKING' -Text $summaryText
  Add-CollectorNote ('Synthetic oversized validation artifact and chunk set were emitted for collector chunking regression at {0} KB.' -f $RequestedKB)
}

<#
.SYNOPSIS
Applies feature-wave collection enhancements to the current baseline run.

.DESCRIPTION
Creates the targeted-collection scope and plan artifacts, emits the bounded parallelism
assessment, optionally generates synthetic chunk-validation artifacts, and appends the
resulting artifacts and notes to the baseline report and artifact map.

.FUNCTION NAME
Apply-FeatureWaveCollectEnhancements

.INPUTS
Collector state hashtable and baseline result hashtable.

.OUTPUTS
No direct return value. Updates state, baseline artifact maps, report content, and
collector notes/recommendations.
#>
function Apply-FeatureWaveCollectEnhancements {
  param([hashtable]$State,[hashtable]$Baseline)

  $scope = Get-TargetedCollectionScopeObject -State $State
  $scopeText = Get-TargetedCollectionScopeText -Scope $scope
  $scopePath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TARGETED_COLLECTION" -Name "collection_scope.txt" -Text $scopeText
  $State.CollectionScopePath = $scopePath
  $Baseline.ArtifactMap['collection_scope'] = $scopePath
  [void]$Baseline.ArtifactPaths.Add($scopePath)
  Add-Section -Builder $Baseline.ReportBuilder -Name "TARGETED_COLLECTION_SCOPE" -Text $scopeText

  $parallelText = Get-CollectorParallelismAssessmentText
  $parallelPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TARGETED_COLLECTION" -Name "parallelism_assessment.txt" -Text $parallelText
  $State.ParallelismAssessmentPath = $parallelPath
  $Baseline.ArtifactMap['parallelism_assessment'] = $parallelPath
  [void]$Baseline.ArtifactPaths.Add($parallelPath)
  Add-Section -Builder $Baseline.ReportBuilder -Name "COLLECTOR_PARALLELISM_ASSESSMENT" -Text $parallelText

  if ($Targeted -or $scope.has_focus_context -or $scope.has_explicit_time_window) {
    $planText = Get-TargetedCollectionPlanText -Scope $scope
    $planPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "TARGETED_COLLECTION" -Name "targeted_collection_plan.txt" -Text $planText
    $State.TargetedCollectionPlanPath = $planPath
    $Baseline.ArtifactMap['targeted_collection_plan'] = $planPath
    [void]$Baseline.ArtifactPaths.Add($planPath)
    Add-Section -Builder $Baseline.ReportBuilder -Name "TARGETED_COLLECTION_PLAN" -Text $planText

    Add-Recommendation "A targeted collection plan was generated for this run."
    Add-Recommendation "For Gemini uploads, include COLLECTION_SCOPE_PATH and TARGETED_COLLECTION_PLAN_PATH before the full baseline report when the case is narrow or user-reported."
  }

  $syntheticKB = Get-ValidationSyntheticOversizeArtifactKB
  if ($syntheticKB -gt 0) {
    New-SyntheticOversizeChunkValidationArtifacts -State $State -Baseline $Baseline -RequestedKB $syntheticKB
  }

  if ($Targeted) {
    Add-CollectorNote ("Targeted collection mode was enabled with profile [{0}]." -f $TargetProfile)
  }
}
