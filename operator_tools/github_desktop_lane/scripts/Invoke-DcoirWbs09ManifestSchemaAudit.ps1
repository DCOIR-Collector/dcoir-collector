[CmdletBinding()]
param(
    [string]$ManifestPath,
    [Parameter(Mandatory=$true)][string]$SchemaJson,
    [string]$OutputDir,
    [switch]$FailOnWarnings,
    [switch]$AllowSchemaWithoutSelectChoices
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$Version = '2026-05-09.draft2-simple-schema-normalizer'
$BaseId = 'appM4KSwnVf3G3OTK'

function Get-MachineEnvRequired {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    if ([string]::IsNullOrWhiteSpace($value)) { throw "Missing required Machine/System environment variable: $Name" }
    if ($value -match 'C:\\path\\to\\|/path/to/') { throw "Refusing placeholder value for ${Name}: $value" }
    return $value
}

function Write-Utf8Json {
    param([string]$Path, [object]$Value)
    $json = $Value | ConvertTo-Json -Depth 100
    Set-Content -LiteralPath $Path -Value $json -Encoding UTF8
}

function Get-PropValue {
    param([object]$Obj, [string]$Name)
    if ($null -eq $Obj) { return $null }
    $prop = $Obj.PSObject.Properties[$Name]
    if ($null -eq $prop) { return $null }
    return $prop.Value
}

function Get-ArrayItems {
    param([object]$Value)
    if ($null -eq $Value) { return @() }
    if ($Value -is [string]) { return @($Value) }
    if ($Value -is [System.Collections.IEnumerable]) { return @($Value) }
    return @($Value)
}

function Normalize-StringList {
    param([object]$Value)
    $out = @()
    foreach ($item in @(Get-ArrayItems -Value $Value)) {
        if ($null -eq $item) { continue }
        if ($item -is [string] -and -not [string]::IsNullOrWhiteSpace($item)) { $out += [string]$item }
    }
    return @($out)
}

function Get-ChoiceNames {
    param([object]$Field)
    $choices = @()
    $config = Get-PropValue -Obj $Field -Name 'config'
    if ($null -ne $config) {
        $c = Get-PropValue -Obj $config -Name 'choices'
        if ($null -ne $c) { $choices += @(Get-ArrayItems -Value $c) }
    }
    $options = Get-PropValue -Obj $Field -Name 'options'
    if ($null -ne $options) {
        $c = Get-PropValue -Obj $options -Name 'choices'
        if ($null -ne $c) { $choices += @(Get-ArrayItems -Value $c) }
    }
    $names = @()
    foreach ($choice in $choices) {
        $name = Get-PropValue -Obj $choice -Name 'name'
        if (-not [string]::IsNullOrWhiteSpace([string]$name)) { $names += [string]$name }
    }
    return @($names)
}

function Get-FirstTablesArray {
    param([object]$Schema)

    $candidates = @(
        (Get-PropValue -Obj $Schema -Name 'tables'),
        (Get-PropValue -Obj (Get-PropValue -Obj $Schema -Name 'schema') -Name 'tables'),
        (Get-PropValue -Obj (Get-PropValue -Obj $Schema -Name 'base_schema') -Name 'tables'),
        (Get-PropValue -Obj (Get-PropValue -Obj $Schema -Name 'baseSchema') -Name 'tables')
    )

    foreach ($candidate in $candidates) {
        $arr = @(Get-ArrayItems -Value $candidate)
        if ($arr.Count -eq 0) { continue }
        foreach ($t in $arr) {
            $fields = Get-PropValue -Obj $t -Name 'fields'
            if ($null -ne $fields) { return @($arr) }
        }
    }

    throw 'Schema JSON does not contain a recognizable tables array with field metadata. Expected top-level tables or schema.tables.'
}

function Normalize-SchemaTables {
    param([object]$Schema)
    $rawTables = @(Get-FirstTablesArray -Schema $Schema)
    $tables = @()
    foreach ($t in $rawTables) {
        $id = Get-PropValue -Obj $t -Name 'id'
        if ($null -eq $id) { $id = Get-PropValue -Obj $t -Name 'tableId' }
        if ($null -eq $id) { $id = Get-PropValue -Obj $t -Name 'table_id' }
        $name = Get-PropValue -Obj $t -Name 'name'
        if ($null -eq $name) { $name = Get-PropValue -Obj $t -Name 'tableName' }
        if ($null -eq $name) { $name = Get-PropValue -Obj $t -Name 'table_name' }
        $fields = @(Get-ArrayItems -Value (Get-PropValue -Obj $t -Name 'fields'))
        if ([string]::IsNullOrWhiteSpace([string]$id) -and [string]::IsNullOrWhiteSpace([string]$name)) { continue }
        if ($fields.Count -eq 0) { continue }
        $tables += [pscustomobject]@{ id = [string]$id; name = [string]$name; fields = $fields }
    }
    if ($tables.Count -eq 0) { throw 'No schema tables found after normalization.' }
    return @($tables)
}

function New-Issue {
    param([string]$Severity, [string]$ViewKey, [string]$IssueType, [string]$Message, [object]$Details)
    return [pscustomobject]@{
        severity = $Severity
        view_key = $ViewKey
        issue_type = $IssueType
        message = $Message
        details = $Details
    }
}

$repo = Get-MachineEnvRequired -Name 'DCOIR_REPO_ROOT'
$downloads = Get-MachineEnvRequired -Name 'DCOIR_DOWNLOADS_DIR'
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw "DCOIR_REPO_ROOT does not exist or is not a directory: $repo" }
if (-not (Test-Path -LiteralPath $downloads -PathType Container)) { throw "DCOIR_DOWNLOADS_DIR does not exist or is not a directory: $downloads" }

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $ManifestPath = Join-Path $repo 'operator_tools\github_desktop_lane\manifests\wbs09_airtable_native_views_manifest.json'
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw "Manifest not found: $ManifestPath" }
if (-not (Test-Path -LiteralPath $SchemaJson -PathType Leaf)) { throw "Schema JSON not found: $SchemaJson" }

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $downloads ('dcoir_wbs09_manifest_schema_audit_' + $timestamp)
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$logPath = Join-Path $OutputDir 'audit.log'
function Write-AuditLog {
    param([string]$Message)
    $line = ('{0} {1}' -f (Get-Date).ToUniversalTime().ToString('o'), $Message)
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
    Write-Host $line
}

