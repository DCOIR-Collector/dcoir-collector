$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RunId = 'exec-20260505-wbs-evidence-repair-001'
$NowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (Get-Location).Path }
$DownloadsDir = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($DownloadsDir)) { $DownloadsDir = Join-Path $RepoRoot 'chatgpt_staging/tmp_exec_outputs' }
$OutDir = Join-Path $DownloadsDir $RunId
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$IdJson = Join-Path $OutDir 'wbs04_02_id_components.json'
$IdMd = Join-Path $OutDir 'wbs04_02_id_components.md'
$SelectJson = Join-Path $OutDir 'wbs05_01_select_inventory.json'
$SelectMd = Join-Path $OutDir 'wbs05_01_select_inventory.md'
$AuditJson = Join-Path $OutDir 'wbs_completion_audit.json'
$AuditMd = Join-Path $OutDir 'wbs_completion_audit.md'

function Get-RequiredEnv {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if ([string]::IsNullOrWhiteSpace($value)) { $value = [Environment]::GetEnvironmentVariable($Name, 'User') }
    if ([string]::IsNullOrWhiteSpace($value)) { $value = [Environment]::GetEnvironmentVariable($Name, 'Machine') }
    if ([string]::IsNullOrWhiteSpace($value)) { throw ('Missing environment variable: {0}' -f $Name) }
    return $value
}

$BaseId = Get-RequiredEnv 'DCOIR_AIRTABLE_BASE_ID'
$Token = Get-RequiredEnv 'DCOIR_AIRTABLE_TOKEN'
$Headers = @{ Authorization = ('Bearer {0}' -f $Token); 'Content-Type' = 'application/json' }

function Invoke-Airtable {
    param([string]$Method, [string]$Uri, [object]$Body = $null)
    if ($null -eq $Body) { return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers }
    $json = $Body | ConvertTo-Json -Depth 40
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body $json
}

function Patch-AirtableRecord {
    param([string]$TableId, [string]$RecordId, [hashtable]$Fields)
    $uri = 'https://api.airtable.com/v0/{0}/{1}' -f $BaseId, $TableId
    $body = @{ records = @(@{ id = $RecordId; fields = $Fields }); typecast = $true }
    Invoke-Airtable -Method 'PATCH' -Uri $uri -Body $body | Out-Null
}

function Find-AirtableRecord {
    param([string]$TableId, [string]$FieldName, [string]$Value)
    $safe = $Value.Replace("'", "\\'")
    $formula = "{$FieldName} = '$safe'"
    $encoded = [uri]::EscapeDataString($formula)
    $uri = 'https://api.airtable.com/v0/{0}/{1}?filterByFormula={2}&maxRecords=1' -f $BaseId, $TableId, $encoded
    $result = Invoke-Airtable -Method 'GET' -Uri $uri
    if ($result.records.Count -gt 0) { return $result.records[0] }
    return $null
}

function Upsert-AirtableRecord {
    param([string]$TableId, [string]$KeyFieldName, [string]$KeyValue, [hashtable]$Fields)
    $existing = Find-AirtableRecord -TableId $TableId -FieldName $KeyFieldName -Value $KeyValue
    $uri = 'https://api.airtable.com/v0/{0}/{1}' -f $BaseId, $TableId
    if ($null -eq $existing) {
        $body = @{ records = @(@{ fields = $Fields }); typecast = $true }
        Invoke-Airtable -Method 'POST' -Uri $uri -Body $body | Out-Null
    } else {
        $body = @{ records = @(@{ id = $existing.id; fields = $Fields }); typecast = $true }
        Invoke-Airtable -Method 'PATCH' -Uri $uri -Body $body | Out-Null
    }
}

function Test-IdLikeField {
    param([string]$Name)
    if ($Name -eq 'config_name') { return $true }
    if ($Name -match '(?i)(^|[_ /-])(id|key)(s)?($|[_ /-])') { return $true }
    if ($Name -match '(?i)(signature|record[_ ]id|primary_key|source_record_id|target_record_id|parent_.*key|canonical_parent_)') { return $true }
    if ($Name -match '(?i)^(source_|target_|parent_)') { return $true }
    return $false
}

function Get-IdFieldRole {
    param([string]$Name)
    if ($Name -match '(?i)signature') { return 'dedupe_signature' }
    if ($Name -match '(?i)record[_ ]id|source_record_id|target_record_id') { return 'airtable_record_reference' }
    if ($Name -match '(?i)_entry_id$|entry id$') { return 'helper_entry_id' }
    if ($Name -match '(?i)_key$| key$|^key$|primary_key|config_name') { return 'canonical_key' }
    if ($Name -match '(?i)^source_|^target_|^parent_|^canonical_parent_') { return 'lineage_or_target' }
    if ($Name -match '(?i)_id$| id$|^id$|Item ID|Test ID') { return 'identifier' }
    return 'candidate'
}

