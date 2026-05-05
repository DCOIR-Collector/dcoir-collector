# chatgpt-exec: DCOIR Airtable Cleanup WBS04 ID inventory
# Purpose: Complete CLEANUP-WBS-04-01, activate CLEANUP-WBS-04-02, and capture evidence.
# Safe config posture: reads DCOIR_AIRTABLE_BASE_ID and DCOIR_AIRTABLE_TOKEN from environment only; never prints token values.

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RunId = 'exec-20260505-wbs04-id-inventory-001'
$NowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (Get-Location).Path }
$ReportDir = Join-Path $RepoRoot "chatgpt_staging/status_reports/chatgpt-exec/$RunId"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$JsonPath = Join-Path $ReportDir 'id_field_inventory.json'
$MdPath = Join-Path $ReportDir 'workflow_report.md'

function Get-DcoirEnvValue {
  param([Parameter(Mandatory=$true)][string]$Name)
  $v = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if ([string]::IsNullOrWhiteSpace($v)) { $v = [Environment]::GetEnvironmentVariable($Name, 'User') }
  if ([string]::IsNullOrWhiteSpace($v)) { $v = [Environment]::GetEnvironmentVariable($Name, 'Machine') }
  if ([string]::IsNullOrWhiteSpace($v)) { throw "Required environment variable is missing: $Name" }
  return $v
}

$BaseId = Get-DcoirEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID'
$Token = Get-DcoirEnvValue -Name 'DCOIR_AIRTABLE_TOKEN'
$Headers = @{ Authorization = "Bearer $Token"; 'Content-Type' = 'application/json' }

function Invoke-AirtableJson {
  param(
    [Parameter(Mandatory=$true)][ValidateSet('GET','POST','PATCH')][string]$Method,
    [Parameter(Mandatory=$true)][string]$Uri,
    [object]$Body = $null
  )
  if ($null -eq $Body) {
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers
  }
  $json = $Body | ConvertTo-Json -Depth 20
  return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body $json
}

function Get-TableByName {
  param([Parameter(Mandatory=$true)]$Schema, [Parameter(Mandatory=$true)][string]$Name)
  $table = $Schema.tables | Where-Object { $_.name -eq $Name } | Select-Object -First 1
  if ($null -eq $table) { throw "Airtable table not found in schema: $Name" }
  return $table
}

function Update-AirtableRecord {
  param(
    [Parameter(Mandatory=$true)][string]$TableId,
    [Parameter(Mandatory=$true)][string]$RecordId,
    [Parameter(Mandatory=$true)][hashtable]$Fields
  )
  $uri = "https://api.airtable.com/v0/$BaseId/$TableId"
  $body = @{ records = @(@{ id = $RecordId; fields = $Fields }); typecast = $true }
  return Invoke-AirtableJson -Method PATCH -Uri $uri -Body $body
}

function Find-AirtableRecordByTextField {
  param(
    [Parameter(Mandatory=$true)][string]$TableId,
    [Parameter(Mandatory=$true)][string]$FieldName,
    [Parameter(Mandatory=$true)][string]$Value
  )
  $safeValue = $Value.Replace("'", "\\'")
  $formula = "{$FieldName} = '$safeValue'"
  $encoded = [uri]::EscapeDataString($formula)
  $uri = "https://api.airtable.com/v0/$BaseId/$TableId?filterByFormula=$encoded&maxRecords=1"
  $result = Invoke-AirtableJson -Method GET -Uri $uri
  if ($result.records.Count -gt 0) { return $result.records[0] }
  return $null
}

function Upsert-AirtableRecordByTextField {
  param(
    [Parameter(Mandatory=$true)][string]$TableId,
    [Parameter(Mandatory=$true)][string]$FieldName,
    [Parameter(Mandatory=$true)][string]$Value,
    [Parameter(Mandatory=$true)][hashtable]$Fields
  )
  $existing = Find-AirtableRecordByTextField -TableId $TableId -FieldName $FieldName -Value $Value
  $uri = "https://api.airtable.com/v0/$BaseId/$TableId"
  if ($null -ne $existing) {
    $body = @{ records = @(@{ id = $existing.id; fields = $Fields }); typecast = $true }
    return Invoke-AirtableJson -Method PATCH -Uri $uri -Body $body
  }
  $body = @{ records = @(@{ fields = $Fields }); typecast = $true }
  return Invoke-AirtableJson -Method POST -Uri $uri -Body $body
}

function Get-IdFieldCategory {
  param([string]$FieldName)
  if ($FieldName -match '(?i)signature') { return 'dedupe_signature' }
  if ($FieldName -match '(?i)record[_ ]id|source_record_id|target_record_id') { return 'airtable_record_reference' }
  if ($FieldName -match '(?i)_entry_id$|entry id$') { return 'helper_memory_entry_id' }
  if ($FieldName -match '(?i)_key$| key$|^key$|primary_key') { return 'canonical_key' }
  if ($FieldName -eq 'config_name') { return 'canonical_config_name' }
  if ($FieldName -match '(?i)_id$| id$|^id$|Test ID|Item ID') { return 'identifier' }
  if ($FieldName -match '(?i)^source_|^parent_|^target_|^canonical_parent_') { return 'lineage_or_target_pointer' }
  return 'identifier_candidate'
}

