# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- report_scope: progressive-in-session
- report_family: live-heartbeat
- assistant_polling_target: true
- identifier_type: request_id
- poll_until_result: success_or_failure
- do_not_use_repo_workflows_for_live_polling: true
- result: failure
- phase: apply-in-failure
- request_id: unsafe_or_unknown
- request_path: 
- github_run_id: 25678785200
- github_run_attempt: 1
- github_sha: c11d2b64103d6faa1878387b0c7f6f9dcf6080ce
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25678785200
- report_updated_utc: 2026-05-11T15:11:16Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-apply-in/unsafe_or_unknown/progress_history.jsonl
- latest_progress_marker_path: chatgpt_staging/status_reports/chatgpt-apply-in/unsafe_or_unknown/latest_progress_marker.json
- artifact_name: chatgpt-apply-in-failure-25678785200

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

The apply-in workflow failed. Native failure details are appended below.

## Phase history

- 2026-05-11T15:11:16Z | phase=apply-in-failure | result=failure | The apply-in workflow failed. Native failure details are appended below.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.

## Native apply-in failure report

# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: unsafe_or_unknown
- payload_path: 
- expected_payload_shape: single chatgpt_staging/in/<request_id>/payload.zip.b64
- github_run_id: 25678785200
- github_ref: refs/heads/main
- github_sha: c11d2b64103d6faa1878387b0c7f6f9dcf6080ce
- artifact_name: chatgpt-apply-in-failure-25678785200
- artifact_retention_days: 7
- report_created_utc: 2026-05-11T15:11:15Z

## Troubleshooting context

The apply-in workflow failed. This workflow only accepts one payload.zip.b64 file. Parts/chunks, chunk manifests, payload.zip.b64.parts, invalid base64, missing root apply_manifest.json, missing root files/, unsafe paths, stale hashes, create_only violations, delete policy violations, or workflow-change policy violations are hard failures.


## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, regenerate a single payload.zip.b64 with current hashes, then retry. Do not switch to parts/chunks.
