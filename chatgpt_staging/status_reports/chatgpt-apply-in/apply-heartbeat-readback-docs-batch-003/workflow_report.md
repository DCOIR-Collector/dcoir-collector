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
- request_id: apply-heartbeat-readback-docs-batch-003
- request_path: chatgpt_staging/in/apply-heartbeat-readback-docs-batch-003/payload.zip.b64
- github_run_id: 25542336890
- github_run_attempt: 1
- github_sha: 7231ef863cb5ce88f7047fc5de0e1eda7b3caf80
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25542336890
- report_updated_utc: 2026-05-08T07:11:05Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-apply-in/apply-heartbeat-readback-docs-batch-003/progress_history.jsonl
- artifact_name: chatgpt-apply-in-failure-25542336890

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

The apply-in workflow failed. Native failure details are appended below.

## Phase history

- 2026-05-08T07:10:58Z | phase=payload-resolved | result=running | Apply-in payload path resolved. Decode and apply validation are next.
- 2026-05-08T07:11:03Z | phase=running-apply-in | result=running | Apply-in decode, manifest validation, file copy/delete, and hash checks are about to run.
- 2026-05-08T07:11:05Z | phase=apply-in-failure | result=failure | The apply-in workflow failed. Native failure details are appended below.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.

## Native apply-in failure report

# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: apply-heartbeat-readback-docs-batch-003
- payload_path: chatgpt_staging/in/apply-heartbeat-readback-docs-batch-003/payload.zip.b64
- expected_payload_shape: single chatgpt_staging/in/<request_id>/payload.zip.b64
- github_run_id: 25542336890
- github_ref: refs/heads/main
- github_sha: 7231ef863cb5ce88f7047fc5de0e1eda7b3caf80
- artifact_name: chatgpt-apply-in-failure-25542336890
- artifact_retention_days: 7
- report_created_utc: 2026-05-08T07:11:05Z

## Troubleshooting context

The apply-in workflow failed. This workflow only accepts one payload.zip.b64 file. Parts/chunks, chunk manifests, payload.zip.b64.parts, invalid base64, missing root apply_manifest.json, missing root files/, unsafe paths, stale hashes, create_only violations, delete policy violations, or workflow-change policy violations are hard failures.


## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, regenerate a single payload.zip.b64 with current hashes, then retry. Do not switch to parts/chunks.
