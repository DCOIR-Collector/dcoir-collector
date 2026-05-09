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

$Version = '2026-05-09.draft1-schema-gate'
$BaseId = 'appM4KSwnVf3G3OTK'

function Get-MachineEnvRequired {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    if ([string]::IsNullOrWhiteSpace($value)) { throw "Missing required Machine/System environment variable: $Name" }
    if ($value -match 'C:\\path\\to\\|/path/to/') { throw "Refusing placeholder value for $Name: $value" }
    return $value
}

function Write-Utf8Json {
    param([string]$Path, [object]$Value)
    $json = $Value | ConvertTo-Json -Depth 100
    Set-Content -LiteralPath $Path -Value $json -Encoding UTF8
}

function Get-ArrayItems {
    param([object]$Value)
    if ($null -eq $Value) { return @() }
    if ($Value -is [System.Array]) { return @($Value) }
    return @($Value)
}

function Get-PropValue {
    param([object]$Obj, [string]$Name)
    if ($null -eq $Obj) { return $null }
    $prop = $Obj.PSObject.Properties[$Name]
    if ($null -eq $prop) { return $null }
    return $prop.Value
}

function Normalize-StringList {
    param([object]$Value)
    $items = Get-ArrayItems $Value
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($item in $items) {
        if ($null -eq $item) { continue }
        if ($item -is [string]) {
            if (-not [string]::IsNullOrWhiteSpace($item)) { [void]$out.Add($item) }
        }
    }
    return @($out)
}

function Get-ChoiceNames {
    param([object]$Field)
    $choices = @()
    $config = Get-PropValue $Field 'config'
    if ($null -ne $config) {
        $c = Get-PropValue $config 'choices'
        if ($null -ne $c) { $choices += @(Get-ArrayItems $c) }
    }
    $options = Get-PropValue $Field 'options'
    if ($null -ne $options) {
        $c = Get-PropValue $options 'choices'
        if ($null -ne $c) { $choices += @(Get-ArrayItems $c) }
    }
    $names = New-Object System.Collections.Generic.List[string]
    foreach ($choice in $choices) {
        $name = Get-PropValue $choice 'name'
        if (-not [string]::IsNullOrWhiteSpace($name)) { [void]$names.Add([string]$name) }
    }
    return @($names)
}

function Find-TableArrays {
    param([object]$Obj, [int]$Depth = 0)
    $results = New-Object System.Collections.Generic.List[object]
    if ($null -eq $Obj -or $Depth -gt 8) { return @($results) }

    $tables = Get-PropValue $Obj 'tables'
    if ($null -ne $tables) {
        $arr = @(Get-ArrayItems $tables)
        if ($arr.Count -gt 0) {
            $looksLikeTables = $false
            foreach ($candidate in $arr) {
                $id = Get-PropValue $candidate 'id'
                if ($null -eq $id) { $id = Get-PropValue $candidate 'tableId' }
                $name = Get-PropValue $candidate 'name'
                if ($null -eq $name) { $name = Get-PropValue $candidate 'table_name' }
                $fields = Get-PropValue $candidate 'fields'
                if ($null -ne $fields -and (-not [string]::IsNullOrWhiteSpace([string]$id) -or -not [string]::IsNullOrWhiteSpace([string]$name))) {
                    $looksLikeTables = $true
                    break
                }
            }
            if ($looksLikeTables) { [void]$results.Add($arr) }
        }
    }

    if ($Obj -is [System.Array]) {
        foreach ($item in $Obj) {
            foreach ($found in (Find-TableArrays -Obj $item -Depth ($Depth + 1))) { [void]$results.Add($found) }
        }
    } else {
        foreach ($prop in $Obj.PSObject.Properties) {
            if ($prop.Value -is [string] -or $prop.Value -is [ValueType]) { continue }
            foreach ($found in (Find-TableArrays -Obj $prop.Value -Depth ($Depth + 1))) { [void]$results.Add($found) }
        }
    }
    return @($results)
}