function Get-SlugSourceNames {
    param($Table)
    $patterns = @('title','name','summary','work item','test case','locator','surface','tool','object','control','plan','checkpoint','idea','event','finding','preference','purpose')
    $selected = New-Object System.Collections.Generic.List[string]
    foreach ($pattern in $patterns) {
        foreach ($field in $Table.fields) {
            if ($selected.Count -ge 4) { break }
            if ($field.name -match ('(?i)' + [regex]::Escape($pattern))) {
                if (-not (Test-IdLikeField $field.name) -and -not $selected.Contains($field.name)) { $selected.Add($field.name) }
            }
        }
    }
    if ($selected.Count -eq 0) {
        $primary = $Table.fields | Where-Object { $_.id -eq $Table.primaryFieldId } | Select-Object -First 1
        if ($null -ne $primary) { $selected.Add($primary.name) }
    }
    return @($selected)
}

function Get-TableCode {
    param([string]$Name)
    $parts = @([regex]::Matches($Name, '[A-Za-z0-9]+') | ForEach-Object { $_.Value })
    if ($parts.Count -eq 0) { return 'TBL' }
    if ($parts.Count -eq 1) { $code = $parts[0].ToUpperInvariant() } else { $code = ($parts | ForEach-Object { $_.Substring(0,1).ToUpperInvariant() }) -join '' }
    if ($code.Length -gt 10) { return $code.Substring(0,10) }
    return $code
}

$schemaUri = 'https://api.airtable.com/v0/meta/bases/{0}/tables' -f $BaseId
$Schema = Invoke-Airtable -Method 'GET' -Uri $schemaUri
$Tables = @{}
foreach ($table in $Schema.tables) { $Tables[$table.name] = $table.id }
foreach ($required in @('DCOIR Cleanup WBS','Plans','Queue Control','Validation Evidence')) {
    if (-not $Tables.ContainsKey($required)) { throw ('Missing required table: {0}' -f $required) }
}

$idComponents = @()
$selectInventory = @()
foreach ($table in ($Schema.tables | Sort-Object name)) {
    $idFields = @()
    foreach ($field in ($table.fields | Sort-Object name)) {
        if (Test-IdLikeField $field.name) {
            $idFields += [pscustomobject]@{
                field_name = $field.name
                field_id = $field.id
                field_type = $field.type
                role = Get-IdFieldRole $field.name
                is_primary = ($field.id -eq $table.primaryFieldId)
            }
        }
        if ($field.type -in @('singleSelect','multipleSelects')) {
            $choices = @()
            if ($null -ne $field.options -and $null -ne $field.options.choices) {
                foreach ($choice in $field.options.choices) { $choices += [pscustomobject]@{ name = $choice.name; color = $choice.color } }
            }
            $selectInventory += [pscustomobject]@{
                table_name = $table.name
                table_id = $table.id
                field_name = $field.name
                field_id = $field.id
                field_type = $field.type
                choice_count = $choices.Count
                choices = $choices
            }
        }
    }
    $canonical = @($idFields | Where-Object { $_.role -in @('canonical_key','helper_entry_id') } | ForEach-Object { $_.field_name })
    $lineage = @($idFields | Where-Object { $_.role -eq 'lineage_or_target' } | ForEach-Object { $_.field_name })
    $recordRefs = @($idFields | Where-Object { $_.role -eq 'airtable_record_reference' } | ForEach-Object { $_.field_name })
    $slugSources = @(Get-SlugSourceNames $table)
    $identity = if ($canonical.Count -gt 0) { $canonical -join ', ' } elseif ($idFields.Count -gt 0) { @($idFields | Select-Object -First 3 | ForEach-Object { $_.field_name }) -join ', ' } else { 'future_' + (Get-TableCode $table.name).ToLowerInvariant() + '_key' }
    $suffix = if ($lineage.Count -gt 0) { $lineage -join ', ' } elseif ($recordRefs.Count -gt 0) { $recordRefs -join ', ' } else { 'record_id_fallback_for_collision_only' }
    $idComponents += [pscustomobject]@{
        table_name = $table.name
        table_id = $table.id
        table_code = Get-TableCode $table.name
        existing_id_fields = @($idFields | ForEach-Object { $_.field_name })
        canonical_identity_component = $identity
        slug_source_components = $slugSources
        uniqueness_suffix_component = $suffix
        dedupe_signature_component = ('hash(normalize(slug_sources) + scope(uniqueness_suffix))')
        evidence_basis = 'live Airtable metadata schema readback'
    }
}

