# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- report_scope: progressive-in-session
- report_family: live-heartbeat
- assistant_polling_target: true
- identifier_type: request_id
- poll_until_result: success_or_failure
- do_not_use_repo_workflows_for_live_polling: true
- result: failure
- phase: final-readback-commit
- request_id: exec-20260508-wbs22-wave2-readonly-verification-003
- request_path: chatgpt_staging/exec_requests/exec-20260508-wbs22-wave2-readonly-verification-003.json
- github_run_id: 25552051418
- github_run_attempt: 1
- github_sha: f62f2effbe55eda5b68f3f8e6f34bd9734a9d51d
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25552051418
- report_updated_utc: 2026-05-08T11:03:17Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-readonly-verification-003/progress_history.jsonl
- latest_progress_marker_path: chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-readonly-verification-003/latest_progress_marker.json
- artifact_name: chatgpt-exec-exec-20260508-wbs22-wave2-readonly-verification-003
- exit_code: 1

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

Final exec readback is being committed with workflow report, progress history, marker, and artifact_readback files.

## Phase history

- 2026-05-08T11:03:07Z | phase=request-resolved | result=running | Exec request path resolved. The workflow is preparing to run the approved command harness.
- 2026-05-08T11:03:09Z | phase=running-harness | result=running | Approved command harness is about to run. If this report remains in this phase, inspect the GitHub run URL for harness/runtime progress.
- 2026-05-08T11:03:14Z | phase=harness-finished | result=failure | Approved command harness finished with exit code 1. Final native exec report commit is next.
- 2026-05-08T11:03:17Z | phase=final-readback-commit | result=failure | Final exec readback is being committed with workflow report, progress history, marker, and artifact_readback files.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.

## GitHub Actions run

- github_run_id: 25552051418
- github_run_attempt: 1
- github_sha: f62f2effbe55eda5b68f3f8e6f34bd9734a9d51d
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25552051418

## Artifact readback

- artifact_readback_path: chatgpt_staging\status_reports\chatgpt-exec\exec-20260508-wbs22-wave2-readonly-verification-003\artifact_readback
- readback_contract: committed sanitized unzipped artifact files are authoritative for ChatGPT readback before ZIP artifact handling.
