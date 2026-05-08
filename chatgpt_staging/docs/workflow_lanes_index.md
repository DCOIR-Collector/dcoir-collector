# Workflow lanes index

Status: new-session index for ChatGPT-controlled workflow lanes.

| Lane | Use for | Status | Output/readback |
|---|---|---|---|
| `chatgpt-exec` | approved command execution and bulk operational work | `chatgpt_staging/status_reports/chatgpt-exec/<request_id>/workflow_report.md` and `progress_history.jsonl` | `chatgpt_staging/status_reports/chatgpt-exec/<request_id>/artifact_readback/` |
| `chatgpt-apply-in` / `chatgpt-in` | governed repo patches from a payload manifest | `chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/workflow_report.md` and `progress_history.jsonl` | native apply-in report embedded in `workflow_report.md`; use `artifact_readback/` only if generated |
| `chatgpt-stage-out` | repo/file packaging for ChatGPT readback | `chatgpt_staging/status_reports/chatgpt-stage-out/<request_id>/workflow_report.md` and `progress_history.jsonl` | `chatgpt_staging/out/<request_id>/` |

Read exact request-id heartbeat paths first. ZIP artifacts are supplemental.
