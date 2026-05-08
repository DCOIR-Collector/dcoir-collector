$ErrorActionPreference = 'Stop'

$token = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Machine')
$baseId = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if (-not $token) { throw 'Missing DCOIR_AIRTABLE_TOKEN' }
if (-not $baseId) { throw 'Missing DCOIR_AIRTABLE_BASE_ID' }
if (-not $downloads) { throw 'Missing DCOIR_DOWNLOADS_DIR' }

$outDir = Join-Path $downloads 'wbs22_wave2_discovery_20260508_002'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$headers = @{ Authorization = "Bearer $token" }
$metaUrl = "https://api.airtable.com/v0/meta/bases/$baseId/tables"
$meta = Invoke-RestMethod -Method Get -Uri $metaUrl -Headers $headers

$wave2Universe = @(
  'Work Items','Session Checkpoints','Idea Inbox','Plans','Operator Preferences','Validation Test Cases','Queue Control','Gemini Research Reference','Governance Control Plane','Repo Surface Registry','dcoir-memory-preflight','dcoir-decision-policy','dcoir-validation-orchestrator','Delete Queue','Validation Evidence','Admin Registry','DCOIR Lifecycle Ledger','Local Configuration Registry','Operator Tools Registry','DCOIR Cleanup WBS','DCOIR Cleanup Scaffold Registry'
)
$includedNames = @(
  'Work Items','Session Checkpoints','Idea Inbox','Plans','Operator Preferences','Validation Test Cases','Queue Control','Gemini Research Reference','Governance Control Plane','Repo Surface Registry','dcoir-memory-preflight','dcoir-decision-policy','dcoir-validation-orchestrator','Validation Evidence','Admin Registry','DCOIR Lifecycle Ledger','Local Configuration Registry','Operator Tools Registry','DCOIR Cleanup WBS'
)
$readOnlyNames = @('Delete Queue')
$deferredNames = @('DCOIR Cleanup Scaffold Registry')
$targetFieldNames = @('retention_class','review_after','status','state','plan_state','checkpoint_status','active_task_id','active_task_title','next_recommended_action','resume_prompt','decisions_constraints','validation_notes','context','branch_summary','branch_decision','resume_rule','revalidation')

function Get-Class($name) {
  if ($includedNames -contains $name) { return 'included_review_action' }
  if ($readOnlyNames -contains $name) { return 'read_only_excluded_no_queue_action' }
  if ($deferredNames -contains $name) { return 'deferred_wbs23_unless_non_disposition_classification' }
  return 'excluded_outside_wave2_inventory'
}

function Get-Records($tableId) {
  $records = @()
  $offset = $null
  do {
    $uri = "https://api.airtable.com/v0/$baseId/$tableId?pageSize=100"
    if ($offset) { $uri += "&offset=$([uri]::EscapeDataString($offset))" }
    $resp = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
    if ($resp.records) { $records += $resp.records }
    $offset = $resp.offset
  } while ($offset)
  return $records
}

function Text-Of($record) {
  $parts = New-Object System.Collections.Generic.List[string]
  foreach ($p in $record.fields.PSObject.Properties) {
    if ($null -ne $p.Value) { $parts.Add([string]$p.Value) }
  }
  return ($parts -join "`n")
}

$allTables = @()
$candidates = @()
$metrics = [ordered]@{
  generated_at_utc = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
  request_id = 'exec-20260508-wbs22-wave2-discovery-002'
  mode = 'discovery_proposal_only_no_mutation'
  live_table_count = @($meta.tables).Count
  wave2_universe_count = $wave2Universe.Count
  classified_live_tables = 0
  included_tables = 0
  read_only_tables = 0
  deferred_tables = 0
  excluded_tables = 0
  records_scanned_total = 0
  stale_pointer_candidates = 0
  review_retention_candidates = 0
  status_contradiction_candidates = 0
  stale_helper_reference_candidates = 0
  bookkeeping_completion_claim_candidates = 0
  safe_wave2_update_candidates = 0
}

