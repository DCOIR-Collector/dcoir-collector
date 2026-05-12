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
- request_id: stageout-20260512-prime-agent-source-readback-002
- request_path: chatgpt_staging/requests/stageout-20260512-prime-agent-source-readback-002.json
- github_run_id: 25720693251
- github_run_attempt: 1
- github_sha: 9c8e784070f6df93bc37782952f9437601c1212d
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25720693251
- report_updated_utc: 2026-05-12T07:42:56Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-stage-out/stageout-20260512-prime-agent-source-readback-002/progress_history.jsonl
- latest_progress_marker_path: chatgpt_staging/status_reports/chatgpt-stage-out/stageout-20260512-prime-agent-source-readback-002/latest_progress_marker.json

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

Stage-out request path resolved. Request validation and bundle creation are next.

## Phase history

- 2026-05-12T07:42:56Z | phase=request-resolved | result=running | Stage-out request path resolved. Request validation and bundle creation are next.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.
