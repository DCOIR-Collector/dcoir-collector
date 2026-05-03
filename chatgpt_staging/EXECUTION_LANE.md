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
- `OPENAI_API_KEY`

The workflow generates these runner-local values automatically:

- `DCOIR_REPO_ROOT`
- `DCOIR_DOWNLOADS_DIR`
- `DCOIR_CONFIG_DIR`

Operator workstation path values should not be used for those generated runner-local variables in GitHub Actions.

## Verification wait rule

After ChatGPT stages an exec request, do not treat an immediate missing report as failure. GitHub push-triggered workflows can take a short time to enqueue, start, run, commit a report, and make that report visible through readback.

Default ChatGPT verification behavior:

1. Read back the request commit and request file.
2. Wait a reasonable bounded period before classifying the missing workflow report. Use roughly 60-90 seconds before the first no-report conclusion when the conversation/runtime allows it.
3. Poll for the report and workflow-generated commit during a bounded window, normally up to about 3-5 minutes for this lane.
4. If no report appears in that window, say the request is still pending or has not produced a report yet. Ask whether the operator wants continued checking or manual Actions inspection.
5. Do not call the run failed solely because no report exists immediately after staging.

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

Workflow reports include GitHub run metadata after the report is committed:

- `github_run_id`
- `github_run_attempt`
- `github_sha`
- `github_ref`
- `workflow_run_url`

Use these fields to retrieve artifacts and job logs when the report alone is insufficient.

## Failure-report behavior

If the workflow starts and reaches the harness/reporting path, command failures should still produce a committed status report and a sanitized artifact. That report will normally be under `chatgpt_staging/status_reports/chatgpt-exec/<request_id>/workflow_report.md` with `result: failure` or a harness failure identifier.

A report may not be produced if the workflow never starts, the push trigger does not fire, GitHub Actions is disabled, the workflow YAML itself is invalid before the job starts, checkout fails before the harness runs, repository permissions block commits, or GitHub is delayed/outage-affected. In those cases, inspect the Actions tab or manually dispatch the workflow with the same `request_path`.

## Cleanup

The workflow removes the consumed request file from the repository by default. GitHub Actions artifact retention is controlled by `artifact_retention_days` in the request, bounded by repository settings. Status reports remain until ChatGPT reads them and records any needed evidence, then the existing staging cleanup lane can remove them with `cleanup_status_reports=true`.
