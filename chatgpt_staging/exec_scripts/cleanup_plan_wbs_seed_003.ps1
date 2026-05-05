$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$token = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Machine')
$base = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
if ([string]::IsNullOrWhiteSpace($token)) { throw 'Missing DCOIR_AIRTABLE_TOKEN' }
if ([string]::IsNullOrWhiteSpace($base)) { throw 'Missing DCOIR_AIRTABLE_BASE_ID' }

$headers = @{
  Authorization = "Bearer $token"
  'Content-Type' = 'application/json'
}

function Invoke-DcoirAirtableUpsert {
  param(
    [Parameter(Mandatory=$true)][string]$TableId,
    [Parameter(Mandatory=$true)][string]$MergeFieldName,
    [Parameter(Mandatory=$true)][array]$Records
  )
  $bodyObj = @{
    performUpsert = @{ fieldsToMergeOn = @($MergeFieldName) }
    records = $Records
    typecast = $false
  }
  $json = $bodyObj | ConvertTo-Json -Depth 100 -Compress
  $uri = "https://api.airtable.com/v0/$base/$TableId"
  Invoke-RestMethod -Method Patch -Uri $uri -Headers $headers -Body $json | Out-Null
}

$planKey = 'PLAN-AIRTABLE-CLEANUP-RESTRUCTURE'
$reviewAfter = '2026-08-05'

$planRecord = @{
  fields = [ordered]@{
    plan_id = $planKey
    plan_title = 'DCOIR Airtable Cleanup and Restructuring Plan'
    plan_state = 'planning'
    retention_class = 'operational'
    active_task_id = 'CLEANUP-WBS-00'
    active_task_title = 'Planning framework and plan-scoped scaffold initialization'
    scope_constraints = 'Planning framework only. No cleanup execution, deletion, merge, Delete Queue processing, non-scaffold schema change, skill edit, GitHub source edit, or project-instruction edit without explicit operator approval.'
    exact_resume_goal = 'Resume from DCOIR Cleanup WBS and execute in WBS order using the DCOIR Airtable Cleanup Expertise Block.'
    resume_detail = 'Plan covers Airtable cleanup planning, calculated IDs, controlled vocabulary, dedupe prevention, stricter archive rules, Write Gate, drift monitoring, validation, and cross-surface impacts across skills, project instructions, sources, GitHub, and automation.'
    why_current_task_matters = 'This establishes a plan-scoped execution structure detailed enough for future sessions to continue without relying on chat memory and strict enough to prevent flat-plan completion errors.'
    carry_forward_note = 'Future related sessions must include the expertise block. If missing, hard-stop before planning or execution. Prefer chatgpt-exec as autonomous evidence lane when suitable.'
    flush_trigger = 'After scaffold seed, after each WBS decomposition pass, before execution-session closeout, and before final scaffold disposition.'
    pending_flush_items = 'Future decomposition of top-level WBS workstreams into ordered child tasks, subtasks, and atomic items.'
    promotion_candidates = 'Potential future integration of WBS/scaffold registry into standard DCOIR planning architecture after the plan concludes.'
    remain_local_notes = 'No cleanup execution is authorized by this seed. The scaffold is plan-scoped until final disposition decision.'
    next_recommended_action = 'Decompose CLEANUP-WBS-01 Discovery into ordered child tasks.'
    last_updated_text = '2026-05-05T13:40:00Z'
    review_after = $reviewAfter
  }
}
Invoke-DcoirAirtableUpsert -TableId 'tblBcp5FyMIfOm7Xe' -MergeFieldName 'plan_id' -Records @($planRecord)

$wbsLines = @'
01|Discovery and Airtable Inventory|airtable|planning_only
02|Table-by-Table Review Methodology|airtable|planning_only
03|Structured Field and Free-Text Boundary|airtable|planning_only
04|Calculated ID and Dedupe Signature Design|airtable|planning_only
05|Controlled Vocabulary and Taxonomy Design|airtable|planning_only
06|Cleanup Classification Model|airtable|planning_only
07|Cross-Surface Impact Review|mixed|planning_only
08|Enforcement Assurance Model|mixed|planning_only
09|DCOIR Airtable Write Gate Design|airtable|planning_only
10|Review-After and Drift Monitoring Design|automation|planning_only
11|Validation and Readback Strategy|validation|planning_only
12|Execution-Lane Decision Rules|mixed|planning_only
13|Safety and Approval Gates|governance|planning_only
14|Prompt and Expertise Block Enforcement|project_config|planning_only
15|DCOIR Skill Impact and Restructure Review|skill|skill_change
16|ChatGPT Project Instructions Impact Review|project_config|config_change
17|Project Sources and Attachment Set Review|source|planning_only
18|GitHub Files and Workflow Impact Review|github|github_change
19|Toolbox and Automation Architecture Review|automation|planning_only
20|Cross-Surface Change Sequencing and Approval Model|mixed|operator_review
21|Work Breakdown Structure and Execution Traceability Model|governance|planning_only
22|Scaffold Lifecycle and Decommissioning Review|governance|operator_review
22.01|Inventory scaffold objects created for this plan|airtable|planning_only
22.02|Review scaffold objects for integration fit|mixed|operator_review
22.03|Execute approved scaffold disposition decisions|mixed|operator_review
22.04|Record scaffold disposition evidence|validation|planning_only
'@

