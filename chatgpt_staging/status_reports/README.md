# ChatGPT status reports

This directory has two different report families. Do not mix them.

## Live heartbeat reports

Use these for active ChatGPT-staged jobs while they are running.

Paths:

- `chatgpt_staging/status_reports/chatgpt-exec/<request_id>/workflow_report.md`
- `chatgpt_staging/status_reports/chatgpt-stage-out/<request_id>/workflow_report.md`
- `chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/workflow_report.md`

Expected metadata:

- `report_family: live-heartbeat`
- `assistant_polling_target: true`
- `identifier_type: request_id`
- `poll_until_result: success_or_failure`

Operating rule for ChatGPT:

1. Stage the request once.
2. Poll the stable `workflow_report.md` path by `request_id` while the job runs.
3. Keep polling until `result` is `success` or `failure`.
4. Use `progress_history.jsonl` and the report phase history to understand current progress.
5. Do not restage or modify the request while the run may be queued or running.

## Completed workflow-run summaries

Use these after a GitHub workflow has completed, especially for bounded failure-log excerpts.

Path pattern:

- `chatgpt_staging/status_reports/repo-workflows/<workflow>/<github_run_id>/workflow_report.md`

Expected metadata:

- `report_family: completed-run-summary`
- `assistant_polling_target: false`
- `identifier_type: github_run_id`
- `do_not_use_for_live_polling: true`

Operating rule for ChatGPT:

Use repo-workflows reports for post-completion diagnostics and failure summaries. Do not use repo-workflows reports to monitor active ChatGPT-staged jobs. For active jobs, use the live heartbeat request-id path instead.
