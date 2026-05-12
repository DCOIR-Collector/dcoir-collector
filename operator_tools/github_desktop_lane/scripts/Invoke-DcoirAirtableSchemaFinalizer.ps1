[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$ManifestJson,
  [ValidateSet('Plan','Validate','Apply')][string]$Mode = 'Plan',
  [string]$OutputDir,
  [string]$LogPath,
  [switch]$AllowCreateFields,
  [switch]$AllowUpsertRecords,
  [switch]$StrictNativeTasks
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$ToolName = 'dcoir_airtable_schema_finalizer'
$ToolVersion = '2026-05-11.1'

function New-SafeName {
  param([string]$Value)
  if ([string]::IsNullOrWhiteSpace($Value)) { return 'run' }
  $safe = ($Value -replace '[^A-Za-z0-9_.-]', '_').Trim('_')
  if ([string]::IsNullOrWhiteSpace($safe)) { return 'run' }
  return $safe
}

function Write-Utf8 {
  param([Parameter(Mandatory=$true)][string]$Path,[AllowNull()][string]$Text)
  $parent = Split-Path -Parent $Path
  if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path,[string]$Text,$enc)
}

function Initialize-Log {
  if ([string]::IsNullOrWhiteSpace($script:LogPath)) {
    $downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
    if ([string]::IsNullOrWhiteSpace($downloads)) { $downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Process') }
    if ([string]::IsNullOrWhiteSpace($downloads)) {
      $profile = [Environment]::GetEnvironmentVariable('USERPROFILE','Process')
      if (-not [string]::IsNullOrWhiteSpace($profile)) { $downloads = Join-Path $profile 'Downloads' }
    }
    if ([string]::IsNullOrWhiteSpace($downloads)) { $downloads = (Get-Location).Path }
    if (-not (Test-Path -LiteralPath $downloads -PathType Container)) { New-Item -ItemType Directory -Force -Path $downloads | Out-Null }
    $script:LogPath = Join-Path $downloads ((New-SafeName $ToolName) + '_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log.txt')
  }
  Write-Log "Starting $ToolName version $ToolVersion"
  Write-Log "LogPath: $script:LogPath"
  Write-Log "Mode: $Mode"
  Write-Log "CurrentDirectory: $((Get-Location).Path)"
}

function Write-Log {
  param([AllowNull()][string]$Message)
  $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), [string]$Message
  Write-Host $line
  if (-not [string]::IsNullOrWhiteSpace($script:LogPath)) {
    $parent = Split-Path -Parent $script:LogPath
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Add-Content -LiteralPath $script:LogPath -Value $line -Encoding UTF8
  }
}

function Get-EnvValue {
  param([Parameter(Mandatory=$true)][string]$Name,[AllowNull()][string]$Default,[switch]$Required)
  foreach ($scope in @('Machine','User','Process')) {
    $v = [Environment]::GetEnvironmentVariable($Name,$scope)
    if (-not [string]::IsNullOrWhiteSpace($v)) {
      if ($v -match '^(your|changeme|placeholder|pat_here|token_here|base_here|app_here)$') { throw "$Name in $scope scope looks like a placeholder." }
      return [pscustomobject]@{ Name=$Name; Value=$v.Trim(); Source=$scope; Present=$true }
    }
  }
  if (-not [string]::IsNullOrWhiteSpace($Default)) { return [pscustomobject]@{ Name=$Name; Value=$Default; Source='manifest_default'; Present=$true } }
  if ($Required) { throw "$Name is not set in Machine, User, or Process environment scope." }
  return [pscustomobject]@{ Name=$Name; Value=$null; Source='missing'; Present=$false }
}

function Invoke-Airtable {
  param([Parameter(Mandatory=$true)][string]$Method,[Parameter(Mandatory=$true)][string]$Uri,[Parameter(Mandatory=$true)][hashtable]$Headers,[AllowNull()]$Body)
  try {
    if ($null -ne $Body) {
      $json = $Body | ConvertTo-Json -Depth 60
      return Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers -ContentType 'application/json' -Body $json -ErrorAction Stop
    }
    return Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers -ErrorAction Stop
  } catch {
    throw "Airtable API $Method failed for $Uri :: $($_.Exception.Message)"
  }
}