$wbsRecords = @()
foreach ($line in ($wbsLines.Trim() -split "`n")) {
  $parts = $line.Trim().Split('|')
  $path = $parts[0]
  $title = $parts[1]
  $surface = $parts[2]
  $gate = $parts[3]
  $level = if ($path.Contains('.')) { 'task' } else { 'workstream' }
  $parent = if ($path -like '22.*') { 'CLEANUP-WBS-22' } else { '' }
  $rank = if ($path.Contains('.')) { [int]($path.Split('.')[1]) } else { [int]$path }
  $key = 'CLEANUP-WBS-' + ($path -replace '\.','-')
  $done = if ($path -eq '22') {
    'Complete only when all scaffold objects have a reviewed final disposition decision: integrate, leave temporarily, or retire, and evidence is recorded.'
  } else {
    'Complete only when child tasks are complete, skipped with reason, or blocked/operator-review with evidence and required readback passes.'
  }
  $context = if ($path -like '22*') {
    'Scaffold lifecycle item. Track temporary support objects created for this plan so they do not become project bloat. At plan conclusion decide integrate, leave temporarily, or retire.'
  } else {
    'Plan-scoped WBS item for DCOIR Airtable Cleanup and Restructuring Plan. Future sessions must use WBS order and not rely on chat memory.'
  }
  $wbsRecords += @{
    fields = [ordered]@{
      wbs_key = $key
      plan_key = $planKey
      wbs_path = $path
      parent_wbs_key = $parent
      rank = $rank
      title = $title
      level = $level
      surface = $surface
      state = 'planned'
      gate = $gate
      target = 'plan-scoped framework'
      done_criteria = $done
      validation_notes = 'Read back WBS row values and preserve workflow report/artifact as evidence. No cleanup execution authorized.'
      context = $context
      review_after = $reviewAfter
    }
  }
}

for ($i = 0; $i -lt $wbsRecords.Count; $i += 10) {
  $chunk = @($wbsRecords[$i..([Math]::Min($i + 9, $wbsRecords.Count - 1))])
  Invoke-DcoirAirtableUpsert -TableId 'tblRxTmpW0VunQlUK' -MergeFieldName 'wbs_key' -Records $chunk
}

$scaffoldRecords = @(
  @{
    fields = [ordered]@{
      scaffold_key = 'SCAFFOLD-AIRTABLE-TABLE-DCOIR-CLEANUP-WBS'
      plan_key = $planKey
      scaffold_name = 'DCOIR Cleanup WBS'
      scaffold_type = 'airtable_table'
      status = 'active_scaffold'
      purpose = 'Plan-scoped WBS hierarchy table for nested execution planning.'
      created_surface = 'Airtable'
      created_locator = 'tblRxTmpW0VunQlUK'
      final_disposition = 'pending'
      review_after = $reviewAfter
      notes = 'At plan conclusion decide integrate, leave temporarily, or retire.'
    }
  },
  @{
    fields = [ordered]@{
      scaffold_key = 'SCAFFOLD-AIRTABLE-TABLE-DCOIR-CLEANUP-SCAFFOLD-REGISTRY'
      plan_key = $planKey
      scaffold_name = 'DCOIR Cleanup Scaffold Registry'
      scaffold_type = 'airtable_table'
      status = 'active_scaffold'
      purpose = 'Tracks scaffold objects so they do not become project bloat.'
      created_surface = 'Airtable'
      created_locator = 'tblvtcId7PiFKvfKO'
      final_disposition = 'pending'
      review_after = $reviewAfter
      notes = 'At plan conclusion decide integrate, leave temporarily, or retire.'
    }
  },
  @{
    fields = [ordered]@{
      scaffold_key = 'SCAFFOLD-GITHUB-WORKFLOW-CHATGPT-EXEC-CLEANUP-SEED'
      plan_key = $planKey
      scaffold_name = 'chatgpt-exec cleanup plan scaffold seed request'
      scaffold_type = 'workflow'
      status = 'active_scaffold'
      purpose = 'Uses GitHub Actions chatgpt-exec for autonomous seed/readback evidence.'
      created_surface = 'GitHub Actions'
      created_locator = 'chatgpt_staging/exec_requests/exec-20260505-cleanup-plan-wbs-seed-003.json and chatgpt_staging/exec_scripts/cleanup_plan_wbs_seed_003.ps1'
      final_disposition = 'pending'
      review_after = $reviewAfter
      notes = 'Track and disposition this workflow/script scaffold at plan conclusion.'
    }
  }
)
Invoke-DcoirAirtableUpsert -TableId 'tblvtcId7PiFKvfKO' -MergeFieldName 'scaffold_key' -Records $scaffoldRecords

$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if (-not [string]::IsNullOrWhiteSpace($downloads)) {
  $summary = [ordered]@{
    request_id = 'exec-20260505-cleanup-plan-wbs-seed-003'
    plan_key = $planKey
    plan_table = 'tblBcp5FyMIfOm7Xe'
    wbs_table = 'tblRxTmpW0VunQlUK'
    scaffold_registry_table = 'tblvtcId7PiFKvfKO'
    wbs_rows_seeded = $wbsRecords.Count
    scaffold_rows_seeded = $scaffoldRecords.Count
    cleanup_execution = $false
    delete_queue_processing = $false
    finished_utc = (Get-Date).ToUniversalTime().ToString('o')
  }
  New-Item -ItemType Directory -Path $downloads -Force | Out-Null
  $summary | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $downloads 'cleanup_plan_wbs_seed_summary.json') -Encoding UTF8
}

Write-Host "Seeded cleanup plan, $($wbsRecords.Count) WBS rows, and $($scaffoldRecords.Count) scaffold registry rows via chatgpt-exec."
