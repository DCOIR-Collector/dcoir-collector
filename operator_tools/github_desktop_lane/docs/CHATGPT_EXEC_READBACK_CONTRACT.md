# ChatGPT exec readback contract

Use this note when a session is working with `chatgpt-exec`, `chatgpt-apply-in`, or `chatgpt-stage-out`.

## Required read order

1. Read the workflow report for the exact request id.
2. Read the progress history for the exact request id.
3. Read committed unzipped output before using ZIP artifacts.

## Canonical paths

```text
chatgpt_staging/status_reports/<workflow>/<request_id>/workflow_report.md
chatgpt_staging/status_reports/<workflow>/<request_id>/progress_history.jsonl
chatgpt_staging/status_reports/<workflow>/<request_id>/artifact_readback/
chatgpt_staging/out/<request_id>/
```

## Exec output path

For `chatgpt-exec`, command output files written under `DCOIR_DOWNLOADS_DIR` appear under:

```text
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/artifact_readback/downloads/<output_folder>/
```

## Canonical policy

```text
chatgpt_staging/HEARTBEAT_AND_ARTIFACT_READBACK.md
```

`chatgpt-exec` copies sanitized artifact contents into `artifact_readback/` beside the committed workflow report. ZIP artifacts remain available but are supplemental.
