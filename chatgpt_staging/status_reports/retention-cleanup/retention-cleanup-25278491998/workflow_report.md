# ChatGPT workflow report

## Result

- workflow: chatgpt-report-retention-cleanup
- report_scope: retention-cleanup
- result: success
- mode: delete
- success_retention_days: 1
- failure_retention_days: 7
- cleanup_retention_days: 2
- keep_latest_per_workflow: true
- workflow_filter: 
- candidate_count: 0
- retained_count: 13
- github_run_id: 25278491998
- github_sha: 6d2906d4a4e31a69e6229e9d739ae6229dab9409
- report_created_utc: 2026-05-03T11:56:19Z

## Reports selected for cleanup
- none

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/cleanup_failure_25259970239/workflow_report.md` | result=failure | age_days=0.7 | reason=age 0.7d < 7d
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260502-/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 2d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261023978/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261233739/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261570066/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25278297611/workflow_report.md` | result=success | age_days=0.0 | reason=age 0.0d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25278448907/workflow_report.md` | result=success | age_days=0.0 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-reporting-validation/25261773354/workflow_report.md` | result=failure | age_days=0.6 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25277259876/workflow_report.md` | result=success | age_days=0.0 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25262009553/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25262135315/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25270210887/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25273138405/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material.
