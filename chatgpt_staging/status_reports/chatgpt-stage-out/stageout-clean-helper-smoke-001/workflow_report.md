# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- report_scope: progressive-in-session
- report_family: live-heartbeat
- assistant_polling_target: true
- identifier_type: request_id
- poll_until_result: success_or_failure
- do_not_use_repo_workflows_for_live_polling: true
- result: running
- phase: request-resolved
- request_id: stageout-clean-helper-smoke-001
- request_path: chatgpt_staging/requests/stageout-clean-helper-smoke-001.json
- github_run_id: 25513359787
- github_run_attempt: 1
- github_sha: 00393b595897b68aec536434c741a403a31d384d
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25513359787
- report_updated_utc: 2026-05-07T18:04:30Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-stage-out/stageout-clean-helper-smoke-001/progress_history.jsonl

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

Stage-out request path resolved. Request validation and bundle creation are next.

## Phase history

- 2026-05-07T18:04:30Z | phase=request-resolved | result=running | Stage-out request path resolved. Request validation and bundle creation are next.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.
