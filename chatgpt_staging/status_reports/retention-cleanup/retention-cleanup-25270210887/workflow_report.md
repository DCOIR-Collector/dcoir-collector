# ChatGPT workflow report

## Result

- workflow: chatgpt-report-retention-cleanup
- report_scope: retention-cleanup
- result: success
- mode: delete
- success_retention_days: 7
- failure_retention_days: 30
- cleanup_retention_days: 7
- keep_latest_per_workflow: true
- workflow_filter: 
- candidate_count: 0
- retained_count: 9
- github_run_id: 25270210887
- github_sha: d670c15915e1f725d5198a50cfaf4ce99c54c5bd
- report_created_utc: 2026-05-03T04:49:48Z

## Reports selected for cleanup
- none

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/cleanup_failure_25259970239/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 30d
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260502-/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261023978/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261233739/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261570066/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-reporting-validation/25261738515/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-reporting-validation/25261773354/workflow_report.md` | result=failure | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25262009553/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25262135315/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 7d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material.
