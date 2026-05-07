# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- result: success
- phase: bundle-created
- request_id: stageout-20260507-heartbeat-regression-001
- request_path: chatgpt_staging/requests/stageout-20260507-heartbeat-regression-001.json
- output_dir: chatgpt_staging/out/stageout-20260507-heartbeat-regression-001
- github_run_id: 25504717350
- github_sha: db0da09130a9eb7111b5c65f2b4d53fbafdb2e2a
- github_ref: refs/heads/main
- report_created_utc: 2026-05-07T15:15:24Z

## Output

- chatgpt_staging/out/stageout-20260507-heartbeat-regression-001/chunks/001__write_chatgpt_progress_report.py__chunk001.txt
- chatgpt_staging/out/stageout-20260507-heartbeat-regression-001/chunks/001__write_chatgpt_progress_report.py__chunk002.txt
- chatgpt_staging/out/stageout-20260507-heartbeat-regression-001/manifest.json
- chatgpt_staging/out/stageout-20260507-heartbeat-regression-001/manifest.md
- chatgpt_staging/out/stageout-20260507-heartbeat-regression-001/staged_files.zip

## Cleanup guidance

After ChatGPT retrieves the needed output, create a cleanup marker for request id 'stageout-20260507-heartbeat-regression-001' with cleanup_out_bundles=true and cleanup_status_reports=true.

## Next ChatGPT action

Read manifest.md/manifest.json and staged_files.zip or chunks under chatgpt_staging/out/stageout-20260507-heartbeat-regression-001. Record evidence, then request cleanup when safe.
