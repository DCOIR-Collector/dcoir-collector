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

New-Item -ItemType Directory -Force -Path 'chatgpt_staging/status_reports/chatgpt-exec/patch-heartbeat-readback-docs-001/artifact_readback' | Out-Null
$reportPath = 'chatgpt_staging/status_reports/chatgpt-exec/patch-heartbeat-readback-docs-001/artifact_readback/docs_patch_result.json'
[ordered]@{
    schema = 'dcoir.docs_patch_result.v1'
    result = 'success'
    changed = $changed
    changed_count = $changed.Count
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding UTF8

if ($changed.Count -gt 0) {
    git config user.name 'github-actions[bot]'
    git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
    foreach ($p in $changed) { git add -- $p }
    git add -- $reportPath
    git commit -m 'Patch heartbeat readback docs [skip ci]'
    git push origin HEAD:main
}

Write-Host "Changed docs: $($changed -join ', ')"
