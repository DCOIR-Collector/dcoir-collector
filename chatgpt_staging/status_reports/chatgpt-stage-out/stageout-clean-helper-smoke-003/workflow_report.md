# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- report_scope: progressive-in-session
- report_family: live-heartbeat
- assistant_polling_target: true
- identifier_type: request_id
- poll_until_result: success_or_failure
- do_not_use_repo_workflows_for_live_polling: true
- result: success
- phase: bundle-created
- request_id: stageout-clean-helper-smoke-003
- request_path: chatgpt_staging/requests/stageout-clean-helper-smoke-003.json
- github_run_id: 25514140072
- github_run_attempt: 1
- github_sha: a1ea296cc8217c3de5df7fbe4a525ad64b2ab5a3
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25514140072
- report_updated_utc: 2026-05-07T18:20:56Z
- progress_history_path: chatgpt_staging/status_reports/chatgpt-stage-out/stageout-clean-helper-smoke-003/progress_history.jsonl

## Report routing

This is the live heartbeat report for an active ChatGPT-staged job. Poll this exact request_id path until result is success or failure. Do not use repo-workflows completed-run summaries for live progress polling.

## Current status

Stage-out bundle was created successfully. Native stage-out output details are appended below.

## Phase history

- 2026-05-07T18:20:48Z | phase=request-resolved | result=running | Stage-out request path resolved. Request validation and bundle creation are next.
- 2026-05-07T18:20:53Z | phase=running-stage-out | result=running | Stage-out bundle creation is about to run. If this report remains in this phase, inspect the GitHub run URL for runtime progress.
- 2026-05-07T18:20:56Z | phase=bundle-created | result=success | Stage-out bundle was created successfully. Native stage-out output details are appended below.

## Next ChatGPT action

Poll this same report path until result is success or failure. If result is running, use the phase history to decide whether to wait, inspect the run URL, or report a blocker.

## Native stage-out report

# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- result: success
- phase: bundle-created
- request_id: stageout-clean-helper-smoke-003
- request_path: chatgpt_staging/requests/stageout-clean-helper-smoke-003.json
- output_dir: chatgpt_staging/out/stageout-clean-helper-smoke-003
- github_run_id: 25514140072
- github_sha: a1ea296cc8217c3de5df7fbe4a525ad64b2ab5a3
- github_ref: refs/heads/main
- report_created_utc: 2026-05-07T18:20:56Z

## Output

- chatgpt_staging/out/stageout-clean-helper-smoke-003/chunks/001__Invoke-ChatGptReportPush.ps1__chunk001.txt
- chatgpt_staging/out/stageout-clean-helper-smoke-003/chunks/001__Invoke-ChatGptReportPush.ps1__chunk002.txt
- chatgpt_staging/out/stageout-clean-helper-smoke-003/chunks/002__Wait-ChatGptWorkflowReport.ps1__chunk001.txt
- chatgpt_staging/out/stageout-clean-helper-smoke-003/manifest.json
- chatgpt_staging/out/stageout-clean-helper-smoke-003/manifest.md
- chatgpt_staging/out/stageout-clean-helper-smoke-003/staged_files.zip

## Cleanup guidance

After ChatGPT retrieves the needed output, create a cleanup marker for request id 'stageout-clean-helper-smoke-003' with cleanup_out_bundles=true and cleanup_status_reports=true.

## Next ChatGPT action

Read manifest.md/manifest.json and staged_files.zip or chunks under chatgpt_staging/out/stageout-clean-helper-smoke-003. Record evidence, then request cleanup when safe.
