# ChatGPT Exec Lane

Status: initial active execution lane for reviewed operator-approved commands in GitHub Actions.

## Purpose

This lane lets ChatGPT stage a reviewed command request for GitHub Actions to execute in a Windows runner while keeping source tools unchanged. The runner bridges GitHub Actions secrets into Machine-scope environment variables so tools that use `[Environment]::GetEnvironmentVariable(..., 'Machine')` can run the same way they run locally.

## Request path

```text
chatgpt_staging/exec_requests/<request_id>.json
```

A request file triggers `.github/workflows/chatgpt-exec.yml` on push to `main`.

## Request contract

Required fields:

- `schema`: `dcoir.chatgpt_staging.exec_request.v1`
- `request_id`: safe identifier using letters, numbers, dots, underscores, or hyphens
- `operator_approved`: `true`
- `approved_command_preview`: the command preview shown to the operator before staging
- `command`: the exact command to execute

Recommended fields:

- `approved_at_utc`
- `shell`: `powershell_5`, `pwsh`, or `cmd`
- `timeout_seconds`
- `artifact_retention_days`
- `cleanup_request_after_run`

## Secret handling

Do not commit secret values into request files. Put values in GitHub Actions repository secrets with the same DCOIR Local Configuration Registry names. The workflow currently bridges these names when present:

- `DCOIR_AIRTABLE_TOKEN`
- `DCOIR_AIRTABLE_BASE_ID`
- `DCOIR_GITHUB_FG_TOKEN`
- `DCOIR_GITHUB_CL_TOKEN`
- `DCOIR_OPENAI_API_KEY`
- `DCOIR_OPENAI_PROJECT_ID`

The workflow generates these runner-local values automatically:

- `DCOIR_REPO_ROOT`
- `DCOIR_DOWNLOADS_DIR`
- `DCOIR_CONFIG_DIR`

## Reports and artifacts

Each run writes one committed status report:

```text
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/workflow_report.md
```

Each run uploads one GitHub Actions artifact:

```text
chatgpt-exec-<request_id>
```

The artifact contains sanitized stdout/stderr, sanitized request/command, `exec_result.json`, and any files written under `DCOIR_DOWNLOADS_DIR`.

## Cleanup

The workflow removes the consumed request file from the repository by default. GitHub Actions artifact retention is controlled by `artifact_retention_days` in the request, bounded by repository settings. Status reports remain until ChatGPT reads them and records any needed evidence, then the existing staging cleanup lane can remove them with `cleanup_status_reports=true`.
