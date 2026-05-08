# Apply-in readback

After staging `chatgpt-apply-in` / `chatgpt-in`, monitor the committed heartbeat files:

```text
chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/workflow_report.md
chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/progress_history.jsonl
```

Read the committed workflow report and native apply-in report before asking the operator for screenshots, logs, or uploads.

If a future apply-in run produces additional artifact-only evidence, the workflow should also commit it under:

```text
chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/artifact_readback/
```
