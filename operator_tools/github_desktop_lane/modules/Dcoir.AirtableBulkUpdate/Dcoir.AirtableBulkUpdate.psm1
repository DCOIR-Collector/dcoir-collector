Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:DcoirAirtableBulkUpdateVersion = '2026-05-08.1'

function Get-DcoirAirtableBulkUpdateVersion {
    [CmdletBinding()]
    param()
    return $script:DcoirAirtableBulkUpdateVersion
}

function Get-DcoirAirtableUpdateFieldValueById {
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

function Get-DcoirAirtableBulkUpdateRecordById {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$BaseId,
        [Parameter(Mandatory=$true)][string]$TableId,
        [Parameter(Mandatory=$true)][string]$RecordId,
        [Parameter(Mandatory=$true)][hashtable]$Headers
    )
    $uri = 'https://api.airtable.com/v0/' + $BaseId + '/' + $TableId + '/' + $RecordId + '?returnFieldsByFieldId=true'
    return Invoke-RestMethod -Uri $uri -Headers $Headers -Method GET -ErrorAction Stop
}

function Invoke-DcoirAirtableBulkPatchRecords {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$BaseId,
        [Parameter(Mandatory=$true)][string]$TableId,
        [Parameter(Mandatory=$true)][hashtable]$Headers,
        [Parameter(Mandatory=$true)]$Records,
        [int]$BatchSize = 10,
        [bool]$Typecast = $false
    )
    if ($BatchSize -lt 1 -or $BatchSize -gt 10) { throw 'BatchSize must be between 1 and 10 for Airtable update records.' }
    $updated = New-Object System.Collections.Generic.List[object]
    $batch = New-Object System.Collections.Generic.List[object]
    foreach ($record in @($Records)) {
        $batch.Add($record) | Out-Null
        if ($batch.Count -eq $BatchSize) {
            $body = @{ records = @($batch.ToArray()); typecast = $Typecast } | ConvertTo-Json -Depth 80
            $uri = 'https://api.airtable.com/v0/' + $BaseId + '/' + $TableId
            $res = Invoke-RestMethod -Uri $uri -Headers $Headers -Method PATCH -Body $body -ErrorAction Stop
            foreach ($item in @($res.records)) { $updated.Add($item) | Out-Null }
            $batch.Clear()
        }
    }
    if ($batch.Count -gt 0) {
        $body = @{ records = @($batch.ToArray()); typecast = $Typecast } | ConvertTo-Json -Depth 80
        $uri = 'https://api.airtable.com/v0/' + $BaseId + '/' + $TableId
        $res = Invoke-RestMethod -Uri $uri -Headers $Headers -Method PATCH -Body $body -ErrorAction Stop
        foreach ($item in @($res.records)) { $updated.Add($item) | Out-Null }
    }
    return @($updated.ToArray())
}

