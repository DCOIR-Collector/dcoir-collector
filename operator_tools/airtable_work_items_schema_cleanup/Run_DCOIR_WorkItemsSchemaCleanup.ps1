param(
    [ValidateSet('self-test','dry-run','apply-options','apply-safe','verify','generate-option-delete-script','attempt-api-option-delete','attempt-field-delete')]
    [string]$Mode = 'dry-run',
    [string]$BaseId = '',
    [string]$TableId = '',
    [switch]$DeletePrefixedFields,
    [string[]]$FieldId = @(),
    [string]$ConfirmFieldDelete = '',
    [string]$ConfirmOptionDelete = ''
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutDir = if ($env:DCOIR_DOWNLOADS_DIR) { $env:DCOIR_DOWNLOADS_DIR } else { Join-Path $ScriptDir 'out' }
if (!(Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$Log = Join-Path $OutDir ("work_items_schema_cleanup_${Mode}_${Stamp}.log")
$Py = Join-Path $ScriptDir 'dcoir_work_items_schema_cleanup.py'

$argsList = @($Py, '--mode', $Mode)
if ($BaseId) { $argsList += @('--base-id', $BaseId) }
if ($TableId) { $argsList += @('--table-id', $TableId) }
if ($DeletePrefixedFields) { $argsList += '--delete-prefixed-fields' }
foreach ($f in $FieldId) { $argsList += @('--field-id', $f) }
if ($ConfirmFieldDelete) { $argsList += @('--confirm-field-delete', $ConfirmFieldDelete) }
if ($ConfirmOptionDelete) { $argsList += @('--confirm-option-delete', $ConfirmOptionDelete) }

Write-Host "DCOIR Work Items schema cleanup mode: $Mode"
Write-Host "Log: $Log"
Write-Host "Expected success marker: DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_DONE"
Write-Host "Token source: DCOIR_AIRTABLE_TOKEN or AIRTABLE_TOKEN (value not printed)"

& python -S @argsList 2>&1 | Tee-Object -FilePath $Log
if ($LASTEXITCODE -ne 0) { throw "Cleanup tool failed with exit code $LASTEXITCODE. See $Log" }
Write-Host "DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_WRAPPER_DONE"
