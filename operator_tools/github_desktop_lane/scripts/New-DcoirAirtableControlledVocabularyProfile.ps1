[CmdletBinding()]
param(
    [string]$OutputNamePrefix = 'dcoir_airtable_controlled_vocabulary_profile',
    [switch]$IncludeDeleteQueue,
    [int]$MaxCandidateUniqueValues = 30,
    [double]$MaxCandidateUniqueRatio = 0.40
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$toolVersion = '2026-05-08.1'

function Get-DcoirEnvValue {
    param([Parameter(Mandatory=$true)][string]$Name, [switch]$Required)
    $value = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    if ([string]::IsNullOrWhiteSpace($value)) { $value = [Environment]::GetEnvironmentVariable($Name, 'Process') }
    if ($Required -and [string]::IsNullOrWhiteSpace($value)) { throw "Required environment variable is not set: $Name" }
    return $value
}

$repo = Get-DcoirEnvValue -Name 'DCOIR_REPO_ROOT' -Required
$outRoot = Get-DcoirEnvValue -Name 'DCOIR_DOWNLOADS_DIR' -Required
$modulePath = Join-Path $repo 'operator_tools\github_desktop_lane\modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
if (Test-Path -LiteralPath $modulePath -PathType Leaf) { Import-Module $modulePath -Force }

function Get-DcoirAirtableSecretValue {
    param([Parameter(Mandatory=$true)][string]$Name)
    if (Get-Command -Name Get-DcoirAirtableSystemEnvValue -ErrorAction SilentlyContinue) {
        return Get-DcoirAirtableSystemEnvValue -Name $Name -Required
    }
    return Get-DcoirEnvValue -Name $Name -Required
}

$baseId = Get-DcoirAirtableSecretValue -Name 'DCOIR_AIRTABLE_BASE_ID'
$token = Get-DcoirAirtableSecretValue -Name 'DCOIR_AIRTABLE_TOKEN'
$headers = @{ Authorization = 'Bearer ' + $token; 'Content-Type' = 'application/json' }

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$runRoot = Join-Path $outRoot ($OutputNamePrefix + '_' + $timestamp)
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null

function Write-JsonFile {
    param([Parameter(Mandatory=$true)]$Object, [Parameter(Mandatory=$true)][string]$Path, [int]$Depth = 80)
    $Object | ConvertTo-Json -Depth $Depth | Out-File -LiteralPath $Path -Encoding utf8
}

function Normalize-DcoirToken {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    $v = $Value.Trim().ToLowerInvariant()
    $v = $v -replace '[\s\-\/]+', '_'
    $v = $v -replace '[^a-z0-9_]+', ''
    $v = $v -replace '_+', '_'
    $v = $v.Trim('_')
    $aliases = @{
        'passed' = 'pass'
        'passing' = 'pass'
        'failed' = 'fail'
        'failure' = 'fail'
        'pre_execution' = 'pre_execution'
        'preexecution' = 'pre_execution'
        'post_execution' = 'post_execution'
        'postexecution' = 'post_execution'
        'post_blocker' = 'post_blocker'
        'postblocker' = 'post_blocker'
        'airtable_first' = 'airtable_first'
        'airtablefirst' = 'airtable_first'
    }
    if ($aliases.ContainsKey($v)) { return $aliases[$v] }
    return $v
}

function Get-DcoirFamilyName {
    param([Parameter(Mandatory=$true)][string]$FieldName)
    $n = Normalize-DcoirToken $FieldName
    if ($n -match '(^|_)retention_class$') { return 'retention_class' }
    if ($n -match '(^|_)(status|state|observed_status|checkpoint_status|authority_status|migration_status|github_promotion_status|plan_state)$') { return 'status_state' }
    if ($n -match '(^|_)(area|related_area)$') { return 'area' }
    if ($n -match '(^|_)(scope|authority_scope|validation_scope)$') { return 'scope' }
    if ($n -match '(^|_)(type|work_type|surface_type|object_type|scaffold_type|tool_family|task_family|decision_family)$') { return 'type_family' }
    if ($n -match '(^|_)(stage|delete_stage|lifecycle_stage|gate)$') { return 'stage_gate' }
    if ($n -match '(^|_)(result|curation_decision|observed_status)$') { return 'result_decision' }
    if ($n -match '(^|_)(priority|queue_rank)$') { return 'priority_rank' }
    if ($n -match '(^|_)(topic|surface_layers|dcoir_gemini_lanes|execution_lane|lane)$') { return 'topic_lane_layer' }
    if ($n -match '(^|_)(active)$') { return 'active_flag' }
    return $n
}

function Get-FieldValue {
    param([AllowNull()]$Fields, [Parameter(Mandatory=$true)][string]$FieldId)
    if ($null -eq $Fields) { return $null }
    $prop = $Fields.PSObject.Properties[$FieldId]
    if ($null -eq $prop) { return $null }
    return $prop.Value
}

function Convert-ValueList {
    param([AllowNull()]$Value)
    if ($null -eq $Value) { return @() }
    if ($Value -is [System.Array]) {
        $items = New-Object System.Collections.Generic.List[string]
        foreach ($item in $Value) {
            if ($null -ne $item -and -not [string]::IsNullOrWhiteSpace([string]$item)) { $items.Add([string]$item) | Out-Null }
        }
        return @($items.ToArray())
    }
    $s = [string]$Value
    if ([string]::IsNullOrWhiteSpace($s)) { return @() }
    return @($s)
}

function Get-RecordsForTable {
    param([Parameter(Mandatory=$true)][string]$TableId)
    $records = New-Object System.Collections.Generic.List[object]
    $offset = $null
    do {
        $uri = 'https://api.airtable.com/v0/' + $baseId + '/' + $TableId + '?pageSize=100&returnFieldsByFieldId=true'
        if (-not [string]::IsNullOrWhiteSpace($offset)) { $uri += '&offset=' + [System.Uri]::EscapeDataString($offset) }
        $result = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers -ErrorAction Stop
        foreach ($record in @($result.records)) { $records.Add($record) | Out-Null }
        $offset = $null
        if ($null -ne $result.PSObject.Properties['offset']) { $offset = [string]$result.offset }
    } while (-not [string]::IsNullOrWhiteSpace($offset))
    return @($records.ToArray())
}

function Get-SelectChoices {
    param($Field)
    $choices = New-Object System.Collections.Generic.List[object]
    $optionsProp = $Field.PSObject.Properties['options']
    if ($null -ne $optionsProp -and $null -ne $optionsProp.Value) {
        $choiceProp = $optionsProp.Value.PSObject.Properties['choices']
        if ($null -ne $choiceProp -and $null -ne $choiceProp.Value) {
            foreach ($choice in @($choiceProp.Value)) {
                $choices.Add([ordered]@{
                    id = if ($choice.PSObject.Properties['id']) { [string]$choice.id } else { $null }
                    name = if ($choice.PSObject.Properties['name']) { [string]$choice.name } else { $null }
                    color = if ($choice.PSObject.Properties['color']) { [string]$choice.color } else { $null }
                }) | Out-Null
            }
        }
    }
    return @($choices.ToArray())
}

function Is-ExcludedTextFieldName {
    param([Parameter(Mandatory=$true)][string]$FieldName)
    $n = Normalize-DcoirToken $FieldName
    if ($n -match '(^|_)(id|key|hash|url|uri|path|locator|repo_path|source_locator|record_id|source_record_id)$') { return $true }
    if ($n -match '(notes|evidence|rationale|reason|summary|detail|description|payload|json|command|script|formula|context|criteria|impact|basis|content|message|body)') { return $true }
    if ($n -match '(^|_)(created|updated|review_after|last_reviewed|confirmed|timestamp|date|time|at)$') { return $true }
    if ($n -match '(created_at|updated_at|requested_at|verified_at|checkpoint_at|captured_at|event_at|last_confirmed|last_updated)') { return $true }
    return $false
}

function Get-PlaceholderReason {
    param([Parameter(Mandatory=$true)][string]$OptionName, [Parameter(Mandatory=$true)][string]$FieldName)
    $o = Normalize-DcoirToken $OptionName
    $f = Normalize-DcoirToken $FieldName
    $bad = @('status','trigger','checkpoint_status','authority_status','historical_source_basis','field','value','option','unknown_placeholder')
    if ($o -eq $f) { return 'option_equals_field_name' }
    if ($bad -contains $o) { return 'known_placeholder_or_field_name_option' }
    if ($o -match '^sel[a-z0-9_]+$') { return 'generated_looking_option_name' }
    return $null
}

try {
    $schemaUri = 'https://api.airtable.com/v0/meta/bases/' + $baseId + '/tables'
    $schema = Invoke-RestMethod -Uri $schemaUri -Method GET -Headers $headers -ErrorAction Stop

    $allTables = @($schema.tables)
    $selectedTables = @($allTables | Where-Object { $IncludeDeleteQueue -or ([string]$_.name -ne 'Delete Queue') })
    $skippedTables = @($allTables | Where-Object { -not $IncludeDeleteQueue -and ([string]$_.name -eq 'Delete Queue') } | ForEach-Object { [ordered]@{ id = [string]$_.id; name = [string]$_.name; reason = 'excluded_by_default_preserve_delete_queue_semantics' } })

    $recordsByTable = @{}
    foreach ($table in $selectedTables) {
        $recordsByTable[[string]$table.id] = @(Get-RecordsForTable -TableId ([string]$table.id))
    }

    $selectInventory = New-Object System.Collections.Generic.List[object]
    $textProfiles = New-Object System.Collections.Generic.List[object]
    $textCandidates = New-Object System.Collections.Generic.List[object]
    $excludedText = New-Object System.Collections.Generic.List[object]
    $families = @{}
    $optionDriftGroups = @{}
    $optionIssues = New-Object System.Collections.Generic.List[object]
    $canonicalOptionsByFamily = @{}

    foreach ($table in $selectedTables) {
        $tableId = [string]$table.id
        $tableName = [string]$table.name
        $records = @($recordsByTable[$tableId])
        foreach ($field in @($table.fields)) {
            $fieldId = [string]$field.id
            $fieldName = [string]$field.name
            $fieldType = [string]$field.type
            $family = Get-DcoirFamilyName -FieldName $fieldName
            if (-not $families.ContainsKey($family)) { $families[$family] = New-Object System.Collections.Generic.List[object] }
            $families[$family].Add([ordered]@{ table_id=$tableId; table_name=$tableName; field_id=$fieldId; field_name=$fieldName; field_type=$fieldType }) | Out-Null

            if ($fieldType -eq 'singleSelect' -or $fieldType -eq 'multipleSelects') {
                $choices = @(Get-SelectChoices -Field $field)
                $counts = @{}
                foreach ($record in $records) {
                    $value = Get-FieldValue -Fields $record.fields -FieldId $fieldId
                    foreach ($item in @(Convert-ValueList -Value $value)) {
                        if (-not $counts.ContainsKey($item)) { $counts[$item] = 0 }
                        $counts[$item]++
                    }
                }
                $choiceProfiles = New-Object System.Collections.Generic.List[object]
                foreach ($choice in $choices) {
                    $name = [string]$choice.name
                    $normalized = Normalize-DcoirToken $name
                    $count = if ($counts.ContainsKey($name)) { [int]$counts[$name] } else { 0 }
                    $placeholderReason = Get-PlaceholderReason -OptionName $name -FieldName $fieldName
                    if ($null -ne $placeholderReason) {
                        $optionIssues.Add([ordered]@{ issue_type=$placeholderReason; table_name=$tableName; field_name=$fieldName; field_type=$fieldType; option_name=$name; observed_count=$count; recommendation='review_or_retire_after_value_migration_if_used' }) | Out-Null
                    }
                    $choiceProfiles.Add([ordered]@{ option_id=$choice.id; name=$name; normalized=$normalized; color=$choice.color; observed_count=$count }) | Out-Null
                    $driftKey = $family + '::' + $normalized
                    if (-not $optionDriftGroups.ContainsKey($driftKey)) { $optionDriftGroups[$driftKey] = New-Object System.Collections.Generic.List[object] }
                    $optionDriftGroups[$driftKey].Add([ordered]@{ table_name=$tableName; field_name=$fieldName; option_name=$name; observed_count=$count }) | Out-Null
                    if (-not $canonicalOptionsByFamily.ContainsKey($family)) { $canonicalOptionsByFamily[$family] = @{} }
                    if (-not $canonicalOptionsByFamily[$family].ContainsKey($normalized)) { $canonicalOptionsByFamily[$family][$normalized] = 0 }
                    $canonicalOptionsByFamily[$family][$normalized] += $count
                }
                $blankCount = 0
                foreach ($record in $records) {
                    $value = Get-FieldValue -Fields $record.fields -FieldId $fieldId
                    if (@(Convert-ValueList -Value $value).Count -eq 0) { $blankCount++ }
                }
                $selectInventory.Add([ordered]@{ table_id=$tableId; table_name=$tableName; field_id=$fieldId; field_name=$fieldName; field_type=$fieldType; family=$family; record_count=$records.Count; blank_count=$blankCount; option_count=$choices.Count; options=@($choiceProfiles.ToArray()) }) | Out-Null
            }

            if ($fieldType -eq 'singleLineText' -or $fieldType -eq 'multilineText') {
                $valueCounts = @{}
                $blankCount = 0
                $maxLen = 0
                $totalLen = 0
                $nonBlank = 0
                foreach ($record in $records) {
                    $value = Get-FieldValue -Fields $record.fields -FieldId $fieldId
                    if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) { $blankCount++; continue }
                    $s = ([string]$value).Trim()
                    $nonBlank++
                    $totalLen += $s.Length
                    if ($s.Length -gt $maxLen) { $maxLen = $s.Length }
                    if (-not $valueCounts.ContainsKey($s)) { $valueCounts[$s] = 0 }
                    $valueCounts[$s]++
                }
                $uniqueCount = $valueCounts.Keys.Count
                $uniqueRatio = if ($nonBlank -gt 0) { [math]::Round($uniqueCount / [double]$nonBlank, 4) } else { 0 }
                $avgLen = if ($nonBlank -gt 0) { [math]::Round($totalLen / [double]$nonBlank, 2) } else { 0 }
                $excludedByName = Is-ExcludedTextFieldName -FieldName $fieldName
                $hasCategoricalName = ((Normalize-DcoirToken $fieldName) -match '(status|state|type|class|scope|area|priority|family|topic|stage|lane|result|decision|surface|role|kind|category)')
                $bounded = ($nonBlank -ge 3 -and $uniqueCount -ge 2 -and $uniqueCount -le $MaxCandidateUniqueValues -and $uniqueRatio -le $MaxCandidateUniqueRatio -and $maxLen -le 100)
                $candidate = (-not $excludedByName -and ($bounded -or ($hasCategoricalName -and $uniqueCount -le $MaxCandidateUniqueValues -and $maxLen -le 120)))
                $values = @($valueCounts.GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object { [ordered]@{ value=[string]$_.Key; normalized=(Normalize-DcoirToken ([string]$_.Key)); count=[int]$_.Value } })
                $profile = [ordered]@{ table_id=$tableId; table_name=$tableName; field_id=$fieldId; field_name=$fieldName; field_type=$fieldType; family=$family; record_count=$records.Count; nonblank_count=$nonBlank; blank_count=$blankCount; unique_count=$uniqueCount; unique_ratio=$uniqueRatio; average_length=$avgLen; max_length=$maxLen; top_values=@($values | Select-Object -First 50) }
                $textProfiles.Add($profile) | Out-Null
                if ($candidate) {
                    $recommendType = if ($fieldName -match 'layers|lanes|tags|areas|scopes|types|categories') { 'multipleSelects_candidate' } else { 'singleSelect_candidate' }
                    $textCandidates.Add([ordered]@{ table_id=$tableId; table_name=$tableName; field_id=$fieldId; field_name=$fieldName; field_type=$fieldType; family=$family; recommendation=$recommendType; inclusion_reason='bounded_reusable_vocabulary_or_categorical_field_name'; record_count=$records.Count; nonblank_count=$nonBlank; blank_count=$blankCount; unique_count=$uniqueCount; unique_ratio=$uniqueRatio; max_length=$maxLen; proposed_options=@($values | Select-Object -First $MaxCandidateUniqueValues) }) | Out-Null
                    if (-not $canonicalOptionsByFamily.ContainsKey($family)) { $canonicalOptionsByFamily[$family] = @{} }
                    foreach ($v in $values) {
                        $norm = [string]$v.normalized
                        if (-not [string]::IsNullOrWhiteSpace($norm)) {
                            if (-not $canonicalOptionsByFamily[$family].ContainsKey($norm)) { $canonicalOptionsByFamily[$family][$norm] = 0 }
                            $canonicalOptionsByFamily[$family][$norm] += [int]$v.count
                        }
                    }
                } else {
                    $reason = if ($excludedByName) { 'excluded_by_name_or_semantic_role' } elseif ($nonBlank -lt 3) { 'too_few_nonblank_values' } elseif ($uniqueCount -gt $MaxCandidateUniqueValues) { 'too_many_unique_values' } elseif ($uniqueRatio -gt $MaxCandidateUniqueRatio) { 'unique_ratio_too_high' } elseif ($maxLen -gt 100) { 'values_too_long_for_select_options' } else { 'not_bounded_or_not_filter_value' }
                    $excludedText.Add([ordered]@{ table_id=$tableId; table_name=$tableName; field_id=$fieldId; field_name=$fieldName; field_type=$fieldType; family=$family; exclusion_reason=$reason; record_count=$records.Count; nonblank_count=$nonBlank; blank_count=$blankCount; unique_count=$uniqueCount; unique_ratio=$uniqueRatio; max_length=$maxLen }) | Out-Null
                }
            }
        }
    }

    $familyReport = New-Object System.Collections.Generic.List[object]
    foreach ($familyKey in ($families.Keys | Sort-Object)) {
        $members = @($families[$familyKey].ToArray())
        $tables = @($members | ForEach-Object { $_.table_name } | Sort-Object -Unique)
        if ($members.Count -gt 1 -or $familyKey -match 'status_state|retention_class|area|scope|type_family|stage_gate|result_decision|topic_lane_layer') {
            $familyReport.Add([ordered]@{ family=$familyKey; field_count=$members.Count; table_count=$tables.Count; tables=$tables; fields=$members }) | Out-Null
        }
    }

    $driftReport = New-Object System.Collections.Generic.List[object]
    foreach ($key in ($optionDriftGroups.Keys | Sort-Object)) {
        $items = @($optionDriftGroups[$key].ToArray())
        $rawNames = @($items | ForEach-Object { $_.option_name } | Sort-Object -Unique)
        if ($rawNames.Count -gt 1) {
            $parts = $key -split '::', 2
            $driftReport.Add([ordered]@{ family=$parts[0]; normalized_option=$parts[1]; raw_option_names=$rawNames; occurrences=$items; issue_type='same_normalized_option_multiple_spellings'; recommendation='standardize_to_canonical_option_after_approval' }) | Out-Null
        }
    }
    foreach ($issue in @($optionIssues.ToArray())) { $driftReport.Add($issue) | Out-Null }

    $canonicalSets = New-Object System.Collections.Generic.List[object]
    foreach ($familyKey in ($canonicalOptionsByFamily.Keys | Sort-Object)) {
        $opts = @($canonicalOptionsByFamily[$familyKey].GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object { [ordered]@{ option=[string]$_.Key; observed_count=[int]$_.Value } })
        if ($opts.Count -gt 0) { $canonicalSets.Add([ordered]@{ family=$familyKey; proposed_options=$opts; source='existing_selects_and_text_candidates'; review_required=$true }) | Out-Null }
    }

    $inventory = [ordered]@{
        tool = 'New-DcoirAirtableControlledVocabularyProfile.ps1'
        tool_version = $toolVersion
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        base_id = $baseId
        include_delete_queue = [bool]$IncludeDeleteQueue
        selected_table_count = $selectedTables.Count
        skipped_tables = $skippedTables
        total_records_profiled = [int](@($recordsByTable.Values | ForEach-Object { @($_).Count } | Measure-Object -Sum).Sum)
        select_field_count = $selectInventory.Count
        text_field_profile_count = $textProfiles.Count
        text_to_select_candidate_count = $textCandidates.Count
        excluded_text_field_count = $excludedText.Count
    }

    $targetRecords = [ordered]@{ read_only = $true; target = 'controlled_vocabulary_inventory'; plan_key = 'PLAN-AIRTABLE-DB-REDESIGN-20260508'; wbs_scope = '02.01-02.05'; selected_tables = @($selectedTables | ForEach-Object { [ordered]@{ id=[string]$_.id; name=[string]$_.name } }); skipped_tables = $skippedTables }
    $plannedPayload = [ordered]@{ read_only = $true; mutation_planned = $false; next_payload_type = 'approval_packet_after_operator_review'; note = 'No Airtable schema/data changes are proposed by this profiling run.' }
    $verification = [ordered]@{ result='pass'; read_only = $true; schema_tables_read = $allTables.Count; tables_profiled = $selectedTables.Count; delete_queue_excluded = (-not [bool]$IncludeDeleteQueue); artifacts_created = @('target_records.json','planned_payload.json','execution_summary.json','after_readback_verification.json','controlled_vocabulary_inventory.json','select_field_inventory.json','text_field_profiles.json','text_to_select_candidates.json','excluded_text_fields.json','common_field_families.json','option_drift_report.json','canonical_option_sets_proposed.json') }

    Write-JsonFile -Object $targetRecords -Path (Join-Path $runRoot 'target_records.json')
    Write-JsonFile -Object $plannedPayload -Path (Join-Path $runRoot 'planned_payload.json')
    Write-JsonFile -Object $inventory -Path (Join-Path $runRoot 'execution_summary.json')
    Write-JsonFile -Object $verification -Path (Join-Path $runRoot 'after_readback_verification.json')
    Write-JsonFile -Object $inventory -Path (Join-Path $runRoot 'controlled_vocabulary_inventory.json')
    Write-JsonFile -Object @($selectInventory.ToArray()) -Path (Join-Path $runRoot 'select_field_inventory.json')
    Write-JsonFile -Object @($textProfiles.ToArray()) -Path (Join-Path $runRoot 'text_field_profiles.json')
    Write-JsonFile -Object @($textCandidates.ToArray()) -Path (Join-Path $runRoot 'text_to_select_candidates.json')
    Write-JsonFile -Object @($excludedText.ToArray()) -Path (Join-Path $runRoot 'excluded_text_fields.json')
    Write-JsonFile -Object @($familyReport.ToArray()) -Path (Join-Path $runRoot 'common_field_families.json')
    Write-JsonFile -Object @($driftReport.ToArray()) -Path (Join-Path $runRoot 'option_drift_report.json')
    Write-JsonFile -Object @($canonicalSets.ToArray()) -Path (Join-Path $runRoot 'canonical_option_sets_proposed.json')

    [ordered]@{
        result = 'success'
        output_dir = $runRoot
        selected_table_count = $selectedTables.Count
        skipped_table_count = $skippedTables.Count
        select_field_count = $selectInventory.Count
        text_to_select_candidate_count = $textCandidates.Count
        option_drift_issue_count = $driftReport.Count
    } | ConvertTo-Json -Depth 20
}
catch {
    $errorObject = [ordered]@{
        result = 'failed'
        error_message = $_.Exception.Message
        error_type = $_.Exception.GetType().FullName
        script_stack_trace = $_.ScriptStackTrace
        output_dir = $runRoot
    }
    Write-JsonFile -Object $errorObject -Path (Join-Path $runRoot 'error_report.json') -Depth 20
    throw
}
