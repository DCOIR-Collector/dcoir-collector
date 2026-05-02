# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- result: failure
- phase: stage-out
- request_id: val-20260502-stageout-bad-schema-001
- request_path: chatgpt_staging/requests/val-20260502-stageout-bad-schema-001.json
- github_run_id: 25260118770
- github_sha: 7fea3578bf8b5817ef39227c9208c7ea0f1757ed
- github_ref: refs/heads/main
- report_created_utc: 2026-05-02T19:36:16Z

## Troubleshooting notes

The stage-out workflow failed before producing a trusted output bundle. Common causes include malformed JSON, missing or wrong schema, unsafe request_id, missing allowed_roots, disallowed paths, or no selected files. Inspect the GitHub Actions run logs for full details.

## Cleanup guidance

Do not retry with the same request id until ChatGPT reads this report. Create a cleanup marker with cleanup_status_reports=true when this report is no longer needed.

## Next ChatGPT action

Read this report, inspect the run log if needed, update Airtable with the failure phase, then repair or regenerate the request.