function Find-Table {
  param($Schema,[string]$TableId,[string]$TableName)
  foreach ($t in @($Schema.tables)) {
    if ($TableId -and [string]$t.id -eq $TableId) { return $t }
    if ($TableName -and [string]$t.name -eq $TableName) { return $t }
  }
  return $null
}

function Find-Field {
  param($Table,[string]$FieldName)
  foreach ($f in @($Table.fields)) { if ([string]$f.name -eq $FieldName) { return $f } }
  return $null
}

function New-FieldBody {
  param($FieldSpec)
  $body = [ordered]@{ name=[string]$FieldSpec.name; type=[string]$FieldSpec.type }
  if ($FieldSpec.PSObject.Properties['description']) { $body['description'] = [string]$FieldSpec.description }
  if ($FieldSpec.PSObject.Properties['options']) { $body['options'] = $FieldSpec.options }
  return $body
}

function Get-Records {
  param([string]$BaseId,[string]$TableId,[hashtable]$Headers)
  $records = New-Object System.Collections.Generic.List[object]
  $offset = $null
  do {
    $uri = 'https://api.airtable.com/v0/' + $BaseId + '/' + [System.Uri]::EscapeDataString($TableId) + '?returnFieldsByFieldId=true&pageSize=100'
    if (-not [string]::IsNullOrWhiteSpace($offset)) { $uri += '&offset=' + [System.Uri]::EscapeDataString($offset) }
    $result = Invoke-Airtable -Method GET -Uri $uri -Headers $Headers -Body $null
    foreach ($r in @($result.records)) { $records.Add($r) | Out-Null }
    $offset = $null
    if ($result.PSObject.Properties['offset']) { $offset = [string]$result.offset }
  } while (-not [string]::IsNullOrWhiteSpace($offset))
  return @($records.ToArray())
}

function Get-FieldValueById {
  param($Fields,[string]$FieldId)
  if ($null -eq $Fields) { return $null }
  $p = $Fields.PSObject.Properties[$FieldId]
  if ($null -eq $p) { return $null }
  return $p.Value
}

function Write-ReportMarkdown {
  param($Report,[string]$Path)
  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add('# DCOIR Airtable Schema Finalizer Report') | Out-Null
  $lines.Add('') | Out-Null
  $lines.Add('- generated_at: ' + $Report.generated_at) | Out-Null
  $lines.Add('- success: ' + $Report.success) | Out-Null
  $lines.Add('- mode: ' + $Report.mode) | Out-Null
  $lines.Add('- table: ' + $Report.table_name + ' / ' + $Report.table_id) | Out-Null
  $lines.Add('') | Out-Null
  $lines.Add('## Schema readback') | Out-Null
  foreach ($a in @($Report.schema_actions)) { $lines.Add('- ' + $a.status + ': ' + $a.field_name + ' (' + $a.field_type + ')') | Out-Null }
  $lines.Add('') | Out-Null
  $lines.Add('## Record readback') | Out-Null
  $lines.Add('- existing_record_count: ' + $Report.record_validation.existing_record_count) | Out-Null
  $lines.Add('- expected_count: ' + $Report.record_validation.expected_count) | Out-Null
  $lines.Add('- missing_expected_keys: ' + @($Report.record_validation.missing_expected_keys).Count) | Out-Null
  $lines.Add('- duplicate_expected_keys: ' + @($Report.record_validation.duplicate_expected_keys).Count) | Out-Null
  $lines.Add('') | Out-Null
  $lines.Add('## Native UI/default tasks') | Out-Null
  foreach ($t in @($Report.native_tasks)) {
    $lines.Add('- ' + $t.task_type + ': ' + $t.field_name) | Out-Null
    if ($t.PSObject.Properties['default_value']) { $lines.Add('  - default: `' + $t.default_value + '`') | Out-Null }
    if ($t.PSObject.Properties['formula']) { $lines.Add('  - formula: `' + $t.formula + '`') | Out-Null }
    if ($t.PSObject.Properties['reason']) { $lines.Add('  - reason: ' + $t.reason) | Out-Null }
  }
  Write-Utf8 -Path $Path -Text (($lines -join [Environment]::NewLine) + [Environment]::NewLine)
}