[pscustomobject]@{ run_id = $RunId; observed_at_utc = $NowUtc; table_count = $Schema.tables.Count; table_components = $idComponents } | ConvertTo-Json -Depth 30 | Set-Content -Path $IdJson -Encoding UTF8
[pscustomobject]@{ run_id = $RunId; observed_at_utc = $NowUtc; table_count = $Schema.tables.Count; select_field_count = $selectInventory.Count; select_inventory = $selectInventory } | ConvertTo-Json -Depth 30 | Set-Content -Path $SelectJson -Encoding UTF8

$idLines = New-Object System.Collections.Generic.List[string]
$idLines.Add('# WBS04-02 ID component repair evidence')
$idLines.Add('')
$idLines.Add(('Run: {0}' -f $RunId))
$idLines.Add(('Observed UTC: {0}' -f $NowUtc))
$idLines.Add(('Tables covered: {0}' -f $idComponents.Count))
$idLines.Add('')
foreach ($row in $idComponents) {
    $idLines.Add(('## {0}' -f $row.table_name))
    $idLines.Add(('table_code: {0}' -f $row.table_code))
    $idLines.Add(('canonical_identity_component: {0}' -f $row.canonical_identity_component))
    $idLines.Add(('slug_source_components: {0}' -f (($row.slug_source_components) -join ', ')))
    $idLines.Add(('uniqueness_suffix_component: {0}' -f $row.uniqueness_suffix_component))
    $idLines.Add(('existing_id_fields: {0}' -f (($row.existing_id_fields) -join ', ')))
    $idLines.Add('')
}
$idLines | Set-Content -Path $IdMd -Encoding UTF8

$selectLines = New-Object System.Collections.Generic.List[string]
$selectLines.Add('# WBS05-01 select field inventory repair evidence')
$selectLines.Add('')
$selectLines.Add(('Run: {0}' -f $RunId))
$selectLines.Add(('Observed UTC: {0}' -f $NowUtc))
$selectLines.Add(('Select or multi-select fields covered: {0}' -f $selectInventory.Count))
$selectLines.Add('')
foreach ($group in ($selectInventory | Group-Object table_name | Sort-Object Name)) {
    $selectLines.Add(('## {0}' -f $group.Name))
    foreach ($row in ($group.Group | Sort-Object field_name)) {
        $choiceText = ($row.choices | ForEach-Object { $_.name }) -join ', '
        $selectLines.Add(('- {0} [{1}] choices={2}: {3}' -f $row.field_name, $row.field_type, $row.choice_count, $choiceText))
    }
    $selectLines.Add('')
}
$selectLines | Set-Content -Path $SelectMd -Encoding UTF8

$auditRows = @(
    [pscustomobject]@{ wbs_key = 'CLEANUP-WBS-04-02'; verdict = 'repaired_pass'; evidence = 'fresh live schema artifact generated in this run' },
    [pscustomobject]@{ wbs_key = 'CLEANUP-WBS-05-01'; verdict = 'repaired_pass'; evidence = 'fresh live schema select inventory artifact generated in this run' },
    [pscustomobject]@{ wbs_key = 'CLEANUP-WBS-05-02..05-06'; verdict = 'bounded_pass'; evidence = 'planning definitions present in WBS validation notes; no schema mutation claimed' },
    [pscustomobject]@{ wbs_key = 'CLEANUP-WBS-06'; verdict = 'bounded_pass'; evidence = 'classification model definitions present in WBS validation notes; no cleanup execution claimed' },
    [pscustomobject]@{ wbs_key = 'CLEANUP-WBS-07'; verdict = 'bounded_pass'; evidence = 'cross-surface mapping model definitions present in WBS validation notes; no source changes claimed' },
    [pscustomobject]@{ wbs_key = 'CLEANUP-WBS-08'; verdict = 'active_not_complete'; evidence = 'only activation happened; child tasks still must be completed with evidence' }
)
[pscustomobject]@{ run_id = $RunId; observed_at_utc = $NowUtc; audit = $auditRows } | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditJson -Encoding UTF8
$auditLines = @('# WBS completion evidence audit', '', ('Run: {0}' -f $RunId), '', 'This audit was generated after the operator required double-checking that tasks are actually done before state=complete.', '')
foreach ($row in $auditRows) { $auditLines += ('- {0}: {1} - {2}' -f $row.wbs_key, $row.verdict, $row.evidence) }
$auditLines | Set-Content -Path $AuditMd -Encoding UTF8

