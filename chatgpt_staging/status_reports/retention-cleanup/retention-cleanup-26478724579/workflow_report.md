# ChatGPT workflow report

## Result

- workflow: chatgpt-report-retention-cleanup
- report_scope: retention-cleanup
- report_family: retention-cleanup-summary
- assistant_polling_target: false
- identifier_type: cleanup_run_id
- do_not_use_for_live_polling: true
- result: success
- mode: delete
- success_retention_days: 1
- failure_retention_days: 7
- cleanup_retention_days: 2
- keep_latest_per_workflow: true
- workflow_filter: 
- candidate_count: 0
- retained_count: 2
- github_run_id: 26478724579
- github_sha: 4465ed3684c0e2b99aa8b9b7cdbceaddd3d12514
- report_created_utc: 2026-05-26T22:27:12Z

## Reports selected for cleanup
- none

## Reports retained or skipped
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26462091818/workflow_report.md` | result=cleanup | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26463647792/workflow_report.md` | result=cleanup | age_days=0.2 | reason=latest report for workflow

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
