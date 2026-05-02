# ChatGPT Staging Lane Operator Guide

Use this lane only when normal ChatGPT/GitHub connector edits or readback are too small, fragile, or awkward for the current task.

## Operator promise

When the staging workflows produce `chatgpt_staging/status_reports/`, ChatGPT should read those reports before asking you for screenshots, pasted logs, uploaded logs, or a commit SHA.

## Where ChatGPT looks first

```text
chatgpt_staging/status_reports/<workflow-name>/<request-id-or-run-id>/workflow_report.md
```

Each workflow result should have one committed Markdown report. Do not expect paired JSON and Markdown reports unless a future design explicitly justifies a second artifact.

## What reports contain

A good report includes:

- workflow name and result
- run id, ref, triggering SHA, and request id when available
- request, payload, output, or cleanup marker path
- changed, applied, removed, retained, or skipped paths
- failure phase and bounded troubleshooting context
- stale-write/hash details when relevant
- artifact name/run id when full raw logs or bulky diagnostics are needed
- cleanup guidance and next ChatGPT action

## Hash and stale-write rule

For apply-in bundles:

- Existing tracked files require `expected_blob_sha` or `expected_current_sha256`.
- New files require `create_only: true` and `expected_new_sha256`.
- `create_only` fails if the target already exists.
- Existing untracked files are not overwritten.
- Any `allow_missing_current_hash: true` override should be visible in the workflow report.

This means stale or under-specified bundles should fail before changing repo files.


## Trigger isolation rule

The staging workflows keep automatic push triggers, but only for the staging transfer paths on `main`:

- `chatgpt_staging/requests/*.json`
- `chatgpt_staging/in/*/payload.zip.b64`
- `chatgpt_staging/cleanup_requests/*.json`

Workflow-generated commits use `[skip ci]` to avoid unnecessary recursive push runs. Request, apply, and cleanup inputs also require explicit schema fields. Workflow file mutation remains blocked by default; apply manifests that touch `.github/workflows/` require `allow_workflow_changes: true` and `workflow_change_reason`.

## Cleanup expectation

After ChatGPT reads and records the needed evidence, ChatGPT may create a cleanup marker under:

```text
chatgpt_staging/cleanup_requests/<request_id>.json
```

That marker can remove scoped status reports, output bundles, inbound payloads, apply reports, or failure reports while preserving `.gitkeep` scaffolds.

## Operator action

For staging-lane workflow troubleshooting, normally say `cap` after you commit/push a bundle or ask ChatGPT to inspect the latest workflow reports. ChatGPT should use connector readback and status reports before asking you for logs.
