$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$repoRoot = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT', 'Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR', 'Machine')
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw 'Missing DCOIR_REPO_ROOT' }
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing DCOIR_DOWNLOADS_DIR' }

$outDir = Join-Path $downloads 'wbs22_wave2_bulk_maintenance_update_001'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$transcriptPath = Join-Path $outDir 'terminal_transcript.txt'
Start-Transcript -Path $transcriptPath -Force | Out-Null

try {
    $modulePath = Join-Path $repoRoot 'operator_tools\github_desktop_lane\modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
    if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) { throw "Missing Airtable module: $modulePath" }
    Import-Module $modulePath -Force

    $token = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TOKEN' -Required
    $baseId = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID' -Required
    $headers = New-DcoirAirtableAuthHeader -ApiToken $token

    $waveReviewShort = '2026-06-08'
    $waveReviewStandard = '2026-08-06'
    $policyByTable = [ordered]@{
        'Work Items' = [ordered]@{ retention_class = 'review'; review_after = $waveReviewShort; basis = 'DEFAULT-WORK-ITEMS-RETENTION says retention_class=review until promoted/retained/delete-candidate.' }
        'Session Checkpoints' = [ordered]@{ retention_class = 'retain'; review_after = $waveReviewStandard; basis = 'Session checkpoints are continuity evidence; blank retention/review fields should be retained and dated for later review.' }
        'Operator Preferences' = [ordered]@{ retention_class = 'retain'; status = 'active'; review_after = $waveReviewStandard; basis = 'DEFAULT-POLICY-OPERATOR-PREFERENCES says status=Active and retention_class=retain.' }
        'Idea Inbox' = [ordered]@{ retention_class = 'retain'; review_after = $waveReviewStandard; basis = 'DEFAULT-POLICY-IDEA-INBOX says retention_class=retain unless dropped/promoted.' }
        'DCOIR Lifecycle Ledger' = [ordered]@{ retention_class = 'retain'; review_after = $waveReviewStandard; basis = 'DEFAULT-POLICY-DCOIR-LIFECYCLE-LEDGER says retention_class=retain.' }
        'Admin Registry' = [ordered]@{ retention_class = 'retain'; review_after = $waveReviewStandard; basis = 'Admin Registry governance rows are retained administrative authority/evidence unless separately retired.' }
        'Repo Surface Registry' = [ordered]@{ retention_class = 'review'; review_after = $waveReviewShort; basis = 'Repo Surface Registry rows need review/retention triage, not delete/archive.' }
        'Operator Tools Registry' = [ordered]@{ retention_class = 'operational'; review_after = $waveReviewStandard; basis = 'Operator tool rows are operational tool registry entries unless separately retired.' }
        'DCOIR Cleanup WBS' = [ordered]@{ retention_class = 'working'; review_after = $waveReviewShort; basis = 'Current cleanup WBS rows are working maintenance-plan rows during WBS22.' }
        'dcoir-memory-preflight' = [ordered]@{ retention_class = 'operational'; review_after = $waveReviewStandard; basis = 'Core helper-memory rows are operational unless separately retired.' }
        'dcoir-decision-policy' = [ordered]@{ retention_class = 'operational'; review_after = $waveReviewStandard; basis = 'Core helper-memory rows are operational unless separately retired.' }
        'dcoir-validation-orchestrator' = [ordered]@{ retention_class = 'operational'; review_after = $waveReviewStandard; basis = 'Core helper-memory rows are operational unless separately retired.' }
    }

    function Write-JsonFile {
        param([Parameter(Mandatory=$true)][string]$Path, [Parameter(Mandatory=$true)]$Object)
        $enc = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($Path, ($Object | ConvertTo-Json -Depth 80), $enc)
    }

    function Is-BlankValue {
        param([AllowNull()]$Value)
        if ($null -eq $Value) { return $true }
        if ($Value -is [string]) { return [string]::IsNullOrWhiteSpace($Value) }
        if ($Value -is [array]) { return ($Value.Count -eq 0) }
        return $false
    }

    function Get-RecordFieldValue {
        param([Parameter(Mandatory=$true)]$Record, [Parameter(Mandatory=$true)][string]$FieldName)
        if ($null -eq $Record.PSObject.Properties['fields']) { return $null }
        $prop = $Record.fields.PSObject.Properties[$FieldName]
        if ($prop) { return $prop.Value }
        return $null
    }

    function Get-TableByName {
        param([Parameter(Mandatory=$true)]$Schema, [Parameter(Mandatory=$true)][string]$Name)
        return @($Schema.tables | Where-Object { $_.name -eq $Name } | Select-Object -First 1)
    }

    function Get-FieldByName {
        param([Parameter(Mandatory=$true)]$Table, [Parameter(Mandatory=$true)][string]$Name)
        return @($Table.fields | Where-Object { $_.name -eq $Name } | Select-Object -First 1)
    }

    function Get-SelectChoiceNames {
        param([AllowNull()]$Field)
        $names = @()
        if ($null -eq $Field) { return $names }
        if ($null -eq $Field.PSObject.Properties['options']) { return $names }
        if ($null -eq $Field.options.PSObject.Properties['choices']) { return $names }
        foreach ($choice in @($Field.options.choices)) { $names += [string]$choice.name }
        return $names
    }

    function Invoke-AirtablePatchBatch {
        param(
            [Parameter(Mandatory=$true)][string]$BaseId,
            [Parameter(Mandatory=$true)][string]$TableId,
            [Parameter(Mandatory=$true)][hashtable]$Headers,
            [Parameter(Mandatory=$true)]$Records
        )
        $encodedTable = [System.Uri]::EscapeDataString($TableId)
        $uri = "https://api.airtable.com/v0/$BaseId/$encodedTable"
        $body = @{ records = @($Records); typecast = $false } | ConvertTo-Json -Depth 20
        return Invoke-RestMethod -Uri $uri -Headers $Headers -Method PATCH -Body $body -ContentType 'application/json' -ErrorAction Stop
    }

    Write-Host "Loading Airtable schema for base $baseId"
    $schema = Get-DcoirAirtableBaseSchema -BaseId $baseId -Headers $headers

    $policyOut = [ordered]@{
        schema = 'dcoir.wbs22.wave2.bulk_policy.v2'
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        source = 'live scan of explicit Wave 2 policy tables; no repo artifact_readback dependency'
        review_after_short = $waveReviewShort
        review_after_standard = $waveReviewStandard
        policy_by_table = $policyByTable
        scope = 'Wave 2 maintenance fields only: blank retention_class, blank review_after, and blank status where explicit policy exists.'
        hard_stops = @('no deletes','no Delete Queue processing','no schema changes','no duplicate/merge','no GitHub/source/skill/workflow changes','no scaffold disposition')
    }
    Write-JsonFile -Path (Join-Path $outDir 'wave2_bulk_policy.json') -Object $policyOut

    $beforeRows = New-Object System.Collections.Generic.List[object]
    $planned = New-Object System.Collections.Generic.List[object]
    $skipped = New-Object System.Collections.Generic.List[object]
    $updatesByTable = @{}

    foreach ($tableName in @($policyByTable.Keys)) {
        $policy = $policyByTable[$tableName]
        $table = Get-TableByName -Schema $schema -Name $tableName
        if ($null -eq $table -or $table.Count -eq 0) {
            $skipped.Add([pscustomobject][ordered]@{ table_name=$tableName; reason='table_not_found_in_live_schema' }) | Out-Null
            continue
        }

        $retentionField = Get-FieldByName -Table $table -Name 'retention_class'
        $reviewField = Get-FieldByName -Table $table -Name 'review_after'
        $statusField = Get-FieldByName -Table $table -Name 'status'
        if ($null -eq $statusField -or $statusField.Count -eq 0) { $statusField = Get-FieldByName -Table $table -Name 'Status' }
        $retentionChoices = Get-SelectChoiceNames -Field $retentionField
        $statusChoices = Get-SelectChoiceNames -Field $statusField

        Write-Host "Scanning live records for table $tableName ($($table.id))"
        $records = @(Get-DcoirAirtableRecords -BaseId $baseId -Table $table -Headers $headers -RedactLikelySecrets)
        foreach ($record in $records) {
            $recordId = [string]$record.id
            $currentRetention = Get-RecordFieldValue -Record $record -FieldName 'retention_class'
            $currentReview = Get-RecordFieldValue -Record $record -FieldName 'review_after'
            $statusName = if ($null -ne $statusField -and $statusField.Count -gt 0) { [string]$statusField.name } else { 'status' }
            $currentStatus = Get-RecordFieldValue -Record $record -FieldName $statusName
            $primary = ''
            if ($table.primaryFieldId) {
                $primaryField = @($table.fields | Where-Object { $_.id -eq $table.primaryFieldId } | Select-Object -First 1)
                if ($primaryField) { $primary = [string](Get-RecordFieldValue -Record $record -FieldName ([string]$primaryField.name)) }
            }

            $fields = [ordered]@{}
            $changes = New-Object System.Collections.Generic.List[string]
            $skipReasons = New-Object System.Collections.Generic.List[string]

            if (Is-BlankValue $currentRetention) {
                $desiredRetention = [string]$policy.retention_class
                if ($null -eq $retentionField -or $retentionField.Count -eq 0) { $skipReasons.Add('missing_retention_class_field_in_schema') | Out-Null }
                elseif ($retentionField.type -eq 'singleSelect' -and ($retentionChoices -notcontains $desiredRetention)) { $skipReasons.Add("retention_choice_not_allowed:$desiredRetention") | Out-Null }
                else { $fields['retention_class'] = $desiredRetention; $changes.Add("retention_class=$desiredRetention") | Out-Null }
            }

            if (Is-BlankValue $currentReview) {
                $desiredReview = [string]$policy.review_after
                if ($null -eq $reviewField -or $reviewField.Count -eq 0) { $skipReasons.Add('missing_review_after_field_in_schema') | Out-Null }
                else { $fields['review_after'] = $desiredReview; $changes.Add("review_after=$desiredReview") | Out-Null }
            }

            if ($policy.Contains('status') -and ($null -ne $statusField -and $statusField.Count -gt 0) -and (Is-BlankValue $currentStatus)) {
                $desiredStatus = [string]$policy.status
                if ($statusField.type -eq 'singleSelect' -and ($statusChoices -notcontains $desiredStatus)) { $skipReasons.Add("status_choice_not_allowed:$desiredStatus") | Out-Null }
                else { $fields[$statusName] = $desiredStatus; $changes.Add("$statusName=$desiredStatus") | Out-Null }
            }

            if ($fields.Count -eq 0) {
                if ($skipReasons.Count -gt 0) {
                    $skipped.Add([pscustomobject][ordered]@{ table_name=$tableName; table_id=[string]$table.id; record_id=$recordId; primary_value=$primary; reason=($skipReasons.ToArray() -join ';') }) | Out-Null
                }
                continue
            }

            $beforeRows.Add([pscustomobject][ordered]@{
                table_name = $tableName
                table_id = [string]$table.id
                record_id = $recordId
                primary_value = $primary
                current_retention_class = $currentRetention
                current_review_after = $currentReview
                current_status = $currentStatus
                planned_fields = $fields
                basis = [string]$policy.basis
            }) | Out-Null

            if (-not $updatesByTable.ContainsKey($tableName)) { $updatesByTable[$tableName] = New-Object System.Collections.Generic.List[object] }
            $updatesByTable[$tableName].Add([pscustomobject][ordered]@{ id = $recordId; fields = $fields }) | Out-Null
            $planned.Add([pscustomobject][ordered]@{ table_name=$tableName; table_id=[string]$table.id; record_id=$recordId; primary_value=$primary; changes=@($changes.ToArray()); basis=[string]$policy.basis }) | Out-Null
        }
    }

    Write-JsonFile -Path (Join-Path $outDir 'wave2_bulk_before.json') -Object @($beforeRows.ToArray())
    Write-JsonFile -Path (Join-Path $outDir 'wave2_bulk_update_plan.json') -Object @($planned.ToArray())
    Write-JsonFile -Path (Join-Path $outDir 'wave2_bulk_skipped.json') -Object @($skipped.ToArray())

    $results = New-Object System.Collections.Generic.List[object]
    $totalUpdated = 0
    foreach ($tableName in @($updatesByTable.Keys | Sort-Object)) {
        $table = Get-TableByName -Schema $schema -Name $tableName
        $updates = @($updatesByTable[$tableName].ToArray())
        Write-Host "Applying $($updates.Count) update(s) to $tableName ($($table.id))"
        for ($i = 0; $i -lt $updates.Count; $i += 10) {
            $end = [Math]::Min($i + 9, $updates.Count - 1)
            $batch = @($updates[$i..$end])
            $response = Invoke-AirtablePatchBatch -BaseId $baseId -TableId ([string]$table.id) -Headers $headers -Records $batch
            $updatedIds = @($response.records | ForEach-Object { [string]$_.id })
            $totalUpdated += $updatedIds.Count
            $results.Add([pscustomobject][ordered]@{ table_name=$tableName; table_id=[string]$table.id; batch_start=$i; batch_count=$batch.Count; updated_record_ids=$updatedIds }) | Out-Null
        }
    }
    Write-JsonFile -Path (Join-Path $outDir 'wave2_bulk_update_results.json') -Object @($results.ToArray())

    $afterRows = New-Object System.Collections.Generic.List[object]
    $verificationFailures = New-Object System.Collections.Generic.List[object]
    foreach ($tableName in @($updatesByTable.Keys | Sort-Object)) {
        $table = Get-TableByName -Schema $schema -Name $tableName
        Write-Host "Readback after updates for $tableName"
        $records = @(Get-DcoirAirtableRecords -BaseId $baseId -Table $table -Headers $headers -RedactLikelySecrets)
        $recordMap = @{}
        foreach ($r in $records) { $recordMap[[string]$r.id] = $r }
        foreach ($u in @($updatesByTable[$tableName].ToArray())) {
            $recordId = [string]$u.id
            if (-not $recordMap.ContainsKey($recordId)) { $verificationFailures.Add([pscustomobject][ordered]@{ table_name=$tableName; record_id=$recordId; reason='updated_record_missing_on_readback' }) | Out-Null; continue }
            $record = $recordMap[$recordId]
            $verified = $true
            $actual = [ordered]@{}
            foreach ($fieldProp in $u.fields.PSObject.Properties) {
                $actualValue = Get-RecordFieldValue -Record $record -FieldName $fieldProp.Name
                $actual[$fieldProp.Name] = $actualValue
                if ([string]$actualValue -ne [string]$fieldProp.Value) { $verified = $false }
            }
            if (-not $verified) { $verificationFailures.Add([pscustomobject][ordered]@{ table_name=$tableName; record_id=$recordId; expected=$u.fields; actual=$actual; reason='field_value_mismatch' }) | Out-Null }
            $afterRows.Add([pscustomobject][ordered]@{ table_name=$tableName; table_id=[string]$table.id; record_id=$recordId; verified=$verified; actual_fields=$actual }) | Out-Null
        }
    }
    Write-JsonFile -Path (Join-Path $outDir 'wave2_bulk_after_readback.json') -Object @($afterRows.ToArray())
    Write-JsonFile -Path (Join-Path $outDir 'wave2_bulk_verification_failures.json') -Object @($verificationFailures.ToArray())

    $summary = [ordered]@{
        schema = 'dcoir.wbs22.wave2.bulk_update_summary.v2'
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        scanned_table_count = $policyByTable.Count
        planned_update_count = $planned.Count
        updated_record_count = $totalUpdated
        skipped_count = $skipped.Count
        verification_failure_count = $verificationFailures.Count
        updated_tables = @($updatesByTable.Keys | Sort-Object)
        no_mutation_boundaries = @('no deletes','no Delete Queue processing','no schema changes','no duplicate/merge','no GitHub/source/skill/workflow changes','no scaffold disposition')
    }
    Write-JsonFile -Path (Join-Path $outDir 'wave2_bulk_summary.json') -Object $summary

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add('# WBS22 Wave 2 bulk maintenance update report') | Out-Null
    $lines.Add('') | Out-Null
    $lines.Add("Generated UTC: $($summary.generated_at_utc)") | Out-Null
    $lines.Add('') | Out-Null
    $lines.Add('## Result') | Out-Null
    $lines.Add('') | Out-Null
    $lines.Add("- scanned_table_count: $($summary.scanned_table_count)") | Out-Null
    $lines.Add("- planned_update_count: $($summary.planned_update_count)") | Out-Null
    $lines.Add("- updated_record_count: $($summary.updated_record_count)") | Out-Null
    $lines.Add("- skipped_count: $($summary.skipped_count)") | Out-Null
    $lines.Add("- verification_failure_count: $($summary.verification_failure_count)") | Out-Null
    $lines.Add("- updated_tables: $((@($summary.updated_tables)) -join ', ')") | Out-Null
    $lines.Add('') | Out-Null
    $lines.Add('## Scope') | Out-Null
    $lines.Add('') | Out-Null
    $lines.Add('Applied only Wave 2 maintenance fields: blank retention_class, blank review_after, and blank status where explicit table policy existed. No deletes, Delete Queue processing, schema changes, duplicate/merge work, GitHub/source/skill/workflow changes, or scaffold disposition.') | Out-Null
    $lines.Add('') | Out-Null
    $lines.Add('## Artifacts') | Out-Null
    $lines.Add('') | Out-Null
    foreach ($name in @('wave2_bulk_policy.json','wave2_bulk_before.json','wave2_bulk_update_plan.json','wave2_bulk_update_results.json','wave2_bulk_after_readback.json','wave2_bulk_verification_failures.json','wave2_bulk_skipped.json','wave2_bulk_summary.json','terminal_transcript.txt')) { $lines.Add("- $name") | Out-Null }
    $lines -join [Environment]::NewLine | Set-Content -LiteralPath (Join-Path $outDir 'wave2_bulk_update_report.md') -Encoding UTF8

    Write-Host "Wave 2 bulk maintenance complete. Updated records: $totalUpdated. Verification failures: $($verificationFailures.Count). Output: $outDir"
    if ($verificationFailures.Count -gt 0) { throw "Verification failures detected: $($verificationFailures.Count)" }
}
finally {
    Stop-Transcript | Out-Null
}
