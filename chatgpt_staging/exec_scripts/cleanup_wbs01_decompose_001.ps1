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
$wbsTable = 'tblRxTmpW0VunQlUK'
$scaffoldTable = 'tblvtcId7PiFKvfKO'
$planTable = 'tblBcp5FyMIfOm7Xe'

$parentRecord = @{
  fields = [ordered]@{
    wbs_key = 'CLEANUP-WBS-01'
    plan_key = $planKey
    wbs_path = '01'
    parent_wbs_key = ''
    rank = 1
    title = 'Discovery and Airtable Inventory'
    level = 'workstream'
    surface = 'airtable'
    state = 'planned'
    gate = 'planning_only'
    target = 'DCOIR Airtable base discovery only'
    done_criteria = 'Complete only when every ordered child task 01.01 through 01.14 is complete, skipped with reason, or blocked/operator-review with evidence. No cleanup action is part of this workstream.'
    validation_notes = 'Read back child WBS row count, parent linkage, and workflow report. Discovery execution later must preserve read-only evidence exports.'
    context = 'Top-level discovery workstream for the DCOIR Airtable Cleanup and Restructuring Plan. It decomposes the read-only inventory needed before table review, classification, ID design, taxonomy, enforcement, or execution sequencing.'
    review_after = $reviewAfter
  }
}
Invoke-DcoirAirtableUpsert -TableId $wbsTable -MergeFieldName 'wbs_key' -Records @($parentRecord)

$items = @(
  @{ Path='01.01'; Title='Confirm discovery scope and authority boundary'; Surface='governance'; Gate='planning_only'; Target='Expertise block and no-cleanup boundary'; Done='Session confirms planning/read-only discovery posture, Airtable authority, GitHub support role, no cleanup execution, no queue processing, no merge, and no schema change unless separately approved.'; Context='First guardrail task before any discovery pass. Future sessions must ensure the DCOIR Airtable Cleanup Expertise Block is present before continuing.' },
  @{ Path='01.02'; Title='Confirm live base and scaffold readback'; Surface='airtable'; Gate='planning_only'; Target='Airtable base, Plans, DCOIR Cleanup WBS, Scaffold Registry'; Done='Live readback confirms parent Plan, CLEANUP-WBS-01, and scaffold registry rows are present and reachable.'; Context='Ensures future sessions start from Airtable live state rather than chat memory.' },
  @{ Path='01.03'; Title='Export base schema inventory'; Surface='airtable'; Gate='planning_only'; Target='All Airtable tables and fields'; Done='Read-only schema export captures table IDs, names, descriptions, primary fields, field IDs, field types, select options, formula fields when available, and linked-record fields.'; Context='Foundation for all later table review and schema-sensitive planning.' },
  @{ Path='01.04'; Title='Export bounded record samples for discovery evidence'; Surface='workflow'; Gate='planning_only'; Target='chatgpt-exec Airtable evidence export'; Done='Read-only evidence bundle exists for bounded records from relevant tables and is referenced by workflow report or artifact.'; Context='Use chatgpt-exec and the reusable Airtable health export tool where practical. This is evidence collection only.' },
  @{ Path='01.05'; Title='Build table inventory index'; Surface='airtable'; Gate='planning_only'; Target='All tables in base'; Done='Each table has a discovery row or WBS note capturing table name, table id, purpose signals, primary field, record count if available, and initial risk posture.'; Context='Creates an operator-readable index of every table before table-by-table review begins.' },
  @{ Path='01.06'; Title='Identify table authority roles'; Surface='airtable'; Gate='planning_only'; Target='All tables in base'; Done='Every table receives an initial authority-role hypothesis such as live authority, support registry, helper memory, validation, reference, history, scaffold, or unknown.'; Context='This is a hypothesis only; later review confirms or changes it.' },
  @{ Path='01.07'; Title='Map linked-record dependencies'; Surface='airtable'; Gate='planning_only'; Target='Linked-record fields'; Done='Linked-record fields are inventoried with source table, target table, dependency direction, and cleanup risk note.'; Context='Required before any future merge, retirement, or row disposition decision.' },
  @{ Path='01.08'; Title='Inventory ID-related fields'; Surface='airtable'; Gate='planning_only'; Target='ID, key, canonical, source, locator, and primary fields'; Done='ID-related fields are listed by table with current type, field purpose, search usefulness, and whether they appear formula-generated, manual, inconsistent, or unknown.'; Context='Feeds calculated ID and dedupe-signature design workstream.' },
  @{ Path='01.09'; Title='Inventory controlled vocabulary fields'; Surface='airtable'; Gate='planning_only'; Target='Single-select and multi-select fields'; Done='Select fields are inventoried with option lists and initial notes on which fields are authoritative decisions versus supplemental tags.'; Context='Feeds controlled vocabulary and taxonomy design.' },
  @{ Path='01.10'; Title='Inventory free-text fields and role boundaries'; Surface='airtable'; Gate='planning_only'; Target='Long-text and single-line text fields'; Done='Free-text fields are categorized as explanatory, evidence, operator notes, source locator, title, ID-like, or risky-authoritative-text.'; Context='Feeds structured-field versus free-text boundary design.' },
  @{ Path='01.11'; Title='Inventory lifecycle and review fields'; Surface='airtable'; Gate='planning_only'; Target='created_at, updated_at, review_after, status, retention fields'; Done='Lifecycle fields are inventoried and initial monitoring gaps are identified without changing records.'; Context='Feeds review-after and drift monitoring design.' },
  @{ Path='01.12'; Title='Inventory Airtable-native enforcement mechanisms'; Surface='airtable'; Gate='planning_only'; Target='Field types, defaults, descriptions, formulas, select constraints, linked records, views where visible'; Done='Existing enforcement mechanisms and gaps are captured at table/field level.'; Context='Feeds Enforcement Assurance Model and Write Gate design.' },
  @{ Path='01.13'; Title='Identify discovery evidence gaps and unsupported surfaces'; Surface='validation'; Gate='planning_only'; Target='Unsupported Airtable metadata and project surfaces'; Done='Discovery notes identify what the available tools cannot see, such as automations, interfaces, extensions, or unsupported metadata, and how to handle those gaps.'; Context='Prevents overclaiming completeness from partial evidence.' },
  @{ Path='01.14'; Title='Discovery workstream closeout and next handoff'; Surface='validation'; Gate='planning_only'; Target='CLEANUP-WBS-01'; Done='All child tasks have state, evidence notes, unresolved gaps, and a single recommended next move into WBS 02 table-by-table review.'; Context='Parent WBS 01 cannot be marked complete until this closeout is done.' }
)

