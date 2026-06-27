# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- report_scope: progressive-in-session
- report_family: live-heartbeat
- assistant_polling_target: true
- identifier_type: request_id
- poll_until_result: success_or_failure
- do_not_use_repo_workflows_for_live_polling: true
- result: running
- phase: running-harness
- request_id: dcoir-review-fix-guidance-normalization-20260627T121000Z
- request_path: chatgpt_staging/exec_requests/dcoir-review-fix-guidance-normalization-20260627T121000Z.json
- github_run_id: 28288787187
- github_run_attempt: 1
- github_sha: ac8de39b05081e8ce39a9b2006ed77ad5c36e7e7
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/DCOIR-Collector/dcoir-collector/actions/runs/28288787187
- report_updated_utc: 2026-06-27T12:10:43Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-exec/dcoir-review-fix-guidance-normalization-20260627T121000Z/progress_history.jsonl
- latest_progress_marker_path: chatgpt_staging/status_reports/chatgpt-exec/dcoir-review-fix-guidance-normalization-20260627T121000Z/latest_progress_marker.json

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

Approved command harness is about to run. If this report remains in this phase, inspect the GitHub run URL for harness/runtime progress.

## Phase history

- 2026-06-27T12:10:41Z | phase=request-resolved | result=running | Exec request path resolved. The workflow is preparing to run the approved command harness.
- 2026-06-27T12:10:43Z | phase=running-harness | result=running | Approved command harness is about to run. If this report remains in this phase, inspect the GitHub run URL for harness/runtime progress.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.
