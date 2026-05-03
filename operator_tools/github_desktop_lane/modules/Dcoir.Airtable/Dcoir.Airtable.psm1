Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:DcoirAirtableVersion = '2026-05-03.1'

function Get-DcoirAirtableVersion {
    [CmdletBinding()]
    param()
    return $script:DcoirAirtableVersion
}

function Get-DcoirAirtableSystemEnvValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [switch]$Required,
        [AllowNull()][string]$Default
    )
    $machine = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    if (-not [string]::IsNullOrWhiteSpace($machine)) { return $machine.Trim() }
    if (-not [string]::IsNullOrWhiteSpace($Default)) { return $Default }
    if ($Required) { throw "$Name is not set in Machine/System environment scope. Set it as a System environment variable, then open a new PowerShell window." }
    return $null
}

function New-DcoirAirtableAuthHeader {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$ApiToken)
    if ([string]::IsNullOrWhiteSpace($ApiToken)) { throw 'Airtable API token is empty.' }
    if ($ApiToken -match '^(your|changeme|placeholder|pat_here|token_here)') { throw 'Airtable API token looks like a placeholder.' }
    return @{ Authorization = "Bearer $ApiToken" }
}

function Invoke-DcoirAirtableApi {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Uri,
        [Parameter(Mandatory=$true)][hashtable]$Headers,
        [string]$Method = 'GET'
    )
    try {
        return Invoke-RestMethod -Uri $Uri -Headers $Headers -Method $Method -ErrorAction Stop
    }
    catch {
        $msg = $_.Exception.Message
        throw "Airtable API request failed for $Uri : $msg"
    }
}

function Get-DcoirAirtableBaseSchema {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$BaseId,
        [Parameter(Mandatory=$true)][hashtable]$Headers
    )
    $uri = "https://api.airtable.com/v0/meta/bases/$BaseId/tables"
    return Invoke-DcoirAirtableApi -Uri $uri -Headers $Headers
}

function Select-DcoirAirtableTables {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Schema,
        [AllowNull()][string[]]$RequestedTables
    )
    $tables = @($Schema.tables)
    if ($null -eq $RequestedTables -or $RequestedTables.Count -eq 0) { return $tables }
    $wanted = @{}
    foreach ($t in $RequestedTables) {
        if (-not [string]::IsNullOrWhiteSpace($t)) { $wanted[$t.Trim().ToLowerInvariant()] = $true }
    }
    return @($tables | Where-Object { $wanted.ContainsKey($_.id.ToLowerInvariant()) -or $wanted.ContainsKey($_.name.ToLowerInvariant()) })
}

function ConvertTo-DcoirAirtableSafeName {
    [CmdletBinding()]
    param([AllowNull()][string]$Text)
    if ($null -eq $Text) { return '' }
    return (($Text -replace '[^A-Za-z0-9_.-]', '_').Trim('_'))
}

function Test-DcoirAirtableSensitiveFieldName {
    [CmdletBinding()]
    param([AllowNull()][string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name)) { return $false }
    return ($Name -match '(?i)(token|secret|password|passwd|api[_ -]?key|apikey|credential|private[_ -]?key|pat|bearer|authorization|auth[_ -]?header)')
}

function Redact-DcoirAirtableRecord {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Record,
        [Parameter(Mandatory=$true)]$Table,
        [switch]$RedactLikelySecrets
    )
    if (-not $RedactLikelySecrets) { return $Record }
    $redactedFields = @{}
    foreach ($prop in $Record.fields.PSObject.Properties) {
        if (Test-DcoirAirtableSensitiveFieldName -Name $prop.Name) {
            $redactedFields[$prop.Name] = '[REDACTED_BY_DCOIR_EXPORTER]'
        }
        else {
            $redactedFields[$prop.Name] = $prop.Value
        }
    }
    return [pscustomobject]@{
        id = $Record.id
        createdTime = $Record.createdTime
        fields = $redactedFields
    }
}

function Get-DcoirAirtableRecords {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$BaseId,
        [Parameter(Mandatory=$true)]$Table,
        [Parameter(Mandatory=$true)][hashtable]$Headers,
        [int]$MaxRecords = 0,
        [switch]$RedactLikelySecrets
    )
    $records = New-Object System.Collections.Generic.List[object]
    $offset = $null
    do {
        $encodedTable = [System.Uri]::EscapeDataString($Table.name)
        $uri = "https://api.airtable.com/v0/$BaseId/$encodedTable?pageSize=100"
        if (-not [string]::IsNullOrWhiteSpace($offset)) { $uri += '&offset=' + [System.Uri]::EscapeDataString($offset) }
        $result = Invoke-DcoirAirtableApi -Uri $uri -Headers $Headers
        foreach ($record in @($result.records)) {
            $records.Add((Redact-DcoirAirtableRecord -Record $record -Table $Table -RedactLikelySecrets:$RedactLikelySecrets)) | Out-Null
            if ($MaxRecords -gt 0 -and $records.Count -ge $MaxRecords) { break }
        }
        if ($MaxRecords -gt 0 -and $records.Count -ge $MaxRecords) { break }
        $offset = $result.offset
    } while (-not [string]::IsNullOrWhiteSpace($offset))
    return @($records.ToArray())
}

function Get-DcoirAirtableSchemaSummary {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Tables)
    $summary = New-Object System.Collections.Generic.List[object]
    foreach ($table in @($Tables)) {
        $fieldTypes = @{}
        $linkedFields = @()
        $selectFields = @()
        $sensitiveFields = @()
        foreach ($field in @($table.fields)) {
            if (-not $fieldTypes.ContainsKey($field.type)) { $fieldTypes[$field.type] = 0 }
            $fieldTypes[$field.type]++
            if ($field.type -eq 'multipleRecordLinks') { $linkedFields += $field.name }
            if ($field.type -eq 'singleSelect' -or $field.type -eq 'multipleSelects') { $selectFields += $field.name }
            if (Test-DcoirAirtableSensitiveFieldName -Name $field.name) { $sensitiveFields += $field.name }
        }
        $summary.Add([pscustomobject]@{
            table_id = $table.id
            table_name = $table.name
            field_count = @($table.fields).Count
            field_types = $fieldTypes
            linked_fields = $linkedFields
            select_fields = $selectFields
            likely_sensitive_fields = $sensitiveFields
        }) | Out-Null
    }
    return @($summary.ToArray())
}

function Save-DcoirAirtableJson {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)]$Object,
        [int]$Depth = 80
    )
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, ($Object | ConvertTo-Json -Depth $Depth), $enc)
}

function Save-DcoirAirtableText {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [AllowNull()][string]$Text
    )
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, [string]$Text, $enc)
}

Export-ModuleMember -Function Get-DcoirAirtableVersion,Get-DcoirAirtableSystemEnvValue,New-DcoirAirtableAuthHeader,Invoke-DcoirAirtableApi,Get-DcoirAirtableBaseSchema,Select-DcoirAirtableTables,ConvertTo-DcoirAirtableSafeName,Test-DcoirAirtableSensitiveFieldName,Redact-DcoirAirtableRecord,Get-DcoirAirtableRecords,Get-DcoirAirtableSchemaSummary,Save-DcoirAirtableJson,Save-DcoirAirtableText