foreach ($t in $meta.tables) {
  $class = Get-Class $t.name
  $fieldNames = @($t.fields | ForEach-Object { $_.name })
  $relevant = @($fieldNames | Where-Object { $targetFieldNames -contains $_ })
  $allTables += [pscustomobject][ordered]@{ table_name=$t.name; table_id=$t.id; class=$class; field_count=@($t.fields).Count; relevant_fields=$relevant }
  $metrics.classified_live_tables++
  switch ($class) {
    'included_review_action' { $metrics.included_tables++ }
    'read_only_excluded_no_queue_action' { $metrics.read_only_tables++ }
    'deferred_wbs23_unless_non_disposition_classification' { $metrics.deferred_tables++ }
    default { $metrics.excluded_tables++ }
  }
  if ($class -eq 'excluded_outside_wave2_inventory') { continue }
  $records = Get-Records $t.id
  $metrics.records_scanned_total += @($records).Count
  foreach ($r in $records) {
    $text = Text-Of $r
    $reasons = New-Object System.Collections.Generic.List[string]
    $safe = ($class -eq 'included_review_action')
    if ($text -match 'dcoir-continuity-manager|dcoir-session-manager|dcoir-session-resume|dcoir-source-authority-auditor|dcoir-airtable-write-gate') { $reasons.Add('stale_helper_or_retired_skill_reference'); $metrics.stale_helper_reference_candidates++ }
    if ($text -match 'Wave 2 preparation completed by exec-20260507|Wave 3 batch complete|Wave 4 batch complete|Wave 5 complete|bookkeeping-only|prior Wave [1-5].*bookkeeping') { $reasons.Add('bookkeeping_or_prior_wave_completion_claim_needs_review'); $metrics.bookkeeping_completion_claim_candidates++ }
    if ($text -match 'active_task_id CLEANUP-WBS-08|points to WBS09.*Plan row as drift|active task is CLEANUP-WBS-22-03' -and $text -notmatch 'historical') { $reasons.Add('possible_stale_active_pointer_text'); $metrics.stale_pointer_candidates++ }
    foreach ($fn in @('retention_class','review_after')) {
      if ($fieldNames -contains $fn) {
        $v = $r.fields.$fn
        if ($null -eq $v -or [string]$v -eq '') { $reasons.Add("missing_$fn"); $metrics.review_retention_candidates++ }
      }
    }
    foreach ($sf in @('status','state','plan_state','checkpoint_status')) {
      if ($fieldNames -contains $sf) {
        $sv = [string]$r.fields.$sf
        if ($sv -match 'current|active|final_for_session|open' -and $text -match 'complete|superseded|historical|bookkeeping-only') { $reasons.Add("possible_status_text_contradiction_$sf"); $metrics.status_contradiction_candidates++ }
      }
    }
    if ($reasons.Count -gt 0) {
      if ($safe) { $metrics.safe_wave2_update_candidates++ }
      $primary = $null
      if ($r.fields.PSObject.Properties.Count -gt 0) { $primary = [string]($r.fields.PSObject.Properties | Select-Object -First 1).Value }
      $candidates += [pscustomobject][ordered]@{
        table_name=$t.name
        table_id=$t.id
        record_id=$r.id
        primary_text=$primary
        class=$class
        safe_wave2_candidate=$safe
        reasons=@($reasons)
        proposed_action='review_and_prepare_exact_wave2_safe_text_or_field_update_only'
        prohibited_actions='no delete, no merge, no Delete Queue, no schema, no source/skill/workflow mutation'
        createdTime=$r.createdTime
      }
    }
  }
}

$metrics | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $outDir 'wave2_before_metrics.json')
$allTables | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $outDir 'wave2_table_classification.json')
$candidates | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $outDir 'wave2_candidates.json')

$md = New-Object System.Collections.Generic.List[string]
$md.Add('# WBS22 Wave 2 discovery/proposal report')
$md.Add('')
$md.Add('Mode: discovery/proposal only. No Airtable mutation was performed.')
$md.Add('')
$md.Add('## Before metrics')
foreach ($p in $metrics.GetEnumerator()) { $md.Add("- $($p.Key): $($p.Value)") }
$md.Add('')
$md.Add('## Top candidates')
foreach ($c in ($candidates | Select-Object -First 75)) { $md.Add("- $($c.table_name) / $($c.record_id): $($c.reasons -join ', ')") }
$md.Add('')
$md.Add('## Required next step')
$md.Add('Review candidates and prepare exact Wave 2-safe update payload before mutation.')
$md | Set-Content -Encoding UTF8 (Join-Path $outDir 'wave2_discovery_report.md')

Write-Host 'WBS22 Wave 2 discovery complete'
Write-Host "Output directory: $outDir"
Write-Host "Candidate count: $($candidates.Count)"
