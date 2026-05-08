$ErrorActionPreference = 'Stop'

$repoRoot = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT', 'Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR', 'Machine')
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw 'Missing DCOIR_REPO_ROOT' }
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing DCOIR_DOWNLOADS_DIR' }

$exportTool = Join-Path $repoRoot 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
if (-not (Test-Path -LiteralPath $exportTool -PathType Leaf)) { throw "Missing Airtable export tool: $exportTool" }

$prefix = 'wbs22_wave2_discovery_005'
$outName = 'wbs22_wave2_discovery_from_exporter_005'
Write-Host "Running existing Airtable exporter: $exportTool"
& $exportTool -ExportMode FullRecords -MetadataScope 'All' -ProbeUnsupportedMetadata -RedactLikelySecrets -OutputNamePrefix $prefix -NoZip | Out-Host

$exportFolder = Get-ChildItem -LiteralPath $downloads -Directory -Filter "$prefix*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $exportFolder) { throw "No exporter output folder found for prefix $prefix under $downloads" }
Write-Host "Exporter output folder: $($exportFolder.FullName)"

$manifestPath = Join-Path $exportFolder.FullName 'export_manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Missing export manifest: $manifestPath" }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json

$outDir = Join-Path $downloads $outName
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function ConvertTo-SafeArray($value) {
    if ($null -eq $value) { return @() }
    if ($value -is [System.Array]) { return @($value) }
    return @($value)
}

function Write-JsonObjectFile {
    param([Parameter(Mandatory=$true)][string]$Path, [Parameter(Mandatory=$true)]$Object, [int]$Depth = 20)
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Write-JsonArrayFile {
    param([Parameter(Mandatory=$true)][string]$Path, [AllowNull()]$Items, [int]$Depth = 20)
    $arr = @(ConvertTo-SafeArray $Items)
    if ($arr.Count -eq 0) {
        '[]' | Set-Content -LiteralPath $Path -Encoding UTF8
    } else {
        $arr | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
    }
}

function Get-FieldValue {
    param($Record, [string]$Name)
    if ($null -eq $Record -or $null -eq $Record.fields) { return $null }
    $prop = $Record.fields.PSObject.Properties[$Name]
    if ($prop) { return $prop.Value }
    return $null
}

function ConvertTo-TextValue {
    param($Value)
    if ($null -eq $Value) { return '' }
    if ($Value -is [string]) { return $Value }
    return ($Value | ConvertTo-Json -Depth 8 -Compress)
}

$coreGovernanceTables = @(
    'Plans',
    'Queue Control',
    'Work Items',
    'Session Checkpoints',
    'DCOIR Cleanup WBS',
    'Operator Preferences',
    'Admin Registry',
    'Operator Tools Registry',
    'dcoir-memory-preflight',
    'dcoir-validation-orchestrator',
    'dcoir-decision-policy'
)
$stopTables = @('Delete Queue', 'DCOIR Cleanup Scaffold Registry')
$stalePattern = 'CLEANUP-WBS-08-01|PLAN-TASK|Plan Tasks|Plan Checkpoints|Skill State Registry|Schema Registry|Tracking Registry'

$tableClassifications = New-Object System.Collections.Generic.List[object]
$recordCandidateRows = New-Object System.Collections.Generic.List[object]
$immediateCandidates = New-Object System.Collections.Generic.List[object]
$deferredCandidates = New-Object System.Collections.Generic.List[object]
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
    if ($stopTables -contains $tableName) {
        $handling = 'read_only_stop_surface'
        $stopReason = 'Wave 2 must not process Delete Queue, delete records, or do scaffold disposition.'
    } elseif ($coreGovernanceTables -contains $tableName) {
        $handling = 'wave2_candidate_core_governance_review'
    } elseif ($hasStatus -or $hasReview -or $hasRetention -or $pointerFields.Count -gt 0 -or $hasResume) {
        $handling = 'wave2_deferred_broad_hygiene_review'
    }

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
        $tier = 'deferred_broad_hygiene_review'
        $wave2Safe = $false

        if ($tableName -eq 'Plans') {
            $activeTask = [string](Get-FieldValue -Record $r -Name 'active_task_id')
            $activePlanTask = [string](Get-FieldValue -Record $r -Name 'active_plan_task_id')
            if ($activeTask -and $activePlanTask -and $activeTask -ne $activePlanTask) {
                $candidateReasons.Add("active_task_id_mismatch active_task_id=$activeTask active_plan_task_id=$activePlanTask") | Out-Null
                $tier = 'immediate_wave2_pointer_consistency'
                $wave2Safe = $true
            }
        }

        foreach ($pf in $pointerFields) {
            $text = ConvertTo-TextValue (Get-FieldValue -Record $r -Name $pf)
            if ($text -match $stalePattern) {
                $candidateReasons.Add("stale_reference_in_$pf") | Out-Null
                if ($coreGovernanceTables -contains $tableName -and -not ($stopTables -contains $tableName)) {
                    $tier = 'immediate_wave2_stale_execution_reference_review'
                    $wave2Safe = $true
                }
            }
        }

        if ($coreGovernanceTables -contains $tableName -and -not ($stopTables -contains $tableName)) {
            if ($hasRetention) {
                $retention = Get-FieldValue -Record $r -Name 'retention_class'
                if ($null -eq $retention -or [string]::IsNullOrWhiteSpace([string]$retention)) {
                    $candidateReasons.Add('missing_retention_class_core_table') | Out-Null
                    if ($tier -eq 'deferred_broad_hygiene_review') { $tier = 'deferred_core_review_retention' }
                }
            }
            if ($hasReview) {
                $review = Get-FieldValue -Record $r -Name 'review_after'
                if ($null -eq $review -or [string]::IsNullOrWhiteSpace([string]$review)) {
                    $candidateReasons.Add('missing_review_after_core_table') | Out-Null
                    if ($tier -eq 'deferred_broad_hygiene_review') { $tier = 'deferred_core_review_retention' }
                }
            }
        }

        if ($candidateReasons.Count -gt 0) {
            $row = [pscustomobject][ordered]@{
                table_name = $tableName
                table_id = [string]$t.table_id
                record_id = [string]$r.id
                primary_value = $primary
                candidate_tier = $tier
                wave2_mutation_candidate = $wave2Safe
                reasons = @($candidateReasons.ToArray())
                wave2_action = 'proposal_only_no_mutation'
                stop_if_requires = 'duplicate_merge_delete_queue_record_delete_schema_change_source_skill_workflow_change_scaffold_disposition'
            }
            $recordCandidateRows.Add($row) | Out-Null
            if ($wave2Safe) { $immediateCandidates.Add($row) | Out-Null } else { $deferredCandidates.Add($row) | Out-Null }
        }
    }
}

