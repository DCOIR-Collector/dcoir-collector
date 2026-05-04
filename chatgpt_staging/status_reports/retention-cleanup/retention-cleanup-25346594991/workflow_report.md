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
- candidate_count: 19
- retained_count: 50
- github_run_id: 25346594991
- github_sha: ccea2358cd59c7887818ae5393015c63cc6e3f1e
- report_created_utc: 2026-05-04T22:18:27Z

## Reports selected for cleanup
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260503-exec-hashfix-validation-001/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260503-simple-codeblock-exec-001/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260503-airtable-schema-hashfix-002/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260503-airtable-schema-smoke-001/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260503-simple-codeblock-smoke-001/workflow_report.md` | result=success | age_days=1.1 | reason=age 1.1d >= 1d
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260502-/workflow_report.md` | result=success | age_days=2.1 | reason=age 2.1d >= 2d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25278297611/workflow_report.md` | result=success | age_days=1.4 | reason=age 1.4d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25278448907/workflow_report.md` | result=success | age_days=1.4 | reason=age 1.4d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25286790093/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25287302268/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25277259876/workflow_report.md` | result=success | age_days=1.5 | reason=age 1.5d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25284318502/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25284366031/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25285021493/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25285042722/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25285066966/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25285643135/workflow_report.md` | result=success | age_days=1.2 | reason=age 1.2d >= 1d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25262009553/workflow_report.md` | result=success | age_days=2.0 | reason=age 2.0d >= 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25262135315/workflow_report.md` | result=success | age_days=2.0 | reason=age 2.0d >= 2d

## Reports retained or skipped
- `chatgpt_staging/status_reports/chatgpt-apply-in/airtable-export-policy-20260503/workflow_report.md` | result=failure | age_days=1.4 | reason=age 1.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6-skill-preservation-001/workflow_report.md` | result=failure | age_days=0.6 | reason=age 0.6d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6-skill-preservation-002/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6c-preservation-source-sync-singlezip-001/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6c-retired-skill-source-cleanup-001/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6c-retired-skill-source-cleanup-002/workflow_report.md` | result=failure | age_days=0.4 | reason=age 0.4d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6c-retired-skill-source-cleanup-003/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 2d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6d-session-manager-add-003/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6d-session-manager-source-create-001/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6d-session-manager-source-create-002/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6d-session-old-delete-001/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6e-decision-policy-authority-merge-001/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6e-source-authority-delete-001/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6e-source-authority-delete-002/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-apply-in-delete-support-001/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-live-test-remediation-planner-source-sync-001/workflow_report.md` | result=success | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-readme-retired-skill-cleanup-004/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-readme-retired-skill-cleanup-005/workflow_report.md` | result=success | age_days=0.5 | reason=age 0.5d < 2d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-retired-skill-delete-only-003/workflow_report.md` | result=success | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-retired-skill-file-cleanup-002/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6g-retired-skill-source-cleanup-001/workflow_report.md` | result=failure | age_days=0.5 | reason=age 0.5d < 7d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6l-wave-a-001/workflow_report.md` | result=success | age_days=0.4 | reason=age 0.4d < 1d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6l-wave-c-source-cleanup-001/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 2d
- `chatgpt_staging/status_reports/chatgpt-apply-in/apply-20260504-t6n-core-skill-strengthening-001/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/chatgpt-exec/exec-20260504-t6e-source-authority-delete-001/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/cleanup_failure_25259970239/workflow_report.md` | result=failure | age_days=2.1 | reason=age 2.1d < 7d
- `chatgpt_staging/status_reports/chatgpt-staging-cleanup/val-20260503-apply-in-payload-staging-validation-001/workflow_report.md` | result=success | age_days=1.3 | reason=age 1.3d < 2d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25306289518/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25308114498/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25312363839/workflow_report.md` | result=success | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25328881215/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/Workflow-maintenance-audit/25329000952/workflow_report.md` | result=success | age_days=0.3 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/chatgpt-workflow-reporting-validation/25261773354/workflow_report.md` | result=failure | age_days=2.1 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25310104209/workflow_report.md` | result=success | age_days=0.6 | reason=age 0.6d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25310989166/workflow_report.md` | result=success | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25312850250/workflow_report.md` | result=success | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25313251295/workflow_report.md` | result=success | age_days=0.5 | reason=age 0.5d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25324526523/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25328669934/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25328933475/workflow_report.md` | result=failure | age_days=0.3 | reason=age 0.3d < 7d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25329035110/workflow_report.md` | result=success | age_days=0.3 | reason=age 0.3d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25330435014/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25330999416/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25334239326/workflow_report.md` | result=success | age_days=0.2 | reason=age 0.2d < 1d
- `chatgpt_staging/status_reports/repo-workflows/refresh-skill-parity-surfaces/25335784348/workflow_report.md` | result=success | age_days=0.2 | reason=latest report for workflow
- `chatgpt_staging/status_reports/repo-workflows/scheduled-health-check/25306279467/workflow_report.md` | result=success | age_days=0.6 | reason=latest report for workflow
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25270210887/workflow_report.md` | result=success | age_days=1.7 | reason=age 1.7d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25273138405/workflow_report.md` | result=success | age_days=1.6 | reason=age 1.6d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25278491998/workflow_report.md` | result=success | age_days=1.4 | reason=age 1.4d < 2d
- `chatgpt_staging/status_reports/retention-cleanup/retention-cleanup-25292264604/workflow_report.md` | result=success | age_days=1.0 | reason=age 1.0d < 2d

## Next ChatGPT action

Read this cleanup report, verify scoped deletion/readback when cleanup was not a dry run, then record Airtable evidence if material.