Write-AuditLog "Starting WBS09 manifest schema audit. Version=$Version"
Write-AuditLog "Manifest: $ManifestPath"
Write-AuditLog "Schema JSON: $SchemaJson"
Write-AuditLog "OutputDir: $OutputDir"

$manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$schema = Get-Content -LiteralPath $SchemaJson -Raw | ConvertFrom-Json

$views = @(Get-ArrayItems -Value (Get-PropValue -Obj $manifest -Name 'views'))
if ($views.Count -eq 0) { throw 'Manifest contains no views array.' }
$tables = @(Normalize-SchemaTables -Schema $schema)

$tableById = @{}
$tableByNameLower = @{}
foreach ($t in $tables) {
    if (-not [string]::IsNullOrWhiteSpace($t.id)) { $tableById[$t.id] = $t }
    if (-not [string]::IsNullOrWhiteSpace($t.name)) { $tableByNameLower[$t.name.ToLowerInvariant()] = $t }
}

$issues = @()
$viewResults = @()
$filterOperators = @('=','!=','is one of','is not one of','contains','does not contain','is empty','is not empty','on or before','on or after','before','after')
$sortableTypes = @('singleLineText','multilineText','number','date','dateTime','singleSelect','multipleSelects','checkbox','formula','rollup','lookup','createdTime','lastModifiedTime','autoNumber','url','email','phoneNumber','currency','percent','duration','rating')

