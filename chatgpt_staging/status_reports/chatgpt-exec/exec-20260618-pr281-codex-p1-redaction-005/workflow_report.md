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
- request_id: exec-20260618-pr281-codex-p1-redaction-005
- request_path: chatgpt_staging/exec_requests/exec-20260618-pr281-codex-p1-redaction-005.json
- github_run_id: 27793463610
- github_run_attempt: 1
- github_sha: 7784e9f324baedf0fe3b5a287b2d2ec45e5e8b67
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/DCOIR-Collector/dcoir-collector/actions/runs/27793463610
- report_updated_utc: 2026-06-18T22:35:12Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-exec/exec-20260618-pr281-codex-p1-redaction-005/progress_history.jsonl
- latest_progress_marker_path: chatgpt_staging/status_reports/chatgpt-exec/exec-20260618-pr281-codex-p1-redaction-005/latest_progress_marker.json
- artifact_name: chatgpt-exec-exec-20260618-pr281-codex-p1-redaction-005
- exit_code: 1

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

Final exec status is being committed with workflow report, progress history, marker, and any tracked summary files already produced by the request/tool. Full output remains in the uploaded GitHub Actions artifact.

## Phase history

- 2026-06-18T22:34:57Z | phase=request-resolved | result=running | Exec request path resolved. The workflow is preparing to run the approved command harness.
- 2026-06-18T22:35:00Z | phase=running-harness | result=running | Approved command harness is about to run. If this report remains in this phase, inspect the GitHub run URL for harness/runtime progress.
- 2026-06-18T22:35:10Z | phase=harness-finished | result=failure | Approved command harness finished with exit code 1. Final native exec status commit is next.
- 2026-06-18T22:35:12Z | phase=final-readback-commit | result=failure | Final exec status is being committed with workflow report, progress history, marker, and any tracked summary files already produced by the request/tool. Full output remains in the uploaded GitHub Actions artifact.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.

## GitHub Actions run

- github_run_id: 27793463610
- github_run_attempt: 1
- github_sha: 7784e9f324baedf0fe3b5a287b2d2ec45e5e8b67
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/DCOIR-Collector/dcoir-collector/actions/runs/27793463610

## Output readback contract

- heartbeat_report: committed in this request-scoped status directory
- tracked_summaries: read any concise summary files beside this report when present
- full_output: uploaded GitHub Actions artifact named in this report
- artifact_readback: optional and normally not committed for chatgpt-exec because .gitignore intentionally excludes unzipped artifact_readback trees