$summaryByTier = @($recordCandidateRows.ToArray() | Group-Object candidate_tier | Sort-Object Name | ForEach-Object { [pscustomobject][ordered]@{ tier=$_.Name; count=$_.Count } })
$summaryByTable = @($recordCandidateRows.ToArray() | Group-Object table_name | Sort-Object Count -Descending | ForEach-Object { [pscustomobject][ordered]@{ table_name=$_.Name; count=$_.Count } })

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
    immediate_wave2_candidate_count = $immediateCandidates.Count
    deferred_candidate_count = $deferredCandidates.Count
    table_access_failure_count = $accessFailures.Count
}

$candidateSummary = [ordered]@{
    schema = 'dcoir.wbs22.wave2.candidate_summary.v1'
    generated_at_utc = $beforeMetrics.generated_at_utc
    immediate_wave2_candidate_count = $immediateCandidates.Count
    deferred_candidate_count = $deferredCandidates.Count
    total_candidate_record_count = $recordCandidateRows.Count
    table_access_failure_count = $accessFailures.Count
    by_tier = @($summaryByTier)
    by_table = @($summaryByTable)
    mutation_guidance = 'Only immediate_wave2_* candidates are eligible for an exact Wave 2-safe payload. Deferred candidates require separate review and must not be bulk-mutated.'
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
$reportLines.Add("- total_records_exported: $($beforeMetrics.total_records_exported)") | Out-Null
$reportLines.Add("- candidate_record_count: $($beforeMetrics.candidate_record_count)") | Out-Null
$reportLines.Add("- immediate_wave2_candidate_count: $($beforeMetrics.immediate_wave2_candidate_count)") | Out-Null
$reportLines.Add("- deferred_candidate_count: $($beforeMetrics.deferred_candidate_count)") | Out-Null
$reportLines.Add("- table_access_failure_count: $($beforeMetrics.table_access_failure_count)") | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('## Immediate Wave 2 candidates') | Out-Null
$reportLines.Add('') | Out-Null
if ($immediateCandidates.Count -eq 0) {
    $reportLines.Add('- none') | Out-Null
} else {
    foreach ($c in @($immediateCandidates.ToArray())) {
        $reportLines.Add(("- {0} / {1} / {2}: {3}" -f $c.table_name, $c.record_id, $c.primary_value, (($c.reasons) -join '; '))) | Out-Null
    }
}
$reportLines.Add('') | Out-Null
$reportLines.Add('## Deferred candidates') | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('Deferred candidates are reported for review only and are not approved for bulk Wave 2 mutation.') | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('## Next recommended move') | Out-Null
$reportLines.Add('') | Out-Null
$reportLines.Add('Prepare an exact Wave 2-safe update payload only for immediate_wave2_* candidates after write-gate review. Do not mutate deferred candidates in bulk.') | Out-Null

Write-JsonObjectFile -Path (Join-Path $outDir 'wave2_before_metrics.json') -Object $beforeMetrics -Depth 12
Write-JsonArrayFile -Path (Join-Path $outDir 'wave2_table_classification.json') -Items @($tableClassifications.ToArray()) -Depth 12
Write-JsonArrayFile -Path (Join-Path $outDir 'wave2_candidates.json') -Items @($recordCandidateRows.ToArray()) -Depth 12
Write-JsonArrayFile -Path (Join-Path $outDir 'wave2_immediate_candidates.json') -Items @($immediateCandidates.ToArray()) -Depth 12
Write-JsonArrayFile -Path (Join-Path $outDir 'wave2_deferred_candidates.json') -Items @($deferredCandidates.ToArray()) -Depth 12
Write-JsonArrayFile -Path (Join-Path $outDir 'wave2_table_access_failures.json') -Items @($accessFailures.ToArray()) -Depth 12
Write-JsonObjectFile -Path (Join-Path $outDir 'wave2_candidate_summary.json') -Object $candidateSummary -Depth 12
$reportLines -join [Environment]::NewLine | Set-Content -LiteralPath (Join-Path $outDir 'wave2_discovery_report.md') -Encoding UTF8

Write-Host "Wave 2 discovery/proposal artifacts written to: $outDir"
Write-Host "Immediate candidate count: $($immediateCandidates.Count)"
Write-Host "Deferred candidate count: $($deferredCandidates.Count)"
Write-Host "Table access failure count: $($accessFailures.Count)"
