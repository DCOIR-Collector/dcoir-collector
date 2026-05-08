# Exec request readback

After staging a `chatgpt-exec` request, monitor the committed heartbeat files:

```text
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/workflow_report.md
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/progress_history.jsonl
```

For output inspection, read the committed unzipped readback path first:

```text
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/artifact_readback/
```

Use the ZIP artifact only as fallback or supplemental provenance.
