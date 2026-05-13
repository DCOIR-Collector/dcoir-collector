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
- candidate_count: 15
- retained_count: 20
- github_run_id: 25829916461
- github_sha: e3d51c1eec3d7846383b3f33399652ca402038e0
- report_created_utc: 2026-05-13T22:24:16Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-functional-chunk-bundle-003/workflow_report.md` | result=success | age_days=1.4 | reason=age 1.4d >= 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-functional-chunk-pilot-002/workflow_report.md` | result=success | age_days=1.4 | reason=age 1.4d >= 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-smoke-20260512-nonworkflow-001/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-airtable-schema-finalizer-validate-001/workflow_report.md` | result=success | age_days=1.7 | reason=age 1.7d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-airtable-schema-finalizer-validate-002/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-generated-prime-migration-001/workflow_report.md` | result=unknown | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-generated-prime-migration-002/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-prime-checksum-update-001/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-prime-chunks-validate-001/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-prime-agent-boundary-analysis-001/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-prime-agent-chunk-refactor-001/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-prime-agent-chunk-refactor-002/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/chatgpt-stage-out/stageout-20260512-prime-agent-source-readback-002/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25741867291/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25700705148/workflow_report.md` | result=success | age_days=2.0 | reason=age 2.0d >= 2d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-functional-chunk-pilot-001/workflow_report.md` | result=failure | age_days=1.4 | reason=age 1.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-source-runtime-contract-001/workflow_report.md` | result=failure | age_days=1.5 | reason=age 1.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/unsafe_or_unknown/workflow_report.md` | result=failure | age_days=2.3 | reason=age 2.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/wbs09-verify-relative-date-filters-v1-20260512/workflow_report.md` | result=failure | age_days=1.1 | reason=age 1.1d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-generated-prime-final-validate-001/workflow_report.md` | result=failure | age_days=1.5 | reason=age 1.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-source-runtime-contract-001/workflow_report.md` | result=failure | age_days=1.5 | reason=age 1.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/25756342044/workflow_report.md` | result=cleanup | age_days=1.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25730999014/workflow_report.md` | result=success | age_days=1.5 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/25742288277/workflow_report.md` | result=success | age_days=1.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25724461532/workflow_report.md` | result=failure | age_days=1.6 | reason=age 1.6d < 7d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25724931892/workflow_report.md` | result=failure | age_days=1.5 | reason=age 1.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25750898931/workflow_report.md` | result=success | age_days=1.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690857522/workflow_report.md` | result=success | age_days=2.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/25742514870/workflow_report.md` | result=success | age_days=1.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25678941477/workflow_report.md` | result=failure | age_days=2.3 | reason=age 2.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25725395804/workflow_report.md` | result=failure | age_days=1.5 | reason=age 1.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25729500696/workflow_report.md` | result=failure | age_days=1.5 | reason=age 1.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25730243097/workflow_report.md` | result=failure | age_days=1.5 | reason=age 1.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25741454106/workflow_report.md` | result=success | age_days=1.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25765752827/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
