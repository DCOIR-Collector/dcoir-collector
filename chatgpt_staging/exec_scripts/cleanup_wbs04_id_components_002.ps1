# chatgpt-exec: DCOIR Airtable Cleanup WBS04 ID component design
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RunId = 'exec-20260505-wbs04-id-components-002'
$NowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (Get-Location).Path }
$DownloadsDir = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($DownloadsDir)) { $DownloadsDir = Join-Path $RepoRoot 'chatgpt_staging/tmp_exec_outputs' }
$OutDir = Join-Path $DownloadsDir $RunId
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$JsonPath = Join-Path $OutDir 'wbs04_id_components.json'
$MdPath = Join-Path $OutDir 'wbs04_id_components.md'

function Get-DcoirEnvValue([string]$Name) {
  $v = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if ([string]::IsNullOrWhiteSpace($v)) { $v = [Environment]::GetEnvironmentVariable($Name, 'User') }
  if ([string]::IsNullOrWhiteSpace($v)) { $v = [Environment]::GetEnvironmentVariable($Name, 'Machine') }
  if ([string]::IsNullOrWhiteSpace($v)) { throw "Required environment variable is missing: $Name" }
  return $v
}

$BaseId = Get-DcoirEnvValue 'DCOIR_AIRTABLE_BASE_ID'
$Token = Get-DcoirEnvValue 'DCOIR_AIRTABLE_TOKEN'
$Headers = @{ Authorization = "Bearer $Token"; 'Content-Type' = 'application/json' }

function Invoke-AirtableJson {
  param([string]$Method, [string]$Uri, [object]$Body = $null)
  if ($null -eq $Body) { return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers }
  return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body ($Body | ConvertTo-Json -Depth 30)
}
function Patch-AtRecord([string]$TableId, [string]$RecordId, [hashtable]$Fields) {
  $uri = ('https://api.airtable.com/v0/{0}/{1}' -f $BaseId, $TableId)
  Invoke-AirtableJson PATCH $uri @{ records = @(@{ id = $RecordId; fields = $Fields }); typecast = $true } | Out-Null
}
function Find-AtRecord([string]$TableId, [string]$FieldName, [string]$Value) {
  $safe = $Value.Replace("'", "\\'")
  $formula = "{$FieldName} = '$safe'"
  $encoded = [uri]::EscapeDataString($formula)
  $uri = ('https://api.airtable.com/v0/{0}/{1}?filterByFormula={2}&maxRecords=1' -f $BaseId, $TableId, $encoded)
  $r = Invoke-AirtableJson GET $uri
  if ($r.records.Count -gt 0) { return $r.records[0] }
  return $null
}
function Upsert-AtRecord([string]$TableId, [string]$FieldName, [string]$Value, [hashtable]$Fields) {
  $existing = Find-AtRecord $TableId $FieldName $Value
  $uri = ('https://api.airtable.com/v0/{0}/{1}' -f $BaseId, $TableId)
  if ($null -ne $existing) {
    Invoke-AirtableJson PATCH $uri @{ records = @(@{ id = $existing.id; fields = $Fields }); typecast = $true } | Out-Null
  } else {
    Invoke-AirtableJson POST $uri @{ records = @(@{ fields = $Fields }); typecast = $true } | Out-Null
  }
}
function Is-IdLike([string]$Name) {
  if ($Name -eq 'config_name') { return $true }
  if ($Name -match '(?i)(^|[_ /-])(id|key)(s)?($|[_ /-])') { return $true }
  if ($Name -match '(?i)(signature|record[_ ]id|primary_key|source_record_id|target_record_id|parent_.*key|canonical_parent_)') { return $true }
  if ($Name -match '(?i)^(source_|target_|parent_)') { return $true }
  return $false
}
function IdCategory([string]$Name) {
  if ($Name -match '(?i)signature') { return 'dedupe_signature' }
  if ($Name -match '(?i)record[_ ]id|source_record_id|target_record_id') { return 'airtable_record_reference' }
  if ($Name -match '(?i)_entry_id$|entry id$') { return 'helper_memory_entry_id' }
  if ($Name -match '(?i)_key$| key$|^key$|primary_key') { return 'canonical_key' }
  if ($Name -eq 'config_name') { return 'canonical_config_name' }
  if ($Name -match '(?i)^source_|^parent_|^target_|^canonical_parent_') { return 'lineage_or_target_pointer' }
  if ($Name -match '(?i)_id$| id$|^id$|Test ID|Item ID') { return 'identifier' }
  return 'identifier_candidate'
}
function TableCode([string]$Name) {
  $parts = @([regex]::Matches($Name, '[A-Za-z0-9]+') | ForEach-Object { $_.Value })
  if ($parts.Count -eq 0) { return 'TBL' }
  if ($parts.Count -gt 1) { $code = ($parts | ForEach-Object { $_.Substring(0,1).ToUpperInvariant() }) -join '' } else { $code = $parts[0].ToUpperInvariant() }
  if ($code.Length -gt 10) { $code = $code.Substring(0,10) }
  return $code
}

