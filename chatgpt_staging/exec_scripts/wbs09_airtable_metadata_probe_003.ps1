$ErrorActionPreference = 'Stop'
$RequestId = 'exec-20260514-wbs09-airtable-metadata-probe-003'
$RepoRoot = (Get-Location).Path
$ReportDir = Join-Path $RepoRoot (Join-Path 'chatgpt_staging/status_reports/chatgpt-exec' $RequestId)
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$summaryPath = Join-Path $ReportDir 'probe_summary.json'
$reportPath = Join-Path $ReportDir 'probe_report.md'
$targetViewsPath = Join-Path $ReportDir 'probe_target_views.json'

$summary = [ordered]@{
    schema = 'dcoir.wbs09.airtable_metadata_probe.v3'
    request_id = $RequestId
    created_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    exporter_success = $false
    exporter_error = $null
    exporter_output_folder = $null
    table_count = 0
    total_view_count = 0
    wbs09_or_gvwi_view_count = 0
    view_property_names_union = @()
    any_view_has_filter_property = $false
    any_view_has_sort_property = $false
    any_view_has_group_property = $false
    any_view_has_visible_field_order = $false
    conclusion = $null
}

$targetViews = @()
try {
    $exportScript = Join-Path $RepoRoot 'operator_tools/github_desktop_lane/scripts/New-DcoirAirtableDatabaseHealthExport.ps1'
    if (-not (Test-Path -LiteralPath $exportScript -PathType Leaf)) {
        throw "Missing exporter script: $exportScript"
    }

    $exportJsonText = & $exportScript -SchemaOnly -MetadataScope 'All' -ProbeUnsupportedMetadata -OutputNamePrefix 'wbs09_metadata_probe_003' -NoZip 2>&1 | Out-String
    $jsonStart = $exportJsonText.LastIndexOf('{')
    if ($jsonStart -lt 0) { throw 'Exporter did not return a JSON result object.' }
    $exportResult = $exportJsonText.Substring($jsonStart) | ConvertFrom-Json
    $summary.exporter_success = [bool]$exportResult.success
    $summary.exporter_output_folder = [string]$exportResult.output_folder
    if (-not $summary.exporter_success) { throw 'Exporter returned success=false.' }

    $schemaFile = Join-Path $summary.exporter_output_folder 'schema/schema.base_tables.json'
    if (-not (Test-Path -LiteralPath $schemaFile -PathType Leaf)) {
        throw "Missing base schema file: $schemaFile"
    }
    $schemaData = Get-Content -LiteralPath $schemaFile -Raw | ConvertFrom-Json
    $tables = @($schemaData.tables)
    $viewRows = New-Object System.Collections.Generic.List[object]
    foreach ($table in $tables) {
        foreach ($view in @($table.views)) {
            $propNames = @($view.PSObject.Properties.Name)
            $viewRows.Add([pscustomobject]@{
                table_id = $table.id
                table_name = $table.name
                view_id = $view.id
                view_name = $view.name
                view_type = $view.type
                property_names = $propNames
                has_visible_field_order = ($propNames -contains 'visibleFieldIds')
                has_filter = ($propNames -contains 'filter' -or $propNames -contains 'filters' -or $propNames -contains 'filterByFormula')
                has_sort = ($propNames -contains 'sort' -or $propNames -contains 'sorts')
                has_group = ($propNames -contains 'group' -or $propNames -contains 'groups')
            }) | Out-Null
        }
    }

    $viewRowsArray = @($viewRows.ToArray())
    $targetViews = @($viewRowsArray | Where-Object { $_.view_name -match '^(WBS09|GVWI)-' -or $_.view_name -match '^WBS09 ' })
    $summary.table_count = $tables.Count
    $summary.total_view_count = $viewRowsArray.Count
    $summary.wbs09_or_gvwi_view_count = $targetViews.Count
    $summary.view_property_names_union = @($viewRowsArray | ForEach-Object { $_.property_names } | Sort-Object -Unique)
    $summary.any_view_has_filter_property = [bool](@($viewRowsArray | Where-Object { $_.has_filter }).Count -gt 0)
    $summary.any_view_has_sort_property = [bool](@($viewRowsArray | Where-Object { $_.has_sort }).Count -gt 0)
    $summary.any_view_has_group_property = [bool](@($viewRowsArray | Where-Object { $_.has_group }).Count -gt 0)
    $summary.any_view_has_visible_field_order = [bool](@($viewRowsArray | Where-Object { $_.has_visible_field_order }).Count -gt 0)

    if (-not $summary.any_view_has_filter_property -and -not $summary.any_view_has_sort_property -and -not $summary.any_view_has_group_property) {
        $summary.conclusion = 'Airtable Web API-accessible metadata exposes view identity/type only for views and does not expose saved filter/sort/group configuration in this export.'
    } else {
        $summary.conclusion = 'Airtable Web API-accessible metadata exposed at least one saved view configuration property. Inspect probe_target_views.json before deciding manual coverage.'
    }
}
catch {
    $summary.exporter_error = $_.Exception.Message
    if ([string]::IsNullOrWhiteSpace($summary.conclusion)) {
        $summary.conclusion = 'Probe did not complete successfully. See exporter_error in probe_summary.json.'
    }
}

$summary | ConvertTo-Json -Depth 20 | Out-File -FilePath $summaryPath -Encoding utf8
$targetViews | ConvertTo-Json -Depth 20 | Out-File -FilePath $targetViewsPath -Encoding utf8
@(
    '# WBS09 Airtable Metadata Probe 003',
    '',
    "created_utc: $($summary.created_utc)",
    "exporter_success: $($summary.exporter_success)",
    "exporter_error: $($summary.exporter_error)",
    "table_count: $($summary.table_count)",
    "total_view_count: $($summary.total_view_count)",
    "wbs09_or_gvwi_view_count: $($summary.wbs09_or_gvwi_view_count)",
    "view_property_names_union: $($summary.view_property_names_union -join ', ')",
    "any_view_has_filter_property: $($summary.any_view_has_filter_property)",
    "any_view_has_sort_property: $($summary.any_view_has_sort_property)",
    "any_view_has_group_property: $($summary.any_view_has_group_property)",
    "any_view_has_visible_field_order: $($summary.any_view_has_visible_field_order)",
    '',
    '## Conclusion',
    '',
    $summary.conclusion,
    '',
    '## Tracked outputs',
    '',
    '- probe_summary.json',
    '- probe_report.md',
    '- probe_target_views.json'
) | Out-File -FilePath $reportPath -Encoding utf8

Write-Host 'WBS09 metadata probe tracked summary completed.'
exit 0
