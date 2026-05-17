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
- candidate_count: 1
- retained_count: 23
- github_run_id: 26004259857
- github_sha: 6d42ce424de727e92d0a45c464b7ca7597c34c05
- report_created_utc: 2026-05-17T22:15:17Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25888999760/workflow_report.md` | result=success | age_days=3.0 | reason=age 3.0d >= 2d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-functional-chunk-pilot-001/workflow_report.md` | result=failure | age_days=5.4 | reason=age 5.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-source-runtime-contract-001/workflow_report.md` | result=failure | age_days=5.5 | reason=age 5.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/unsafe_or_unknown/workflow_report.md` | result=failure | age_days=6.3 | reason=age 6.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/wbs09-verify-relative-date-filters-v1-20260512/workflow_report.md` | result=failure | age_days=5.1 | reason=age 5.1d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-generated-prime-final-validate-001/workflow_report.md` | result=failure | age_days=5.5 | reason=age 5.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-source-runtime-contract-001/workflow_report.md` | result=failure | age_days=5.5 | reason=age 5.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260514-wbs09-airtable-metadata-probe/workflow_report.md` | result=failure | age_days=3.5 | reason=age 3.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260514-wbs09-airtable-metadata-probe-002/workflow_report.md` | result=failure | age_days=3.5 | reason=age 3.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/25756342044/workflow_report.md` | result=cleanup | age_days=5.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25856229762/workflow_report.md` | result=success | age_days=3.5 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/25742288277/workflow_report.md` | result=success | age_days=5.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25724461532/workflow_report.md` | result=failure | age_days=5.6 | reason=age 5.6d < 7d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25724931892/workflow_report.md` | result=failure | age_days=5.5 | reason=age 5.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25750898931/workflow_report.md` | result=success | age_days=5.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690857522/workflow_report.md` | result=success | age_days=6.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/25742514870/workflow_report.md` | result=success | age_days=5.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25678941477/workflow_report.md` | result=failure | age_days=6.3 | reason=age 6.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25725395804/workflow_report.md` | result=failure | age_days=5.5 | reason=age 5.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25729500696/workflow_report.md` | result=failure | age_days=5.5 | reason=age 5.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25730243097/workflow_report.md` | result=failure | age_days=5.5 | reason=age 5.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25741454106/workflow_report.md` | result=success | age_days=5.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25944036960/workflow_report.md` | result=success | age_days=2.0 | reason=age 2.0d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25974327219/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