$Schema = Invoke-AirtableJson GET ('https://api.airtable.com/v0/meta/bases/{0}/tables' -f $BaseId)
$Tables = @{}; foreach ($t in $Schema.tables) { $Tables[$t.name] = $t.id }
foreach ($required in @('DCOIR Cleanup WBS','Plans','Queue Control','Validation Evidence','Operator Preferences')) { if (-not $Tables.ContainsKey($required)) { throw "Missing table: $required" } }

$Inventory = @(); $Components = @()
foreach ($table in ($Schema.tables | Sort-Object name)) {
  $primary = $table.fields | Where-Object { $_.id -eq $table.primaryFieldId } | Select-Object -First 1
  $idFields = @()
  foreach ($field in $table.fields) {
    if (Is-IdLike $field.name) {
      $cat = IdCategory $field.name
      $o = [pscustomobject]@{ field_name = $field.name; field_id = $field.id; field_type = $field.type; category = $cat; is_primary = ($field.id -eq $table.primaryFieldId) }
      $idFields += $o
      $Inventory += [pscustomobject]@{ table_name = $table.name; table_id = $table.id; field_name = $field.name; field_id = $field.id; field_type = $field.type; category = $cat; is_primary_field = $o.is_primary }
    }
  }
  $canonical = @($idFields | Where-Object { $_.category -in @('canonical_key','canonical_config_name','helper_memory_entry_id') } | ForEach-Object { $_.field_name })
  $lineage = @($idFields | Where-Object { $_.category -eq 'lineage_or_target_pointer' } | ForEach-Object { $_.field_name })
  $recordRefs = @($idFields | Where-Object { $_.category -eq 'airtable_record_reference' } | ForEach-Object { $_.field_name })
  $slug = @($table.fields | Where-Object { $_.name -match '(?i)(title|name|summary|work item|test case|locator|surface|tool|object|control|plan|checkpoint|idea|event)' } | ForEach-Object { $_.name } | Select-Object -Unique | Select-Object -First 4)
  if ($slug.Count -eq 0 -and $null -ne $primary) { $slug = @($primary.name) }
  $code = TableCode $table.name
  $identity = if ($canonical.Count -gt 0) { $canonical -join ', ' } elseif ($idFields.Count -gt 0) { @($idFields | Select-Object -First 3 | ForEach-Object { $_.field_name }) -join ', ' } else { 'future_' + $code.ToLowerInvariant() + '_key' }
  $suffix = if ($lineage.Count -gt 0) { $lineage -join ', ' } elseif ($recordRefs.Count -gt 0) { $recordRefs -join ', ' } else { 'Airtable record id only as collision fallback' }
  $slugText = if ($slug.Count -gt 0) { $slug -join ', ' } else { 'primary field' }
  $Components += [pscustomobject]@{
    table_name = $table.name; table_id = $table.id; table_code = $code; primary_field = $(if ($primary) { $primary.name } else { '' });
    existing_id_fields = @($idFields | ForEach-Object { $_.field_name }); canonical_identity_component = $identity;
    slug_source_components = $slug; uniqueness_suffix_component = $suffix; dedupe_signature_candidate = ('normalize(' + $slugText + ') + scope(' + $suffix + ')');
    recommendation = $(if ($canonical.Count -gt 0) { 'keep existing canonical key pattern; standardize slug and dedupe formula around it' } else { 'do not add schema yet; use proposed key component in later schema review only if needed' })
  }
}

[pscustomobject]@{ run_id=$RunId; observed_at_utc=$NowUtc; table_count=$Schema.tables.Count; id_like_field_count=$Inventory.Count; component_design_count=$Components.Count; inventory=$Inventory; table_components=$Components } | ConvertTo-Json -Depth 30 | Set-Content $JsonPath -Encoding UTF8
$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# WBS04 ID component design'); $lines.Add(''); $lines.Add("Run: $RunId"); $lines.Add("Observed UTC: $NowUtc"); $lines.Add('')
foreach ($row in ($Components | Sort-Object table_name)) { $lines.Add("## $($row.table_name)"); $lines.Add("- table_code: `$($row.table_code)`"); $lines.Add("- canonical_identity_component: `$($row.canonical_identity_component)`"); $lines.Add("- slug_source_components: `$((@($row.slug_source_components) -join ', '))`"); $lines.Add("- uniqueness_suffix_component: `$($row.uniqueness_suffix_component)`"); $lines.Add("- dedupe_signature_candidate: `$($row.dedupe_signature_candidate)`"); $lines.Add("- recommendation: $($row.recommendation)"); $lines.Add('') }
$lines | Set-Content $MdPath -Encoding UTF8