function Test-IsIdLikeField {
  param([string]$FieldName)
  if ($FieldName -in @('config_name')) { return $true }
  if ($FieldName -match '(?i)(^|[_ /-])(id|key)(s)?($|[_ /-])') { return $true }
  if ($FieldName -match '(?i)(signature|record[_ ]id|primary_key|source_record_id|target_record_id|parent_.*key|canonical_parent_)') { return $true }
  if ($FieldName -match '(?i)^(source_|target_|parent_)') { return $true }
  return $false
}

$SchemaUri = "https://api.airtable.com/v0/meta/bases/$BaseId/tables"
$Schema = Invoke-AirtableJson -Method GET -Uri $SchemaUri

$Inventory = @()
foreach ($table in $Schema.tables) {
  foreach ($field in $table.fields) {
    if (Test-IsIdLikeField -FieldName $field.name) {
      $Inventory += [pscustomobject]@{
        table_name = $table.name
        table_id = $table.id
        field_name = $field.name
        field_id = $field.id
        field_type = $field.type
        is_primary_field = ($field.id -eq $table.primaryFieldId)
        category = Get-IdFieldCategory -FieldName $field.name
      }
    }
  }
}

$Grouped = $Inventory | Group-Object table_name | Sort-Object Name
$Summary = [pscustomobject]@{
  run_id = $RunId
  observed_at_utc = $NowUtc
  base_id_present = $true
  table_count = $Schema.tables.Count
  id_like_field_count = $Inventory.Count
  inventory = $Inventory
}
$Summary | ConvertTo-Json -Depth 20 | Set-Content -Path $JsonPath -Encoding UTF8

$md = New-Object System.Collections.Generic.List[string]
$md.Add("# $RunId")
$md.Add('')
$md.Add("Observed at UTC: $NowUtc")
$md.Add('')
$md.Add('## Result')
$md.Add('')
$md.Add('WBS04-01 ID-related field inventory completed from live Airtable metadata. Token values were not printed, logged, or stored.')
$md.Add('')
$md.Add("Tables inspected: $($Schema.tables.Count)")
$md.Add("ID-like fields inventoried: $($Inventory.Count)")
$md.Add('')
$md.Add('## Inventory')
$md.Add('')
foreach ($group in $Grouped) {
  $md.Add("### $($group.Name)")
  foreach ($item in ($group.Group | Sort-Object field_name)) {
    $primary = if ($item.is_primary_field) { ' primary' } else { '' }
    $md.Add("- `$($item.field_name)` [$($item.field_type); $($item.category)$primary]")
  }
  $md.Add('')
}
$md.Add('## Airtable state changes requested by this script')
$md.Add('')
$md.Add('- `CLEANUP-WBS-04` state -> `active`.')
$md.Add('- `CLEANUP-WBS-04-01` state -> `complete`.')
$md.Add('- `CLEANUP-WBS-04-02` state -> `active`.')
$md.Add('- `PLAN-AIRTABLE-CLEANUP-RESTRUCTURE` active task title corrected to live WBS04 title and child pointer advanced to `CLEANUP-WBS-04-02`.')
$md.Add('- Queue Control refreshed for cleanup-plan resume.')
$md.Add('- Operator lane preference captured/updated: prefer chatgpt-exec/chatgpt staging for bulk Airtable and GitHub work; connectors remain fallback for simple one-off actions.')
$md.Add('')
$md | Set-Content -Path $MdPath -Encoding UTF8

$Tables = @{}
foreach ($t in $Schema.tables) { $Tables[$t.name] = $t.id }
foreach ($required in @('DCOIR Cleanup WBS','Plans','Queue Control','Validation Evidence','Operator Preferences')) {
  if (-not $Tables.ContainsKey($required)) { throw "Required table missing: $required" }
}

$InventoryText = "Completed by $RunId at $NowUtc. Live metadata inventory found $($Inventory.Count) ID/key/signature-like fields across $($Schema.tables.Count) tables. Evidence paths: chatgpt_staging/status_reports/chatgpt-exec/$RunId/id_field_inventory.json and workflow_report.md."

Update-AirtableRecord -TableId $Tables['DCOIR Cleanup WBS'] -RecordId 'recDtAA48oO71h9xd' -Fields @{
  state = 'active'
  validation_notes = 'Parent WBS04 activated by chatgpt-exec after live WBS-title readback. Complete only after all WBS04 children close with evidence.'
} | Out-Null

Update-AirtableRecord -TableId $Tables['DCOIR Cleanup WBS'] -RecordId 'recK35XsTUYBZnvqG' -Fields @{
  state = 'complete'
  validation_notes = $InventoryText
} | Out-Null

