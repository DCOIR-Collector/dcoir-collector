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
- candidate_count: 3
- retained_count: 26
- github_run_id: 25292264604
- github_sha: 95248961cffa7756d7abd72512cf4523ddacc517
- report_created_utc: 2026-05-03T22:11:13Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261023978/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261233739/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25261570066/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-apply-in/airtable-export-policy-20260503/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260503-exec-hashfix-validation-001/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260503-simple-codeblock-exec-001/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260503-airtable-schema-hashfix-002/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260503-airtable-schema-smoke-001/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260503-simple-codeblock-smoke-001/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/cleanup_failure_25259970239/workflow_report.md` | result=failure | age_days=1.1 | reason=age 1.1d < 7d
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260502-/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d < 2d
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260503-apply-in-payload-staging-validation-001/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 2d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25278297611/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25278448907/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25286790093/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25287302268/workflow_report.md` | result=success | age_days=0.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-reporting-validation/25261773354/workflow_report.md` | result=failure | age_days=1.0 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25277259876/workflow_report.md` | result=success | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25284318502/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25284366031/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25285021493/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25285042722/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25285066966/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25285643135/workflow_report.md` | result=success | age_days=0.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25262009553/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25262135315/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25270210887/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25273138405/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25278491998/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material.
