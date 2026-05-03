Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:DcoirAirtableVersion = '2026-05-03.5'

function Get-DcoirAirtableVersion {
    [CmdletBinding()]
    param()
    return $script:DcoirAirtableVersion
}

function Test-DcoirAirtablePlaceholderValue {
    [CmdletBinding()]
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    $v = $Value.Trim()
    return ($v -match '^(your|changeme|placeholder|pat_here|token_here|base_here|app_here)$' -or
            $v -match '^[A-Za-z]:\\path\\to(\\|$)' -or
            $v -match '^/path/to(/|$)' -or
            $v -match 'your[_ -]?repo')
}

function Get-DcoirAirtableSystemEnvValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [switch]$Required,
        [AllowNull()][string]$Default
    )
    $machine = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    if (Test-DcoirAirtablePlaceholderValue -Value $machine) {
        throw "$Name is set to a placeholder value in Machine/System environment scope. Replace it with a real value, then open a new PowerShell window."
    }
    if (-not [string]::IsNullOrWhiteSpace($machine)) { return $machine.Trim() }
    if (-not [string]::IsNullOrWhiteSpace($Default)) { return $Default }
    if ($Required) { throw "$Name is not set in Machine/System environment scope. Set it as a System environment variable, then open a new PowerShell window." }
    return $null
}

function New-DcoirAirtableAuthHeader {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$ApiToken)
    if ([string]::IsNullOrWhiteSpace($ApiToken)) { throw 'Airtable API token is empty.' }
    if (Test-DcoirAirtablePlaceholderValue -Value $ApiToken) { throw 'Airtable API token looks like a placeholder.' }
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
    $normalized = ($Name -replace '[^A-Za-z0-9]+', '_').Trim('_').ToLowerInvariant()
    $tokens = @($normalized -split '_' | Where-Object { $_ })
    if ($tokens -contains 'token') { return $true }
    if ($tokens -contains 'secret') { return $true }
    if ($tokens -contains 'password') { return $true }
    if ($tokens -contains 'passwd') { return $true }
    if ($tokens -contains 'credential' -or $tokens -contains 'credentials') { return $true }
    if ($tokens -contains 'bearer') { return $true }
    if ($tokens -contains 'authorization') { return $true }
    if ($tokens -contains 'apikey' -or $normalized -match '(^|_)api(_)?key($|_)') { return $true }
    if ($normalized -match '(^|_)private(_)?key($|_)') { return $true }
    if ($tokens -contains 'pat') { return $true }
    if ($normalized -match '(^|_)auth(_)?header($|_)') { return $true }
    return $false
}

function Protect-DcoirAirtableRecordFields {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Record,
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
        $tableIdentifier = $null
        if ($null -ne $Table.PSObject.Properties['id']) { $tableIdentifier = [string]$Table.id }
        if ([string]::IsNullOrWhiteSpace($tableIdentifier)) { $tableIdentifier = [string]$Table.name }
        if ([string]::IsNullOrWhiteSpace($tableIdentifier)) { throw 'Airtable table is missing both id and name.' }
        $encodedTable = [System.Uri]::EscapeDataString($tableIdentifier)
        $uri = ('https://api.airtable.com/v0/{0}/{1}?pageSize=100' -f $BaseId, $encodedTable)
        if (-not [string]::IsNullOrWhiteSpace($offset)) { $uri += '&offset=' + [System.Uri]::EscapeDataString($offset) }
        $result = Invoke-DcoirAirtableApi -Uri $uri -Headers $Headers
        foreach ($record in @($result.records)) {
            $records.Add((Protect-DcoirAirtableRecordFields -Record $record -RedactLikelySecrets:$RedactLikelySecrets)) | Out-Null
            if ($MaxRecords -gt 0 -and $records.Count -ge $MaxRecords) { break }
        }
        if ($MaxRecords -gt 0 -and $records.Count -ge $MaxRecords) { break }
        $nextOffset = $null
        if ($null -ne $result -and $null -ne $result.PSObject.Properties['offset']) {
            $nextOffset = [string]$result.offset
        }
        $offset = $nextOffset
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

function Write-DcoirAirtableJson {
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

function Write-DcoirAirtableText {
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

Export-ModuleMember -Function Get-DcoirAirtableVersion,Test-DcoirAirtablePlaceholderValue,Get-DcoirAirtableSystemEnvValue,New-DcoirAirtableAuthHeader,Invoke-DcoirAirtableApi,Get-DcoirAirtableBaseSchema,Select-DcoirAirtableTables,ConvertTo-DcoirAirtableSafeName,Test-DcoirAirtableSensitiveFieldName,Protect-DcoirAirtableRecordFields,Get-DcoirAirtableRecords,Get-DcoirAirtableSchemaSummary,Write-DcoirAirtableJson,Write-DcoirAirtableText