function Invoke-DcoirAirtableSelectAliasUpdateWithBeforeGates {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$BaseId,
        [Parameter(Mandatory=$true)][hashtable]$Headers,
        [Parameter(Mandatory=$true)]$TargetRecords,
        [int]$BatchSize = 10,
        [bool]$Typecast = $false
    )

    $targets = @($TargetRecords)
    $seen = @{}
    $before = New-Object System.Collections.Generic.List[object]
    foreach ($target in $targets) {
        foreach ($name in @('table_id','record_id','field_id','old_choice_id','new_choice_id')) {
            if (-not ($target.PSObject.Properties.Name -contains $name)) { throw "Target missing required property: $name" }
            if ([string]::IsNullOrWhiteSpace([string]$target.$name)) { throw "Target has blank required property: $name" }
        }
        $targetKey = ([string]$target.table_id) + '|' + ([string]$target.record_id) + '|' + ([string]$target.field_id)
        if ($seen.ContainsKey($targetKey)) { throw "Duplicate target table/record/field: $targetKey" }
        $seen[$targetKey] = $true

        $record = Get-DcoirAirtableBulkUpdateRecordById -BaseId $BaseId -TableId ([string]$target.table_id) -RecordId ([string]$target.record_id) -Headers $Headers
        $actual = [string](Get-DcoirAirtableUpdateFieldValueById -Fields $record.fields -FieldId ([string]$target.field_id))
        $expected = [string]$target.old_choice_id
        $before.Add([ordered]@{
            table_id = [string]$target.table_id
            table_name = [string]$target.table_name
            record_id = [string]$target.record_id
            display_key = [string]$target.display_key
            field_id = [string]$target.field_id
            field_name = [string]$target.field_name
            expected_old_choice_id = $expected
            expected_old_choice_name = [string]$target.old_choice_name
            actual_before_choice_id = $actual
            new_choice_id = [string]$target.new_choice_id
            new_choice_name = [string]$target.new_choice_name
            before_gate_result = if ($actual -eq $expected) { 'pass' } else { 'fail' }
        }) | Out-Null
        if ($actual -ne $expected) {
            throw "Before-value gate failed for $targetKey. Expected $expected but found $actual."
        }
    }

    $byTable = @{}
    foreach ($target in $targets) {
        $tableId = [string]$target.table_id
        if (-not $byTable.ContainsKey($tableId)) { $byTable[$tableId] = New-Object System.Collections.Generic.List[object] }
        $fields = [ordered]@{}
        $fields[[string]$target.field_id] = [string]$target.new_choice_id
        $byTable[$tableId].Add([ordered]@{ id = [string]$target.record_id; fields = $fields }) | Out-Null
    }

    $updated = New-Object System.Collections.Generic.List[object]
    foreach ($tableId in $byTable.Keys) {
        $tableUpdates = @($byTable[$tableId].ToArray())
        $patched = @(Invoke-DcoirAirtableBulkPatchRecords -BaseId $BaseId -TableId $tableId -Headers $Headers -Records $tableUpdates -BatchSize $BatchSize -Typecast $Typecast)
        foreach ($item in $patched) { $updated.Add($item) | Out-Null }
    }
    if ($updated.Count -ne $targets.Count) { throw "Updated count mismatch. Expected $($targets.Count) got $($updated.Count)." }

    $after = New-Object System.Collections.Generic.List[object]
    $mismatchAfter = New-Object System.Collections.Generic.List[object]
    foreach ($target in $targets) {
        $record = Get-DcoirAirtableBulkUpdateRecordById -BaseId $BaseId -TableId ([string]$target.table_id) -RecordId ([string]$target.record_id) -Headers $Headers
        $actual = [string](Get-DcoirAirtableUpdateFieldValueById -Fields $record.fields -FieldId ([string]$target.field_id))
        $expected = [string]$target.new_choice_id
        $row = [ordered]@{
            table_id = [string]$target.table_id
            table_name = [string]$target.table_name
            record_id = [string]$target.record_id
            display_key = [string]$target.display_key
            field_id = [string]$target.field_id
            field_name = [string]$target.field_name
            expected_new_choice_id = $expected
            expected_new_choice_name = [string]$target.new_choice_name
            actual_after_choice_id = $actual
            after_gate_result = if ($actual -eq $expected) { 'pass' } else { 'fail' }
        }
        $after.Add($row) | Out-Null
        if ($actual -ne $expected) { $mismatchAfter.Add($row) | Out-Null }
    }

    $success = ($mismatchAfter.Count -eq 0)
    return [pscustomobject][ordered]@{
        result = if ($success) { 'success' } else { 'failed' }
        input_count = $targets.Count
        updated_count = $updated.Count
        before_readback = @($before.ToArray())
        after_readback = @($after.ToArray())
        after_mismatches = @($mismatchAfter.ToArray())
        planned_payload = [ordered]@{
            mode = 'update_select_aliases_with_before_value_gates'
            table_count = $byTable.Keys.Count
            target_count = $targets.Count
            updates_by_table = $byTable
        }
    }
}

Export-ModuleMember -Function @(
    'Get-DcoirAirtableBulkUpdateVersion',
    'Get-DcoirAirtableUpdateFieldValueById',
    'Get-DcoirAirtableBulkUpdateRecordById',
    'Invoke-DcoirAirtableBulkPatchRecords',
    'Invoke-DcoirAirtableSelectAliasUpdateWithBeforeGates'
)
