# ChatGPT workflow report

## Result

- workflow: chatgpt-staging-cleanup
- result: success
- phase: cleanup
- request_id_filter: artifact-readback-staging-26581484030-validate-gemini-behavioral-replay
- github_run_id: 26598610666
- github_sha: b81b5258fc6b3420a36c618cdf859c734fd0adc4
- github_ref: refs/heads/main
- removed_count: 3
- report_created_utc: 2026-05-28T19:54:48Z

## Removed paths
- chatgpt_staging/out/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay
- chatgpt_staging/status_reports/chatgpt-github-artifact-readback/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay
- chatgpt_staging/cleanup_requests/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay.json

## Retained or skipped paths
- chatgpt_staging/status_reports/chatgpt-staging-cleanup/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay

## Cleanup guidance

This cleanup report can be removed by a future cleanup marker with cleanup_status_reports=true after ChatGPT reads it.

## Next ChatGPT action

Verify scoped deletion by GitHub readback, update Airtable evidence if material, then remove this report when safe.
