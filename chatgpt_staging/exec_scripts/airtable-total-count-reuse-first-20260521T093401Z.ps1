$ErrorActionPreference = 'Stop'

$requestId = 'airtable-total-count-reuse-first-20260521T093401Z'
$summaryRoot = Join-Path 'chatgpt_staging/status_reports/chatgpt-exec' $requestId
$summaryPath = Join-Path $summaryRoot 'count_summary.md'

Write-Host 'Starting read-only Airtable total-count verification.'

# Reuse the governed export helper first so this test follows the existing tool path.
# This remains intentionally read-only.
$jsonText = & .\operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1 `
  -ExportMode FullRecords `
  -RedactLikelySecrets `
  -OutputNamePrefix $requestId

if ([string]::IsNullOrWhiteSpace($jsonText)) {
    throw 'The Airtable health export helper did not return a JSON summary.'
}

$result = $jsonText | ConvertFrom-Json
if (-not $result.success) {
    throw "The Airtable health export helper reported failure. Output folder: $($result.output_folder)"
}

$manifestPath = Join-Path $result.output_folder 'export_manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Expected export manifest was not found: $manifestPath"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$tableCount = 0
$recordCount = 0

if ($manifest.selected_tables) {
    $tableCount = @($manifest.selected_tables).Count
    foreach ($table in @($manifest.selected_tables)) {
        if ($null -ne $table.record_count_exported) {
            $recordCount += [int]$table.record_count_exported
        }
    }
}

New-Item -ItemType Directory -Force -Path $summaryRoot | Out-Null
@(
    '# Airtable Total Count Summary',
    '',
    "- request_id: $requestId",
    "- export_mode: $($manifest.export_mode)",
    "- selected_table_count: $tableCount",
    "- total_records_counted: $recordCount",
    "- export_manifest_path: $manifestPath",
    "- export_output_folder: $($result.output_folder)",
    '',
    'This summary is derived from the existing Airtable health export helper in a read-only run.'
) | Out-File -FilePath $summaryPath -Encoding utf8

Write-Host "Count summary written to $summaryPath"
