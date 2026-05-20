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
- candidate_count: 5
- retained_count: 20
- github_run_id: 26193633121
- github_sha: c143415e741f5a9bddaba202ac940175dd137ff3
- report_created_utc: 2026-05-20T22:28:09Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-four-table-export-003/workflow_report.md` | result=success | age_days=1.4 | reason=age 1.4d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-merge-delete-batch1-export-001/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-post-first-four-export-002/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-remaining-normalization-export-001/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-26063717655/workflow_report.md` | result=success | age_days=2.0 | reason=age 2.0d >= 2d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260514-wbs09-airtable-metadata-probe/workflow_report.md` | result=failure | age_days=6.5 | reason=age 6.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260514-wbs09-airtable-metadata-probe-002/workflow_report.md` | result=failure | age_days=6.5 | reason=age 6.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-four-table-export-002/workflow_report.md` | result=failure | age_days=1.4 | reason=age 1.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-next-cleanup-export-001/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d < 2d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs04-merge-delete-batch2-export-001/workflow_report.md` | result=success | age_days=0.8 | reason=age 0.8d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs04-merge-delete-batch3-export-001/workflow_report.md` | result=success | age_days=0.8 | reason=age 0.8d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-aggressive-rename-candidates-batch2-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-aggressive-rename-candidates-batch3-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-field-rename-apply-batch1-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-field-rename-apply-batch2-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-final-verify-retirement-packet-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-rename-ledger-dryrun-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/25756342044/workflow_report.md` | result=cleanup | age_days=8.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26020386957/workflow_report.md` | result=success | age_days=2.6 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/25742288277/workflow_report.md` | result=success | age_days=8.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25750898931/workflow_report.md` | result=success | age_days=8.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690857522/workflow_report.md` | result=success | age_days=9.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/26020305274/workflow_report.md` | result=success | age_days=2.6 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25741454106/workflow_report.md` | result=success | age_days=8.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-26128976512/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
