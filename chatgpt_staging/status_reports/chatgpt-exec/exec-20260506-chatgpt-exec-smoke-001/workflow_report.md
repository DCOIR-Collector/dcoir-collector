# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- result: success
- phase: approved-command-execution
- request_id: exec-20260506-chatgpt-exec-smoke-001
- shell: powershell_5
- exit_code: 0
- timed_out: False
- command_sha256: e0572cd0a4a492ee80e24dba1d0fd5ffb0cbb39a692809160335698f9cf0901d
- artifact_name: chatgpt-exec-exec-20260506-chatgpt-exec-smoke-001
- artifact_retention_days: 7
- started_utc: 2026-05-06T17:13:20Z
- finished_utc: 2026-05-06T17:13:20Z
- report_created_utc: 2026-05-06T17:13:20Z

## Approved command preview

```text
Harmless chatgpt-exec smoke test after restoring workflow allowlist. Print static status, PowerShell version, repo path presence, and current UTC time. Do not print secrets.
```

## Executed command

```powershell
$ErrorActionPreference = 'Stop'
Write-Output 'DCOIR_CHATGPT_EXEC_SMOKE=started'
Write-Output ('PSVersion=' + $PSVersionTable.PSVersion.ToString())
Write-Output ('RepoRootExists=' + (Test-Path -LiteralPath $env:GITHUB_WORKSPACE -PathType Container))
Write-Output ('UtcNow=' + (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))
Write-Output 'DCOIR_CHATGPT_EXEC_SMOKE=success'
```

## Standard output preview

```text
DCOIR_CHATGPT_EXEC_SMOKE=started
PSVersion=5.1.26100.32684
RepoRootExists=True
UtcNow=2026-05-06T17:13:20Z
DCOIR_CHATGPT_EXEC_SMOKE=success

```

## Standard error preview

```text

```

## Artifact guidance

Artifact chatgpt-exec-exec-20260506-chatgpt-exec-smoke-001 contains sanitized stdout/stderr, sanitized request, sanitized command, exec_result.json, and any files written under DCOIR_DOWNLOADS_DIR.

## Cleanup guidance

The request file is removed automatically when cleanup_request_after_run=true. This status report can be cleaned later with cleanup_status_reports=true after ChatGPT records evidence. GitHub Actions artifacts expire by configured retention.

## Next ChatGPT action

Read this report and download the artifact if needed; record evidence and clean the status report when safe.

## GitHub Actions run

- github_run_id: 25450006458
- github_run_attempt: 1
- github_sha: 0e334bac8569f520b396fc169a99b94045fa8409
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25450006458
