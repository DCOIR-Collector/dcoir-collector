[CmdletBinding()]
param(
    [switch]$SchemaOnly,
    [switch]$RedactLikelySecrets,
    [int]$MaxRecordsPerTable = 0,
    [string]$OutputNamePrefix = 'dcoir_airtable_health_export',
    [string]$TableList,
    [switch]$NoZip
)

$ErrorActionPreference = 'Stop'
$Script:DcoirAirtableExporterVersion = '2026-05-03.1'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$toolRoot = Split-Path -Parent $scriptRoot
$modulePath = Join-Path $toolRoot 'modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
$zipScript = Join-Path $toolRoot 'scripts\New-DcoirChatGPTFriendlyZip.ps1'
if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) { throw "Dcoir.Airtable module not found: $modulePath" }
Import-Module $modulePath -Force

$repoRoot = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_REPO_ROOT' -Required
$downloadsDir = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_DOWNLOADS_DIR' -Required
$apiToken = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_API_TOKEN' -Required
$baseId = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID' -Required

if (-not (Test-Path -LiteralPath $downloadsDir -PathType Container)) { New-Item -ItemType Directory -Force -Path $downloadsDir | Out-Null }

$tablesEnv = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TABLES' -Default $null
$rawTableList = if (-not [string]::IsNullOrWhiteSpace($TableList)) { $TableList } else { $tablesEnv }
$requestedTables = @()
if (-not [string]::IsNullOrWhiteSpace($rawTableList)) {
    $requestedTables = @($rawTableList -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$safePrefix = ConvertTo-DcoirAirtableSafeName -Text $OutputNamePrefix
$outRoot = Join-Path $downloadsDir ("{0}_{1}" -f $safePrefix, $stamp)
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null

$headers = New-DcoirAirtableAuthHeader -ApiToken $apiToken
$schema = Get-DcoirAirtableBaseSchema -BaseId $baseId -Headers $headers
$selectedTables = @(Select-DcoirAirtableTables -Schema $schema -RequestedTables $requestedTables)
if ($selectedTables.Count -eq 0) { throw 'No Airtable tables selected. Check DCOIR_AIRTABLE_TABLES or -TableList.' }

$schemaFolder = Join-Path $outRoot 'schema'
$recordsFolder = Join-Path $outRoot 'records'
New-Item -ItemType Directory -Force -Path $schemaFolder | Out-Null
if (-not $SchemaOnly) { New-Item -ItemType Directory -Force -Path $recordsFolder | Out-Null }

Save-DcoirAirtableJson -Path (Join-Path $schemaFolder 'schema.base_tables.json') -Object $schema
Save-DcoirAirtableJson -Path (Join-Path $schemaFolder 'schema.summary.json') -Object (Get-DcoirAirtableSchemaSummary -Tables $selectedTables)

$tableExports = New-Object System.Collections.Generic.List[object]
foreach ($table in $selectedTables) {
    $safeTable = ConvertTo-DcoirAirtableSafeName -Text ("{0}_{1}" -f $table.name, $table.id)
    Save-DcoirAirtableJson -Path (Join-Path $schemaFolder ("table.{0}.schema.json" -f $safeTable)) -Object $table
    $recordCount = $null
    if (-not $SchemaOnly) {
        $records = @(Get-DcoirAirtableRecords -BaseId $baseId -Table $table -Headers $headers -MaxRecords $MaxRecordsPerTable -RedactLikelySecrets:$RedactLikelySecrets)
        $recordCount = $records.Count
        Save-DcoirAirtableJson -Path (Join-Path $recordsFolder ("table.{0}.records.json" -f $safeTable)) -Object ([ordered]@{
            table_id = $table.id
            table_name = $table.name
            record_count_exported = $records.Count
            max_records_per_table = $MaxRecordsPerTable
            redacted_likely_secrets = [bool]$RedactLikelySecrets
            records = $records
        })
    }
    $tableExports.Add([pscustomobject]@{
        table_id = $table.id
        table_name = $table.name
        schema_file = "schema/table.$safeTable.schema.json"
        records_file = if ($SchemaOnly) { $null } else { "records/table.$safeTable.records.json" }
        record_count_exported = $recordCount
    }) | Out-Null
}

$manifest = [ordered]@{
    tool = 'New-DcoirAirtableDatabaseHealthExport.ps1'
    tool_version = $Script:DcoirAirtableExporterVersion
    module_version = Get-DcoirAirtableVersion
    created_at = (Get-Date -Format o)
    base_id_source = 'DCOIR_AIRTABLE_BASE_ID Machine/System environment variable'
    token_source = 'DCOIR_AIRTABLE_API_TOKEN Machine/System environment variable; value not exported'
    output_folder = $outRoot
    schema_only = [bool]$SchemaOnly
    redacted_likely_secrets = [bool]$RedactLikelySecrets
    max_records_per_table = $MaxRecordsPerTable
    requested_tables = $requestedTables
    selected_table_count = $selectedTables.Count
    selected_tables = @($tableExports.ToArray())
    safety = [ordered]@{
        read_only_airtable = $true
        token_value_written_to_output = $false
        likely_secret_field_redaction_enabled = [bool]$RedactLikelySecrets
        future_cleanup_governance = 'Review candidates in ChatGPT; use DCOIR Delete Queue and dependency order for any approved cleanup.'
    }
}
Save-DcoirAirtableJson -Path (Join-Path $outRoot 'export_manifest.json') -Object $manifest

$index = @(
    '# DCOIR Airtable Database Health Export',
    '',
    "Created: $($manifest.created_at)",
    "Tool version: $($manifest.tool_version)",
    "Schema only: $([bool]$SchemaOnly)",
    "Redacted likely secrets: $([bool]$RedactLikelySecrets)",
    "Max records per table: $MaxRecordsPerTable",
    "Selected tables: $($selectedTables.Count)",
    '',
    '## Fast triage files',
    '- export_manifest.json',
    '- schema/schema.summary.json',
    '- schema/schema.base_tables.json',
    '',
    '## Safety notes',
    '- The Airtable API token value is not written to this export.',
    '- Use -RedactLikelySecrets when exporting record data.',
    '- Any cleanup recommendation from downstream analysis must go through the DCOIR Delete Queue workflow.',
    '',
    '## Selected tables'
)
foreach ($table in $selectedTables) { $index += ("- {0} ({1})" -f $table.name, $table.id) }
Save-DcoirAirtableText -Path (Join-Path $outRoot 'diagnostic_index.md') -Text ($index -join "`n")

$zipPath = $null
if (-not $NoZip) {
    if (-not (Test-Path -LiteralPath $zipScript -PathType Leaf)) { throw "ChatGPT-friendly ZIP helper not found: $zipScript" }
    $zipPath = Join-Path $downloadsDir ("{0}_{1}.chatgpt.zip" -f $safePrefix, $stamp)
    & $zipScript -SourceFolder $outRoot -OutputZip $zipPath -IndexTitle 'DCOIR Airtable Database Health Export' -NormalizeTextEncoding | Out-Null
}

$result = [pscustomobject]@{
    output_folder = $outRoot
    output_zip = $zipPath
    schema_only = [bool]$SchemaOnly
    redacted_likely_secrets = [bool]$RedactLikelySecrets
    selected_table_count = $selectedTables.Count
    max_records_per_table = $MaxRecordsPerTable
}
$result | ConvertTo-Json -Depth 5
