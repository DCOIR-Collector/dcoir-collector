$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = (Get-Location).Path }
$out = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($out)) { throw 'DCOIR_DOWNLOADS_DIR is not set.' }

$module = Join-Path $repo 'operator_tools\github_desktop_lane\modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
Import-Module $module -Force

$baseId = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID' -Required
$token = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TOKEN' -Required
$headers = New-DcoirAirtableAuthHeader -ApiToken $token
$headers['Content-Type'] = 'application/json'

$planKey = 'PLAN-AIRTABLE-DB-REDESIGN-20260508'
$schema = Get-DcoirAirtableBaseSchema -BaseId $baseId -Headers $headers
$wbsTable = @($schema.tables | Where-Object { $_.name -eq 'DCOIR Cleanup WBS' }) | Select-Object -First 1
if (-not $wbsTable) { throw 'DCOIR Cleanup WBS table not found.' }
$tableId = [string]$wbsTable.id

$fieldByName = @{}
foreach ($f in @($wbsTable.fields)) { $fieldByName[[string]$f.name] = [string]$f.id }
$required = @('wbs_key','plan_key','wbs_path','parent_wbs_key','rank','title','level','surface','state','gate','target','done_criteria','validation_notes','context')
foreach ($name in $required) {
  if (-not $fieldByName.ContainsKey($name)) { throw ('Missing WBS field: ' + $name) }
}

function Get-DcoirDynamicFieldValue {
  param([AllowNull()]$Fields, [Parameter(Mandatory=$true)][string]$FieldId)
  if ($null -eq $Fields) { return $null }
  $prop = $Fields.PSObject.Properties[$FieldId]
  if ($null -eq $prop) { return $null }
  return $prop.Value
}

function Add-DcoirParsedJsonRows {
  param(
    [Parameter(Mandatory=$true)]$Parsed,
    [Parameter(Mandatory=$true)]$TargetList
  )
  if ($null -eq $Parsed) { return }
  if ($Parsed -is [System.Array]) {
    foreach ($item in $Parsed) { $TargetList.Add($item) | Out-Null }
  } else {
    $TargetList.Add($Parsed) | Out-Null
  }
}

function Get-AllRecordsForTable {
  param([string]$BaseId, [string]$TableId, [hashtable]$Headers)
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

function Convert-TargetRowToFields {
  param($Row, [hashtable]$FieldByName)
  $fields = [ordered]@{}
  foreach ($name in @('wbs_key','plan_key','wbs_path','parent_wbs_key','rank','title','level','surface','state','gate','target','done_criteria','validation_notes','context')) {
    if ($Row.PSObject.Properties.Name -contains $name) {
      $value = $Row.$name
      if ($null -ne $value -and -not ([string]$value -eq '')) { $fields[$FieldByName[$name]] = $value }
    }
  }
  return $fields
}

$inputDir = Join-Path $repo 'chatgpt_staging\exec_inputs\dcoir-db-redesign-wbs-scaffold-20260508'
$inputFiles = @(
  (Join-Path $inputDir 'remaining_wbs_rows.json')
  (Join-Path $inputDir 'remaining_wbs_rows_part2.json')
)
$targetRows = New-Object System.Collections.Generic.List[object]
foreach ($file in $inputFiles) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw ('Missing input file: ' + $file) }
  $parsed = Get-Content -LiteralPath $file -Raw -Encoding UTF8 | ConvertFrom-Json
  Add-DcoirParsedJsonRows -Parsed $parsed -TargetList $targetRows
}

$targetKeys = @{}
foreach ($row in @($targetRows.ToArray())) {
  $key = [string]$row.wbs_key
  if ([string]::IsNullOrWhiteSpace($key)) { throw 'Input row missing wbs_key.' }
  if ($targetKeys.ContainsKey($key)) { throw ('Duplicate input wbs_key: ' + $key) }
  $targetKeys[$key] = $true
  if ([string]$row.plan_key -ne $planKey) { throw ('Unexpected plan_key for ' + $key) }
}

$before = @(Get-AllRecordsForTable -BaseId $baseId -TableId $tableId -Headers $headers)
$wbsKeyField = $fieldByName['wbs_key']
$planKeyField = $fieldByName['plan_key']
$existingByKey = @{}
foreach ($record in $before) {
  $key = [string](Get-DcoirDynamicFieldValue -Fields $record.fields -FieldId $wbsKeyField)
  if (-not [string]::IsNullOrWhiteSpace($key)) { $existingByKey[$key] = $record.id }
}

$missingRows = New-Object System.Collections.Generic.List[object]
$existingRows = New-Object System.Collections.Generic.List[object]
foreach ($row in @($targetRows.ToArray())) {
  $key = [string]$row.wbs_key
  if ($existingByKey.ContainsKey($key)) {
    $existingRows.Add([ordered]@{ wbs_key = $key; record_id = $existingByKey[$key]; action = 'skip_existing' }) | Out-Null
  } else {
    $missingRows.Add($row) | Out-Null
  }
}

$planned = New-Object System.Collections.Generic.List[object]
foreach ($row in @($missingRows.ToArray())) {
  $planned.Add([ordered]@{ fields = (Convert-TargetRowToFields -Row $row -FieldByName $fieldByName) }) | Out-Null
}

