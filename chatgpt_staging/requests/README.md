# ChatGPT staging requests

This directory is for narrow staging-lane request helpers.

For any staging workflow, read the exact request-id heartbeat files first:

```text
chatgpt_staging/status_reports/<workflow>/<request_id>/workflow_report.md
chatgpt_staging/status_reports/<workflow>/<request_id>/progress_history.jsonl
```

For output files, prefer committed folders over ZIP artifacts:

```text
chatgpt_staging/status_reports/<workflow>/<request_id>/artifact_readback/
chatgpt_staging/out/<request_id>/
```
