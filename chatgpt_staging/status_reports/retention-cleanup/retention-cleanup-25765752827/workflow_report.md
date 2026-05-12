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
- candidate_count: 10
- retained_count: 34
- github_run_id: 25765752827
- github_sha: 37895e006328cef34ce5d6bda86f8111094e8780
- report_created_utc: 2026-05-12T22:23:59Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25679334502/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25680071490/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/25680630103/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25680615496/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25689874254/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690640098/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/25680642112/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25679334132/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25680588407/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25690640035/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-functional-chunk-bundle-003/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-functional-chunk-pilot-001/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-functional-chunk-pilot-002/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-20260512-gemini-source-runtime-contract-001/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/applyin-smoke-20260512-nonworkflow-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/unsafe_or_unknown/workflow_report.md` | result=failure | age_days=1.3 | reason=age 1.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/wbs09-verify-relative-date-filters-v1-20260512/workflow_report.md` | result=failure | age_days=0.1 | reason=age 0.1d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-airtable-schema-finalizer-validate-001/workflow_report.md` | result=success | age_days=0.7 | reason=age 0.7d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-airtable-schema-finalizer-validate-002/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-generated-prime-final-validate-001/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-generated-prime-migration-001/workflow_report.md` | result=unknown | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-generated-prime-migration-002/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-prime-checksum-update-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-prime-chunks-validate-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-gemini-source-runtime-contract-001/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-prime-agent-boundary-analysis-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-prime-agent-chunk-refactor-001/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260512-prime-agent-chunk-refactor-002/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-stage-out/stageout-20260512-prime-agent-source-readback-002/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Dependabot-auto-merge/25756342044/workflow_report.md` | result=cleanup | age_days=0.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25730999014/workflow_report.md` | result=success | age_days=0.5 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-full-validation/25742288277/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25724461532/workflow_report.md` | result=failure | age_days=0.6 | reason=age 0.6d < 7d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25724931892/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25741867291/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25750898931/workflow_report.md` | result=success | age_days=0.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25690857522/workflow_report.md` | result=success | age_days=1.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/25742514870/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25678941477/workflow_report.md` | result=failure | age_days=1.3 | reason=age 1.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25725395804/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25729500696/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25730243097/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/repo-workflows/validate-on-push/25741454106/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25700705148/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
