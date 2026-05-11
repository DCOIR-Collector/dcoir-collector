# ChatGPT workflow report

## Result

- workflow: chatgpt-staging-cleanup
- result: success
- phase: cleanup
- request_id_filter: applyin-20260511-gemini-usb-subagent-clean-001
- github_run_id: 25677276399
- github_sha: a16b2bb9ce33cb4a6e1a2afcff63e6f6eb763214
- github_ref: refs/heads/main
- removed_count: 3
- report_created_utc: 2026-05-11T14:44:56Z

## Removed paths
- chatgpt_staging/in/applyin-20260511-gemini-usb-subagent-clean-001
- chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260511-gemini-usb-subagent-clean-001
- chatgpt_staging/cleanup_requests/cleanup-20260511-usb-gemini-applyin-stale-payload-001.json

## Retained or skipped paths
- chatgpt_staging/status_reports/chatgpt-staging-cleanup/applyin-20260511-gemini-usb-subagent-clean-001

## Cleanup guidance

This cleanup report can be removed by a future cleanup marker with cleanup_status_reports=true after ChatGPT reads it.

## Next ChatGPT action

Verify scoped deletion by GitHub readback, update Airtable evidence if material, then remove this report when safe.