$Evidence04_02 = 'Repaired by ' + $RunId + '. WBS04-02 now has live-schema-derived ID component evidence for ' + $idComponents.Count + ' tables. Artifact files: wbs04_02_id_components.json and wbs04_02_id_components.md.'
$Evidence05_01 = 'Repaired by ' + $RunId + '. WBS05-01 now has live-schema-derived select inventory evidence for ' + $selectInventory.Count + ' select or multi-select fields. Artifact files: wbs05_01_select_inventory.json and wbs05_01_select_inventory.md.'
$AuditSummary = 'Task-completion evidence audit completed by ' + $RunId + '. WBS04-02 and WBS05-01 repaired with live-schema artifacts; WBS05-02..WBS07 remain bounded planning/model definitions; WBS08 remains active and not complete.'

Patch-AirtableRecord $Tables['DCOIR Cleanup WBS'] 'recrFmt9ic8RFtuLC' @{ state = 'complete'; validation_notes = $Evidence04_02 }
Patch-AirtableRecord $Tables['DCOIR Cleanup WBS'] 'recaq7c5Qa6K00ehv' @{ state = 'complete'; validation_notes = $Evidence05_01 }
Patch-AirtableRecord $Tables['DCOIR Cleanup WBS'] 'rec5MVBrpxAofQx3c' @{ state = 'active'; validation_notes = 'Active, not complete. WBS08 enforcement assurance must be worked with concrete rule-to-control evidence before closeout.' }
Patch-AirtableRecord $Tables['DCOIR Cleanup WBS'] 'recTOncI4tCFvfmdO' @{ state = 'active'; validation_notes = 'Active, not complete. Must list enforcement rules with intended outcomes before WBS08-01 closeout.' }
Patch-AirtableRecord $Tables['Plans'] 'recoLHyurY4OZx3K8' @{ active_task_id = 'CLEANUP-WBS-08'; active_task_title = 'Enforcement Assurance Model'; active_plan_task_id = 'CLEANUP-WBS-08-01'; exact_resume_goal = 'Resume at CLEANUP-WBS-08-01. Earlier over-advanced rows have been audited; WBS08 remains active and must not be closed without evidence.'; next_recommended_action = 'Complete WBS08-01 by listing enforcement rules and accountable evidence for each rule.'; last_updated_text = $NowUtc; plan_state = 'active' }
Patch-AirtableRecord $Tables['Queue Control'] 'recW8cAlClYFEVhjF' @{ branch_summary = 'Active branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE / CLEANUP-WBS-08 Enforcement Assurance Model.'; branch_decision = 'Completion audit repaired evidence gaps for WBS04-02 and WBS05-01. Continue from WBS08-01 with double-check gate before completion.'; resume_rule = 'Resume cleanup plan at CLEANUP-WBS-08-01 unless live Airtable state changes.'; next_revalidation_trigger = 'Before any WBS08 child is marked complete.'; last_confirmed_text = $NowUtc }

Upsert-AirtableRecord $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-04-02-ID-COMPONENTS-REPAIR-20260505' @{ evidence_key = 'EVID-CLEANUP-WBS-04-02-ID-COMPONENTS-REPAIR-20260505'; validation_case_key = 'CLEANUP-WBS-04-02'; work_item_key = 'CLEANUP-WBS-04-02'; evidence_summary = $Evidence04_02; source_locator = $RunId; result = 'pass' }
Upsert-AirtableRecord $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-05-01-SELECT-INVENTORY-REPAIR-20260505' @{ evidence_key = 'EVID-CLEANUP-WBS-05-01-SELECT-INVENTORY-REPAIR-20260505'; validation_case_key = 'CLEANUP-WBS-05-01'; work_item_key = 'CLEANUP-WBS-05-01'; evidence_summary = $Evidence05_01; source_locator = $RunId; result = 'pass' }
Upsert-AirtableRecord $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-COMPLETION-AUDIT-20260505' @{ evidence_key = 'EVID-CLEANUP-WBS-COMPLETION-AUDIT-20260505'; validation_case_key = 'PLAN-AIRTABLE-CLEANUP-RESTRUCTURE'; work_item_key = 'CLEANUP-WBS-AUDIT'; evidence_summary = $AuditSummary; source_locator = $RunId; result = 'pass' }

Write-Host ('[{0}] success: repaired WBS04-02 and WBS05-01 evidence; audit complete; WBS08 remains active.' -f $RunId)
