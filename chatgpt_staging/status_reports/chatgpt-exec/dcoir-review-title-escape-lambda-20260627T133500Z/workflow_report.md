# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- report_scope: progressive-in-session
- report_family: live-heartbeat
- assistant_polling_target: true
- identifier_type: request_id
- poll_until_result: success_or_failure
- do_not_use_repo_workflows_for_live_polling: true
- result: success
- phase: final-readback-commit
- request_id: dcoir-review-title-escape-lambda-20260627T133500Z
- request_path: chatgpt_staging/exec_requests/dcoir-review-title-escape-lambda-20260627T133500Z.json
- github_run_id: 28290688825
- github_run_attempt: 1
- github_sha: 603f59cbaa807baa38880138e97438a7cbcb8fed
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/DCOIR-Collector/dcoir-collector/actions/runs/28290688825
- report_updated_utc: 2026-06-27T13:32:02Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-exec/dcoir-review-title-escape-lambda-20260627T133500Z/progress_history.jsonl
- latest_progress_marker_path: chatgpt_staging/status_reports/chatgpt-exec/dcoir-review-title-escape-lambda-20260627T133500Z/latest_progress_marker.json
- artifact_name: chatgpt-exec-dcoir-review-title-escape-lambda-20260627T133500Z
- exit_code: 0

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

Final exec status is being committed with workflow report, progress history, marker, and any tracked summary files already produced by the request/tool. Full output remains in the uploaded GitHub Actions artifact.

## Phase history

- 2026-06-27T13:31:51Z | phase=request-resolved | result=running | Exec request path resolved. The workflow is preparing to run the approved command harness.
- 2026-06-27T13:31:54Z | phase=running-harness | result=running | Approved command harness is about to run. If this report remains in this phase, inspect the GitHub run URL for harness/runtime progress.
- 2026-06-27T13:31:59Z | phase=harness-finished | result=success | Approved command harness finished with exit code 0. Final native exec status commit is next.
- 2026-06-27T13:32:02Z | phase=final-readback-commit | result=success | Final exec status is being committed with workflow report, progress history, marker, and any tracked summary files already produced by the request/tool. Full output remains in the uploaded GitHub Actions artifact.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.

## GitHub Actions run

- github_run_id: 28290688825
- github_run_attempt: 1
- github_sha: 603f59cbaa807baa38880138e97438a7cbcb8fed
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/DCOIR-Collector/dcoir-collector/actions/runs/28290688825

## Output readback contract

- heartbeat_report: committed in this request-scoped status directory
- tracked_summaries: read any concise summary files beside this report when present
- full_output: uploaded GitHub Actions artifact named in this report
- artifact_readback: optional and normally not committed for chatgpt-exec because .gitignore intentionally excludes unzipped artifact_readback trees
