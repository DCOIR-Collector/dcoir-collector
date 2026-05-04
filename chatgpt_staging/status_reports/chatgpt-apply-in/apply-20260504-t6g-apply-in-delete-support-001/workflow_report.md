# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: apply-20260504-t6g-apply-in-delete-support-001
- payload_path: chatgpt_staging/in/apply-20260504-t6g-apply-in-delete-support-001/payload.zip.b64
- github_run_id: 25312186158
- github_ref: refs/heads/main
- github_sha: 7cc517af2fcecedb02747137c4ebaf328b90dbf3
- artifact_name: chatgpt-apply-in-failure-25312186158
- artifact_retention_days: 7
- report_created_utc: 2026-05-04T09:45:24Z

## Troubleshooting context

The apply-in workflow failed. Common causes are decode errors, missing apply_manifest.json, unsafe paths, missing sources, stale-write hash failures, create_only violations, hash mismatches, missing apply_manifest schema, missing workflow_change_reason for workflow edits, or git commit/push failure.

Hash policy: existing tracked files require expected_blob_sha or expected_current_sha256 unless manifest allow_missing_current_hash=true is explicitly set; new files require create_only=true and expected_new_sha256. Workflow mutation policy: .github/workflows targets require allow_workflow_changes=true and workflow_change_reason. Payload policy: payload.zip.b64 may contain base64 directly, or it may contain only '# dcoir-payload-b64-parts-v1' with sorted chunks under sibling payload.zip.b64.parts/*.b64.


## Artifact pointer

Detailed diagnostics, hashes, and any copied manifest are uploaded as GitHub Actions artifact 'chatgpt-apply-in-failure-25312186158' for run 25312186158 when available.

## Cleanup guidance

After ChatGPT reads this report and retrieves any needed artifact/log details, create a cleanup marker for request id 'apply-20260504-t6g-apply-in-delete-support-001' with cleanup_status_reports=true and cleanup_in_payloads=true.

## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, decide whether to regenerate the payload with current hashes or repair the workflow, then update Airtable.
