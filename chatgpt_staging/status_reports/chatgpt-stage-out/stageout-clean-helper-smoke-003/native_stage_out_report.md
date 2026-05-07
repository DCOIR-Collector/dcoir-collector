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
