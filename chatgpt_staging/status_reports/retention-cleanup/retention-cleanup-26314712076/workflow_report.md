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
- candidate_count: 14
- retained_count: 9
- github_run_id: 26314712076
- github_sha: 98dfba333927ef5090f91f335861667fc25cf8ba
- report_created_utc: 2026-05-22T22:19:10Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/chatgpt-exec/airtable-total-count-corrected-20260521T100417Z/workflow_report.md` | result=success | age_days=1.5 | reason=age 1.5d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/airtable-total-count-reuse-first-20260521T093401Z/workflow_report.md` | result=success | age_days=1.5 | reason=age 1.5d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260514-wbs09-airtable-metadata-probe/workflow_report.md` | result=failure | age_days=8.5 | reason=age 8.5d >= 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260514-wbs09-airtable-metadata-probe-002/workflow_report.md` | result=failure | age_days=8.5 | reason=age 8.5d >= 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-next-cleanup-export-001/workflow_report.md` | result=success | age_days=3.3 | reason=age 3.3d >= 2d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs04-merge-delete-batch2-export-001/workflow_report.md` | result=success | age_days=2.8 | reason=age 2.8d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs04-merge-delete-batch3-export-001/workflow_report.md` | result=success | age_days=2.8 | reason=age 2.8d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-aggressive-rename-candidates-batch2-001/workflow_report.md` | result=success | age_days=2.6 | reason=age 2.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-aggressive-rename-candidates-batch3-001/workflow_report.md` | result=success | age_days=2.6 | reason=age 2.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-field-rename-apply-batch1-001/workflow_report.md` | result=success | age_days=2.6 | reason=age 2.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-field-rename-apply-batch2-001/workflow_report.md` | result=success | age_days=2.6 | reason=age 2.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-final-verify-retirement-packet-001/workflow_report.md` | result=success | age_days=2.6 | reason=age 2.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260520-wbs06-rename-ledger-dryrun-001/workflow_report.md` | result=success | age_days=2.6 | reason=age 2.6d >= 1d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-26128976512/workflow_report.md` | result=success | age_days=3.0 | reason=age 3.0d >= 2d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-four-table-export-002/workflow_report.md` | result=failure | age_days=3.4 | reason=age 3.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/25756342044/workflow_report.md` | result=cleanup | age_days=10.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26020386957/workflow_report.md` | result=success | age_days=4.6 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/25742288277/workflow_report.md` | result=success | age_days=10.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25750898931/workflow_report.md` | result=success | age_days=10.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690857522/workflow_report.md` | result=success | age_days=11.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/26020305274/workflow_report.md` | result=success | age_days=4.6 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25741454106/workflow_report.md` | result=success | age_days=10.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-26193633121/workflow_report.md` | result=success | age_days=2.0 | reason=age 2.0d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
