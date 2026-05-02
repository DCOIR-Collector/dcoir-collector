# ChatGPT workflow report

## Result

- workflow: chatgpt-staging-cleanup
- result: success
- phase: cleanup
- request_id_filter: val-20260502-
- github_run_id: 25260217844
- github_sha: 1610e195079156ef1e6dadf3ed1de75d38643d8f
- github_ref: refs/heads/main
- removed_count: 14
- report_created_utc: 2026-05-02T19:41:33Z

## Removed paths
- chatgpt_staging/requests/val-20260502-stageout-bad-schema-001.json
- chatgpt_staging/in/val-20260502-apply-bad-schema-001
- chatgpt_staging/in/val-20260502-missing-hash-001
- chatgpt_staging/in/val-20260502-workflow-guard-001
- chatgpt_staging/apply_reports/val-20260502-apply-create-only-001_apply_report.md
- chatgpt_staging/apply_reports/val-20260502-override-visible-001_apply_report.md
- chatgpt_staging/status_reports/chatgpt-apply-in/val-20260502-apply-bad-schema-001
- chatgpt_staging/status_reports/chatgpt-apply-in/val-20260502-apply-create-only-001
- chatgpt_staging/status_reports/chatgpt-apply-in/val-20260502-missing-hash-001
- chatgpt_staging/status_reports/chatgpt-apply-in/val-20260502-override-visible-001
- chatgpt_staging/status_reports/chatgpt-apply-in/val-20260502-workflow-guard-001
- chatgpt_staging/status_reports/chatgpt-stage-out/val-20260502-stageout-bad-schema-001
- chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260502-stageout-docs-001
- chatgpt_staging/cleanup_requests/val-20260502-cleanup-batch-001.json

## Retained or skipped paths
- chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260502-

## Cleanup guidance

This cleanup report can be removed by a future cleanup marker with cleanup_status_reports=true after ChatGPT reads it.

## Next ChatGPT action

Verify scoped deletion by GitHub readback, update Airtable evidence if material, then remove this report when safe.
