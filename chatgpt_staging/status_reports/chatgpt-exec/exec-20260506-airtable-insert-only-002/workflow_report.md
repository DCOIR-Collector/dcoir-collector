# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- result: success
- phase: approved-command-execution
- request_id: exec-20260506-airtable-insert-only-002
- shell: powershell_5
- exit_code: 0
- timed_out: False
- command_sha256: d0484a228fff748d7bfc9497244d4ba39e24a2c38a54ba985477bbf8e3daf3b8
- artifact_name: chatgpt-exec-exec-20260506-airtable-insert-only-002
- artifact_retention_days: 3
- started_utc: 2026-05-06T17:58:37Z
- finished_utc: 2026-05-06T17:58:39Z
- report_created_utc: 2026-05-06T17:58:39Z

## Approved command preview

```text
Run approved repo script chatgpt_staging/exec_scripts/airtable_insert_only_002.ps1 for corrected Airtable insert-only smoke test. Do not delete the row in this workflow.
```

## Executed command

```powershell
& 'D:\a\dcoir-collector\dcoir-collector\chatgpt_staging\exec_scripts\airtable_insert_only_002.ps1'
```

## Standard output preview

```text
DCOIR_AIRTABLE_INSERT_ONLY_002=started
INSERT_RECORD_ID=recuCEINatbFNXWE6
INSERT_EVIDENCE_KEY=VAL-CHATGPT-EXEC-AIRTABLE-INSERT-ONLY-20260506-002
DCOIR_AIRTABLE_INSERT_ONLY_002=success

```

## Standard error preview

```text

```

## Artifact guidance

Artifact chatgpt-exec-exec-20260506-airtable-insert-only-002 contains sanitized stdout/stderr, sanitized request, sanitized command, exec_result.json, and any files written under DCOIR_DOWNLOADS_DIR.

## Cleanup guidance

The request file is removed automatically when cleanup_request_after_run=true. This status report can be cleaned later with cleanup_status_reports=true after ChatGPT records evidence. GitHub Actions artifacts expire by configured retention.

## Next ChatGPT action

Read this report and download the artifact if needed; record evidence and clean the status report when safe.

## GitHub Actions run

- github_run_id: 25452140184
- github_run_attempt: 1
- github_sha: e93ebb94849369e9fa945ced3670bf7844d744be
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25452140184
