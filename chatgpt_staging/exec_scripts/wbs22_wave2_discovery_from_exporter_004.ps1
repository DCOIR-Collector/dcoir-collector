$ErrorActionPreference = 'Stop'

$repoRoot = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT', 'Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR', 'Machine')
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw 'Missing DCOIR_REPO_ROOT' }
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing DCOIR_DOWNLOADS_DIR' }

$exportTool = Join-Path $repoRoot 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
if (-not (Test-Path -LiteralPath $exportTool -PathType Leaf)) { throw "Missing Airtable export tool: $exportTool" }

$prefix = 'wbs22_wave2_discovery_004'
Write-Host "Running existing Airtable exporter: $exportTool"
& $exportTool -ExportMode FullRecords -MetadataScope 'All' -ProbeUnsupportedMetadata -RedactLikelySecrets -OutputNamePrefix $prefix -NoZip | Out-Host

$exportFolder = Get-ChildItem -LiteralPath $downloads -Directory -Filter "$prefix*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $exportFolder) { throw "No exporter output folder found for prefix $prefix under $downloads" }
Write-Host "Exporter output folder: $($exportFolder.FullName)"

$manifestPath = Join-Path $exportFolder.FullName 'export_manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Missing export manifest: $manifestPath" }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

$outDir = Join-Path $downloads 'wbs22_wave2_discovery_from_exporter_004'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function ConvertTo-SafeArray($value) {
    if ($null -eq $value) { return @() }
    if ($value -is [System.Array]) { return @($value) }
    return @($value)
}

function Get-FieldValue {
    param($Record, [string]$Name)
    if ($null -eq $Record -or $null -eq $Record.fields) { return $null }
    $prop = $Record.fields.PSObject.Properties[$Name]
    if ($prop) { return $prop.Value }
    return $null
}

function Has-FieldName {
    param($TableExport, [string[]]$Names)
    $schemaFile = Join-Path $exportFolder.FullName $TableExport.schema_file
    if (-not (Test-Path -LiteralPath $schemaFile -PathType Leaf)) { return $false }
    $tableSchema = Get-Content -LiteralPath $schemaFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $fieldNames = @($tableSchema.fields | ForEach-Object { [string]$_.name })
    foreach ($n in $Names) {
        if ($fieldNames -contains $n) { return $true }
    }
    return $false
}

$tableClassifications = New-Object System.Collections.Generic.List[object]
$recordCandidateRows = New-Object System.Collections.Generic.List[object]
$accessFailures = New-Object System.Collections.Generic.List[object]
$totalRecords = 0
$totalFields = 0
$tablesWithStatus = 0
$tablesWithReviewAfter = 0
$tablesWithRetentionClass = 0
$tablesWithPointerFields = 0
$tablesWithResumePrompt = 0

