# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- report_scope: progressive-in-session
- report_family: live-heartbeat
- assistant_polling_target: true
- identifier_type: request_id
- poll_until_result: success_or_failure
- do_not_use_repo_workflows_for_live_polling: true
- result: success
- phase: bundle-applied-before-commit
- request_id: apply-heartbeat-readback-docs-final-001
- request_path: chatgpt_staging/in/apply-heartbeat-readback-docs-final-001/payload.zip.b64
- github_run_id: 25542991912
- github_run_attempt: 1
- github_sha: eb51e0abafb68ca053966aaae42dd4859ad4e924
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25542991912
- report_updated_utc: 2026-05-08T07:27:27Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-apply-in/apply-heartbeat-readback-docs-final-001/progress_history.jsonl

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

Apply-in bundle was applied successfully before commit. Native apply-in details are appended below.

## Phase history

- 2026-05-08T07:27:18Z | phase=payload-resolved | result=running | Apply-in payload path resolved. Decode and apply validation are next.
- 2026-05-08T07:27:24Z | phase=running-apply-in | result=running | Apply-in decode, manifest validation, file copy/delete, and hash checks are about to run.
- 2026-05-08T07:27:27Z | phase=bundle-applied-before-commit | result=success | Apply-in bundle was applied successfully before commit. Native apply-in details are appended below.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.

## Native apply-in success report

# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: success
- phase: bundle-applied-before-commit
- request_id: apply-heartbeat-readback-docs-final-001
- payload_path: chatgpt_staging/in/apply-heartbeat-readback-docs-final-001/payload.zip.b64
- payload_shape: single payload.zip.b64
- github_run_id: 25542991912
- github_sha: eb51e0abafb68ca053966aaae42dd4859ad4e924
- github_ref: refs/heads/main
- report_created_utc: 2026-05-08T07:27:27Z

## Applied paths
- chatgpt_staging/docs/README.md
- chatgpt_staging/docs/workflow_status_output_quickstart.md
- chatgpt_staging/docs/exec_request_readback.md
- chatgpt_staging/docs/apply_in_readback.md
- chatgpt_staging/docs/stage_out_readback.md
- chatgpt_staging/docs/workflow_lanes_index.md
- chatgpt_staging/docs/apply_in_payload_generation.md
- chatgpt_staging/in/README.md
- chatgpt_staging/exec_requests/README.md
- chatgpt_staging/requests/README.md
- operator_tools/github_desktop_lane/docs/CHATGPT_HEARTBEAT_READBACK.md
- operator_tools/github_desktop_lane/docs/CHATGPT_EXEC_READBACK_CONTRACT.md

## Deleted paths
- none

## Cleanup guidance

After ChatGPT verifies the commit/readback and no longer needs this report, create a cleanup marker for request id 'apply-heartbeat-readback-docs-final-001' with cleanup_status_reports=true.

## Next ChatGPT action

Verify the committed target changes, hash policy outcome, deletion outcome, and apply report. If readback is good, update Airtable and clean this status report when safe.
