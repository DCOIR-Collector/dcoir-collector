# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: apply-20260504-t6c-retired-skill-source-cleanup-002
- payload_path: chatgpt_staging/in/apply-20260504-t6c-retired-skill-source-cleanup-002/payload.zip.b64
- github_run_id: 25319673422
- github_ref: refs/heads/main
- github_sha: feff950f1dd9b7c413d2112a35b36c5dd931e36b
- artifact_name: chatgpt-apply-in-failure-25319673422
- artifact_retention_days: 7
- report_created_utc: 2026-05-04T12:44:02Z

## Troubleshooting context

The apply-in workflow failed. Common causes are decode errors, missing apply_manifest.json, unsafe paths, missing sources, stale-write hash failures, create_only violations, hash mismatches, delete path validation failures, missing apply_manifest schema, missing workflow_change_reason for workflow edits, or git commit/push failure.

Hash policy: existing tracked files require expected_blob_sha or expected_current_sha256 unless manifest allow_missing_current_hash=true is explicitly set; new files require create_only=true and expected_new_sha256. Delete policy: deletion entries go in manifest.deletes, require allowed roots, safe paths, and recursive=true for directory deletes. Workflow mutation policy: .github/workflows targets require allow_workflow_changes=true and workflow_change_reason.

### Manifest excerpt

```json
{
  "schema": "dcoir.chatgpt_staging.apply_manifest.v1",
  "request_id": "apply-20260504-t6c-retired-skill-source-cleanup-002",
  "allowed_roots": ["dcoir_skills"],
  "files": [],
  "deletes": [
    {"path":"dcoir_skills/dcoir-plan-tracker/SKILL.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/agents/openai.yaml","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/assets/icon.svg","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/references/airtable_operational_schema_contract.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/references/airtable_plan_sync_workflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/references/blocker_promotion_workflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/references/command_surface.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/references/file_layout.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/references/github_write_workflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/references/local_plan_state_workflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/ref",
uel_scheolble_plru],
workflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/refsessr_prbufackan_state_workflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-tracker/refal_rtup_ma_iv/airtabrecoveryan_state_workflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-scripkeradd_task.pykflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-scripkerencomees/local_pl.pykflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-scripkerinites/lo.pykflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-scripkers/loctems/l
  .pykflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-scripkerkerdckaerences/airtabbundll.pykflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-scripkerupd_plas/local_pl.pykflow.md","require_exists":true},
    {"path":"dcoir_skills/dcoir-plan-scripkervalid_plas/locae_plru],
wpykflow.md","require_exists":true},
    {"path":"dcoir_skillattackr_p-sigopean-tracker/SKILL.md","require_exists":true},
    {"path":"dcoir_skillattackr_p-sigopean-tracker/agents/openai.yaml","require_exists":true},
    {"path":"dcoir_skillattackr_p-sigopean-tracker/assets/icon.svg","require_exists":true},
    {"path":"dcoir_skillattackr_p-sigopean-tracker/references/airtable_operational_schema_contract.md","require_exists":true},
    {"path":"dcoir_skillattackr_p-sigopean-tracker/refettackr_p_mod,
workflow.md","require_exists":true},
    {"path":"dcoir_skillattackr_p-sigopean-tracker/refbannckamesstractems/l
  .orkflow.md","require_exists":true},
    {"path":"dcoir_skillattackr_p-sigopean-scripkerkerdckaettackr_p_sigopewpykflow.md","require_exist":t]
}

```

## Artifact pointer

Detailed diagnostics, hashes, and any copied manifest are uploaded as GitHub Actions artifact 'chatgpt-apply-in-failure-25319673422' for run 25319673422 when available.

## Cleanup guidance

After ChatGPT reads this report and retrieves any needed artifact/log details, create a cleanup marker for request id 'apply-20260504-t6c-retired-skill-source-cleanup-002' with cleanup_status_reports=true and cleanup_in_payloads=true.

## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, decide whether to regenerate the payload with current hashes or repair the workflow, then update Airtable.
