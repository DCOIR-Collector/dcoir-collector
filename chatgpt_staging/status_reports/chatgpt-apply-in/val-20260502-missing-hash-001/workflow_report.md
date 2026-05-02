# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: val-20260502-missing-hash-001
- payload_path: chatgpt_staging/in/val-20260502-missing-hash-001/payload.zip.b64
- github_run_id: 25259618970
- github_ref: refs/heads/main
- github_sha: 572171ccdedb4b0f6b1056231233ee13e5a2806d
- artifact_name: chatgpt-apply-in-failure-25259618970
- artifact_retention_days: 7
- report_created_utc: 2026-05-02T19:10:12Z

## Troubleshooting context

The apply-in workflow failed. Common causes are decode errors, missing apply_manifest.json, unsafe paths, missing sources, stale-write hash failures, create_only violations, hash mismatches, missing apply_manifest schema, missing workflow_change_reason for workflow edits, or git commit/push failure.

Hash policy: existing tracked files require expected_blob_sha or expected_current_sha256 unless manifest allow_missing_current_hash=true is explicitly set; new files require create_only=true and expected_new_sha256. Workflow mutation policy: .github/workflows targets require allow_workflow_changes=true and workflow_change_reason.

### Manifest excerpt

```json
{
  "schema": "dcoir.chatgpt_staging.apply_manifest.v1",
  "request_id": "val-20260502-missing-hash-001",
  "allowed_roots": [
    "chatgpt_staging"
  ],
  "files": [
    {
      "path": "chatgpt_staging/validation/val-20260502-apply-create-only-001.md",
      "source": "files/replacement.md",
      "expected_new_sha256": "abe8fb55eabfcb84ef106afcb27f0799162cd71c022e6ff47eba59fdfa8490dc"
    }
  ]
}

```

## Artifact pointer

Detailed diagnostics, hashes, and any copied manifest are uploaded as GitHub Actions artifact 'chatgpt-apply-in-failure-25259618970' for run 25259618970 when available.

## Cleanup guidance

After ChatGPT reads this report and retrieves any needed artifact/log details, create a cleanup marker for request id 'val-20260502-missing-hash-001' with cleanup_status_reports=true and cleanup_in_payloads=true.

## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, decide whether to regenerate the payload with current hashes or repair the workflow, then update Airtable.
