$ErrorActionPreference = 'Stop'

function Insert-AfterHeading {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Heading,
        [Parameter(Mandatory=$true)][string]$InsertText,
        [Parameter(Mandatory=$true)][string]$Marker
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing file: $Path" }
    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ($text -like "*$Marker*") { return $false }
    $idx = $text.IndexOf($Heading)
    if ($idx -lt 0) { throw "Heading not found in $Path: $Heading" }
    $lineEnd = $text.IndexOf("`n", $idx)
    if ($lineEnd -lt 0) { $lineEnd = $text.Length - 1 }
    $before = $text.Substring(0, $lineEnd + 1)
    $after = $text.Substring($lineEnd + 1)
    $newText = $before + "`n" + $InsertText.TrimEnd() + "`n`n" + $after
    Set-Content -LiteralPath $Path -Value $newText -Encoding UTF8
    return $true
}

$changed = @()

$readmeInsert = @'
<!-- heartbeat-readback-contract-20260508 -->

## Heartbeat and artifact readback

For `chatgpt-exec`, `chatgpt-apply-in` / `chatgpt-in`, and `chatgpt-stage-out`, read the committed heartbeat files before asking the operator for screenshots, copied logs, uploaded files, or artifact ZIP handling:

```text
chatgpt_staging/status_reports/<workflow>/<request_id>/workflow_report.md
chatgpt_staging/status_reports/<workflow>/<request_id>/progress_history.jsonl
```

When output files are needed, prefer committed unzipped readback paths before ZIP artifacts:

```text
chatgpt_staging/status_reports/<workflow>/<request_id>/artifact_readback/
chatgpt_staging/out/<request_id>/
```

See `chatgpt_staging/HEARTBEAT_AND_ARTIFACT_READBACK.md` for the shared contract and `chatgpt_staging/docs/` for workflow-specific pointers.
'@
if (Insert-AfterHeading -Path 'chatgpt_staging/README.md' -Heading '## New-session rule' -InsertText $readmeInsert -Marker 'heartbeat-readback-contract-20260508') { $changed += 'chatgpt_staging/README.md' }

$policyInsert = @'
<!-- heartbeat-readback-contract-20260508 -->

## Heartbeat and artifact readback policy

The active shared policy for `chatgpt-exec`, `chatgpt-apply-in` / `chatgpt-in`, and `chatgpt-stage-out` is:

```text
chatgpt_staging/HEARTBEAT_AND_ARTIFACT_READBACK.md
```

Those workflows are live-heartbeat workflows. They should commit `workflow_report.md` and `progress_history.jsonl` after meaningful phase changes so ChatGPT can poll the exact request-id path through the GitHub connector.

When a workflow creates ZIP artifacts, the ZIP is supplemental. Sanitized unzipped output that ChatGPT may need should also be committed as ordinary repo files, normally under `artifact_readback/`; for `chatgpt-stage-out`, `chatgpt_staging/out/<request_id>/` is the primary committed output surface.
'@
if (Insert-AfterHeading -Path 'chatgpt_staging/WORKFLOW_REPORTING_POLICY.md' -Heading '## Reporting model' -InsertText $policyInsert -Marker 'heartbeat-readback-contract-20260508') { $changed += 'chatgpt_staging/WORKFLOW_REPORTING_POLICY.md' }

$execInsert = @'
<!-- heartbeat-readback-contract-20260508 -->

## Heartbeat and artifact readback

Each `chatgpt-exec` run commits live heartbeat files:

```text
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/workflow_report.md
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/progress_history.jsonl
```

Each meaningful phase update should be committed with `[skip ci]` so ChatGPT can read the latest status through the GitHub connector.

The workflow still uploads a ZIP artifact, but the exec harness also copies sanitized artifact contents into:

```text
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/artifact_readback/
```

ChatGPT should read `artifact_readback/` before asking the operator to download/upload a ZIP artifact. See `chatgpt_staging/HEARTBEAT_AND_ARTIFACT_READBACK.md` for the shared contract.
'@
if (Insert-AfterHeading -Path 'chatgpt_staging/EXECUTION_LANE.md' -Heading '## Reports and artifacts' -InsertText $execInsert -Marker 'heartbeat-readback-contract-20260508') { $changed += 'chatgpt_staging/EXECUTION_LANE.md' }

$resultDir = 'chatgpt_staging/status_reports/chatgpt-exec/patch-heartbeat-readback-docs-002/artifact_readback'
New-Item -ItemType Directory -Force -Path $resultDir | Out-Null
$resultPath = Join-Path $resultDir 'docs_patch_result.json'
[ordered]@{
    schema = 'dcoir.docs_patch_result.v1'
    result = 'success'
    changed = $changed
    changed_count = $changed.Count
    note = 'v2 uses Invoke-ChatGptReportPush.ps1 to avoid losing to concurrent heartbeat commits.'
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding UTF8

$paths = @($resultPath)
foreach ($p in $changed) { $paths += $p }
& .\.github\scripts\Invoke-ChatGptReportPush.ps1 -CommitMessage 'Patch heartbeat readback docs v2 [skip ci]' -Paths $paths -RequirePush
if ($LASTEXITCODE -ne 0) { throw "Invoke-ChatGptReportPush.ps1 failed with exit code $LASTEXITCODE" }

Write-Host "Changed docs: $($changed -join ', ')"
