# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- result: success
- phase: approved-command-execution
- request_id: exec-20260505-wbs03-note-format-001
- shell: powershell_5
- exit_code: 0
- timed_out: False
- command_sha256: d5aae03601415623d61888f501bca22bc47a6a23396911e44af0aea5492d4868
- artifact_name: chatgpt-exec-exec-20260505-wbs03-note-format-001
- artifact_retention_days: 3
- started_utc: 2026-05-05T17:40:41Z
- finished_utc: 2026-05-05T17:40:41Z
- report_created_utc: 2026-05-05T17:40:41Z

## Approved command preview

```text
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
$outDir = Join-Path $downloads 'wbs03_note_format_20260505'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$model = [ordered]@{ note_purpose='explain structured state without replacing it'; required_sections=@('context','evidence','structured_anchor','decision_or_recommendation','approval_gate','next_review'); rule='A note must cite or align to a structured field, evidence report, or registry key when it makes an operational claim.'; forbidden_patterns=@('approval only in note','completion only in note','deletion only in note','source authority only in note','unanchored readiness claim') }
$model | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $outDir 'standard_note_format.json') -Encoding UTF8
$md = @('# WBS03 standard note format','','Purpose: keep free text explanatory while structured fields carry authority.','','## Required note sections','','- context: why the note exists','- evidence: report, row, or source locator','- structured_anchor: field/key/state the note explains','- decision_or_recommendation: non-authoritative narrative unless backed by structured field','- approval_gate: explicit if action needs operator approval','- next_review: review_after or follow-up trigger when applicable','','## Forbidden patterns','','- approval only in note','- completion only in note','- deletion only in note','- source authority only in note','- unanchored readiness claim')
$md | Set-Content -LiteralPath (Join-Path $outDir 'standard_note_format.md') -Encoding UTF8
Write-Output ('Generated WBS03 standard note format at ' + $outDir)
```

## Executed command

```powershell
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
$outDir = Join-Path $downloads 'wbs03_note_format_20260505'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$model = [ordered]@{ note_purpose='explain structured state without replacing it'; required_sections=@('context','evidence','structured_anchor','decision_or_recommendation','approval_gate','next_review'); rule='A note must cite or align to a structured field, evidence report, or registry key when it makes an operational claim.'; forbidden_patterns=@('approval only in note','completion only in note','deletion only in note','source authority only in note','unanchored readiness claim') }
$model | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $outDir 'standard_note_format.json') -Encoding UTF8
$md = @('# WBS03 standard note format','','Purpose: keep free text explanatory while structured fields carry authority.','','## Required note sections','','- context: why the note exists','- evidence: report, row, or source locator','- structured_anchor: field/key/state the note explains','- decision_or_recommendation: non-authoritative narrative unless backed by structured field','- approval_gate: explicit if action needs operator approval','- next_review: review_after or follow-up trigger when applicable','','## Forbidden patterns','','- approval only in note','- completion only in note','- deletion only in note','- source authority only in note','- unanchored readiness claim')
$md | Set-Content -LiteralPath (Join-Path $outDir 'standard_note_format.md') -Encoding UTF8
Write-Output ('Generated WBS03 standard note format at ' + $outDir)
```

## Standard output preview

```text
Generated WBS03 standard note format at D:\a\_temp\dcoir_chatgpt_exec\exec-20260505-wbs03-note-format-001\downloads\wbs03_note_format_20260505

```

## Standard error preview

```text

```

## Artifact guidance

Artifact chatgpt-exec-exec-20260505-wbs03-note-format-001 contains sanitized stdout/stderr, sanitized request, sanitized command, exec_result.json, and any files written under DCOIR_DOWNLOADS_DIR.

## Cleanup guidance

The request file is removed automatically when cleanup_request_after_run=true. This status report can be cleaned later with cleanup_status_reports=true after ChatGPT records evidence. GitHub Actions artifacts expire by configured retention.

## Next ChatGPT action

Read this report and download the artifact if needed; record evidence and clean the status report when safe.

## GitHub Actions run

- github_run_id: 25392377044
- github_run_attempt: 1
- github_sha: 121921fda163d5ba47d39a0f5704f36480ce3df9
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25392377044
