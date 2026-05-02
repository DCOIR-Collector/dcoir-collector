# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: val-20260502-apply-bad-schema-001
- payload_path: chatgpt_staging/in/val-20260502-apply-bad-schema-001/payload.zip.b64
- github_run_id: 25260146826
- github_ref: refs/heads/main
- github_sha: f75c3a2622d7d3ff89f996d77a09c542418a5f6e
- artifact_name: chatgpt-apply-in-failure-25260146826
- artifact_retention_days: 7
- report_created_utc: 2026-05-02T19:37:52Z

## Troubleshooting context

The apply-in workflow failed. Common causes are decode errors, missing apply_manifest.json, unsafe paths, missing sources, stale-write hash failures, create_only violations, hash mismatches, missing apply_manifest schema, missing workflow_change_reason for workflow edits, or git commit/push failure.

Hash policy: existing tracked files require expected_blob_sha or expected_current_sha256 unless manifest allow_missing_current_hash=true is explicitly set; new files require create_only=true and expected_new_sha256. Workflow mutation policy: .github/workflows targets require allow_workflow_changes=true and workflow_change_reason.

### Manifest excerpt

```json
{
  "schema": "dcoir.chatgpt_staging.apply_manifest.WRONG",
  "request_id": "val-20260502-apply-bad-schema-001",
  "allowed_roots": [
    "chatgpt_staging"
  ],
  "files": [
    {
      "path": "chatgpt_staging/validation/val-20260502-apply-bad-schema-001.md",
      "source": "files/new.md",
      "create_only": true,
      "expected_new_sha256": "9332c4c55c4ecb761249370c0731eb05dbb35d7efa8259459c8c5c5fe8d012bc"
    }
  ]
}

```

## Artifact pointer

Detailed diagnostics, hashes, and any copied manifest are uploaded as GitHub Actions artifact 'chatgpt-apply-in-failure-25260146826' for run 25260146826 when available.

## Cleanup guidance

After ChatGPT reads this report and retrieves any needed artifact/log details, create a cleanup marker for request id 'val-20260502-apply-bad-schema-001' with cleanup_status_reports=true and cleanup_in_payloads=true.

## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, decide whether to regenerate the payload with current hashes or repair the workflow, then update Airtable.
