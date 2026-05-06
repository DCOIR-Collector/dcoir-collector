$ErrorActionPreference = 'Stop'
Write-Output 'DCOIR_AIRTABLE_INSERT_ONLY_002=started'

if ([string]::IsNullOrWhiteSpace($env:DCOIR_AIRTABLE_BASE_ID)) { throw 'Missing DCOIR_AIRTABLE_BASE_ID' }
if ([string]::IsNullOrWhiteSpace($env:DCOIR_AIRTABLE_TOKEN)) { throw 'Missing DCOIR_AIRTABLE_TOKEN' }

$baseId = $env:DCOIR_AIRTABLE_BASE_ID
$tableId = 'tblrPFQH2uZEYBYE9'
$evidenceKey = 'VAL-CHATGPT-EXEC-AIRTABLE-INSERT-ONLY-20260506-002'
$headers = @{
  Authorization = ('Bearer ' + $env:DCOIR_AIRTABLE_TOKEN)
  'Content-Type' = 'application/json'
}

$fields = [ordered]@{
  'fldua3G9lRVdiIpEO' = $evidenceKey
  'fld42VCNN0p0kbzVp' = 'CHATGPT-EXEC-AIRTABLE-INSERT-ONLY'
  'fldD5IQJtuwW2GKXH' = 'CLEANUP-WBS-08-02'
  'fld6PWvy2bMvqMpUt' = 'Insert-only smoke test created by chatgpt-exec using Airtable Records API with field IDs only. This row should be returned by the next row-return workflow and deleted by the following delete workflow.'
  'flddBu10OfbDkTxfj' = 'chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-insert-only-002/workflow_report.md'
}

$body = @{ records = @(@{ fields = $fields }) } | ConvertTo-Json -Depth 8
$createUrl = "https://api.airtable.com/v0/$baseId/$tableId"

try {
  $created = Invoke-RestMethod -Method Post -Uri $createUrl -Headers $headers -Body $body
} catch {
  $status = 'unknown'
  try { $status = [int]$_.Exception.Response.StatusCode } catch {}
  $errBody = ''
  try {
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $errBody = $reader.ReadToEnd()
  } catch {}
  if ($errBody.Length -gt 1200) { $errBody = $errBody.Substring(0,1200) }
  $errBody = $errBody -replace $env:DCOIR_AIRTABLE_TOKEN, '[REDACTED_TOKEN]'
  Write-Error ("Airtable insert failed; http_status={0}; body={1}" -f $status, $errBody)
}

$recordId = $created.records[0].id
if ([string]::IsNullOrWhiteSpace($recordId)) { throw 'Insert succeeded but record id missing' }

Write-Output ('INSERT_RECORD_ID=' + $recordId)
Write-Output ('INSERT_EVIDENCE_KEY=' + $evidenceKey)
Write-Output 'DCOIR_AIRTABLE_INSERT_ONLY_002=success'