function Normalize-SchemaTables {
    param([object]$Schema)
    $arrays = @(Find-TableArrays -Obj $Schema)
    if ($arrays.Count -eq 0) { throw 'Schema JSON does not contain a recognizable tables array with field metadata.' }

    $best = $arrays | Sort-Object { @($_).Count } -Descending | Select-Object -First 1
    $tables = New-Object System.Collections.Generic.List[object]
    foreach ($t in @($best)) {
        $id = Get-PropValue $t 'id'
        if ($null -eq $id) { $id = Get-PropValue $t 'tableId' }
        if ($null -eq $id) { $id = Get-PropValue $t 'table_id' }
        $name = Get-PropValue $t 'name'
        if ($null -eq $name) { $name = Get-PropValue $t 'tableName' }
        if ($null -eq $name) { $name = Get-PropValue $t 'table_name' }
        $fields = @(Get-ArrayItems (Get-PropValue $t 'fields'))
        if ([string]::IsNullOrWhiteSpace([string]$id) -and [string]::IsNullOrWhiteSpace([string]$name)) { continue }
        if ($fields.Count -eq 0) { continue }
        [void]$tables.Add([pscustomobject]@{ id = [string]$id; name = [string]$name; fields = $fields })
    }
    return @($tables)
}

function Add-Issue {
    param([System.Collections.Generic.List[object]]$List, [string]$Severity, [string]$ViewKey, [string]$IssueType, [string]$Message, [object]$Details)
    [void]$List.Add([pscustomobject]@{
        severity = $Severity
        view_key = $ViewKey
        issue_type = $IssueType
        message = $Message
        details = $Details
    })
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

$views = @(Get-ArrayItems (Get-PropValue $manifest 'views'))
if ($views.Count -eq 0) { throw 'Manifest contains no views array.' }
$tables = @(Normalize-SchemaTables -Schema $schema)
if ($tables.Count -eq 0) { throw 'No schema tables found after normalization.' }

$tableById = @{}
$tableByNameLower = @{}
foreach ($t in $tables) {
    if (-not [string]::IsNullOrWhiteSpace($t.id)) { $tableById[$t.id] = $t }
    if (-not [string]::IsNullOrWhiteSpace($t.name)) { $tableByNameLower[$t.name.ToLowerInvariant()] = $t }
}

$issues = New-Object System.Collections.Generic.List[object]
$viewResults = New-Object System.Collections.Generic.List[object]
$filterOperators = @('=','!=','is one of','is not one of','contains','does not contain','is empty','is not empty','on or before','on or after','before','after')
$sortableTypes = @('singleLineText','multilineText','number','date','dateTime','singleSelect','multipleSelects','checkbox','formula','rollup','lookup','createdTime','lastModifiedTime','autoNumber','url','email','phoneNumber','currency','percent','duration','rating')

foreach ($view in $views) {
    $viewName = [string](Get-PropValue $view 'view_name')
    $tableId = [string](Get-PropValue $view 'table_id')
    $tableName = [string](Get-PropValue $view 'table_name')
    $viewKey = [string](Get-PropValue $view 'view_key')
    if ([string]::IsNullOrWhiteSpace($viewKey)) { $viewKey = "$tableName::$viewName" }

    $viewErrorsBefore = ($issues | Where-Object { $_.severity -eq 'error' }).Count
    $viewWarningsBefore = ($issues | Where-Object { $_.severity -eq 'warning' }).Count

    $table = $null
    if (-not [string]::IsNullOrWhiteSpace($tableId) -and $tableById.ContainsKey($tableId)) { $table = $tableById[$tableId] }
    elseif (-not [string]::IsNullOrWhiteSpace($tableName) -and $tableByNameLower.ContainsKey($tableName.ToLowerInvariant())) { $table = $tableByNameLower[$tableName.ToLowerInvariant()] }

    if ($null -eq $table) {
        Add-Issue -List $issues -Severity 'error' -ViewKey $viewKey -IssueType 'missing_table' -Message "Table not found: $tableName / $tableId" -Details @{ table_name = $tableName; table_id = $tableId }
        [void]$viewResults.Add([pscustomobject]@{ view_key = $viewKey; status = 'FAIL'; table_name = $tableName; filter_count = 0; sort_count = 0 })
        continue
    }

    $fieldByNameLower = @{}
    $fieldById = @{}
    foreach ($field in @(Get-ArrayItems $table.fields)) {
        $fid = Get-PropValue $field 'id'
        if ($null -eq $fid) { $fid = Get-PropValue $field 'fieldId' }
        $fname = Get-PropValue $field 'name'
        if ($null -ne $fid) { $fieldById[[string]$fid] = $field }
        if ($null -ne $fname) { $fieldByNameLower[[string]$fname.ToLowerInvariant()] = $field }
    }

    foreach ($filter in @(Get-ArrayItems (Get-PropValue $view 'filters'))) {
        $fieldName = [string](Get-PropValue $filter 'field')
        $operator = [string](Get-PropValue $filter 'operator')
        $value = Get-PropValue $filter 'value'
        if ([string]::IsNullOrWhiteSpace($fieldName)) {
            Add-Issue -List $issues -Severity 'error' -ViewKey $viewKey -IssueType 'missing_filter_field_name' -Message 'Filter is missing field name.' -Details $filter
            continue
        }
        if (-not $fieldByNameLower.ContainsKey($fieldName.ToLowerInvariant())) {
            Add-Issue -List $issues -Severity 'error' -ViewKey $viewKey -IssueType 'missing_filter_field' -Message "Filter field not found: $fieldName" -Details @{ field = $fieldName }
            continue
        }
        $field = $fieldByNameLower[$fieldName.ToLowerInvariant()]
        $fieldType = [string](Get-PropValue $field 'type')
        if (-not [string]::IsNullOrWhiteSpace($operator) -and ($filterOperators -notcontains $operator)) {
            Add-Issue -List $issues -Severity 'warning' -ViewKey $viewKey -IssueType 'unknown_filter_operator' -Message "Filter operator not in allow-list: $operator" -Details @{ field = $fieldName; operator = $operator }
        }
        if ($fieldType -eq 'singleSelect' -or $fieldType -eq 'multipleSelects') {
            $values = @(Normalize-StringList -Value $value)
            if ($values.Count -gt 0) {
                $choices = @(Get-ChoiceNames -Field $field)
                if ($choices.Count -eq 0) {
                    $severity = 'error'
                    if ($AllowSchemaWithoutSelectChoices) { $severity = 'warning' }
                    Add-Issue -List $issues -Severity $severity -ViewKey $viewKey -IssueType 'select_choices_unavailable' -Message "Select field '$fieldName' has no choices in schema JSON; cannot verify values." -Details @{ field = $fieldName; values = $values }
                } else {
                    foreach ($v in $values) {
                        if ($choices -notcontains $v) {
                            Add-Issue -List $issues -Severity 'error' -ViewKey $viewKey -IssueType 'invalid_select_value' -Message "Invalid select value '$v' for field '$fieldName'." -Details @{ field = $fieldName; value = $v; valid_values = $choices }
                        }
                    }
                }
            }
        } elseif ($fieldType -eq 'checkbox') {
            if ($null -ne $value -and -not ($value -is [bool])) {
                Add-Issue -List $issues -Severity 'error' -ViewKey $viewKey -IssueType 'invalid_checkbox_value' -Message "Checkbox filter '$fieldName' must use true/false." -Details @{ field = $fieldName; value = $value }
            }
        }
    }

    foreach ($sort in @(Get-ArrayItems (Get-PropValue $view 'sorts'))) {
        $fieldName = [string](Get-PropValue $sort 'field')
        $direction = [string](Get-PropValue $sort 'direction')
        if ([string]::IsNullOrWhiteSpace($fieldName)) {
            Add-Issue -List $issues -Severity 'error' -ViewKey $viewKey -IssueType 'missing_sort_field_name' -Message 'Sort is missing field name.' -Details $sort
            continue
        }
        if (-not $fieldByNameLower.ContainsKey($fieldName.ToLowerInvariant())) {
            Add-Issue -List $issues -Severity 'error' -ViewKey $viewKey -IssueType 'missing_sort_field' -Message "Sort field not found: $fieldName" -Details @{ field = $fieldName }
            continue
        }
        $field = $fieldByNameLower[$fieldName.ToLowerInvariant()]
        $fieldType = [string](Get-PropValue $field 'type')
        if ($sortableTypes -notcontains $fieldType) {
            Add-Issue -List $issues -Severity 'warning' -ViewKey $viewKey -IssueType 'possibly_unsortable_field_type' -Message "Sort field '$fieldName' has possibly unsupported type '$fieldType'." -Details @{ field = $fieldName; type = $fieldType }
        }
        if ($direction -ne 'asc' -and $direction -ne 'desc') {
            Add-Issue -List $issues -Severity 'error' -ViewKey $viewKey -IssueType 'invalid_sort_direction' -Message "Sort direction must be asc or desc for field '$fieldName'." -Details @{ field = $fieldName; direction = $direction }
        }
    }

    $viewErrorsAfter = ($issues | Where-Object { $_.severity -eq 'error' }).Count
    $viewWarningsAfter = ($issues | Where-Object { $_.severity -eq 'warning' }).Count
    $status = 'PASS'
    if ($viewErrorsAfter -gt $viewErrorsBefore) { $status = 'FAIL' }
    elseif ($viewWarningsAfter -gt $viewWarningsBefore) { $status = 'PASS_WITH_WARNINGS' }
    [void]$viewResults.Add([pscustomobject]@{
        view_key = $viewKey
        view_name = $viewName
        table_name = $table.name
        table_id = $table.id
        status = $status
        filter_count = @(Get-ArrayItems (Get-PropValue $view 'filters')).Count
        sort_count = @(Get-ArrayItems (Get-PropValue $view 'sorts')).Count
    })
}

$errorCount = ($issues | Where-Object { $_.severity -eq 'error' }).Count
$warningCount = ($issues | Where-Object { $_.severity -eq 'warning' }).Count
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
    valid_view_count = ($viewResults | Where-Object { $_.status -eq 'PASS' }).Count
    warning_view_count = ($viewResults | Where-Object { $_.status -eq 'PASS_WITH_WARNINGS' }).Count
    failing_view_count = ($viewResults | Where-Object { $_.status -eq 'FAIL' }).Count
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

$md = New-Object System.Collections.Generic.List[string]
[void]$md.Add('# WBS09 Manifest Schema Audit')
[void]$md.Add('')
[void]$md.Add(('- Status: {0}' -f $status))
[void]$md.Add(('- Tool version: {0}' -f $Version))
[void]$md.Add(('- Manifest views: {0}' -f $views.Count))
[void]$md.Add(('- Valid views: {0}' -f $report.valid_view_count))
[void]$md.Add(('- Warning views: {0}' -f $report.warning_view_count))
[void]$md.Add(('- Failing views: {0}' -f $report.failing_view_count))
[void]$md.Add(('- Errors: {0}' -f $errorCount))
[void]$md.Add(('- Warnings: {0}' -f $warningCount))
[void]$md.Add('')
[void]$md.Add('## Issues')
if ($issues.Count -eq 0) {
    [void]$md.Add('No blocking errors or warnings were found.')
} else {
    foreach ($issue in $issues) {
        [void]$md.Add(('- **{0}** `{1}` - {2}: {3}' -f $issue.severity.ToUpperInvariant(), $issue.view_key, $issue.issue_type, $issue.message))
    }
}
[void]$md.Add('')
[void]$md.Add('## View Results')
foreach ($vr in $viewResults) {
    [void]$md.Add(('- `{0}` - {1}' -f $vr.view_key, $vr.status))
}
Set-Content -LiteralPath $mdPath -Value $md -Encoding UTF8

Write-AuditLog "Audit complete. Status=$status Errors=$errorCount Warnings=$warningCount"
Write-Host "Audit JSON: $jsonPath"
Write-Host "Audit Markdown: $mdPath"

if ($errorCount -gt 0) { exit 2 }
if ($FailOnWarnings -and $warningCount -gt 0) { exit 3 }
exit 0
