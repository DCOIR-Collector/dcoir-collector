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
- candidate_count: 2
- retained_count: 42
- github_run_id: 26542555845
- github_sha: b64890d717fcec376921d08618f6d595a35c5263
- report_created_utc: 2026-05-27T22:30:01Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26462091818/workflow_report.md` | result=cleanup | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26463647792/workflow_report.md` | result=cleanup | age_days=1.2 | reason=age 1.2d >= 1d

## Reports retained or skipped
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26494677795/workflow_report.md` | result=cleanup | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26496298699/workflow_report.md` | result=cleanup | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26497181747/workflow_report.md` | result=cleanup | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26507093755/workflow_report.md` | result=cleanup | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26508221815/workflow_report.md` | result=cleanup | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26508747651/workflow_report.md` | result=cleanup | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26509380532/workflow_report.md` | result=cleanup | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26516633359/workflow_report.md` | result=cleanup | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26518332820/workflow_report.md` | result=cleanup | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26529647085/workflow_report.md` | result=cleanup | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26530343508/workflow_report.md` | result=cleanup | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/26533450274/workflow_report.md` | result=cleanup | age_days=0.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Dependency-Review/26509784190/workflow_report.md` | result=success | age_days=0.4 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Publish-Knowledge-to-Wiki/26517037428/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Publish-Knowledge-to-Wiki/26518669861/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26493881056/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26493912531/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26494166656/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26494168987/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26494215657/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26494245555/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26494887461/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26497464648/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26512409192/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/26530674835/workflow_report.md` | result=success | age_days=0.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26492485610/workflow_report.md` | result=failure | age_days=0.7 | reason=age 0.7d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26493881064/workflow_report.md` | result=failure | age_days=0.7 | reason=age 0.7d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26493912585/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26494168957/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26494459297/workflow_report.md` | result=failure | age_days=0.7 | reason=age 0.7d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26494483154/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26494887509/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26507040225/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26508219409/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26512409208/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26515815100/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26515840419/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26515869556/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26517037423/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26518233029/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26518317838/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/26518669773/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
