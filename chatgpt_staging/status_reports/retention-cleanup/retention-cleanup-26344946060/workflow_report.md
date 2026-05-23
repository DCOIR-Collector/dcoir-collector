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
- candidate_count: 6
- retained_count: 55
- github_run_id: 26344946060
- github_sha: 1f1e954372f05eddc8be21cc273671f9047702a3
- report_created_utc: 2026-05-23T22:14:55Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/25756342044/workflow_report.md` | result=cleanup | age_days=11.1 | reason=age 11.1d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26020386957/workflow_report.md` | result=success | age_days=5.6 | reason=age 5.6d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/25742288277/workflow_report.md` | result=success | age_days=11.3 | reason=age 11.3d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25750898931/workflow_report.md` | result=success | age_days=11.2 | reason=age 11.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25741454106/workflow_report.md` | result=success | age_days=11.3 | reason=age 11.3d >= 1d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-26193633121/workflow_report.md` | result=success | age_days=3.0 | reason=age 3.0d >= 2d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-exec/airtable-final-full-export-20260523T085416Z/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260519-wbs04-four-table-export-002/workflow_report.md` | result=failure | age_days=4.4 | reason=age 4.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260523-airtable-full-health-export-001/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26319850559/workflow_report.md` | result=cleanup | age_days=0.9 | reason=age 0.9d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26319875682/workflow_report.md` | result=cleanup | age_days=0.9 | reason=age 0.9d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26320243163/workflow_report.md` | result=cleanup | age_days=0.9 | reason=age 0.9d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26336689624/workflow_report.md` | result=cleanup | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26341669345/workflow_report.md` | result=cleanup | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26341945587/workflow_report.md` | result=cleanup | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26342058348/workflow_report.md` | result=cleanup | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26342265178/workflow_report.md` | result=cleanup | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26342573444/workflow_report.md` | result=cleanup | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26343590544/workflow_report.md` | result=cleanup | age_days=0.0 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26320032326/workflow_report.md` | result=success | age_days=0.9 | reason=age 0.9d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26336701744/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26336966286/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-collector-runtime-package-build/26343004434/workflow_report.md` | result=success | age_days=0.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/26343013036/workflow_report.md` | result=success | age_days=0.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/26336326639/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/26337305132/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/26343008552/workflow_report.md` | result=success | age_days=0.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690857522/workflow_report.md` | result=success | age_days=12.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/26020305274/workflow_report.md` | result=success | age_days=5.6 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26320032323/workflow_report.md` | result=success | age_days=0.9 | reason=age 0.9d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26332384367/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26332386492/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26332396032/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26333107054/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26333108502/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26333109873/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26334205111/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26334211384/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26336116647/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26336118482/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26336120005/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26336590889/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26336701750/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26336960235/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26336966285/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26341664743/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26341944751/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26342057783/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26342264709/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26342579492/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26342982184/workflow_report.md` | result=success | age_days=0.1 | reason=age 0.1d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343410711/workflow_report.md` | result=failure | age_days=0.1 | reason=age 0.1d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343427558/workflow_report.md` | result=failure | age_days=0.1 | reason=age 0.1d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343454328/workflow_report.md` | result=failure | age_days=0.1 | reason=age 0.1d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343458507/workflow_report.md` | result=success | age_days=0.0 | reason=age 0.0d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343534936/workflow_report.md` | result=failure | age_days=0.0 | reason=age 0.0d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343539728/workflow_report.md` | result=failure | age_days=0.0 | reason=age 0.0d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343540763/workflow_report.md` | result=failure | age_days=0.0 | reason=age 0.0d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343579019/workflow_report.md` | result=failure | age_days=0.0 | reason=age 0.0d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26343580355/workflow_report.md` | result=success | age_days=0.0 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-26314712076/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
