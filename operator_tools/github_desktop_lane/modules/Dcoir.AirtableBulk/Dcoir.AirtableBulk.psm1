Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:DcoirAirtableBulkVersion = '2026-05-08.1'

function Get-DcoirAirtableBulkVersion {
    [CmdletBinding()]
    param()
    return $script:DcoirAirtableBulkVersion
}

function Get-DcoirAirtableFieldValueById {
    [CmdletBinding()]
    param(
        [AllowNull()]$Fields,
        [Parameter(Mandatory=$true)][string]$FieldId
    )
    if ($null -eq $Fields) { return $null }
    $prop = $Fields.PSObject.Properties[$FieldId]
    if ($null -eq $prop) { return $null }
    return $prop.Value
}

function Add-DcoirAirtableBulkParsedRows {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Parsed,
        [Parameter(Mandatory=$true)]$TargetList
    )
    if ($null -eq $Parsed) { return }
    if ($Parsed -is [System.Array]) {
        foreach ($item in $Parsed) { $TargetList.Add($item) | Out-Null }
    }
    else {
        $TargetList.Add($Parsed) | Out-Null
    }
}

function Read-DcoirAirtableBulkJsonRows {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string[]]$Path
    )
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($file in $Path) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Input file not found: $file" }
        $parsed = Get-Content -LiteralPath $file -Raw -Encoding UTF8 | ConvertFrom-Json
        Add-DcoirAirtableBulkParsedRows -Parsed $parsed -TargetList $rows
    }
    return @($rows.ToArray())
}

function Get-DcoirAirtableBulkRecordsByFieldId {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$BaseId,
        [Parameter(Mandatory=$true)][string]$TableId,
        [Parameter(Mandatory=$true)][hashtable]$Headers
    )
    $records = New-Object System.Collections.Generic.List[object]
    $offset = $null
    do {
        $uri = 'https://api.airtable.com/v0/' + $BaseId + '/' + $TableId + '?pageSize=100&returnFieldsByFieldId=true'
        if (-not [string]::IsNullOrWhiteSpace($offset)) { $uri += '&offset=' + [System.Uri]::EscapeDataString($offset) }
        $result = Invoke-RestMethod -Uri $uri -Headers $Headers -Method GET -ErrorAction Stop
        foreach ($record in @($result.records)) { $records.Add($record) | Out-Null }
        $offset = $null
        if ($null -ne $result.PSObject.Properties['offset']) { $offset = [string]$result.offset }
    } while (-not [string]::IsNullOrWhiteSpace($offset))
    return @($records.ToArray())
}

function New-DcoirAirtableBulkExistingKeyMap {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Records,
        [Parameter(Mandatory=$true)][string]$KeyFieldId
    )
    $map = @{}
    foreach ($record in @($Records)) {
        $key = [string](Get-DcoirAirtableFieldValueById -Fields $record.fields -FieldId $KeyFieldId)
        if (-not [string]::IsNullOrWhiteSpace($key)) { $map[$key] = [string]$record.id }
    }
    return $map
}

function ConvertTo-DcoirAirtableBulkFieldPayload {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Row,
        [Parameter(Mandatory=$true)][hashtable]$FieldIdByInputName,
        [string[]]$InputNames = @()
    )
    $fields = [ordered]@{}
    $names = @($InputNames)
    if ($names.Count -eq 0) { $names = @($FieldIdByInputName.Keys) }
    foreach ($name in $names) {
        if (-not $FieldIdByInputName.ContainsKey($name)) { throw "No Airtable field id mapping for input property: $name" }
        if ($Row.PSObject.Properties.Name -contains $name) {
            $value = $Row.$name
            if ($null -ne $value -and -not ([string]$value -eq '')) { $fields[$FieldIdByInputName[$name]] = $value }
        }
    }
    return $fields
}

function Invoke-DcoirAirtableBulkCreateRecords {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$BaseId,
        [Parameter(Mandatory=$true)][string]$TableId,
        [Parameter(Mandatory=$true)][hashtable]$Headers,
        [Parameter(Mandatory=$true)]$Records,
        [int]$BatchSize = 10,
        [bool]$Typecast = $false
    )
    if ($BatchSize -lt 1 -or $BatchSize -gt 10) { throw 'BatchSize must be between 1 and 10 for Airtable create records.' }
    $created = New-Object System.Collections.Generic.List[object]
    $batch = New-Object System.Collections.Generic.List[object]
    foreach ($record in @($Records)) {
        $batch.Add($record) | Out-Null
        if ($batch.Count -eq $BatchSize) {
            $body = @{ records = @($batch.ToArray()); typecast = $Typecast } | ConvertTo-Json -Depth 80
            $uri = 'https://api.airtable.com/v0/' + $BaseId + '/' + $TableId
            $res = Invoke-RestMethod -Uri $uri -Headers $Headers -Method POST -Body $body -ErrorAction Stop
            foreach ($item in @($res.records)) { $created.Add($item) | Out-Null }
            $batch.Clear()
        }
    }
    if ($batch.Count -gt 0) {
        $body = @{ records = @($batch.ToArray()); typecast = $Typecast } | ConvertTo-Json -Depth 80
        $uri = 'https://api.airtable.com/v0/' + $BaseId + '/' + $TableId
        $res = Invoke-RestMethod -Uri $uri -Headers $Headers -Method POST -Body $body -ErrorAction Stop
        foreach ($item in @($res.records)) { $created.Add($item) | Out-Null }
    }
    return @($created.ToArray())
}

