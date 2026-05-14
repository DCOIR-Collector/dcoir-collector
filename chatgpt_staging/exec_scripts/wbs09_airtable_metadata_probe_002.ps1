$ErrorActionPreference = 'Stop'

function Get-EnvValue {
    param([Parameter(Mandatory=$true)][string]$Name)
    $processValue = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if (-not [string]::IsNullOrWhiteSpace($processValue)) { return $processValue }
    $machineValue = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    if (-not [string]::IsNullOrWhiteSpace($machineValue)) { return $machineValue }
    return $null
}

$token = Get-EnvValue -Name 'DCOIR_AIRTABLE_TOKEN'
$baseId = Get-EnvValue -Name 'DCOIR_AIRTABLE_BASE_ID'
if ([string]::IsNullOrWhiteSpace($token)) { throw 'DCOIR_AIRTABLE_TOKEN is not available to the runner.' }
if ([string]::IsNullOrWhiteSpace($baseId)) { throw 'DCOIR_AIRTABLE_BASE_ID is not available to the runner.' }

$out = Get-EnvValue -Name 'DCOIR_DOWNLOADS_DIR'
if ([string]::IsNullOrWhiteSpace($out)) { $out = Join-Path $env:RUNNER_TEMP 'dcoir_probe_out' }
New-Item -ItemType Directory -Force -Path $out | Out-Null

$headers = @{ Authorization = "Bearer $token" }
$uri = "https://api.airtable.com/v0/meta/bases/$baseId/tables"
$schema = Invoke-RestMethod -Uri $uri -Headers $headers -Method GET
$tables = @($schema.tables)

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
            raw_public_shape_json = ($view | ConvertTo-Json -Depth 20)
        }) | Out-Null
    }
}

$targetViews = @($viewRows.ToArray() | Where-Object { $_.view_name -match '^(WBS09|GVWI)-' -or $_.view_name -match '^WBS09 ' })
$viewPropertyNamesUnion = @($viewRows | ForEach-Object { $_.property_names } | Sort-Object -Unique)
$anyFilter = [bool](@($viewRows | Where-Object { $_.has_filter }).Count -gt 0)
$anySort = [bool](@($viewRows | Where-Object { $_.has_sort }).Count -gt 0)
$anyGroup = [bool](@($viewRows | Where-Object { $_.has_group }).Count -gt 0)
$anyVisibleFieldOrder = [bool](@($viewRows | Where-Object { $_.has_visible_field_order }).Count -gt 0)

$conclusion = if (-not $anyFilter -and -not $anySort -and -not $anyGroup) {
    'Airtable metadata endpoint returned view metadata but did not expose saved filter/sort/group configuration properties to this token/API response.'
} else {
    'Airtable metadata endpoint exposed at least one saved view configuration property; inspect target view rows for filter/sort/group coverage.'
}

$summary = [ordered]@{
    schema = 'dcoir.wbs09.airtable_metadata_probe.v1'
    created_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    table_count = $tables.Count
    total_view_count = @($viewRows).Count
    wbs09_or_gvwi_view_count = @($targetViews).Count
    view_property_names_union = $viewPropertyNamesUnion
    any_view_has_filter_property = $anyFilter
    any_view_has_sort_property = $anySort
    any_view_has_group_property = $anyGroup
    any_view_has_visible_field_order = $anyVisibleFieldOrder
    conclusion = $conclusion
}

$summaryPath = Join-Path $out 'wbs09_airtable_metadata_probe_summary.json'
$viewsPath = Join-Path $out 'wbs09_airtable_metadata_probe_views.json'
$targetsPath = Join-Path $out 'wbs09_airtable_metadata_probe_target_views.json'
$mdPath = Join-Path $out 'wbs09_airtable_metadata_probe_report.md'

$summary | ConvertTo-Json -Depth 20 | Out-File -FilePath $summaryPath -Encoding utf8
$viewRows.ToArray() | ConvertTo-Json -Depth 30 | Out-File -FilePath $viewsPath -Encoding utf8
$targetViews | ConvertTo-Json -Depth 30 | Out-File -FilePath $targetsPath -Encoding utf8
@(
    '# WBS09 Airtable Metadata Probe',
    '',
    "created_utc: $($summary.created_utc)",
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
    '## Output files',
    '',
    '- wbs09_airtable_metadata_probe_summary.json',
    '- wbs09_airtable_metadata_probe_views.json',
    '- wbs09_airtable_metadata_probe_target_views.json'
) | Out-File -FilePath $mdPath -Encoding utf8

Write-Host 'WBS09 Airtable metadata probe complete. Sanitized report files written to DCOIR_DOWNLOADS_DIR.'
