$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = (Get-Location).Path }
$out = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($out)) { throw 'DCOIR_DOWNLOADS_DIR is not set.' }

$airtableModule = Join-Path $repo 'operator_tools\github_desktop_lane\modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
$updateModule = Join-Path $repo 'operator_tools\github_desktop_lane\modules\Dcoir.AirtableBulkUpdate\Dcoir.AirtableBulkUpdate.psm1'
Import-Module $airtableModule -Force
Import-Module $updateModule -Force

$baseId = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID' -Required
$token = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TOKEN' -Required
$headers = New-DcoirAirtableAuthHeader -ApiToken $token
$headers['Content-Type'] = 'application/json'

$inputPath = Join-Path $repo 'chatgpt_staging\exec_inputs\dcoir-alias-normalization-20260508\approval_packet.json'
if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) { throw ('Missing approval packet input: ' + $inputPath) }
$packet = Get-Content -LiteralPath $inputPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$packet.packet_id -ne 'APPROVAL-DBREDESIGN-WBS02-ALIAS-NORMALIZATION-20260508') { throw 'Unexpected packet_id.' }
if (-not [bool]$packet.operator_approved_in_chat) { throw 'Approval packet is not marked operator_approved_in_chat.' }
if ([int]$packet.expected_total_updates -ne 8) { throw 'Expected total updates must be 8.' }
$targets = @($packet.target_records)
if ($targets.Count -ne 8) { throw ('Target count mismatch. Expected 8 got ' + $targets.Count) }

$runRoot = Join-Path $out 'dcoir_alias_normalization_20260508'
New-Item -ItemType Directory -Force -Path $runRoot | Out-Null
$targetPath = Join-Path $runRoot 'target_records.json'
$payloadPath = Join-Path $runRoot 'planned_payload.json'
$summaryPath = Join-Path $runRoot 'execution_summary.json'
$verifyPath = Join-Path $runRoot 'after_readback_verification.json'
$errorPath = Join-Path $runRoot 'error_report.json'

try {
  [ordered]@{
    packet_id = [string]$packet.packet_id
    plan_key = [string]$packet.plan_key
    readback_required = $true
    expected_total_updates = [int]$packet.expected_total_updates
    target_records = $targets
    disallowed_actions = $packet.disallowed_actions
  } | ConvertTo-Json -Depth 60 | Out-File -FilePath $targetPath -Encoding utf8

  $result = Invoke-DcoirAirtableSelectAliasUpdateWithBeforeGates -BaseId $baseId -Headers $headers -TargetRecords $targets -BatchSize 10 -Typecast:$false

  $result.planned_payload | ConvertTo-Json -Depth 80 | Out-File -FilePath $payloadPath -Encoding utf8
  [ordered]@{
    result = [string]$result.result
    packet_id = [string]$packet.packet_id
    plan_key = [string]$packet.plan_key
    input_count = [int]$result.input_count
    updated_count = [int]$result.updated_count
    expected_total_updates = [int]$packet.expected_total_updates
    module_version = Get-DcoirAirtableBulkUpdateVersion
    artifacts = @('target_records.json','planned_payload.json','execution_summary.json','after_readback_verification.json')
  } | ConvertTo-Json -Depth 30 | Out-File -FilePath $summaryPath -Encoding utf8

  [ordered]@{
    result = if ([string]$result.result -eq 'success') { 'pass' } else { 'fail' }
    packet_id = [string]$packet.packet_id
    before_readback = $result.before_readback
    after_readback = $result.after_readback
    after_mismatches = $result.after_mismatches
  } | ConvertTo-Json -Depth 80 | Out-File -FilePath $verifyPath -Encoding utf8

  if ([string]$result.result -ne 'success') { throw 'Alias normalization update failed after-readback verification.' }
  [ordered]@{ result='success'; packet_id=[string]$packet.packet_id; updated_count=[int]$result.updated_count; output_dir=$runRoot } | ConvertTo-Json -Depth 10
}
catch {
  [ordered]@{
    result = 'failed'
    packet_id = if ($packet) { [string]$packet.packet_id } else { $null }
    error_message = $_.Exception.Message
    error_type = $_.Exception.GetType().FullName
    script_stack_trace = $_.ScriptStackTrace
    output_dir = $runRoot
  } | ConvertTo-Json -Depth 20 | Out-File -FilePath $errorPath -Encoding utf8
  throw
}
