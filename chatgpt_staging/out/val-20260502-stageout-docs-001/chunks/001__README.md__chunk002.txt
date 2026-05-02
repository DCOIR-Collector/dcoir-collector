original_path: chatgpt_staging/README.md
blob_sha: 75b4012d1dd88469343078a71608def408028c05
sha256: 566a2bc3e5f6c51f9c8a45d7fe8c3ee8b5011c4e088f4c628b26f84b90188b4c
chunk: 2
line_start: 121
line_end: 175
---

## Workflow status report contract

Staging workflows should write exactly one committed Markdown report per workflow result:

```text
chatgpt_staging/status_reports/<workflow-name>/<request-id-or-run-id>/workflow_report.md
```

Do not create paired JSON and Markdown reports for the same result. If additional evidence is required, use a GitHub Actions artifact and include the artifact name/run id inside `workflow_report.md`.

A useful report includes:

- workflow name, result, phase, run id, ref, triggering SHA, and request id when available
- request path, payload path, output path, or cleanup marker path when relevant
- changed, applied, removed, retained, or skipped paths
- failure phase and bounded troubleshooting context
- hash mismatch, unsafe path, malformed marker, stale-write, create_only, or validation details when relevant
- artifact pointer only when large raw diagnostics are needed
- cleanup guidance and next ChatGPT action

ChatGPT should read this report before asking the operator for screenshots, pasted logs, uploaded logs, or a commit SHA.

## Cleanup marker schema

Create cleanup markers only after ChatGPT has read or recorded needed output and reports.

```json
{
  "schema": "dcoir.chatgpt_staging.cleanup_request.v1",
  "request_id": "request-id",
  "cleanup_requests": true,
  "cleanup_in_payloads": true,
  "cleanup_out_bundles": true,
  "cleanup_apply_reports": false,
  "cleanup_failure_reports": false,
  "cleanup_status_reports": true,
  "delete_marker_after_success": true,
  "reason": "ChatGPT consumed the needed report/output and recorded evidence."
}
```

All cleanup booleans must be explicit when ChatGPT creates a marker. GitHub must fail closed if a marker is malformed.

## Stop conditions

Stop and ask for operator guidance if:

- a request or manifest needs a broad repo root
- a workflow file must be changed outside an approved workflow-repair branch
- a payload contains secrets or suspected secrets
- source hash checks fail
- cleanup would delete scaffold or unrelated files
- workflow report creation fails repeatedly and no readable evidence is available
- GitHub Actions behavior differs from this contract
