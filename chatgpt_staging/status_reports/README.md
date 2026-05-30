# ChatGPT status reports

This directory has three report families. Do not mix them.

## Live heartbeat reports

Use these for active ChatGPT-staged jobs while they are running.

Paths:

- `chatgpt_staging/status_reports/chatgpt-exec/<request_id>/workflow_report.md`
- `chatgpt_staging/status_reports/chatgpt-stage-out/<request_id>/workflow_report.md`
- `chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/workflow_report.md`
- `chatgpt_staging/status_reports/chatgpt-github-artifact-readback/<request_id>/workflow_report.md`

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

### Custom markdown handoff

Completed-run workflows may add concise workflow-specific context to the central reporter by uploading an artifact with this exact shape:

- artifact name: `chatgpt-workflow-report-section`
- file path inside artifact: `chatgpt_workflow_report_section.md`

The central `chatgpt-workflow-run-reporter` appends that markdown to the completed-run `workflow_report.md` after the standard generated report body. Use this for short, high-signal summaries that help ChatGPT read back run-specific results without opening every artifact or log. Do not use this handoff for live heartbeat status; request-scoped ChatGPT workflows should keep using their stable live heartbeat report path.

Current custom markdown producers:

- `run-gemini-behavioral-replay-manual`
- `manual-gemini-model-comparison`
- `chatgpt-workflow-reporting-validation`
- `Workflow maintenance audit`

## Standalone committed reports

Use these after cleanup or retention workflows produce their own committed report outside the central repo-workflows reporter.

Path examples:

- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/<request_id-or-run>/workflow_report.md`
- `chatgpt_staging/status_reports/retention-cleanup/<run-id>/workflow_report.md`

Expected metadata:

- `report_family`: workflow-specific cleanup or retention report
- `assistant_polling_target`: false unless the workflow explicitly documents live polling
- `identifier_type`: request id, run id, or retention cleanup id, as documented by the workflow

Operating rule for ChatGPT:

Use standalone committed reports as scoped cleanup or retention evidence. Do not assume these reports came from the central completed-run reporter, and do not use them as live heartbeat targets unless the workflow-specific header says to do so.
