$ErrorActionPreference = 'Stop'

$repoRoot = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT', 'Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR', 'Machine')
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw 'Missing DCOIR_REPO_ROOT' }
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing DCOIR_DOWNLOADS_DIR' }

$outDir = Join-Path $downloads 'wbs22_wave2_readonly_verification_002'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Start-Transcript -Path (Join-Path $outDir 'terminal_transcript.txt') -Force | Out-Null

try {
    $modulePath = Join-Path $repoRoot 'operator_tools\github_desktop_lane\modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
    if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) { throw "Missing Airtable module: $modulePath" }
    Import-Module $modulePath -Force

    $token = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TOKEN' -Required
    $baseId = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID' -Required
    $headers = New-DcoirAirtableAuthHeader -ApiToken $token

    $tablePolicies = @(
        @{ name='Work Items'; retention='review'; review_after='2026-06-08'; status=$null },
        @{ name='Session Checkpoints'; retention='retain'; review_after='2026-08-06'; status=$null },
        @{ name='Operator Preferences'; retention='retain'; review_after='2026-08-06'; status='active' },
        @{ name='Idea Inbox'; retention='retain'; review_after='2026-08-06'; status=$null },
        @{ name='DCOIR Lifecycle Ledger'; retention='retain'; review_after='2026-08-06'; status=$null },
        @{ name='Admin Registry'; retention='retain'; review_after='2026-08-06'; status=$null },
        @{ name='Repo Surface Registry'; retention='review'; review_after='2026-06-08'; status=$null },
        @{ name='Operator Tools Registry'; retention='operational'; review_after='2026-08-06'; status=$null },
        @{ name='DCOIR Cleanup WBS'; retention='working'; review_after='2026-06-08'; status=$null },
        @{ name='dcoir-memory-preflight'; retention='operational'; review_after='2026-08-06'; status=$null },
        @{ name='dcoir-decision-policy'; retention='operational'; review_after='2026-08-06'; status=$null },
        @{ name='dcoir-validation-orchestrator'; retention='operational'; review_after='2026-08-06'; status=$null }
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

    function GetField($Record, [string]$Name) {
        if ($null -eq $Record -or $null -eq $Record.PSObject.Properties['fields']) { return $null }
        $p = $Record.fields.PSObject.Properties[$Name]
        if ($p) { return $p.Value }
        return $null
    }

    function Norm($Value) {
        if ($null -eq $Value) { return $null }
        if ($Value -is [string]) { return $Value.Trim() }
        if ($Value.PSObject.Properties['name']) { return ([string]$Value.name).Trim() }
        return ([string]$Value).Trim()
    }

    function GetTableByName($Schema, [string]$Name) {
        $m = @($Schema.tables | Where-Object { $_.name -eq $Name })
        if ($m.Count -lt 1) { return $null }
        return $m[0]
    }

    Write-Host "Loading schema for $baseId"
    $schema = Get-DcoirAirtableBaseSchema -BaseId $baseId -Headers $headers

    $summaryRows = New-Object System.Collections.Generic.List[object]
    $remainingRows = New-Object System.Collections.Generic.List[object]
    $sampleRows = New-Object System.Collections.Generic.List[object]

    foreach ($policy in $tablePolicies) {
        $table = GetTableByName $schema $policy.name
        if ($null -eq $table) {
            $summaryRows.Add([pscustomobject]@{ table_name=$policy.name; found=$false; record_count=0; retention_blank=0; review_after_blank=0; status_blank=0; matching_policy_records=0 }) | Out-Null
            continue
        }

        Write-Host "Read-only scan: $($policy.name) ($($table.id))"
        $records = @(Get-DcoirAirtableRecords -BaseId $baseId -Table $table -Headers $headers -RedactLikelySecrets)
        $retentionBlank = 0
        $reviewBlank = 0
        $statusBlank = 0
        $matching = 0

        foreach ($record in $records) {
            $rid = [string]$record.id
            $ret = Norm (GetField $record 'retention_class')
            $rev = Norm (GetField $record 'review_after')
            $statusName = if ($null -ne (GetField $record 'status')) { 'status' } else { 'Status' }
            $status = Norm (GetField $record $statusName)

            $hasBlank = $false
            if (IsBlank $ret) { $retentionBlank++; $hasBlank = $true }
            if (IsBlank $rev) { $reviewBlank++; $hasBlank = $true }
            if ($policy.status -and (IsBlank $status)) { $statusBlank++; $hasBlank = $true }
            if ($ret -eq $policy.retention -and ((-not $policy.status) -or $status -eq $policy.status)) { $matching++ }

            if ($hasBlank) {
                $remainingRows.Add([pscustomobject]@{ table_name=$policy.name; table_id=[string]$table.id; record_id=$rid; retention_class=$ret; review_after=$rev; normalized_status=$status; expected_retention=$policy.retention; expected_review_after=$policy.review_after; expected_status=$policy.status }) | Out-Null
            }
        }

        $summaryRows.Add([pscustomobject]@{ table_name=$policy.name; table_id=[string]$table.id; found=$true; record_count=$records.Count; retention_blank=$retentionBlank; review_after_blank=$reviewBlank; status_blank=$statusBlank; matching_policy_records=$matching }) | Out-Null
        foreach ($r in @($records | Select-Object -First 5)) {
            $sampleRows.Add([pscustomobject]@{ table_name=$policy.name; record_id=[string]$r.id; retention_class=(Norm (GetField $r 'retention_class')); review_after=(Norm (GetField $r 'review_after')); status_lower_field=(Norm (GetField $r 'status')); status_title_field=(Norm (GetField $r 'Status')) }) | Out-Null
        }
    }

    $summary = [ordered]@{
        schema = 'dcoir.wbs22.wave2.readonly_verification.v2'
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        result = 'success'
        mutation_performed = $false
        scanned_table_count = $tablePolicies.Count
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

    $report = @(
        '# WBS22 Wave 2 read-only verification report',
        '',
        "Generated UTC: $($summary.generated_at_utc)",
        '',
        '## Result',
        '',
        '- mutation_performed: false',
        "- scanned_table_count: $($summary.scanned_table_count)",
        "- total_records_scanned: $($summary.total_records_scanned)",
        "- total_retention_blank: $($summary.total_retention_blank)",
        "- total_review_after_blank: $($summary.total_review_after_blank)",
        "- total_status_blank: $($summary.total_status_blank)",
        "- remaining_blank_record_count: $($summary.remaining_blank_record_count)",
        '',
        '## Notes',
        '',
        'This pass is read-only. It normalizes simple Airtable select values for reporting and does not write records.'
    )
    $report | Set-Content -LiteralPath (Join-Path $outDir 'wave2_readonly_verification_report.md') -Encoding UTF8

    Write-Host "Read-only verification complete. Remaining blank records: $($remainingRows.Count). Output: $outDir"
}
finally {
    Stop-Transcript | Out-Null
}