foreach ($view in $views) {
    $viewName = [string](Get-PropValue -Obj $view -Name 'view_name')
    $tableId = [string](Get-PropValue -Obj $view -Name 'table_id')
    $tableName = [string](Get-PropValue -Obj $view -Name 'table_name')
    $viewKey = [string](Get-PropValue -Obj $view -Name 'view_key')
    if ([string]::IsNullOrWhiteSpace($viewKey)) { $viewKey = "$tableName::$viewName" }

    $viewErrorsBefore = @($issues | Where-Object { $_.severity -eq 'error' }).Count
    $viewWarningsBefore = @($issues | Where-Object { $_.severity -eq 'warning' }).Count

    $table = $null
    if (-not [string]::IsNullOrWhiteSpace($tableId) -and $tableById.ContainsKey($tableId)) { $table = $tableById[$tableId] }
    elseif (-not [string]::IsNullOrWhiteSpace($tableName) -and $tableByNameLower.ContainsKey($tableName.ToLowerInvariant())) { $table = $tableByNameLower[$tableName.ToLowerInvariant()] }

    if ($null -eq $table) {
        $issues += New-Issue -Severity 'error' -ViewKey $viewKey -IssueType 'missing_table' -Message "Table not found: $tableName / $tableId" -Details @{ table_name = $tableName; table_id = $tableId }
        $viewResults += [pscustomobject]@{ view_key = $viewKey; view_name = $viewName; table_name = $tableName; table_id = $tableId; status = 'FAIL'; filter_count = 0; sort_count = 0 }
        continue
    }

    $fieldByNameLower = @{}
    $fieldById = @{}
    foreach ($field in @(Get-ArrayItems -Value $table.fields)) {
        $fid = Get-PropValue -Obj $field -Name 'id'
        if ($null -eq $fid) { $fid = Get-PropValue -Obj $field -Name 'fieldId' }
        $fname = Get-PropValue -Obj $field -Name 'name'
        if ($null -ne $fid) { $fieldById[[string]$fid] = $field }
        if ($null -ne $fname) { $fieldByNameLower[[string]$fname.ToLowerInvariant()] = $field }
    }

    foreach ($filter in @(Get-ArrayItems -Value (Get-PropValue -Obj $view -Name 'filters'))) {
        $fieldName = [string](Get-PropValue -Obj $filter -Name 'field')
        $operator = [string](Get-PropValue -Obj $filter -Name 'operator')
        $value = Get-PropValue -Obj $filter -Name 'value'
        if ([string]::IsNullOrWhiteSpace($fieldName)) {
            $issues += New-Issue -Severity 'error' -ViewKey $viewKey -IssueType 'missing_filter_field_name' -Message 'Filter is missing field name.' -Details $filter
            continue
        }
        if (-not $fieldByNameLower.ContainsKey($fieldName.ToLowerInvariant())) {
            $issues += New-Issue -Severity 'error' -ViewKey $viewKey -IssueType 'missing_filter_field' -Message "Filter field not found: $fieldName" -Details @{ field = $fieldName }
            continue
        }
        $field = $fieldByNameLower[$fieldName.ToLowerInvariant()]
        $fieldType = [string](Get-PropValue -Obj $field -Name 'type')
        if (-not [string]::IsNullOrWhiteSpace($operator) -and ($filterOperators -notcontains $operator)) {
            $issues += New-Issue -Severity 'warning' -ViewKey $viewKey -IssueType 'unknown_filter_operator' -Message "Filter operator not in allow-list: $operator" -Details @{ field = $fieldName; operator = $operator }
        }
        if ($fieldType -eq 'singleSelect' -or $fieldType -eq 'multipleSelects') {
            $values = @(Normalize-StringList -Value $value)
            if ($values.Count -gt 0) {
                $choices = @(Get-ChoiceNames -Field $field)
                if ($choices.Count -eq 0) {
                    $severity = 'error'
                    if ($AllowSchemaWithoutSelectChoices) { $severity = 'warning' }
                    $issues += New-Issue -Severity $severity -ViewKey $viewKey -IssueType 'select_choices_unavailable' -Message "Select field '$fieldName' has no choices in schema JSON; cannot verify values." -Details @{ field = $fieldName; values = $values }
                } else {
                    foreach ($v in $values) {
                        if ($choices -notcontains $v) {
                            $issues += New-Issue -Severity 'error' -ViewKey $viewKey -IssueType 'invalid_select_value' -Message "Invalid select value '$v' for field '$fieldName'." -Details @{ field = $fieldName; value = $v; valid_values = $choices }
                        }
                    }
                }
            }
        } elseif ($fieldType -eq 'checkbox') {
            if ($null -ne $value -and -not ($value -is [bool])) {
                $issues += New-Issue -Severity 'error' -ViewKey $viewKey -IssueType 'invalid_checkbox_value' -Message "Checkbox filter '$fieldName' must use true/false." -Details @{ field = $fieldName; value = $value }
            }
        }
    }

    foreach ($sort in @(Get-ArrayItems -Value (Get-PropValue -Obj $view -Name 'sorts'))) {
        $fieldName = [string](Get-PropValue -Obj $sort -Name 'field')
        $direction = [string](Get-PropValue -Obj $sort -Name 'direction')
        if ([string]::IsNullOrWhiteSpace($fieldName)) {
            $issues += New-Issue -Severity 'error' -ViewKey $viewKey -IssueType 'missing_sort_field_name' -Message 'Sort is missing field name.' -Details $sort
            continue
        }
        if (-not $fieldByNameLower.ContainsKey($fieldName.ToLowerInvariant())) {
            $issues += New-Issue -Severity 'error' -ViewKey $viewKey -IssueType 'missing_sort_field' -Message "Sort field not found: $fieldName" -Details @{ field = $fieldName }
            continue
        }
        $field = $fieldByNameLower[$fieldName.ToLowerInvariant()]
        $fieldType = [string](Get-PropValue -Obj $field -Name 'type')
        if ($sortableTypes -notcontains $fieldType) {
            $issues += New-Issue -Severity 'warning' -ViewKey $viewKey -IssueType 'possibly_unsortable_field_type' -Message "Sort field '$fieldName' has possibly unsupported type '$fieldType'." -Details @{ field = $fieldName; type = $fieldType }
        }
        if ($direction -ne 'asc' -and $direction -ne 'desc') {
            $issues += New-Issue -Severity 'error' -ViewKey $viewKey -IssueType 'invalid_sort_direction' -Message "Sort direction must be asc or desc for field '$fieldName'." -Details @{ field = $fieldName; direction = $direction }
        }
    }

    $viewErrorsAfter = @($issues | Where-Object { $_.severity -eq 'error' }).Count
    $viewWarningsAfter = @($issues | Where-Object { $_.severity -eq 'warning' }).Count
    $status = 'PASS'
    if ($viewErrorsAfter -gt $viewErrorsBefore) { $status = 'FAIL' }
    elseif ($viewWarningsAfter -gt $viewWarningsBefore) { $status = 'PASS_WITH_WARNINGS' }
    $viewResults += [pscustomobject]@{
        view_key = $viewKey
        view_name = $viewName
        table_name = $table.name
        table_id = $table.id
        status = $status
        filter_count = @(Get-ArrayItems -Value (Get-PropValue -Obj $view -Name 'filters')).Count
        sort_count = @(Get-ArrayItems -Value (Get-PropValue -Obj $view -Name 'sorts')).Count
    }
}