$records = @()
foreach ($item in $items) {
  $key = 'CLEANUP-WBS-' + ($item.Path -replace '\.','-')
  $rank = [int]($item.Path.Split('.')[1])
  $records += @{
    fields = [ordered]@{
      wbs_key = $key
      plan_key = $planKey
      wbs_path = $item.Path
      parent_wbs_key = 'CLEANUP-WBS-01'
      rank = $rank
      title = $item.Title
      level = 'task'
      surface = $item.Surface
      state = 'planned'
      gate = $item.Gate
      target = $item.Target
      done_criteria = $item.Done
      validation_notes = 'Readback of this WBS row and later task evidence required. This row is planning/discovery scaffolding only.'
      context = $item.Context
      review_after = $reviewAfter
    }
  }
}
for ($i = 0; $i -lt $records.Count; $i += 10) {
  $chunk = @($records[$i..([Math]::Min($i + 9, $records.Count - 1))])
  Invoke-DcoirAirtableUpsert -TableId $wbsTable -MergeFieldName 'wbs_key' -Records $chunk
}

$planUpdate = @{
  fields = [ordered]@{
    plan_id = $planKey
    active_task_id = 'CLEANUP-WBS-01'
    active_task_title = 'Discovery and Airtable Inventory decomposition'
    next_recommended_action = 'Begin CLEANUP-WBS-01-01, then proceed through 01.14 in order. Keep discovery read-only.'
    last_updated_text = '2026-05-05T14:20:00Z'
    review_after = $reviewAfter
  }
}
Invoke-DcoirAirtableUpsert -TableId $planTable -MergeFieldName 'plan_id' -Records @($planUpdate)

$scaffoldRecord = @{
  fields = [ordered]@{
    scaffold_key = 'SCAFFOLD-GITHUB-WORKFLOW-CHATGPT-EXEC-WBS01-DECOMPOSITION'
    plan_key = $planKey
    scaffold_name = 'chatgpt-exec WBS 01 decomposition request'
    scaffold_type = 'workflow'
    status = 'active_scaffold'
    purpose = 'Uses GitHub Actions chatgpt-exec to seed ordered WBS 01 child planning tasks and evidence.'
    created_surface = 'GitHub Actions'
    created_locator = 'chatgpt_staging/exec_requests/exec-20260505-cleanup-wbs01-decompose-001.json and chatgpt_staging/exec_scripts/cleanup_wbs01_decompose_001.ps1'
    final_disposition = 'pending'
    review_after = $reviewAfter
    notes = 'Track and disposition this workflow/script scaffold under WBS 22 at plan conclusion.'
  }
}
Invoke-DcoirAirtableUpsert -TableId $scaffoldTable -MergeFieldName 'scaffold_key' -Records @($scaffoldRecord)

$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if (-not [string]::IsNullOrWhiteSpace($downloads)) {
  New-Item -ItemType Directory -Path $downloads -Force | Out-Null
  [ordered]@{
    request_id = 'exec-20260505-cleanup-wbs01-decompose-001'
    parent_wbs_key = 'CLEANUP-WBS-01'
    child_rows_seeded = $records.Count
    cleanup_execution = $false
    discovery_execution = $false
    table_changes = 'WBS planning rows only plus scaffold registry tracking row'
    finished_utc = (Get-Date).ToUniversalTime().ToString('o')
  } | ConvertTo-Json -Depth 10 | Set-Content -Path (Join-Path $downloads 'cleanup_wbs01_decomposition_summary.json') -Encoding UTF8
}

Write-Host "Seeded CLEANUP-WBS-01 decomposition: $($records.Count) child tasks plus scaffold tracking row."
