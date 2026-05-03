[CmdletBinding()]
param(
    [switch]$SchemaOnly,
    [ValidateSet('Auto','SchemaOnly','BoundedRecords','FullRecords')][string]$ExportMode = 'Auto',
    [switch]$FullRecordDump,
    [switch]$SkipRecords,
    [switch]$RedactLikelySecrets,
    [int]$MaxRecordsPerTable = 0,
    [string]$MetadataScope = 'BaseSchema,Tables,Fields,Views',
    [switch]$ProbeUnsupportedMetadata,
    [string]$OutputNamePrefix = 'dcoir_airtable_health_export',
    [string]$TableList,
    [switch]$NoZip
)

$ErrorActionPreference = 'Stop'
$Script:DcoirAirtableExporterVersion = '2026-05-03.5'

function ConvertTo-DcoirLocalSafeName {
    [CmdletBinding()]
    param([AllowNull()][string]$Text)
    if ($null -eq $Text) { return '' }
    return (($Text -replace '[^A-Za-z0-9_.-]', '_').Trim('_'))
}

function Write-DcoirLocalText {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path, [AllowNull()][string]$Text)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, [string]$Text, $enc)
}

function Write-DcoirLocalJson {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path, [Parameter(Mandatory=$true)]$Object, [int]$Depth = 80)
    Write-DcoirLocalText -Path $Path -Text ($Object | ConvertTo-Json -Depth $Depth)
}

function Add-DcoirLocalLine {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path, [AllowNull()][string]$Text)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::AppendAllText($Path, ([string]$Text) + [Environment]::NewLine, $enc)
}

function Get-DcoirMachineEnvPresence {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    return [pscustomobject]@{
        name = $Name
        present = -not [string]::IsNullOrWhiteSpace($value)
        value_exported = $false
        source = 'Machine/System environment variable'
    }
}

function New-DcoirEmergencyDownloadsDir {
    [CmdletBinding()]
    param()
    $downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR', 'Machine')
    if (-not [string]::IsNullOrWhiteSpace($downloads)) { return $downloads.Trim() }
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        $candidate = Join-Path $env:USERPROFILE 'Downloads'
        if (Test-Path -LiteralPath $candidate -PathType Container) { return $candidate }
    }
    return (Get-Location).Path
}

function Write-DcoirRunStatus {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Message)
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    if ($script:RunLogPath) { Add-DcoirLocalLine -Path $script:RunLogPath -Text $line }
}

function New-DcoirFailureZip {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$OutRoot,
        [Parameter(Mandatory=$true)][string]$ZipPath,
        [AllowNull()][string]$ZipScript
    )
    if ($NoZip) { return $null }
    try {
        if ($ZipScript -and (Test-Path -LiteralPath $ZipScript -PathType Leaf)) {
            & $ZipScript -SourceFolder $OutRoot -OutputZip $ZipPath -IndexTitle 'DCOIR Airtable Database Health Export Diagnostic' -NormalizeTextEncoding | Out-Null
            return $ZipPath
        }
        if (Test-Path -LiteralPath $ZipPath -PathType Leaf) { Remove-Item -LiteralPath $ZipPath -Force }
        Compress-Archive -LiteralPath (Join-Path $OutRoot '*') -DestinationPath $ZipPath -Force
        return $ZipPath
    }
    catch {
        Write-DcoirRunStatus ("ZIP creation failed: {0}" -f $_.Exception.Message)
        return $null
    }
}