function Invoke-DcoirAirtableBulkCreateMissingByKey {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$BaseId,
        [Parameter(Mandatory=$true)][string]$TableId,
        [Parameter(Mandatory=$true)][hashtable]$Headers,
        [Parameter(Mandatory=$true)]$TargetRows,
        [Parameter(Mandatory=$true)][string]$InputKeyProperty,
        [Parameter(Mandatory=$true)][string]$AirtableKeyFieldId,
        [Parameter(Mandatory=$true)][hashtable]$FieldIdByInputName,
        [string[]]$InputNames = @(),
        [int]$BatchSize = 10,
        [bool]$Typecast = $false
    )

    $existingRecords = @(Get-DcoirAirtableBulkRecordsByFieldId -BaseId $BaseId -TableId $TableId -Headers $Headers)
    $existingByKey = New-DcoirAirtableBulkExistingKeyMap -Records $existingRecords -KeyFieldId $AirtableKeyFieldId
    $targetKeys = @{}
    $missingRows = New-Object System.Collections.Generic.List[object]
    $existingRows = New-Object System.Collections.Generic.List[object]

    foreach ($row in @($TargetRows)) {
        if (-not ($row.PSObject.Properties.Name -contains $InputKeyProperty)) { throw "Input row missing key property: $InputKeyProperty" }
        $key = [string]$row.$InputKeyProperty
        if ([string]::IsNullOrWhiteSpace($key)) { throw "Input row has blank key property: $InputKeyProperty" }
        if ($targetKeys.ContainsKey($key)) { throw "Duplicate input key: $key" }
        $targetKeys[$key] = $true
        if ($existingByKey.ContainsKey($key)) {
            $existingRows.Add([ordered]@{ key = $key; record_id = $existingByKey[$key]; action = 'skip_existing' }) | Out-Null
        }
        else {
            $missingRows.Add($row) | Out-Null
        }
    }

    $planned = New-Object System.Collections.Generic.List[object]
    foreach ($row in @($missingRows.ToArray())) {
        $planned.Add([ordered]@{ fields = (ConvertTo-DcoirAirtableBulkFieldPayload -Row $row -FieldIdByInputName $FieldIdByInputName -InputNames $InputNames) }) | Out-Null
    }

    $created = @(Invoke-DcoirAirtableBulkCreateRecords -BaseId $BaseId -TableId $TableId -Headers $Headers -Records @($planned.ToArray()) -BatchSize $BatchSize -Typecast $Typecast)
    if ($created.Count -ne $missingRows.Count) { throw "Created count mismatch. Expected $($missingRows.Count) got $($created.Count)." }

    $after = @(Get-DcoirAirtableBulkRecordsByFieldId -BaseId $BaseId -TableId $TableId -Headers $Headers)
    $afterKeyCounts = @{}
    foreach ($record in $after) {
        $key = [string](Get-DcoirAirtableFieldValueById -Fields $record.fields -FieldId $AirtableKeyFieldId)
        if (-not [string]::IsNullOrWhiteSpace($key)) {
            if (-not $afterKeyCounts.ContainsKey($key)) { $afterKeyCounts[$key] = 0 }
            $afterKeyCounts[$key]++
        }
    }

    $missingAfter = New-Object System.Collections.Generic.List[string]
    $duplicateAfter = New-Object System.Collections.Generic.List[object]
    foreach ($key in $targetKeys.Keys) {
        if (-not $afterKeyCounts.ContainsKey($key)) { $missingAfter.Add($key) | Out-Null }
        elseif ([int]$afterKeyCounts[$key] -ne 1) { $duplicateAfter.Add([ordered]@{ key = $key; count = [int]$afterKeyCounts[$key] }) | Out-Null }
    }
    $success = ($missingAfter.Count -eq 0 -and $duplicateAfter.Count -eq 0)

    return [pscustomobject][ordered]@{
        result = if ($success) { 'success' } else { 'failed' }
        input_count = @($TargetRows).Count
        skipped_existing_count = $existingRows.Count
        expected_create_count = $missingRows.Count
        created_count = $created.Count
        created_record_ids = @($created | ForEach-Object { $_.id })
        skipped_existing = @($existingRows.ToArray())
        missing_after = @($missingAfter.ToArray())
        duplicate_after = @($duplicateAfter.ToArray())
        planned_payload = [ordered]@{
            mode = 'create_missing_by_key'
            table_id = $TableId
            input_key_property = $InputKeyProperty
            airtable_key_field_id = $AirtableKeyFieldId
            expected_create_count = $missingRows.Count
            records = @($planned.ToArray())
        }
    }
}

Export-ModuleMember -Function @(
    'Get-DcoirAirtableBulkVersion',
    'Get-DcoirAirtableFieldValueById',
    'Add-DcoirAirtableBulkParsedRows',
    'Read-DcoirAirtableBulkJsonRows',
    'Get-DcoirAirtableBulkRecordsByFieldId',
    'New-DcoirAirtableBulkExistingKeyMap',
    'ConvertTo-DcoirAirtableBulkFieldPayload',
    'Invoke-DcoirAirtableBulkCreateRecords',
    'Invoke-DcoirAirtableBulkCreateMissingByKey'
)