$script:LogPath = $LogPath
Initialize-Log
try {
  $ManifestJson = [System.IO.Path]::GetFullPath($ManifestJson)
  if (-not (Test-Path -LiteralPath $ManifestJson -PathType Leaf)) { throw "Manifest not found: $ManifestJson" }
  if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
    if ([string]::IsNullOrWhiteSpace($downloads)) { $downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Process') }
    if ([string]::IsNullOrWhiteSpace($downloads)) { $downloads = Split-Path -Parent $script:LogPath }
    $OutputDir = Join-Path $downloads ('dcoir_airtable_schema_finalizer_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
  }
  if (-not (Test-Path -LiteralPath $OutputDir -PathType Container)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }
  Write-Log "OutputDir: $OutputDir"

  $manifest = Get-Content -LiteralPath $ManifestJson -Raw | ConvertFrom-Json
  if ($manifest.schema -ne 'dcoir.airtable.schema_finalizer.v1') { throw "Unexpected manifest schema: $($manifest.schema)" }
  $tokenName = if ($manifest.token_env) { [string]$manifest.token_env } else { 'DCOIR_AIRTABLE_TOKEN' }
  $baseName = if ($manifest.base_id_env) { [string]$manifest.base_id_env } else { 'DCOIR_AIRTABLE_BASE_ID' }
  $token = Get-EnvValue -Name $tokenName -Required
  $base = Get-EnvValue -Name $baseName -Default ([string]$manifest.base_id) -Required
  Write-Log "Airtable token env present from: $($token.Source)"
  Write-Log "Airtable base env source: $($base.Source)"
  $headers = @{ Authorization = 'Bearer ' + $token.Value; Accept = 'application/json' }

  $schema = Invoke-Airtable -Method GET -Uri ('https://api.airtable.com/v0/meta/bases/' + $base.Value + '/tables') -Headers $headers -Body $null
  $table = Find-Table -Schema $schema -TableId ([string]$manifest.table.id) -TableName ([string]$manifest.table.name)
  if ($null -eq $table) { throw "Target table not found: $($manifest.table.name) / $($manifest.table.id)" }

  $schemaActions = New-Object System.Collections.Generic.List[object]
  foreach ($f in @($manifest.supported_fields)) {
    $existing = Find-Field -Table $table -FieldName ([string]$f.name)
    if ($existing) {
      $schemaActions.Add([ordered]@{status='present'; field_name=[string]$f.name; field_type=[string]$existing.type; field_id=[string]$existing.id}) | Out-Null
    } elseif ($Mode -eq 'Apply' -and $AllowCreateFields) {
      $uri = 'https://api.airtable.com/v0/meta/bases/' + $base.Value + '/tables/' + [string]$table.id + '/fields'
      $created = Invoke-Airtable -Method POST -Uri $uri -Headers $headers -Body (New-FieldBody -FieldSpec $f)
      $schemaActions.Add([ordered]@{status='created'; field_name=[string]$created.name; field_type=[string]$created.type; field_id=[string]$created.id}) | Out-Null
    } else {
      $schemaActions.Add([ordered]@{status='missing_planned_only'; field_name=[string]$f.name; field_type=[string]$f.type; field_id=$null}) | Out-Null
    }
  }

  if ($Mode -eq 'Apply' -and $AllowUpsertRecords) {
    Write-Log 'AllowUpsertRecords was set, but this compact first version performs validation-only record readback. Use connector/import lane for new rows until row-upsert extension is promoted.'
  }

  $schema = Invoke-Airtable -Method GET -Uri ('https://api.airtable.com/v0/meta/bases/' + $base.Value + '/tables') -Headers $headers -Body $null
  $table = Find-Table -Schema $schema -TableId ([string]$manifest.table.id) -TableName ([string]$manifest.table.name)
  $fieldMap = @{}
  foreach ($f in @($table.fields)) { $fieldMap[[string]$f.name] = [string]$f.id }
  $records = @(Get-Records -BaseId $base.Value -TableId ([string]$table.id) -Headers $headers)
  $missing = @()
  $dupes = @()
  $expectedKeys = @()
  if ($manifest.records -and $manifest.records.expected_keys) { $expectedKeys = @($manifest.records.expected_keys | ForEach-Object { [string]$_ }) }
  $keyField = if ($manifest.records -and $manifest.records.key_field) { [string]$manifest.records.key_field } else { 'workflow_key' }
  if (-not $fieldMap.ContainsKey($keyField)) { throw "Key field not found: $keyField" }
  $keyFieldId = [string]$fieldMap[$keyField]
  $byKey = @{}
  foreach ($r in $records) {
    $key = [string](Get-FieldValueById -Fields $r.fields -FieldId $keyFieldId)
    if ([string]::IsNullOrWhiteSpace($key)) { continue }
    if (-not $byKey.ContainsKey($key)) { $byKey[$key] = 0 }
    $byKey[$key]++
  }
  foreach ($key in $expectedKeys) {
    if (-not $byKey.ContainsKey($key)) { $missing += $key }
    elseif ($byKey[$key] -gt 1) { $dupes += $key }
  }

  $nativeTasks = @()
  if ($manifest.ui_only_fields) { $nativeTasks += @($manifest.ui_only_fields) }
  if ($manifest.field_defaults) { $nativeTasks += @($manifest.field_defaults) }
  if ($StrictNativeTasks -and @($nativeTasks).Count -gt 0) { throw 'Native UI/default tasks remain and StrictNativeTasks was set.' }

  $success = $true
  if (@($missing).Count -gt 0) { $success = $false }
  if (@($dupes).Count -gt 0) { $success = $false }
  $expectedCount = if ($manifest.records -and $manifest.records.expected_count) { [int]$manifest.records.expected_count } else { 0 }
  if ($expectedCount -gt 0 -and @($records).Count -lt $expectedCount) { $success = $false }

  $report = [ordered]@{
    schema = 'dcoir.airtable.schema_finalizer.report.v1'
    generated_at = (Get-Date -Format o)
    tool = $ToolName
    tool_version = $ToolVersion
    mode = $Mode
    success = $success
    table_id = [string]$table.id
    table_name = [string]$table.name
    schema_actions = @($schemaActions.ToArray())
    native_tasks = @($nativeTasks)
    record_validation = [ordered]@{
      existing_record_count = @($records).Count
      expected_count = $expectedCount
      expected_key_count = @($expectedKeys).Count
      missing_expected_keys = @($missing)
      duplicate_expected_keys = @($dupes)
    }
    output_dir = $OutputDir
    log_path = $script:LogPath
  }
  $jsonPath = Join-Path $OutputDir 'schema_finalizer_report.json'
  $mdPath = Join-Path $OutputDir 'schema_finalizer_report.md'
  Write-Utf8 -Path $jsonPath -Text ($report | ConvertTo-Json -Depth 80)
  Write-ReportMarkdown -Report ([pscustomobject]$report) -Path $mdPath
  $zipPath = Join-Path (Split-Path -Parent $OutputDir) ((Split-Path -Leaf $OutputDir) + '.zip')
  if (Get-Command Compress-Archive -ErrorAction SilentlyContinue) {
    if (Test-Path -LiteralPath $zipPath -PathType Leaf) { Remove-Item -LiteralPath $zipPath -Force }
    Compress-Archive -LiteralPath (Join-Path $OutputDir '*') -DestinationPath $zipPath -Force
    $report['diagnostic_zip'] = $zipPath
    Write-Utf8 -Path $jsonPath -Text ($report | ConvertTo-Json -Depth 80)
  }
  Write-Log "Report: $jsonPath"
  Write-Log "Markdown: $mdPath"
  if ($report.Contains('diagnostic_zip')) { Write-Log "DiagnosticZip: $($report['diagnostic_zip'])" }
  $report | ConvertTo-Json -Depth 80
  if (-not $success) { exit 2 }
} catch {
  Write-Log "ERROR: $($_.Exception.Message)"
  [ordered]@{ success=$false; error=$_.Exception.Message; log_path=$script:LogPath } | ConvertTo-Json -Depth 8
  exit 1
}