foreach ($t in @($manifest.selected_tables)) {
    $tableName = [string]$t.table_name
    $schemaFile = if ($t.schema_file) { Join-Path $exportFolder.FullName ([string]$t.schema_file) } else { $null }
    $recordsFile = if ($t.records_file) { Join-Path $exportFolder.FullName ([string]$t.records_file) } else { $null }
    $tableSchema = $null
    if ($schemaFile -and (Test-Path -LiteralPath $schemaFile -PathType Leaf)) {
        $tableSchema = Get-Content -LiteralPath $schemaFile -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    $fieldNames = @()
    if ($tableSchema) { $fieldNames = @($tableSchema.fields | ForEach-Object { [string]$_.name }) }
    $totalFields += $fieldNames.Count

    $hasStatus = @('status','Status','state','State','plan_state','checkpoint_status','curation_decision','delete_stage','Observed Status','authority_status') | Where-Object { $fieldNames -contains $_ } | Select-Object -First 1
    $hasReview = $fieldNames -contains 'review_after'
    $hasRetention = $fieldNames -contains 'retention_class'
    $pointerFields = @($fieldNames | Where-Object { $_ -match '(active_|resume|pointer|checkpoint|plan_task|task_id|queue|source_|target_|locator|replacement)' })
    $hasResume = $fieldNames -contains 'resume_prompt'

    if ($hasStatus) { $tablesWithStatus++ }
    if ($hasReview) { $tablesWithReviewAfter++ }
    if ($hasRetention) { $tablesWithRetentionClass++ }
    if ($pointerFields.Count -gt 0) { $tablesWithPointerFields++ }
    if ($hasResume) { $tablesWithResumePrompt++ }

    $recordExport = $null
    $records = @()
    if ($recordsFile -and (Test-Path -LiteralPath $recordsFile -PathType Leaf)) {
        $recordExport = Get-Content -LiteralPath $recordsFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $records = @(ConvertTo-SafeArray $recordExport.records)
        $totalRecords += $records.Count
    } else {
        $accessFailures.Add([pscustomobject][ordered]@{ table_name=$tableName; table_id=[string]$t.table_id; result='missing_records_file'; records_file=[string]$t.records_file }) | Out-Null
    }

    $handling = 'read_only_reference'
    $stopReason = ''
    if ($tableName -eq 'Delete Queue') { $handling = 'read_only_stop_if_delete_queue_action'; $stopReason = 'Wave 2 must not process Delete Queue or delete records.' }
    elseif ($tableName -eq 'DCOIR Cleanup Scaffold Registry') { $handling = 'read_only_stop_if_scaffold_disposition'; $stopReason = 'Wave 2 must not do scaffold disposition.' }
    elseif ($tableName -eq 'DCOIR Cleanup WBS') { $handling = 'read_only_task_context'; $stopReason = 'Do not change WBS/task scope during Wave 2 cleanup.' }
    elseif ($hasStatus -or $hasReview -or $hasRetention -or $pointerFields.Count -gt 0 -or $hasResume) { $handling = 'wave2_candidate_status_review_retention_pointer_resume' }

    $tableClassifications.Add([pscustomobject][ordered]@{
        table_name = $tableName
        table_id = [string]$t.table_id
        handling = $handling
        stop_reason = $stopReason
        field_count = $fieldNames.Count
        record_count_exported = [int]$t.record_count_exported
        has_status_like_field = [bool]$hasStatus
        has_review_after = [bool]$hasReview
        has_retention_class = [bool]$hasRetention
        has_resume_prompt = [bool]$hasResume
        pointer_like_fields = @($pointerFields)
        records_file = [string]$t.records_file
        schema_file = [string]$t.schema_file
    }) | Out-Null

    foreach ($r in $records) {
        $primary = ''
        if ($tableSchema -and $tableSchema.primaryFieldId) {
            $primaryField = @($tableSchema.fields | Where-Object { $_.id -eq $tableSchema.primaryFieldId } | Select-Object -First 1)
            if ($primaryField) { $primary = [string](Get-FieldValue -Record $r -Name ([string]$primaryField.name)) }
        }
        $candidateReasons = New-Object System.Collections.Generic.List[string]
        if ($hasRetention) {
            $retention = Get-FieldValue -Record $r -Name 'retention_class'
            if ($null -eq $retention -or [string]::IsNullOrWhiteSpace([string]$retention)) { $candidateReasons.Add('missing_retention_class') | Out-Null }
        }
        if ($hasReview) {
            $review = Get-FieldValue -Record $r -Name 'review_after'
            if ($null -eq $review -or [string]::IsNullOrWhiteSpace([string]$review)) { $candidateReasons.Add('missing_review_after') | Out-Null }
        }
        if ($tableName -eq 'Plans') {
            $activeTask = [string](Get-FieldValue -Record $r -Name 'active_task_id')
            $activePlanTask = [string](Get-FieldValue -Record $r -Name 'active_plan_task_id')
            if ($activeTask -and $activePlanTask -and $activeTask -ne $activePlanTask) { $candidateReasons.Add("active_task_id_mismatch active_task_id=$activeTask active_plan_task_id=$activePlanTask") | Out-Null }
        }
        foreach ($pf in $pointerFields) {
            $v = Get-FieldValue -Record $r -Name $pf
            $text = if ($null -eq $v) { '' } else { ($v | ConvertTo-Json -Depth 6 -Compress) }
            if ($text -match 'CLEANUP-WBS-08-01|PLAN-TASK|Plan Tasks|Plan Checkpoints|Skill State Registry|Schema Registry|Tracking Registry') {
                $candidateReasons.Add("stale_reference_in_$pf") | Out-Null
            }
        }
        if ($candidateReasons.Count -gt 0) {
            $recordCandidateRows.Add([pscustomobject][ordered]@{
                table_name = $tableName
                table_id = [string]$t.table_id
                record_id = [string]$r.id
                primary_value = $primary
                reasons = @($candidateReasons.ToArray())
                wave2_action = 'proposal_only_no_mutation'
                stop_if_requires = 'duplicate_merge_delete_queue_record_delete_schema_change_source_skill_workflow_change_scaffold_disposition'
            }) | Out-Null
        }
    }
}

$beforeMetrics = [ordered]@{
    schema = 'dcoir.wbs22.wave2.before_metrics.v1'
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    source = 'New-DcoirAirtableDatabaseHealthExport.ps1 full-record export'
    export_folder = $exportFolder.FullName
    selected_table_count = [int]$manifest.selected_table_count
    total_field_count = $totalFields
    total_records_exported = $totalRecords
    tables_with_status_like_field = $tablesWithStatus
    tables_with_review_after = $tablesWithReviewAfter
    tables_with_retention_class = $tablesWithRetentionClass
    tables_with_pointer_like_fields = $tablesWithPointerFields
    tables_with_resume_prompt = $tablesWithResumePrompt
    candidate_record_count = $recordCandidateRows.Count
    table_access_failure_count = $accessFailures.Count
}

$reportLines = New-Object System.Collections.Generic.List[string]
$reportLines.Add('# WBS22 Wave 2 discovery from exporter') | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add("Generated UTC: $($beforeMetrics.generated_at_utc)") | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('## Scope') | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('Discovery/proposal-only. No Airtable writes, deletes, schema changes, GitHub source changes, skill changes, workflow changes, duplicate/merge work, Delete Queue processing, record deletion, scaffold disposition, or cosmetic cleanup.') | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('## Metrics') | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add("- selected_table_count: $($beforeMetrics.selected_table_count)") | Out-Null
$reportLines.Add("- total_field_count: $($beforeMetrics.total_field_count)") | Out-Null
$reportLines.Add("- total_records_exported: $($beforeMetrics.total_records_exported)") | Out-Null
$reportLines.Add("- candidate_record_count: $($beforeMetrics.candidate_record_count)") | Out-Null
$reportLines.Add("- table_access_failure_count: $($beforeMetrics.table_access_failure_count)") | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('## Candidate reasons') | Out-Null
$reportLines.Add('') | Out-Null
if ($recordCandidateRows.Count -eq 0) {
    $reportLines.Add('- none') | Out-Null
} else {
    foreach ($c in @($recordCandidateRows.ToArray() | Select-Object -First 50)) {
        $reportLines.Add(("- {0} / {1} / {2}: {3}" -f $c.table_name, $c.record_id, $c.primary_value, (($c.reasons) -join '; '))) | Out-Null
    }
    if ($recordCandidateRows.Count -gt 50) { $reportLines.Add("- truncated in markdown; see wave2_candidates.json for all $($recordCandidateRows.Count) candidates") | Out-Null }
}
$reportLines.Add('') | Out-Null
$reportLines.Add('## Next recommended move') | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('Review wave2_candidates.json and prepare an exact Wave 2-safe update payload only for approved status/review/retention/pointer/resume consistency fixes. Do not mutate without a write gate.') | Out-Null

$beforeMetrics | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $outDir 'wave2_before_metrics.json') -Encoding UTF8
@($tableClassifications.ToArray()) | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $outDir 'wave2_table_classification.json') -Encoding UTF8
@($recordCandidateRows.ToArray()) | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $outDir 'wave2_candidates.json') -Encoding UTF8
@($accessFailures.ToArray()) | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $outDir 'wave2_table_access_failures.json') -Encoding UTF8
$reportLines -join [Environment]::NewLine | Set-Content -LiteralPath (Join-Path $outDir 'wave2_discovery_report.md') -Encoding UTF8

Write-Host "Wave 2 discovery/proposal artifacts written to: $outDir"
Write-Host "Candidate record count: $($recordCandidateRows.Count)"
Write-Host "Table access failure count: $($accessFailures.Count)"
