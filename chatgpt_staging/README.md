# ChatGPT GitHub Staging Lane Safety Contract

Status: active safety and operations contract for `PLAN-20260501-chatgpt-github-staging-lane`.

This folder supports the ChatGPT GitHub staging lane: a controlled path for large-file readback, stage-out bundles, reviewed apply-in bundles, cleanup markers, and workflow status reports when normal connector edits or readback are too small, fragile, or cumbersome.

## New-session rule

When a session sees staging-lane, cleanup, failure-report, workflow-report, large-file readback, or batch-apply work:

1. Read Airtable Queue Control, active Plan, and Work Item.
2. Consult the Airtable `SKILLROUTE-CHATGPT-STAGING-LANE` and `DECISION-CHATGPT-STAGING-LANE-DEFAULTS` rows.
3. Read this file and `chatgpt_staging/SCENARIO_MATRIX.md` from GitHub when repo-source behavior is in scope.
4. Check `chatgpt_staging/status_reports/` before asking the operator for screenshots, copied logs, or uploaded logs.
5. Check `chatgpt_staging/failure_reports/` before retrying an old request id.
6. Check `chatgpt_staging/cleanup_requests/` before assuming cleanup was requested or completed.
7. Never claim cleanup, retry safety, or production readiness without GitHub readback and Airtable evidence.

## Production safety principles

1. Narrow by default. Each request or apply manifest must explicitly list the roots it may read or write.
2. No broad root writes. Manifests must not allow the repository root, empty strings, `.`, or wildcard-style broad coverage.
3. No path traversal. Absolute paths, drive-letter paths, parent segments, and root escapes are prohibited.
4. No secrets. Payloads must not include API keys, tokens, credentials, `.env` files, private config values, or secret-bearing logs.
5. No workflow mutation by default. `.github/` and especially `.github/workflows/` changes require an explicit workflow-repair branch and operator approval.
6. No stale overwrites. Apply-in must use current-source hash checks or blob SHA checks for existing files whenever overwriting tracked content.
7. No repo bloat. Payloads, ZIPs, extracted work folders, generated logs, output bundles, status reports, and failure reports must be cleaned or explicitly retained as validation evidence.
8. Evidence before readiness. The lane cannot be called production-ready until blocked-path, hash-mismatch, cleanup, workflow-report, and happy-path validation all pass.

## Folder roles

```text
chatgpt_staging/
  requests/          # ChatGPT-created stage-out requests
  in/                # ChatGPT-created apply-in payloads
  out/               # GitHub-created stage-out bundles retained until ChatGPT cleanup
  work/              # transient workflow work area; never intentionally committed
  apply_reports/     # apply-in reports when retained
  failure_reports/   # legacy/special failure locators; use status_reports for new workflow result reports
  status_reports/    # one committed workflow_report.md per workflow result
  cleanup_requests/  # ChatGPT-created cleanup markers
```

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
- hash mismatch, unsafe path, malformed marker, or validation details when relevant
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
