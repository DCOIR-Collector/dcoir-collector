# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- result: success
- phase: approved-command-execution
- request_id: exec-20260506-airtable-token-diagnostic-001
- shell: powershell_5
- exit_code: 0
- timed_out: False
- command_sha256: 1d48f378a288be10d8e465bc38f98eb0283492b054f7f5e24f7a4aa4eaa80053
- artifact_name: chatgpt-exec-exec-20260506-airtable-token-diagnostic-001
- artifact_retention_days: 3
- started_utc: 2026-05-06T17:32:29Z
- finished_utc: 2026-05-06T17:32:33Z
- report_created_utc: 2026-05-06T17:32:33Z

## Approved command preview

```text
Read-only Airtable token diagnostic via chatgpt-exec. Test DCOIR_AIRTABLE_BASE_ID and DCOIR_AIRTABLE_TOKEN against known table IDs using Records API with maxRecords=1. Print only sanitized HTTP status and table labels, no secrets.
```

## Executed command

```powershell
$ErrorActionPreference = 'Stop'
Write-Output 'DCOIR_AIRTABLE_TOKEN_DIAG=started'
if ([string]::IsNullOrWhiteSpace($env:DCOIR_AIRTABLE_BASE_ID)) { throw 'Missing DCOIR_AIRTABLE_BASE_ID' }
if ([string]::IsNullOrWhiteSpace($env:DCOIR_AIRTABLE_TOKEN)) { throw 'Missing DCOIR_AIRTABLE_TOKEN' }
$baseId = $env:DCOIR_AIRTABLE_BASE_ID
$headers = @{ Authorization = ('Bearer ' + $env:DCOIR_AIRTABLE_TOKEN); 'Content-Type' = 'application/json' }
$tests = @(
  @{label='Session Checkpoints'; id='tblTe75HKZOJaPDGn'},
  @{label='DCOIR Cleanup WBS'; id='tblRxTmpW0VunQlUK'},
  @{label='Validation Evidence'; id='tblrPFQH2uZEYBYE9'},
  @{label='Local Configuration Registry'; id='tblcJxCoYGpEda0FM'}
)
foreach ($t in $tests) {
  $url = "https://api.airtable.com/v0/$baseId/$($t.id)?maxRecords=1"
  try {
    $r = Invoke-RestMethod -Method Get -Uri $url -Headers $headers
    $count = 0
    if ($null -ne $r.records) { $count = $r.records.Count }
    Write-Output ("TABLE_TEST label={0}; table_id={1}; result=success; records_returned={2}" -f $t.label, $t.id, $count)
  } catch {
    $status = 'unknown'
    try { $status = [int]$_.Exception.Response.StatusCode } catch {}
    $body = ''
    try {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $body = $reader.ReadToEnd()
    } catch {}
    if ($body.Length -gt 300) { $body = $body.Substring(0,300) }
    $body = $body -replace $env:DCOIR_AIRTABLE_TOKEN, '[REDACTED_TOKEN]'
    Write-Output ("TABLE_TEST label={0}; table_id={1}; result=failure; http_status={2}; body={3}" -f $t.label, $t.id, $status, $body)
  }
}
Write-Output 'DCOIR_AIRTABLE_TOKEN_DIAG=complete'
```

## Standard output preview

```text
DCOIR_AIRTABLE_TOKEN_DIAG=started
TABLE_TEST label=Session Checkpoints; table_id=tblTe75HKZOJaPDGn; result=success; records_returned=1
TABLE_TEST label=DCOIR Cleanup WBS; table_id=tblRxTmpW0VunQlUK; result=success; records_returned=1
TABLE_TEST label=Validation Evidence; table_id=tblrPFQH2uZEYBYE9; result=success; records_returned=1
TABLE_TEST label=Local Configuration Registry; table_id=tblcJxCoYGpEda0FM; result=success; records_returned=1
DCOIR_AIRTABLE_TOKEN_DIAG=complete

```

## Standard error preview

```text

```

## Artifact guidance

Artifact chatgpt-exec-exec-20260506-airtable-token-diagnostic-001 contains sanitized stdout/stderr, sanitized request, sanitized command, exec_result.json, and any files written under DCOIR_DOWNLOADS_DIR.

## Cleanup guidance

The request file is removed automatically when cleanup_request_after_run=true. This status report can be cleaned later with cleanup_status_reports=true after ChatGPT records evidence. GitHub Actions artifacts expire by configured retention.

## Next ChatGPT action

Read this report and download the artifact if needed; record evidence and clean the status report when safe.

## GitHub Actions run

- github_run_id: 25450911139
- github_run_attempt: 1
- github_sha: 91508ab11c4e5e5d6b155a12e02df24514f95888
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25450911139
