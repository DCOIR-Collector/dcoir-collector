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
- artifact name/run id when full raw logs or bulky diagnostics are needed
- cleanup guidance and next ChatGPT action

## Cleanup expectation

After ChatGPT reads and records the needed evidence, ChatGPT may create a cleanup marker under:

```text
chatgpt_staging/cleanup_requests/<request_id>.json
```

That marker can remove scoped status reports, output bundles, inbound payloads, apply reports, or failure reports while preserving `.gitkeep` scaffolds.

## Operator action

For staging-lane workflow troubleshooting, normally say `cap` after you commit/push a bundle or ask ChatGPT to inspect the latest workflow reports. ChatGPT should use connector readback and status reports before asking you for logs.
