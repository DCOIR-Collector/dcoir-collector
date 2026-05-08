$ErrorActionPreference = 'Stop'

$expectedBaseId = 'appM4KSwnVf3G3OTK'
$tableName = 'Work Items'
$tableId = 'tblgsQAVWvh8K7gIR'
$secretName = ('DCOIR_' + 'AIRTABLE_' + 'TOKEN')
$baseName = ('DCOIR_' + 'AIRTABLE_' + 'BASE_ID')
$downloadsName = ('DCOIR_' + 'DOWNLOADS_' + 'DIR')
$bearer = [Environment]::GetEnvironmentVariable($secretName, 'Machine')
$baseId = [Environment]::GetEnvironmentVariable($baseName, 'Machine')
$downloads = [Environment]::GetEnvironmentVariable($downloadsName, 'Machine')

if ([string]::IsNullOrWhiteSpace($bearer)) { throw "Missing $secretName" }
if ([string]::IsNullOrWhiteSpace($baseId)) { throw "Missing $baseName" }
if ([string]::IsNullOrWhiteSpace($downloads)) { throw "Missing $downloadsName" }

$outDir = Join-Path $downloads 'wbs22_wave2_single_table_probe_001'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

function Redact-Id([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return '' }
    if ($value.Length -le 8) { return '<short>' }
    return ($value.Substring(0, 6) + '...' + $value.Substring($value.Length - 4))
}

$result = [ordered]@{
    schema = 'dcoir.wbs22_wave2_single_table_probe.v1'
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
    mode = 'single_table_read_only_probe_no_mutation'
    table_name = $tableName
    table_id = $tableId
    expected_base_id_redacted = (Redact-Id $expectedBaseId)
    configured_base_id_redacted = (Redact-Id $baseId)
    configured_matches_expected = ($baseId -eq $expectedBaseId)
    record_read_result = 'not_run'
    record_count_returned = 0
    error_status_code = $null
    error_message = $null
    error_details = $null
}

Write-Host "About to read Airtable table: $tableName ($tableId)"
Write-Host ("Configured base matches expected: {0}" -f $result.configured_matches_expected)

try {
    $headers = @{ Authorization = "Bearer $bearer" }
    $uri = "https://api.airtable.com/v0/$baseId/$tableId?pageSize=1"
    $response = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
    $result.record_read_result = 'success'
    $result.record_count_returned = @($response.records).Count
    Write-Host ("Record read result: {0}" -f $result.record_read_result)
    Write-Host ("Record count returned: {0}" -f $result.record_count_returned)
} catch {
    $result.record_read_result = 'failure'
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
        $result.error_status_code = [int]$_.Exception.Response.StatusCode
    }
    $result.error_message = $_.Exception.Message
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
        $result.error_details = $_.ErrorDetails.Message
    }
    Write-Host ("Record read result: {0}" -f $result.record_read_result)
    Write-Host ("Error status code: {0}" -f $result.error_status_code)
    throw
} finally {
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $outDir 'single_table_probe_result.json') -Encoding UTF8
    Write-Host "Output directory: $outDir"
}