function Resolve-DcoirAirtableExportOptions {
    [CmdletBinding()]
    param(
        [bool]$SchemaOnlyFlag,
        [string]$RequestedExportMode,
        [bool]$FullRecordDumpFlag,
        [bool]$SkipRecordsFlag,
        [int]$RequestedMaxRecordsPerTable,
        [AllowNull()][string]$RequestedMetadataScope
    )

    $mode = $RequestedExportMode
    if ($SchemaOnlyFlag -or $SkipRecordsFlag) { $mode = 'SchemaOnly' }
    elseif ($FullRecordDumpFlag) { $mode = 'FullRecords' }
    elseif ($mode -eq 'Auto') {
        if ($RequestedMaxRecordsPerTable -gt 0) { $mode = 'BoundedRecords' } else { $mode = 'FullRecords' }
    }

    $effectiveMax = 0
    if ($mode -eq 'BoundedRecords') {
        if ($RequestedMaxRecordsPerTable -gt 0) { $effectiveMax = $RequestedMaxRecordsPerTable } else { $effectiveMax = 25 }
    }
    elseif ($mode -eq 'FullRecords') { $effectiveMax = 0 }

    $metadata = @{}
    $tokens = @()
    if ([string]::IsNullOrWhiteSpace($RequestedMetadataScope)) {
        $tokens = @('BaseSchema','Tables','Fields','Views')
    }
    else {
        $tokens = @($RequestedMetadataScope -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }
    foreach ($token in $tokens) { $metadata[$token.ToLowerInvariant()] = $true }
    if ($metadata.ContainsKey('all')) {
        foreach ($token in @('baseschema','tables','fields','views')) { $metadata[$token] = $true }
    }

    return [pscustomobject]@{
        export_mode = $mode
        include_records = ($mode -ne 'SchemaOnly')
        effective_max_records_per_table = $effectiveMax
        full_record_dump = ($mode -eq 'FullRecords')
        bounded_record_dump = ($mode -eq 'BoundedRecords')
        include_base_schema_file = ($metadata.ContainsKey('baseschema') -or $metadata.ContainsKey('tables') -or $metadata.ContainsKey('fields') -or $metadata.ContainsKey('views'))
        include_schema_summary = ($metadata.ContainsKey('tables') -or $metadata.ContainsKey('fields') -or $metadata.ContainsKey('views'))
        include_table_schema_files = ($metadata.ContainsKey('tables') -or $metadata.ContainsKey('fields') -or $metadata.ContainsKey('views'))
        metadata_scope_requested = @($tokens)
        metadata_scope_effective = @($metadata.Keys | Sort-Object)
    }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$toolRoot = Split-Path -Parent $scriptRoot
$modulePath = Join-Path $toolRoot 'modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
$zipScript = Join-Path $toolRoot 'scripts\New-DcoirChatGPTFriendlyZip.ps1'
$safePrefix = ConvertTo-DcoirLocalSafeName -Text $OutputNamePrefix
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$downloadsDir = New-DcoirEmergencyDownloadsDir
if (-not (Test-Path -LiteralPath $downloadsDir -PathType Container)) { New-Item -ItemType Directory -Force -Path $downloadsDir | Out-Null }
$outRoot = Join-Path $downloadsDir ("{0}_{1}" -f $safePrefix, $stamp)
New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
$script:RunLogPath = Join-Path $outRoot 'run.log.txt'
$transcriptPath = Join-Path $outRoot 'terminal_transcript.txt'
$zipPath = Join-Path $downloadsDir ("{0}_{1}.chatgpt.zip" -f $safePrefix, $stamp)
$transcriptStarted = $false
$success = $false
$resultObject = $null
$resolvedOptions = Resolve-DcoirAirtableExportOptions -SchemaOnlyFlag ([bool]$SchemaOnly) -RequestedExportMode $ExportMode -FullRecordDumpFlag ([bool]$FullRecordDump) -SkipRecordsFlag ([bool]$SkipRecords) -RequestedMaxRecordsPerTable $MaxRecordsPerTable -RequestedMetadataScope $MetadataScope

try {
    try {
        Start-Transcript -LiteralPath $transcriptPath -Force | Out-Null
        $transcriptStarted = $true
    }
    catch {
        Add-DcoirLocalLine -Path $script:RunLogPath -Text ("Transcript start failed: {0}" -f $_.Exception.Message)
    }

    Write-DcoirRunStatus 'Starting DCOIR Airtable database health export.'
    Write-DcoirRunStatus "Output folder: $outRoot"
    Write-DcoirRunStatus "Output ZIP target: $zipPath"
    Write-DcoirRunStatus ("Resolved export mode: {0}; effective max records per table: {1}" -f $resolvedOptions.export_mode, $resolvedOptions.effective_max_records_per_table)

    $environmentPresence = @(
        Get-DcoirMachineEnvPresence -Name 'DCOIR_REPO_ROOT'
        Get-DcoirMachineEnvPresence -Name 'DCOIR_DOWNLOADS_DIR'
        Get-DcoirMachineEnvPresence -Name 'DCOIR_AIRTABLE_TOKEN'
        Get-DcoirMachineEnvPresence -Name 'DCOIR_AIRTABLE_BASE_ID'
    )

    $context = [ordered]@{
        tool = 'New-DcoirAirtableDatabaseHealthExport.ps1'
        tool_version = $Script:DcoirAirtableExporterVersion
        started_at = (Get-Date -Format o)
        current_directory = (Get-Location).Path
        script_path = $MyInvocation.MyCommand.Path
        module_path = $modulePath
        zip_script_path = $zipScript
        output_folder = $outRoot
        output_zip_target = $zipPath
        powershell = [ordered]@{
            version = $PSVersionTable.PSVersion.ToString()
            edition = $PSVersionTable.PSEdition
            platform = $PSVersionTable.Platform
        }
        machine = [ordered]@{
            computer_name = $env:COMPUTERNAME
            user_domain = $env:USERDOMAIN
            user_name = $env:USERNAME
        }
        parameters = [ordered]@{
            SchemaOnly = [bool]$SchemaOnly
            ExportMode = $ExportMode
            FullRecordDump = [bool]$FullRecordDump
            SkipRecords = [bool]$SkipRecords
            RedactLikelySecrets = [bool]$RedactLikelySecrets
            MaxRecordsPerTable = $MaxRecordsPerTable
            MetadataScope = $MetadataScope
            ProbeUnsupportedMetadata = [bool]$ProbeUnsupportedMetadata
            OutputNamePrefix = $OutputNamePrefix
            TableListProvided = -not [string]::IsNullOrWhiteSpace($TableList)
            NoZip = [bool]$NoZip
        }
        resolved_options = $resolvedOptions
        environment_presence = $environmentPresence
        secrets_policy = 'Only environment variable presence is logged. Secret values and base identifier values are not written by this context capture.'
    }
    Write-DcoirLocalJson -Path (Join-Path $outRoot 'command_context.json') -Object $context

    if (-not (Test-Path -LiteralPath $modulePath -PathType Leaf)) { throw "Dcoir.Airtable module not found: $modulePath" }
    Import-Module $modulePath -Force
    Write-DcoirRunStatus ("Imported Dcoir.Airtable module version {0}." -f (Get-DcoirAirtableVersion))

    $repoRoot = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_REPO_ROOT' -Required
    $configuredDownloadsDir = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_DOWNLOADS_DIR' -Required
    $apiToken = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TOKEN' -Required
    $baseId = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID' -Required

    Write-DcoirRunStatus 'Required Machine/System environment variables are present.'
    if ($configuredDownloadsDir -ne $downloadsDir) {
        Write-DcoirRunStatus "Initial diagnostic folder was created under fallback downloads path before DCOIR_DOWNLOADS_DIR validation: $downloadsDir"
    }

    $requestedTables = @()
    if (-not [string]::IsNullOrWhiteSpace($TableList)) {
        $requestedTables = @($TableList -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    }

    $headers = New-DcoirAirtableAuthHeader -ApiToken $apiToken
    Write-DcoirRunStatus 'Fetching Airtable base schema.'
    $schema = Get-DcoirAirtableBaseSchema -BaseId $baseId -Headers $headers
    $selectedTables = @(Select-DcoirAirtableTables -Schema $schema -RequestedTables $requestedTables)
    if ($selectedTables.Count -eq 0) { throw 'No Airtable tables selected. Check -TableList.' }
    Write-DcoirRunStatus ("Selected {0} Airtable table(s)." -f $selectedTables.Count)

    $schemaFolder = Join-Path $outRoot 'schema'
    $recordsFolder = Join-Path $outRoot 'records'
    $metadataFolder = Join-Path $outRoot 'metadata'
    New-Item -ItemType Directory -Force -Path $schemaFolder | Out-Null
    New-Item -ItemType Directory -Force -Path $metadataFolder | Out-Null
    if ($resolvedOptions.include_records) { New-Item -ItemType Directory -Force -Path $recordsFolder | Out-Null }

    if ($resolvedOptions.include_base_schema_file) { Write-DcoirAirtableJson -Path (Join-Path $schemaFolder 'schema.base_tables.json') -Object $schema }
    if ($resolvedOptions.include_schema_summary) { Write-DcoirAirtableJson -Path (Join-Path $schemaFolder 'schema.summary.json') -Object (Get-DcoirAirtableSchemaSummary -Tables $selectedTables) }

    $unsupportedMetadata = [ordered]@{
        created_at = (Get-Date -Format o)
        probe_requested = [bool]$ProbeUnsupportedMetadata
        note = 'This exporter currently captures Airtable Web API-accessible base schema, table metadata, field metadata/options, view metadata, and records. Automations, extensions/apps, interface designer objects, scripting extension code, and certain workspace/base admin surfaces are not exported unless a supported Airtable API endpoint and token scope are added.'
        unsupported_or_not_yet_implemented = @('automations','extensions_or_apps','interfaces','scripting_extension_code','workspace_admin_inventory')
        current_supported_metadata = @('base tables schema','table id/name/description/primaryFieldId','field id/name/type/description/options','view id/name/type','record id/createdTime/fields')
    }
    Write-DcoirLocalJson -Path (Join-Path $metadataFolder 'metadata_coverage.json') -Object $unsupportedMetadata

    $tableExports = New-Object System.Collections.Generic.List[object]
    foreach ($table in $selectedTables) {
        Write-DcoirRunStatus ("Exporting table schema: {0} ({1})" -f $table.name, $table.id)
        $safeTable = ConvertTo-DcoirAirtableSafeName -Text ("{0}_{1}" -f $table.name, $table.id)
        $schemaFile = $null
        if ($resolvedOptions.include_table_schema_files) {
            $schemaFile = "schema/table.$safeTable.schema.json"
            Write-DcoirAirtableJson -Path (Join-Path $schemaFolder ("table.{0}.schema.json" -f $safeTable)) -Object $table
        }
        $recordCount = $null
        $recordsFile = $null
        if ($resolvedOptions.include_records) {
            Write-DcoirRunStatus ("Exporting records: {0}" -f $table.name)
            $records = @(Get-DcoirAirtableRecords -BaseId $baseId -Table $table -Headers $headers -MaxRecords $resolvedOptions.effective_max_records_per_table -RedactLikelySecrets:$RedactLikelySecrets)
            $recordCount = $records.Count
            $recordsFile = "records/table.$safeTable.records.json"
            Write-DcoirAirtableJson -Path (Join-Path $recordsFolder ("table.{0}.records.json" -f $safeTable)) -Object ([ordered]@{
                table_id = $table.id
                table_name = $table.name
                export_mode = $resolvedOptions.export_mode
                record_count_exported = $records.Count
                max_records_per_table = $resolvedOptions.effective_max_records_per_table
                full_record_dump = [bool]$resolvedOptions.full_record_dump
                redacted_likely_secrets = [bool]$RedactLikelySecrets
                records = $records
            })
        }
        $tableExports.Add([pscustomobject]@{
            table_id = $table.id
            table_name = $table.name
            schema_file = $schemaFile
            records_file = $recordsFile
            record_count_exported = $recordCount
        }) | Out-Null
    }

    $manifest = [ordered]@{
        tool = 'New-DcoirAirtableDatabaseHealthExport.ps1'
        tool_version = $Script:DcoirAirtableExporterVersion
        module_version = Get-DcoirAirtableVersion
        created_at = (Get-Date -Format o)
        base_id_source = 'DCOIR_AIRTABLE_BASE_ID Machine/System environment variable; value not exported'
        token_source = 'DCOIR_AIRTABLE_TOKEN Machine/System environment variable; value not exported'
        output_folder = $outRoot
        schema_only = ($resolvedOptions.export_mode -eq 'SchemaOnly')
        export_mode = $resolvedOptions.export_mode
        full_record_dump = [bool]$resolvedOptions.full_record_dump
        include_records = [bool]$resolvedOptions.include_records
        redacted_likely_secrets = [bool]$RedactLikelySecrets
        max_records_per_table = $resolvedOptions.effective_max_records_per_table
        requested_tables = $requestedTables
        selected_table_count = $selectedTables.Count
        metadata_scope_requested = $resolvedOptions.metadata_scope_requested
        metadata_scope_effective = $resolvedOptions.metadata_scope_effective
        selected_tables = @($tableExports.ToArray())
        safety = [ordered]@{
            read_only_airtable = $true
            token_value_written_to_output = $false
            likely_secret_field_redaction_enabled = [bool]$RedactLikelySecrets
            future_cleanup_governance = 'Review candidates in ChatGPT; use DCOIR Delete Queue and dependency order for any approved cleanup.'
        }
    }
    Write-DcoirAirtableJson -Path (Join-Path $outRoot 'export_manifest.json') -Object $manifest

    $success = $true
    $resultObject = [ordered]@{
        success = $true
        output_folder = $outRoot
        output_zip = if ($NoZip) { $null } else { $zipPath }
        schema_only = ($resolvedOptions.export_mode -eq 'SchemaOnly')
        export_mode = $resolvedOptions.export_mode
        full_record_dump = [bool]$resolvedOptions.full_record_dump
        redacted_likely_secrets = [bool]$RedactLikelySecrets
        selected_table_count = $selectedTables.Count
        max_records_per_table = $resolvedOptions.effective_max_records_per_table
    }
    Write-DcoirRunStatus 'Airtable export completed successfully.'
}
catch {
    $resultObject = [ordered]@{
        success = $false
        output_folder = $outRoot
        output_zip = if ($NoZip) { $null } else { $zipPath }
        error_message = $_.Exception.Message
        error_type = $_.Exception.GetType().FullName
        phase = 'failed_before_or_during_export'
    }
    Write-DcoirRunStatus ("ERROR: {0}" -f $_.Exception.Message)
    Write-DcoirLocalJson -Path (Join-Path $outRoot 'error_report.json') -Object ([ordered]@{
        created_at = (Get-Date -Format o)
        tool = 'New-DcoirAirtableDatabaseHealthExport.ps1'
        tool_version = $Script:DcoirAirtableExporterVersion
        error_message = $_.Exception.Message
        error_type = $_.Exception.GetType().FullName
        script_stack_trace = $_.ScriptStackTrace
        invocation = [ordered]@{
            script_name = $MyInvocation.MyCommand.Name
            script_path = $MyInvocation.MyCommand.Path
            current_directory = (Get-Location).Path
        }
        environment_presence = $environmentPresence
        secrets_policy = 'No secret values are logged. Only presence/absence is captured.'
    })
    $errMd = @(
        '# DCOIR Airtable Database Health Export - Error Report',
        '',
        "Created: $(Get-Date -Format o)",
        "Tool version: $Script:DcoirAirtableExporterVersion",
        '',
        '## Error',
        '```text',
        $_.Exception.Message,
        '```',
        '',
        '## What to upload',
        '- Upload the `.chatgpt.zip` produced next to this run folder if it exists.',
        '- If the ZIP was not created, upload this entire run folder or the files inside it.',
        '',
        '## Secrets policy',
        '- The Airtable API token value is not written to this diagnostic output.',
        '- The diagnostic captures only environment variable presence/absence.'
    )
    Write-DcoirLocalText -Path (Join-Path $outRoot 'error_report.md') -Text ($errMd -join "`n")
}
finally {
    $finishedAt = Get-Date -Format o
    if ($resultObject) {
        $resultObject.finished_at = $finishedAt
        Write-DcoirLocalJson -Path (Join-Path $outRoot 'run_summary.json') -Object $resultObject
    }

    $indexLines = @(
        '# DCOIR Airtable Database Health Export Diagnostic',
        '',
        "Created: $finishedAt",
        "Tool version: $Script:DcoirAirtableExporterVersion",
        "Success: $success",
        "Output folder: $outRoot",
        "Output ZIP: $zipPath",
        '',
        '## Fast triage files',
        '- run_summary.json',
        '- command_context.json',
        '- run.log.txt',
        '- terminal_transcript.txt',
        '- error_report.md / error_report.json when present',
        '- export_manifest.json when export succeeded',
        '- metadata/metadata_coverage.json',
        '- schema/schema.summary.json when schema export succeeded',
        '',
        '## Operator note',
        'This tool intentionally creates this diagnostic folder and ZIP even when configuration validation fails early, so ChatGPT can review the exact terminal/run context without requiring screenshots.'
    )
    Write-DcoirLocalText -Path (Join-Path $outRoot 'diagnostic_index.md') -Text ($indexLines -join "`n")

    if ($transcriptStarted) {
        try { Stop-Transcript | Out-Null } catch { }
    }

    if (-not $NoZip) {
        $createdZip = New-DcoirFailureZip -OutRoot $outRoot -ZipPath $zipPath -ZipScript $zipScript
        if ($resultObject) {
            $resultObject.output_zip = $createdZip
            Write-DcoirLocalJson -Path (Join-Path $outRoot 'run_summary.json') -Object $resultObject
        }
    }

    if ($resultObject) { $resultObject | ConvertTo-Json -Depth 8 }
    if (-not $success) { exit 1 }
}
