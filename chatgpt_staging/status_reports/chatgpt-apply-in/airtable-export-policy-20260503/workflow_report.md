# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: airtable-export-policy-20260503
- payload_path: chatgpt_staging/in/airtable-export-policy-20260503/payload.zip.b64
- github_run_id: 25280175341
- github_ref: refs/heads/main
- github_sha: 15a8004a7d04f2abea8014fa39ed85037a456cde
- artifact_name: chatgpt-apply-in-failure-25280175341
- artifact_retention_days: 7
- report_created_utc: 2026-05-03T13:15:09Z

## Troubleshooting context

The apply-in workflow failed. Common causes are decode errors, missing apply_manifest.json, unsafe paths, missing sources, stale-write hash failures, create_only violations, hash mismatches, missing apply_manifest schema, missing workflow_change_reason for workflow edits, or git commit/push failure.

Hash policy: existing tracked files require expected_blob_sha or expected_current_sha256 unless manifest allow_missing_current_hash=true is explicitly set; new files require create_only=true and expected_new_sha256. Workflow mutation policy: .github/workflows targets require allow_workflow_changes=true and workflow_change_reason.


## Artifact pointer

Detailed diagnostics, hashes, and any copied manifest are uploaded as GitHub Actions artifact 'chatgpt-apply-in-failure-25280175341' for run 25280175341 when available.

## Cleanup guidance

After ChatGPT reads this report and retrieves any needed artifact/log details, create a cleanup marker for request id 'airtable-export-policy-20260503' with cleanup_status_reports=true and cleanup_in_payloads=true.

## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, decide whether to regenerate the payload with current hashes or repair the workflow, then update Airtable.
