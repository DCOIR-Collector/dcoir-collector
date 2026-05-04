# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: apply-20260504-t6g-retired-skill-source-cleanup-001
- payload_path: chatgpt_staging/in/apply-20260504-t6g-retired-skill-source-cleanup-001/payload.zip.b64
- github_run_id: 25312422082
- github_ref: refs/heads/main
- github_sha: 4eed8be3dff8f55e350975be242ccb35b87b8959
- artifact_name: chatgpt-apply-in-failure-25312422082
- artifact_retention_days: 7
- report_created_utc: 2026-05-04T09:50:58Z

## Troubleshooting context

The apply-in workflow failed. Common causes are decode errors, missing apply_manifest.json, unsafe paths, missing sources, stale-write hash failures, create_only violations, hash mismatches, delete path validation failures, missing apply_manifest schema, missing workflow_change_reason for workflow edits, or git commit/push failure.

Hash policy: existing tracked files require expected_blob_sha or expected_current_sha256 unless manifest allow_missing_current_hash=true is explicitly set; new files require create_only=true and expected_new_sha256. Delete policy: deletion entries go in manifest.deletes, require allowed roots, safe paths, and recursive=true for directory deletes. Workflow mutation policy: .github/workflows targets require allow_workflow_changes=true and workflow_change_reason.

### Manifest excerpt

```json
{"schema":"dcoir.chatgpt_staging.apply_manifest.v1","request_id":"apply-20260504-t6g-retired-skill-source-cleanup-001","allowed_roots":["dcoir_skills"],"files":[{"path":"dcoir_skills/README.md","source":"files/dcoir_skills_README.md","expected_blob_sha":"53e8cd5814cebcbd44f093c57ed6116c59b96193","expected_new_sha256":"7d9e783a955604168a7d38f97c7a95496f4a5d781b58935476cf9ac604018e17"}],"deletes":[{"path":"dcoir_skills/dcoir-large-file-intake-manager","recursive":true,"require_exists":true},{"path":"dcoir_skills/dcoir-authority-drift-reporter","recursive":true,"require_exists":true}]}

```

## Artifact pointer

Detailed diagnostics, hashes, and any copied manifest are uploaded as GitHub Actions artifact 'chatgpt-apply-in-failure-25312422082' for run 25312422082 when available.

## Cleanup guidance

After ChatGPT reads this report and retrieves any needed artifact/log details, create a cleanup marker for request id 'apply-20260504-t6g-retired-skill-source-cleanup-001' with cleanup_status_reports=true and cleanup_in_payloads=true.

## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, decide whether to regenerate the payload with current hashes or repair the workflow, then update Airtable.
