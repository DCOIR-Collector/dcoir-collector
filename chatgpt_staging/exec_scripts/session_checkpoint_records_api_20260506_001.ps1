$ErrorActionPreference = 'Stop'

$checkpointId = 'CHK-DCOIR-AIRTABLE-CLEANUP-CLOSEOUT-20260506-CHATGPT-EXEC-TOOLPATH-WBS09'
$tableId = 'tblTe75HKZOJaPDGn'
$baseId = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
if ([string]::IsNullOrWhiteSpace($baseId)) { $baseId = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Process') }
if ([string]::IsNullOrWhiteSpace($baseId)) { $baseId = 'appM4KSwnVf3G3OTK' }

$token = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Machine')
if ([string]::IsNullOrWhiteSpace($token)) { $token = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Process') }
if ([string]::IsNullOrWhiteSpace($token)) { throw 'DCOIR_AIRTABLE_TOKEN is not available to chatgpt-exec.' }

$headers = @{
  Authorization = "Bearer $token"
  'Content-Type' = 'application/json'
}

$checkpointAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$endpoint = "https://api.airtable.com/v0/$baseId/$tableId"

function Invoke-AirtableRecordsApi {
  param(
    [Parameter(Mandatory=$true)][string]$Method,
    [Parameter(Mandatory=$true)][string]$Uri,
    [object]$Body = $null
  )
  if ($null -eq $Body) {
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers
  }
  $jsonBody = $Body | ConvertTo-Json -Depth 20
  return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -Body $jsonBody
}

$fields = [ordered]@{
  checkpoint_id = $checkpointId
  session_id = '20260506-CHATGPT-EXEC-TOOLPATH-WBS09'
  state_summary = 'Closeout recovery checkpoint after regular Airtable connector disappeared and prior closeout failed from Airtable metadata API use. This request uses Airtable records API only against Session Checkpoints table tblTe75HKZOJaPDGn.'
  current_focus = 'Verify durable Session Checkpoint readback, then resume chatgpt-exec tool_path/operator_tools multi-language hardening, then WBS08-01.'
  open_threads = '1. Verify checkpoint workflow report and Airtable records API readback. 2. Resume tool_path/operator_tools hardening for PowerShell, Python, cmd/bat, shell, and future languages. 3. Preserve script_path and inline command compatibility. 4. Add committed diagnostics for malformed exec requests. 5. Return to WBS08-01 only after checkpoint verification and tool_path hardening.'
  decisions_constraints = 'Records API only; no Airtable metadata API for closeout. Do not assume checkpoint exists. Do not mark WBS complete without evidence. Prefer governed chatgpt-exec/apply-in lanes over manual bundles. Missing regular Airtable connector and missing installed dcoir-session-manager surface are drift to carry forward.'
  next_recommended_move = 'Verify this checkpoint by workflow report and Airtable records API readback; then resume tool_path/operator_tools multi-language hardening; then WBS08-01.'
  resume_prompt = 'Resume AFRICOM_SOC_IR / DCOIR. Re-anchor Airtable-first. Verify Session Checkpoint CHK-DCOIR-AIRTABLE-CLEANUP-CLOSEOUT-20260506-CHATGPT-EXEC-TOOLPATH-WBS09 exists in Session Checkpoints table tblTe75HKZOJaPDGn using Airtable records API only. Then resume chatgpt-exec tool_path/operator_tools multi-language hardening, preserving script_path and inline command compatibility, and only after that return to WBS08-01.'
  checkpoint_at = $checkpointAt
}

$escapedCheckpointId = $checkpointId.Replace("'", "\'")
$formula = "{checkpoint_id} = '$escapedCheckpointId'"
$queryUri = $endpoint + '?maxRecords=1&filterByFormula=' + [System.Uri]::EscapeDataString($formula)

$existing = Invoke-AirtableRecordsApi -Method Get -Uri $queryUri
if ($existing.records.Count -gt 0) {
  $recordId = [string]$existing.records[0].id
  $writeResult = Invoke-AirtableRecordsApi -Method Patch -Uri $endpoint -Body @{ records = @(@{ id = $recordId; fields = $fields }) }
  $operation = 'updated'
} else {
  $writeResult = Invoke-AirtableRecordsApi -Method Post -Uri $endpoint -Body @{ records = @(@{ fields = $fields }) }
  $operation = 'created'
  $recordId = [string]$writeResult.records[0].id
}

$readback = Invoke-AirtableRecordsApi -Method Get -Uri $queryUri
if ($readback.records.Count -lt 1) { throw "Checkpoint write completed but readback did not return $checkpointId." }
$readbackFields = $readback.records[0].fields
if ([string]$readbackFields.checkpoint_id -ne $checkpointId) { throw "Checkpoint readback mismatch for $checkpointId." }

$outDir = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($outDir)) { $outDir = Join-Path $env:TEMP 'dcoir_chatgpt_exec_outputs' }
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$verification = [ordered]@{
  schema = 'dcoir.session_checkpoint.closeout_verification.v1'
  checkpoint_id = $checkpointId
  operation = $operation
  record_id = $recordId
  table_id = $tableId
  api_family = 'Airtable records API only'
  metadata_api_used = $false
  verified_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  next_recommended_move = $fields.next_recommended_move
}
$verificationPath = Join-Path $outDir 'session_checkpoint_closeout_records_api_verification.json'
$verification | ConvertTo-Json -Depth 10 | Out-File -FilePath $verificationPath -Encoding utf8
Write-Output ("Session checkpoint {0}: {1} ({2}) via Airtable records API only." -f $operation, $checkpointId, $recordId)
Write-Output ("Verification artifact: {0}" -f $verificationPath)