$errorCount = @($issues | Where-Object { $_.severity -eq 'error' }).Count
$warningCount = @($issues | Where-Object { $_.severity -eq 'warning' }).Count
$status = 'PASS'
if ($errorCount -gt 0) { $status = 'FAIL' }
elseif ($warningCount -gt 0) { $status = 'PASS_WITH_WARNINGS' }

$report = [pscustomobject]@{
    timestamp_utc = (Get-Date).ToUniversalTime().ToString('o')
    tool_version = $Version
    base_id = $BaseId
    status = $status
    manifest_path = $ManifestPath
    schema_json = $SchemaJson
    output_dir = $OutputDir
    table_count_schema = $tables.Count
    manifest_view_count = $views.Count
    valid_view_count = @($viewResults | Where-Object { $_.status -eq 'PASS' }).Count
    warning_view_count = @($viewResults | Where-Object { $_.status -eq 'PASS_WITH_WARNINGS' }).Count
    failing_view_count = @($viewResults | Where-Object { $_.status -eq 'FAIL' }).Count
    error_count = $errorCount
    warning_count = $warningCount
    fail_on_warnings = [bool]$FailOnWarnings
    allow_schema_without_select_choices = [bool]$AllowSchemaWithoutSelectChoices
    view_results = @($viewResults)
    issues = @($issues)
}

$jsonPath = Join-Path $OutputDir 'wbs09_manifest_schema_audit.json'
$mdPath = Join-Path $OutputDir 'wbs09_manifest_schema_audit.md'
Write-Utf8Json -Path $jsonPath -Value $report

$md = @()
$md += '# WBS09 Manifest Schema Audit'
$md += ''
$md += ('- Status: {0}' -f $status)
$md += ('- Tool version: {0}' -f $Version)
$md += ('- Manifest views: {0}' -f $views.Count)
$md += ('- Valid views: {0}' -f $report.valid_view_count)
$md += ('- Warning views: {0}' -f $report.warning_view_count)
$md += ('- Failing views: {0}' -f $report.failing_view_count)
$md += ('- Errors: {0}' -f $errorCount)
$md += ('- Warnings: {0}' -f $warningCount)
$md += ''
$md += '## Issues'
if ($issues.Count -eq 0) {
    $md += 'No blocking errors or warnings were found.'
} else {
    foreach ($issue in $issues) {
        $md += ('- **{0}** `{1}` - {2}: {3}' -f $issue.severity.ToUpperInvariant(), $issue.view_key, $issue.issue_type, $issue.message)
    }
}
$md += ''
$md += '## View Results'
foreach ($vr in $viewResults) {
    $md += ('- `{0}` - {1}' -f $vr.view_key, $vr.status)
}
Set-Content -LiteralPath $mdPath -Value $md -Encoding UTF8

Write-AuditLog "Audit complete. Status=$status Errors=$errorCount Warnings=$warningCount"
Write-Host "Audit JSON: $jsonPath"
Write-Host "Audit Markdown: $mdPath"

if ($errorCount -gt 0) { exit 2 }
if ($FailOnWarnings -and $warningCount -gt 0) { exit 3 }
exit 0
