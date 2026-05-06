$ErrorActionPreference = 'Stop'
Write-Output 'DCOIR_AIRTABLE_RETURN_ROW_001=started'

$baseId = $env:DCOIR_AIRTABLE_BASE_ID
$tableId = 'tblrPFQH2uZEYBYE9'
$recordId = 'recuCEINatbFNXWE6'
$expectedEvidenceKey = 'VAL-CHATGPT-EXEC-AIRTABLE-INSERT-ONLY-20260506-002'

if ([string]::IsNullOrWhiteSpace($baseId)) { throw 'Missing DCOIR_AIRTABLE_BASE_ID' }
if ([string]::IsNullOrWhiteSpace($env:DCOIR_AIRTABLE_TOKEN)) { throw 'Missing DCOIR_AIRTABLE_TOKEN' }

$headers = @{ Authorization = ('Bearer ' + $env:DCOIR_AIRTABLE_TOKEN) }
$url = "https://api.airtable.com/v0/$baseId/$tableId/$recordId?returnFieldsByFieldId=true"
$record = Invoke-RestMethod -Method Get -Uri $url -Headers $headers

$evidenceKey = $record.fields.'fldua3G9lRVdiIpEO'
Write-Output ('RETURN_RECORD_ID=' + $record.id)
Write-Output ('RETURN_EVIDENCE_KEY=' + $evidenceKey)

if ($record.id -ne $recordId) { throw 'Returned record id mismatch' }
if ($evidenceKey -ne $expectedEvidenceKey) { throw 'Returned evidence key mismatch' }

Write-Output 'DCOIR_AIRTABLE_RETURN_ROW_001=success'
