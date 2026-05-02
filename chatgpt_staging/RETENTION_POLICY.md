# ChatGPT Staging Lane Retention Policy

Status: active retention and repo-bloat policy for `PLAN-20260501-chatgpt-github-staging-lane`.

Purpose: keep the staging lane useful without letting request files, payloads, output bundles, reports, or diagnostics accumulate in the repository.

## Default rule

Retain staging artifacts only long enough for ChatGPT to read, verify, troubleshoot, or record evidence. After that, ChatGPT should create a scoped cleanup marker.

Do not delete evidence before ChatGPT has consumed it. Do not keep evidence indefinitely unless it is intentionally retained as validation evidence and recorded in Airtable.

## Retention table

| Surface | Default retention | Cleanup owner | Cleanup flag |
|---|---|---|---|
| `chatgpt_staging/requests/*.json` | Deleted by stage-out after successful bundle creation. | GitHub workflow first; ChatGPT cleanup marker if leftovers remain. | `cleanup_requests` |
| `chatgpt_staging/in/<request_id>/payload.zip.b64` | Deleted by apply-in after successful apply/commit/push. | GitHub workflow first; ChatGPT cleanup marker if failed/stale. | `cleanup_in_payloads` |
| `chatgpt_staging/out/<request_id>/` | Retain until ChatGPT retrieves needed files or records evidence. | ChatGPT cleanup marker. | `cleanup_out_bundles` |
| `chatgpt_staging/apply_reports/*.md` | Retain until ChatGPT verifies apply commit/readback or validation evidence. | ChatGPT cleanup marker. | `cleanup_apply_reports` |
| `chatgpt_staging/failure_reports/<request_id>/` | Retain until failure is diagnosed and retry/stop decision is recorded. | ChatGPT cleanup marker. | `cleanup_failure_reports` |
| `chatgpt_staging/status_reports/<workflow>/<id>/workflow_report.md` | Retain until ChatGPT reads the report and records any needed evidence. | ChatGPT cleanup marker. | `cleanup_status_reports` |
| `chatgpt_staging/work/` | Transient workflow working directory; never intentionally committed. | Workflow runtime. | n/a |
| GitHub Actions artifacts | Short-lived diagnostics for bulky logs/manifests/hashes; default 7 days where configured. | GitHub artifact retention. | n/a |
| `.gitkeep` scaffold files | Retain permanently. | Never delete. | n/a |

## Cleanup marker expectations

ChatGPT-created cleanup markers must be scoped by `request_id` and must set every cleanup boolean explicitly.

Example after ChatGPT has consumed a stage-out bundle and workflow report:

```json
{
  "schema": "dcoir.chatgpt_staging.cleanup_request.v1",
  "request_id": "example-request",
  "cleanup_requests": true,
  "cleanup_in_payloads": false,
  "cleanup_out_bundles": true,
  "cleanup_apply_reports": false,
  "cleanup_failure_reports": false,
  "cleanup_status_reports": true,
  "delete_marker_after_success": true,
  "reason": "ChatGPT retrieved the stage-out bundle and recorded needed evidence."
}
```

Example after ChatGPT has diagnosed a failed apply-in payload:

```json
{
  "schema": "dcoir.chatgpt_staging.cleanup_request.v1",
  "request_id": "example-apply",
  "cleanup_requests": false,
  "cleanup_in_payloads": true,
  "cleanup_out_bundles": false,
  "cleanup_apply_reports": false,
  "cleanup_failure_reports": true,
  "cleanup_status_reports": true,
  "delete_marker_after_success": true,
  "reason": "ChatGPT diagnosed the failure and recorded retry/stop decision."
}
```

## Cleanup report rule

The cleanup workflow writes its own `workflow_report.md` so ChatGPT can verify what was deleted and what was retained. That final cleanup report is intentionally not deleted by the same run that creates it.

After ChatGPT reads a cleanup report and records any needed evidence, a later cleanup marker may remove that cleanup report with `cleanup_status_reports=true`.

## Validation evidence rule

If an artifact must be retained as validation evidence, record that decision in Airtable Validation Evidence or the active Work Item notes. Otherwise, assume staging artifacts are temporary.

## Stop conditions

Stop and ask for operator guidance if cleanup would:

- delete files outside `chatgpt_staging/`
- delete `.gitkeep` scaffolds
- delete output or reports before ChatGPT has consumed them
- delete evidence for an unresolved failure
- affect multiple unrelated request IDs without an explicit operator-approved reason