Update-AirtableRecord -TableId $Tables['DCOIR Cleanup WBS'] -RecordId 'recrFmt9ic8RFtuLC' -Fields @{
  state = 'active'
  validation_notes = "Activated after WBS04-01 inventory by $RunId. Next step: define table-specific ID components from inventory evidence."
} | Out-Null

Update-AirtableRecord -TableId $Tables['Plans'] -RecordId 'recoLHyurY4OZx3K8' -Fields @{
  active_task_id = 'CLEANUP-WBS-04'
  active_task_title = 'Calculated ID and Dedupe Signature Design'
  active_plan_task_id = 'CLEANUP-WBS-04-02'
  exact_resume_goal = 'Resume at CLEANUP-WBS-04-02 in WBS order. WBS04-01 ID-related field inventory is complete and evidence is in chatgpt_staging status reports.'
  next_recommended_action = 'Continue with CLEANUP-WBS-04-02: Define table-specific ID components using the WBS04-01 inventory evidence.'
  last_updated_text = $NowUtc
  plan_state = 'active'
} | Out-Null

Update-AirtableRecord -TableId $Tables['Queue Control'] -RecordId 'recW8cAlClYFEVhjF' -Fields @{
  branch_summary = 'Active branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE / CLEANUP-WBS-04 Calculated ID and Dedupe Signature Design.'
  branch_decision = 'WBS order maintained. Prior active-task title drift resolved by matching the Plan active title to the live WBS04 title. WBS04-01 completed; WBS04-02 active.'
  resume_rule = 'Resume cleanup plan at CLEANUP-WBS-04-02 unless live Airtable state changes.'
  next_revalidation_trigger = 'After WBS04-02 table-specific ID component design is reviewed.'
  last_confirmed_text = $NowUtc
  notes = "Updated by $RunId. Use chatgpt-exec/chatgpt staging as preferred lane for bulk Airtable/GitHub changes when available."
} | Out-Null

Upsert-AirtableRecordByTextField -TableId $Tables['Validation Evidence'] -FieldName 'evidence_key' -Value 'EVID-CLEANUP-WBS-04-01-ID-INVENTORY-20260505' -Fields @{
  evidence_key = 'EVID-CLEANUP-WBS-04-01-ID-INVENTORY-20260505'
  validation_case_key = 'CLEANUP-WBS-04-01'
  work_item_key = 'CLEANUP-WBS-04-01'
  evidence_summary = $InventoryText
  source_locator = "chatgpt_staging/status_reports/chatgpt-exec/$RunId/"
} | Out-Null

Upsert-AirtableRecordByTextField -TableId $Tables['Operator Preferences'] -FieldName 'preference_key' -Value 'PREF-DCOIR-CHATGPT-EXEC-FIRST-FOR-BULK-WORK' -Fields @{
  preference_key = 'PREF-DCOIR-CHATGPT-EXEC-FIRST-FOR-BULK-WORK'
  preference_statement = 'For DCOIR work, prefer chatgpt-exec, chatgpt staging, GitHub-hosted tools, and reusable scripts for Airtable and GitHub bulk work when available; use direct connectors only as fallback for simple one-off actions.'
  effective_behavior = 'Before bulk Airtable or GitHub changes, prefer the chatgpt-exec/chatgpt-in/chatgpt-out lane and existing repo tools. Use connectors for simple onesies/twosies or when the workflow lane is unavailable, blocked, or disproportionate.'
  source_session_id = 'DCOIR-AIRTABLE-CLEANUP-EXECUTION-20260505'
  last_confirmed_text = $NowUtc
  notes = 'Captured from operator guidance during PLAN-AIRTABLE-CLEANUP-RESTRUCTURE. This is an execution-lane preference, not permission to expose secrets or skip validation/readback gates.'
  status = 'active'
  scope = 'workflow'
} | Out-Null

# Refresh report after successful updates.
$md.Add('## Airtable writeback result')
$md.Add('')
$md.Add('Airtable writeback completed through the REST API using environment-sourced configuration. No secret values were printed or stored.')
$md | Set-Content -Path $MdPath -Encoding UTF8

Write-Host "[$RunId] success: inventoried $($Inventory.Count) ID-like fields across $($Schema.tables.Count) tables and updated Airtable plan state."
Write-Host "[$RunId] report: chatgpt_staging/status_reports/chatgpt-exec/$RunId/workflow_report.md"

# Commit generated status report when running inside GitHub Actions and git is available.
try {
  if ($env:GITHUB_ACTIONS -eq 'true') {
    git config user.name 'github-actions[bot]'
    git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
    git add "chatgpt_staging/status_reports/chatgpt-exec/$RunId"
    $pending = git status --porcelain "chatgpt_staging/status_reports/chatgpt-exec/$RunId"
    if (-not [string]::IsNullOrWhiteSpace($pending)) {
      git commit -m "Add WBS04 ID inventory report"
      git push
    }
  }
} catch {
  Write-Warning "Report commit was not completed: $($_.Exception.Message)"
}
