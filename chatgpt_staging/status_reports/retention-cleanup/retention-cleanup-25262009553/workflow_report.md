# ChatGPT workflow report

## Result

- workflow: chatgpt-report-retention-cleanup
- report_scope: retention-cleanup
- result: success
- mode: dry-run
- success_retention_days: 0
- failure_retention_days: 30
- cleanup_retention_days: 7
- keep_latest_per_workflow: true
- workflow_filter: repo-workflows/chatgpt-workflow-reporting-validation
- candidate_count: 1
- retained_count: 6
- github_run_id: 25262009553
- github_sha: 6b08fb578402b6b7e52f2cb4bde9964c98efbf54
- report_created_utc: 2026-05-02T21:13:02Z

## Reports that would be cleaned
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-reporting-validation/25261738515/workflow_report.md` | result=success | age_days=0.0 | reason=age 0.0d >= 0d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/cleanup_failure_25259970239/workflow_report.md` | result=filtered | age_days=0.1 | reason=workflow_filter did not match
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260502-/workflow_report.md` | result=filtered | age_days=0.1 | reason=workflow_filter did not match
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261023978/workflow_report.md` | result=filtered | age_days=0.0 | reason=workflow_filter did not match
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261233739/workflow_report.md` | result=filtered | age_days=0.0 | reason=workflow_filter did not match
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261570066/workflow_report.md` | result=filtered | age_days=0.0 | reason=workflow_filter did not match
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-reporting-validation/25261773354/workflow_report.md` | result=failure | age_days=0.0 | reason=latest report for workflow

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material.
