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