$InventoryEvidence = "WBS04-01 evidence repaired by $RunId. Live metadata inventory observed $($Inventory.Count) ID/key/signature-like fields across $($Schema.tables.Count) tables."
$ComponentEvidence = "WBS04-02 completed by $RunId. Table-specific ID components designed for $($Components.Count) tables. Artifact files: wbs04_id_components.json and wbs04_id_components.md."
Patch-AtRecord $Tables['DCOIR Cleanup WBS'] 'recDtAA48oO71h9xd' @{ state='active'; validation_notes='Parent WBS04 remains active; continue ordered child tasks.' }
Patch-AtRecord $Tables['DCOIR Cleanup WBS'] 'recK35XsTUYBZnvqG' @{ state='complete'; validation_notes=$InventoryEvidence }
Patch-AtRecord $Tables['DCOIR Cleanup WBS'] 'recrFmt9ic8RFtuLC' @{ state='complete'; validation_notes=$ComponentEvidence }
Patch-AtRecord $Tables['DCOIR Cleanup WBS'] 'recrTT6Z0JwQnu9fl' @{ state='active'; validation_notes="Activated by $RunId after WBS04-02 completion. Next: define canonical slug sources." }
Patch-AtRecord $Tables['Plans'] 'recoLHyurY4OZx3K8' @{ active_task_id='CLEANUP-WBS-04'; active_task_title='Calculated ID and Dedupe Signature Design'; active_plan_task_id='CLEANUP-WBS-04-03'; exact_resume_goal='Resume at CLEANUP-WBS-04-03 in WBS order.'; next_recommended_action='Continue with CLEANUP-WBS-04-03: Define canonical slug sources.'; last_updated_text=$NowUtc; plan_state='active' }
Patch-AtRecord $Tables['Queue Control'] 'recW8cAlClYFEVhjF' @{ branch_summary='Active branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE / CLEANUP-WBS-04.'; branch_decision='WBS04-01 evidence repaired; WBS04-02 complete; WBS04-03 active.'; resume_rule='Resume cleanup plan at CLEANUP-WBS-04-03 unless live Airtable state changes.'; next_revalidation_trigger='After WBS04-03 canonical slug source design is complete.'; last_confirmed_text=$NowUtc; notes='Continue working without status-only stops unless operator input is required or a deliverable/blocker exists.' }
Upsert-AtRecord $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-04-01-ID-INVENTORY-20260505' @{ evidence_key='EVID-CLEANUP-WBS-04-01-ID-INVENTORY-20260505'; validation_case_key='CLEANUP-WBS-04-01'; work_item_key='CLEANUP-WBS-04-01'; evidence_summary=$InventoryEvidence; source_locator=$RunId }
Upsert-AtRecord $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-04-02-ID-COMPONENTS-20260505' @{ evidence_key='EVID-CLEANUP-WBS-04-02-ID-COMPONENTS-20260505'; validation_case_key='CLEANUP-WBS-04-02'; work_item_key='CLEANUP-WBS-04-02'; evidence_summary=$ComponentEvidence; source_locator=$RunId }
Upsert-AtRecord $Tables['Operator Preferences'] 'preference_key' 'PREF-DCOIR-CONTINUOUS-PLAN-WORK-NO-STATUS-STOPS' @{ preference_key='PREF-DCOIR-CONTINUOUS-PLAN-WORK-NO-STATUS-STOPS'; preference_statement='During an active authorized DCOIR plan, continue working instead of stopping for status-only updates.'; effective_behavior='Do not pause only to report intermediate status. Continue until operator input is required, a blocker is reached, or a substantive deliverable/result is ready.'; source_session_id='DCOIR-AIRTABLE-CLEANUP-EXECUTION-20260505'; last_confirmed_text=$NowUtc; notes='Captured from operator correction. Does not override safety, source-authority, dependency, or validation stop gates.'; status='active'; scope='workflow' }
Upsert-AtRecord $Tables['Operator Preferences'] 'preference_key' 'PREF-DCOIR-CHATGPT-EXEC-FIRST-FOR-BULK-WORK' @{ preference_key='PREF-DCOIR-CHATGPT-EXEC-FIRST-FOR-BULK-WORK'; preference_statement='Prefer chatgpt-exec/chatgpt staging/GitHub-hosted tools for bulk Airtable and GitHub work; connectors are fallback for simple one-off actions.'; effective_behavior='Stage, monitor, repair, and validate chatgpt-exec work without asking the operator to manually trigger the workflow.'; source_session_id='DCOIR-AIRTABLE-CLEANUP-EXECUTION-20260505'; last_confirmed_text=$NowUtc; notes='Execution-lane preference; do not expose secrets or skip readback gates.'; status='active'; scope='workflow' }
Write-Host "[$RunId] success: WBS04-02 complete; WBS04-03 active."