$runRoot = Join-Path $out 'dcoir_db_redesign_wbs_scaffold_20260508'
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$targetPath = Join-Path $runRoot 'target_records.json'
$payloadPath = Join-Path $runRoot 'planned_payload.json'
$summaryPath = Join-Path $runRoot 'execution_summary.json'
$verifyPath = Join-Path $runRoot 'after_readback_verification.json'
$errorPath = Join-Path $runRoot 'error_report.json'

try {
  [ordered]@{
    plan_key = $planKey
    source_files = $inputFiles
    expected_input_count = $targetRows.Count
    existing_count_before = $existingRows.Count
    missing_count_before = $missingRows.Count
    target_rows = @($targetRows.ToArray())
  } | ConvertTo-Json -Depth 40 | Out-File -FilePath $targetPath -Encoding utf8

  [ordered]@{
    mode = 'create_missing_only'
    table_id = $tableId
    expected_create_count = $missingRows.Count
    records = @($planned.ToArray())
  } | ConvertTo-Json -Depth 40 | Out-File -FilePath $payloadPath -Encoding utf8

  $created = New-Object System.Collections.Generic.List[object]
  $batch = New-Object System.Collections.Generic.List[object]
  foreach ($item in @($planned.ToArray())) {
    $batch.Add($item) | Out-Null
    if ($batch.Count -eq 10) {
      $body = @{ records = @($batch.ToArray()); typecast = $false } | ConvertTo-Json -Depth 40
      $uri = 'https://api.airtable.com/v0/' + $baseId + '/' + $tableId
      $res = Invoke-RestMethod -Uri $uri -Headers $headers -Method POST -Body $body -ErrorAction Stop
      foreach ($record in @($res.records)) { $created.Add($record) | Out-Null }
      $batch.Clear()
    }
  }
  if ($batch.Count -gt 0) {
    $body = @{ records = @($batch.ToArray()); typecast = $false } | ConvertTo-Json -Depth 40
    $uri = 'https://api.airtable.com/v0/' + $baseId + '/' + $tableId
    $res = Invoke-RestMethod -Uri $uri -Headers $headers -Method POST -Body $body -ErrorAction Stop
    foreach ($record in @($res.records)) { $created.Add($record) | Out-Null }
  }

  if ($created.Count -ne $missingRows.Count) { throw ('Created count mismatch. Expected ' + $missingRows.Count + ' got ' + $created.Count) }

  $after = @(Get-AllRecordsForTable -BaseId $baseId -TableId $tableId -Headers $headers)
  $afterKeys = @{}
  $planRecords = New-Object System.Collections.Generic.List[object]
  foreach ($record in $after) {
    $key = [string](Get-DcoirDynamicFieldValue -Fields $record.fields -FieldId $wbsKeyField)
    $pkey = [string](Get-DcoirDynamicFieldValue -Fields $record.fields -FieldId $planKeyField)
    if ($pkey -eq $planKey) { $planRecords.Add([ordered]@{ id = $record.id; wbs_key = $key }) | Out-Null }
    if (-not [string]::IsNullOrWhiteSpace($key)) {
      if (-not $afterKeys.ContainsKey($key)) { $afterKeys[$key] = 0 }
      $afterKeys[$key]++
    }
  }

  $missingAfter = New-Object System.Collections.Generic.List[string]
  $duplicateAfter = New-Object System.Collections.Generic.List[object]
  foreach ($key in $targetKeys.Keys) {
    if (-not $afterKeys.ContainsKey($key)) { $missingAfter.Add($key) | Out-Null }
    elseif ([int]$afterKeys[$key] -ne 1) { $duplicateAfter.Add([ordered]@{ wbs_key = $key; count = [int]$afterKeys[$key] }) | Out-Null }
  }

  $success = ($missingAfter.Count -eq 0 -and $duplicateAfter.Count -eq 0)
  [ordered]@{
    result = if ($success) { 'success' } else { 'failed' }
    plan_key = $planKey
    input_count = $targetRows.Count
    skipped_existing_count = $existingRows.Count
    created_count = $created.Count
    expected_create_count = $missingRows.Count
    plan_record_count_after = $planRecords.Count
    artifacts = @('target_records.json','planned_payload.json','execution_summary.json','after_readback_verification.json')
  } | ConvertTo-Json -Depth 20 | Out-File -FilePath $summaryPath -Encoding utf8

  [ordered]@{
    result = if ($success) { 'pass' } else { 'fail' }
    expected_keys_count = $targetKeys.Count
    missing_after = @($missingAfter.ToArray())
    duplicate_after = @($duplicateAfter.ToArray())
    created_record_ids = @($created | ForEach-Object { $_.id })
    skipped_existing = @($existingRows.ToArray())
  } | ConvertTo-Json -Depth 30 | Out-File -FilePath $verifyPath -Encoding utf8

  if (-not $success) { throw 'After-readback verification failed. See after_readback_verification.json.' }

  [ordered]@{
    result = 'success'
    created_count = $created.Count
    skipped_existing_count = $existingRows.Count
    total_expected_keys = $targetKeys.Count
    output_dir = $runRoot
  } | ConvertTo-Json -Depth 8
}
catch {
  [ordered]@{
    result = 'failed'
    error_message = $_.Exception.Message
    error_type = $_.Exception.GetType().FullName
    script_stack_trace = $_.ScriptStackTrace
    output_dir = $runRoot
  } | ConvertTo-Json -Depth 10 | Out-File -FilePath $errorPath -Encoding utf8
  throw
}
