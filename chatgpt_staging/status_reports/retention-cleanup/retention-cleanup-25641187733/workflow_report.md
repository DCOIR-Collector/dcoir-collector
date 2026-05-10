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
- candidate_count: 8
- retained_count: 59
- github_run_id: 25641187733
- github_sha: 21db8768d3418c2b79746ab2c4cedbeb1fc0212f
- report_created_utc: 2026-05-10T22:13:28Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/chatgpt-apply-in/airtable-export-policy-20260503/workflow_report.md` | result=failure | age_days=7.4 | reason=age 7.4d >= 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-cleanup-plan-scaffold-delete-queue-closeout-001/workflow_report.md` | result=success | age_days=2.2 | reason=age 2.2d >= 2d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-cleanup-plan-scaffold-delete-queue-closeout-002/workflow_report.md` | result=success | age_days=2.2 | reason=age 2.2d >= 2d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-cleanup-plan-scaffold-delete-queue-closeout-003/workflow_report.md` | result=success | age_days=2.2 | reason=age 2.2d >= 2d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-final-postcleanup-export-001/workflow_report.md` | result=success | age_days=2.2 | reason=age 2.2d >= 2d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260509-wbs02-batch2-cv-profile-001/workflow_report.md` | result=success | age_days=2.0 | reason=age 2.0d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260509-wbs02-remaining-text-to-select-bulk-recon-001/workflow_report.md` | result=success | age_days=1.4 | reason=age 1.4d >= 1d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25525219342/workflow_report.md` | result=success | age_days=3.0 | reason=age 3.0d >= 2d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6-skill-preservation-001/workflow_report.md` | result=failure | age_days=6.6 | reason=age 6.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6c-retired-skill-source-cleanup-001/workflow_report.md` | result=failure | age_days=6.4 | reason=age 6.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6c-retired-skill-source-cleanup-002/workflow_report.md` | result=failure | age_days=6.4 | reason=age 6.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6d-session-manager-source-create-001/workflow_report.md` | result=failure | age_days=6.3 | reason=age 6.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6d-session-manager-source-create-002/workflow_report.md` | result=failure | age_days=6.3 | reason=age 6.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6e-source-authority-delete-001/workflow_report.md` | result=failure | age_days=6.2 | reason=age 6.2d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-apply-in-delete-support-001/workflow_report.md` | result=failure | age_days=6.5 | reason=age 6.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-readme-retired-skill-cleanup-004/workflow_report.md` | result=failure | age_days=6.5 | reason=age 6.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-retired-skill-file-cleanup-002/workflow_report.md` | result=failure | age_days=6.5 | reason=age 6.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-retired-skill-source-cleanup-001/workflow_report.md` | result=failure | age_days=6.5 | reason=age 6.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260505-chatgpt-in-fail-001/workflow_report.md` | result=failure | age_days=5.4 | reason=age 5.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-heartbeat-readback-docs-001/workflow_report.md` | result=failure | age_days=2.6 | reason=age 2.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-heartbeat-readback-docs-002/workflow_report.md` | result=failure | age_days=2.6 | reason=age 2.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-heartbeat-readback-docs-batch-003/workflow_report.md` | result=failure | age_days=2.6 | reason=age 2.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-heartbeat-readback-docs-batch-004a/workflow_report.md` | result=failure | age_days=2.6 | reason=age 2.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/sync-mem-skill-20260507-0001/workflow_report.md` | result=failure | age_days=3.6 | reason=age 3.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/dcoir-alias-normalization-20260508-2105z/workflow_report.md` | result=failure | age_days=2.0 | reason=age 2.0d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/dcoir-db-redesign-wbs-scaffold-20260508-2005z/workflow_report.md` | result=failure | age_days=2.1 | reason=age 2.1d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/dcoir-db-redesign-wbs-scaffold-retry-20260508-2016z/workflow_report.md` | result=failure | age_days=2.1 | reason=age 2.1d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/dlt_import_20260506_1300/workflow_report.md` | result=failure | age_days=4.3 | reason=age 4.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260505-cleanup-plan-wbs-seed-002/workflow_report.md` | result=failure | age_days=5.4 | reason=age 5.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260505-cleanup-plan-wbs-seed-003/workflow_report.md` | result=failure | age_days=5.4 | reason=age 5.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260505-wbs04-id-inventory-001/workflow_report.md` | result=failure | age_days=5.1 | reason=age 5.1d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-api-key-readonly-001/workflow_report.md` | result=failure | age_days=4.5 | reason=age 4.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-cleanup-plan-readback-001/workflow_report.md` | result=failure | age_days=4.4 | reason=age 4.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-cleanup-plan-readback-002/workflow_report.md` | result=failure | age_days=4.4 | reason=age 4.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-insert-delete-smoke-001/workflow_report.md` | result=failure | age_days=4.2 | reason=age 4.2d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-insert-only-001/workflow_report.md` | result=failure | age_days=4.2 | reason=age 4.2d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-insert-smoke-001/workflow_report.md` | result=failure | age_days=4.2 | reason=age 4.2d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-return-row-001/workflow_report.md` | result=failure | age_days=4.2 | reason=age 4.2d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-supabase-pivot-state-001/workflow_report.md` | result=failure | age_days=4.5 | reason=age 4.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-airtable-temp-record-cleanup-001/workflow_report.md` | result=failure | age_days=4.2 | reason=age 4.2d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-data-transform-scope-002/workflow_report.md` | result=failure | age_days=4.8 | reason=age 4.8d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-preservation-scaffold-discovery-001/workflow_report.md` | result=failure | age_days=4.4 | reason=age 4.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-reanchor-records-api-001/workflow_report.md` | result=failure | age_days=4.5 | reason=age 4.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260506-session-closeout-001/workflow_report.md` | result=failure | age_days=4.6 | reason=age 4.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260507-completed-summary-script-smoke-001/workflow_report.md` | result=failure | age_days=3.3 | reason=age 3.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260507-completed-summary-script-smoke-002/workflow_report.md` | result=failure | age_days=3.3 | reason=age 3.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-bulk-maintenance-002/workflow_report.md` | result=failure | age_days=2.5 | reason=age 2.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-bulk-maintenance-003/workflow_report.md` | result=failure | age_days=2.5 | reason=age 2.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-discovery-001/workflow_report.md` | result=failure | age_days=2.7 | reason=age 2.7d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-discovery-002/workflow_report.md` | result=failure | age_days=2.7 | reason=age 2.7d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-discovery-003/workflow_report.md` | result=failure | age_days=2.6 | reason=age 2.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-readonly-verification-003/workflow_report.md` | result=failure | age_days=2.5 | reason=age 2.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-readonly-verification-004/workflow_report.md` | result=failure | age_days=2.5 | reason=age 2.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260508-wbs22-wave2-single-table-probe-001/workflow_report.md` | result=failure | age_days=2.6 | reason=age 2.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260509-wbs02-batch2-single-select-migration-001/workflow_report.md` | result=failure | age_days=1.7 | reason=age 1.7d < 7d
- `chatgpt_staging/status_reports/chatgpt-stage-out/stageout-20260507-heartbeat-regression-001/workflow_report.md` | result=failure | age_days=3.3 | reason=age 3.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25548178312/workflow_report.md` | result=success | age_days=2.5 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-reporting-validation/25261773354/workflow_report.md` | result=failure | age_days=8.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-run-reporter/manual-25505432409/workflow_report.md` | result=success | age_days=3.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-collector-runtime-package-build/25440024974/workflow_report.md` | result=success | age_days=4.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/manual-gemini-bundle-build/25440050845/workflow_report.md` | result=success | age_days=4.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25328669934/workflow_report.md` | result=failure | age_days=6.3 | reason=age 6.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25328933475/workflow_report.md` | result=failure | age_days=6.3 | reason=age 6.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25516559522/workflow_report.md` | result=success | age_days=3.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/25306279467/workflow_report.md` | result=success | age_days=6.6 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25582244011/workflow_report.md` | result=success | age_days=2.0 | reason=age 2.0d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25613100655/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material. Do not use retention-cleanup reports for live workflow polling.
