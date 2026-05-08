$ErrorActionPreference = 'Stop'

$repoRoot = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT', 'Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR', 'Machine')
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw 'Missing DCOIR_REPO_ROOT' }
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing DCOIR_DOWNLOADS_DIR' }

$outDir = Join-Path $downloads 'wbs22_wave2_readonly_verification_004'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Start-Transcript -Path (Join-Path $outDir 'terminal_transcript.txt') -Force | Out-Null

try {
    $modulePath = Join-Path $repoRoot 'operator_tools\github_desktop_lane\modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
    if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) { throw "Missing Airtable module: $modulePath" }
    Import-Module $modulePath -Force

    $token = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TOKEN' -Required
    $baseId = 'appM4KSwnVf3G3OTK'
    $headers = @{ Authorization = "Bearer $token" }

    $tablePolicies = @(
        @{ name='Work Items'; table_id='tblgsQAVWvh8K7gIR'; retention='review'; review_after='2026-06-08'; status=$null; status_field='Status' },
        @{ name='Session Checkpoints'; table_id='tblTe75HKZOJaPDGn'; retention='retain'; review_after='2026-08-06'; status=$null; status_field=$null },
        @{ name='Operator Preferences'; table_id='tblnxZ3eLPT3W38wl'; retention='retain'; review_after='2026-08-06'; status='active'; status_field='status' },
        @{ name='Idea Inbox'; table_id='tblWwBxwrjZF6JR3r'; retention='retain'; review_after='2026-08-06'; status=$null; status_field='status' },
        @{ name='DCOIR Lifecycle Ledger'; table_id='tblNsjkGUUIdRpHuE'; retention='retain'; review_after='2026-08-06'; status=$null; status_field=$null },
        @{ name='Admin Registry'; table_id='tblFaJW1V2DPc9css'; retention='retain'; review_after='2026-08-06'; status=$null; status_field='status' },
        @{ name='Repo Surface Registry'; table_id='tblzBiXp7kwTXM0ru'; retention='review'; review_after='2026-06-08'; status=$null; status_field=$null },
        @{ name='Operator Tools Registry'; table_id='tblF1SCJBHRFUhpzi'; retention='operational'; review_after='2026-08-06'; status=$null; status_field='status' },
        @{ name='DCOIR Cleanup WBS'; table_id='tblRxTmpW0VunQlUK'; retention=$null; review_after='2026-06-08'; status=$null; status_field=$null },
        @{ name='dcoir-memory-preflight'; table_id='tblcNNuKqi8IkFsSQ'; retention='operational'; review_after='2026-08-06'; status=$null; status_field='status' },
        @{ name='dcoir-decision-policy'; table_id='tblKHVXq16Xd5I31m'; retention='operational'; review_after='2026-08-06'; status=$null; status_field='status' },
        @{ name='dcoir-validation-orchestrator'; table_id='tbls9O1B0Rs8YvTAj'; retention='operational'; review_after='2026-08-06'; status=$null; status_field='status' }
    )

    function Write-JsonFile($Path, $Object) {
        $enc = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($Path, ($Object | ConvertTo-Json -Depth 80), $enc)
    }

    function IsBlank($Value) {
        if ($null -eq $Value) { return $true }
        if ($Value -is [string]) { return [string]::IsNullOrWhiteSpace($Value) }
        if ($Value -is [array]) { return ($Value.Count -eq 0) }
        return $false
    }

    function Norm($Value) {
        if ($null -eq $Value) { return $null }
        if ($Value -is [string]) { return $Value.Trim() }
        if ($Value.PSObject.Properties['name']) { return ([string]$Value.name).Trim() }
        return ([string]$Value).Trim()
    }

    function Get-FieldByName($Record, [string]$Name) {
        if ($null -eq $Record -or [string]::IsNullOrWhiteSpace($Name)) { return $null }
        if ($null -eq $Record.PSObject.Properties['fields']) { return $null }
        $p = $Record.fields.PSObject.Properties[$Name]
        if ($p) { return $p.Value }
        return $null
    }

    function Get-AirtableRecordsRaw($BaseId, $TableId, $TableName, $Headers) {
        $all = New-Object System.Collections.Generic.List[object]
        $offset = $null
        do {
            $encodedTable = [System.Uri]::EscapeDataString($TableId)
            $uri = "https://api.airtable.com/v0/$BaseId/$encodedTable?pageSize=100"
            if (-not [string]::IsNullOrWhiteSpace($offset)) { $uri = "$uri&offset=$([System.Uri]::EscapeDataString($offset))" }
            try {
                $resp = Invoke-RestMethod -Uri $uri -Headers $Headers -Method GET -ErrorAction Stop
            } catch {
                if ($offset) { throw }
                Write-Warning "GET by table id failed for $TableName ($TableId); retrying by table name. $($_.Exception.Message)"
                $encodedName = [System.Uri]::EscapeDataString($TableName)
                $uri = "https://api.airtable.com/v0/$BaseId/$encodedName?pageSize=100"
                $resp = Invoke-RestMethod -Uri $uri -Headers $Headers -Method GET -ErrorAction Stop
            }
            foreach ($record in @($resp.records)) { $all.Add($record) | Out-Null }
            $offset = $resp.offset
        } while (-not [string]::IsNullOrWhiteSpace($offset))
        return @($all.ToArray())
    }

    $summaryRows = New-Object System.Collections.Generic.List[object]
    $remainingRows = New-Object System.Collections.Generic.List[object]
    $sampleRows = New-Object System.Collections.Generic.List[object]
    $accessFailures = New-Object System.Collections.Generic.List[object]

    foreach ($policy in $tablePolicies) {
        Write-Host "Read-only direct REST scan: $($policy.name) ($($policy.table_id)) in $baseId"
        try {
            $records = @(Get-AirtableRecordsRaw -BaseId $baseId -TableId $policy.table_id -TableName $policy.name -Headers $headers)
        } catch {
            $accessFailures.Add([pscustomobject]@{ table_name=$policy.name; table_id=$policy.table_id; error=$_.Exception.Message }) | Out-Null
            $summaryRows.Add([pscustomobject]@{ table_name=$policy.name; table_id=$policy.table_id; found=$false; record_count=0; retention_blank=0; review_after_blank=0; status_blank=0; matching_retention_records=0; matching_status_records=0 }) | Out-Null
            continue
        }

        $retentionBlank = 0; $reviewBlank = 0; $statusBlank = 0; $matchingRetention = 0; $matchingStatus = 0
        foreach ($record in $records) {
            $ret = Norm (Get-FieldByName $record 'retention_class')
            $rev = Norm (Get-FieldByName $record 'review_after')
            $status = Norm (Get-FieldByName $record $policy.status_field)
            $hasBlank = $false
            if ($policy.retention -and (IsBlank $ret)) { $retentionBlank++; $hasBlank = $true }
            if (IsBlank $rev) { $reviewBlank++; $hasBlank = $true }
            if ($policy.status -and (IsBlank $status)) { $statusBlank++; $hasBlank = $true }
            if ($policy.retention -and $ret -eq $policy.retention) { $matchingRetention++ }
            if ($policy.status -and $status -eq $policy.status) { $matchingStatus++ }
            if ($hasBlank) {
                $remainingRows.Add([pscustomobject]@{ table_name=$policy.name; table_id=$policy.table_id; record_id=[string]$record.id; retention_class=$ret; review_after=$rev; normalized_status=$status; expected_retention=$policy.retention; expected_review_after=$policy.review_after; expected_status=$policy.status }) | Out-Null
            }
        }
        $summaryRows.Add([pscustomobject]@{ table_name=$policy.name; table_id=$policy.table_id; found=$true; record_count=$records.Count; retention_blank=$retentionBlank; review_after_blank=$reviewBlank; status_blank=$statusBlank; matching_retention_records=$matchingRetention; matching_status_records=$matchingStatus }) | Out-Null
        foreach ($r in @($records | Select-Object -First 5)) {
            $sampleRows.Add([pscustomobject]@{ table_name=$policy.name; record_id=[string]$r.id; retention_class=(Norm (Get-FieldByName $r 'retention_class')); review_after=(Norm (Get-FieldByName $r 'review_after')); normalized_status=(Norm (Get-FieldByName $r $policy.status_field)) }) | Out-Null
        }
    }

    $summary = [ordered]@{
        schema = 'dcoir.wbs22.wave2.readonly_verification.v4'
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        result = if ($accessFailures.Count -eq 0) { 'success' } else { 'failure' }
        mutation_performed = $false
        base_id_used = $baseId
        scanned_table_count = $tablePolicies.Count
        access_failure_count = $accessFailures.Count
        total_records_scanned = (@($summaryRows.ToArray()) | Measure-Object -Property record_count -Sum).Sum
        total_retention_blank = (@($summaryRows.ToArray()) | Measure-Object -Property retention_blank -Sum).Sum
        total_review_after_blank = (@($summaryRows.ToArray()) | Measure-Object -Property review_after_blank -Sum).Sum
        total_status_blank = (@($summaryRows.ToArray()) | Measure-Object -Property status_blank -Sum).Sum
        remaining_blank_record_count = $remainingRows.Count
    }

    Write-JsonFile (Join-Path $outDir 'wave2_readonly_verification_summary.json') $summary
    Write-JsonFile (Join-Path $outDir 'wave2_readonly_verification_by_table.json') @($summaryRows.ToArray())
    Write-JsonFile (Join-Path $outDir 'wave2_remaining_blank_records.json') @($remainingRows.ToArray())
    Write-JsonFile (Join-Path $outDir 'wave2_sample_normalized_values.json') @($sampleRows.ToArray())
    Write-JsonFile (Join-Path $outDir 'wave2_access_failures.json') @($accessFailures.ToArray())

    @(
        '# WBS22 Wave 2 read-only verification report', '',
        "Generated UTC: $($summary.generated_at_utc)", '',
        '## Result', '',
        '- mutation_performed: false',
        "- base_id_used: $($summary.base_id_used)",
        "- scanned_table_count: $($summary.scanned_table_count)",
        "- access_failure_count: $($summary.access_failure_count)",
        "- total_records_scanned: $($summary.total_records_scanned)",
        "- total_retention_blank: $($summary.total_retention_blank)",
        "- total_review_after_blank: $($summary.total_review_after_blank)",
        "- total_status_blank: $($summary.total_status_blank)",
        "- remaining_blank_record_count: $($summary.remaining_blank_record_count)", '',
        '## Notes', '',
        'This pass is read-only. It uses direct Airtable REST GET calls against the approved DCOIR base id.'
    ) | Set-Content -LiteralPath (Join-Path $outDir 'wave2_readonly_verification_report.md') -Encoding UTF8

    Write-Host "Read-only direct REST verification complete. Remaining blank records: $($remainingRows.Count). Access failures: $($accessFailures.Count). Output: $outDir"
    if ($accessFailures.Count -gt 0) { throw "Read-only verification access failures: $($accessFailures.Count)" }
}
finally {
    Stop-Transcript | Out-Null
}
