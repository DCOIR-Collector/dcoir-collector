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
- retained_count: 13
- github_run_id: 25700705148
- github_sha: 66ad4cbd37797f4f990266e605111102325d8e12
- report_created_utc: 2026-05-11T22:20:31Z

## Reports selected for cleanup
- none

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-apply-in/unsafe_or_unknown/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25679334502/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25680071490/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/25680630103/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25680615496/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25689874254/workflow_report.md` | result=success | age_days=0.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690640098/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690857522/workflow_report.md` | result=success | age_days=0.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/25680642112/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25678941477/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25679334132/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25680588407/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25690640035/workflow_report.md` | result=success | age_days=0.1 | reason=latest report for workflow

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
