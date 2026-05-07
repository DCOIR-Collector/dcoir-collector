# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- report_scope: progressive-in-session
- result: failure
- phase: stage-out-failure
- request_id: stageout-20260507-heartbeat-regression-001
- request_path: chatgpt_staging/requests/stageout-20260507-heartbeat-regression-001.json
- github_run_id: 25504717350
- github_run_attempt: 1
- github_sha: db0da09130a9eb7111b5c65f2b4d53fbafdb2e2a
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25504717350
- report_updated_utc: 2026-05-07T15:15:25Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-stage-out/stageout-20260507-heartbeat-regression-001/progress_history.jsonl

## Current status

The stage-out workflow failed. Native failure details are appended below.

## Phase history

- 2026-05-07T15:15:21Z | phase=request-resolved | result=running | Stage-out request path resolved. Request validation and bundle creation are next.
- 2026-05-07T15:15:23Z | phase=running-stage-out | result=running | Stage-out bundle creation is about to run. If this report remains in this phase, inspect the GitHub run URL for runtime progress.
- 2026-05-07T15:15:24Z | phase=bundle-created | result=success | Stage-out bundle was created successfully. Native stage-out output details are appended below.
- 2026-05-07T15:15:25Z | phase=stage-out-failure | result=failure | The stage-out workflow failed. Native failure details are appended below.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.

## Native stage-out failure report

# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- result: failure
- phase: stage-out
- request_id: stageout-20260507-heartbeat-regression-001
- request_path: chatgpt_staging/requests/stageout-20260507-heartbeat-regression-001.json
- github_run_id: 25504717350
- github_sha: db0da09130a9eb7111b5c65f2b4d53fbafdb2e2a
- github_ref: refs/heads/main
- report_created_utc: 2026-05-07T15:15:25Z

## Troubleshooting notes

The stage-out workflow failed before producing a trusted output bundle. Common causes include malformed JSON, missing or wrong schema, unsafe request_id, missing allowed_roots, disallowed paths, or no selected files. Inspect the GitHub Actions run logs for full details.

## Cleanup guidance

Do not retry with the same request id until ChatGPT reads this report. Create a cleanup marker with cleanup_status_reports=true when this report is no longer needed.

## Next ChatGPT action

Read this report, inspect the run log if needed, update Airtable with the failure phase, then repair or regenerate the request.
