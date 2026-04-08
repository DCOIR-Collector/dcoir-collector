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

function Get-CollectorParallelismAssessmentText {
  $lines = @()
  $lines += "COLLECTOR_PARALLELISM_ASSESSMENT"
  $lines += "STATUS=ASSESSMENT_ONLY"
  $lines += ""
  $lines += "CURRENT POSITION"
  $lines += "- The collector remains serial by default in this major-version wave."
  $lines += "- The operator requested a durable assessment of whether PowerShell 5.1-safe parallelism is feasible."
  $lines += "- This file records that assessment explicitly so it becomes part of the governed collector output and future planning surface."
  $lines += ""
  $lines += "SAFE CANDIDATE AREAS FOR FUTURE PARALLELISM REVIEW"
  $lines += "1. Independent text-only baseline captures that do not mutate shared state and do not depend on each other."
  $lines += "2. Independent enrichment actions when they are intentionally run in separate sessions and their outputs are isolated."
  $lines += "3. Read-only data gathers that do not race on the same staging or bundle paths."
  $lines += ""
  $lines += "CURRENT BLOCKERS TO DIRECT MULTITHREADING"
  $lines += "1. The current collector assumes ordered state updates, ordered artifact writes, and ordered report assembly."
  $lines += "2. The current run folder and session state handling are easier to reason about in serial execution."
  $lines += "3. PowerShell 5.1 runspace or job-based parallelism would require explicit guardrails for state, logs, error handling, and deterministic output ordering."
  $lines += ""
  $lines += "RECOMMENDATION"
  $lines += "- Keep runtime behavior serial for this release."
  $lines += "- Treat parallelism as a bounded future engineering assessment rather than an already-approved runtime change."
  return ($lines -join [Environment]::NewLine)
}

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

  if ($Targeted) {
    Add-CollectorNote ("Targeted collection mode was enabled with profile [{0}]." -f $TargetProfile)
  }
}
