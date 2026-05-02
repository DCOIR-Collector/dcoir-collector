# ChatGPT Staging Lane Scenario Matrix

Status: active matrix for `PLAN-20260501-chatgpt-github-staging-lane`.

Action order is ChatGPT first, GitHub second, Airtable/skill state third. ChatGPT initiates and verifies. GitHub performs bounded automation. Airtable and helper skills preserve durable state and routing.

## Workflow report scenarios

Scope: ChatGPT-readable workflow success/failure reports and cleanup after ChatGPT reads them.

| Scenario | ChatGPT action | GitHub action | Airtable / skill state |
|---|---|---|---|
| Workflow starts normally | Wait for expected status report, or use GitHub readback if the report does not appear. | Initialize a report target using workflow name plus request id or run id. | Active Work Item remains active or waiting. |
| Workflow succeeds | Read `workflow_report.md`; verify result, changed paths, run id, commit/readback clues, and cleanup hint. Create cleanup marker when no longer needed. | Commit one compact Markdown report under `status_reports/<workflow>/<id>/workflow_report.md`. | Validation Evidence can record success based on report plus GitHub readback. |
| Workflow fails before meaningful work begins | Read failure report if present; otherwise inspect GitHub run metadata/log pointer. | Commit failure report if workflow reached reporting step; include failure phase as startup/preflight. | Work Item becomes waiting or blocked with failure class. |
| Workflow fails after request or payload is resolved | Read report to identify request id, payload path, failure phase, and next action. | Commit report with request or payload context and optional artifact locator. Do not delete input evidence prematurely. | Work Item notes include request id and failure phase. |
| Workflow fails due to validation or hash mismatch | Decide whether to regenerate request/payload from current source or stop. | Fail closed, write mismatch details in the report, commit no unsafe target changes. | Feeds T3 hash/stale-write validation evidence. |
| Workflow fails after partial local work but before commit/push | Confirm from report that no target commit landed; inspect artifact pointer if needed. | Commit failure report only; do not commit partial target changes. Upload detailed artifact if available. | Work Item stays blocked/waiting until retry decision. |
| Workflow succeeds but no changes were needed | Read report and confirm clean/no-op outcome. Create cleanup marker if report is no longer needed. | Commit no target changes if appropriate; write report stating no-op/skipped and why. | Evidence records no-op result if material. |
| Workflow succeeds and creates output needed by ChatGPT | Read report first, then retrieve named output bundle/files. Only after retrieval, create cleanup marker. | Preserve output and status report until cleanup marker appears. | Work Item remains waiting until retrieval/readback. |
| Workflow succeeds and cleanup happened inside the same run | Read report and confirm what cleanup was performed and what remains. | Report lists deleted paths, retained paths, scaffold preservation, and cleanup marker handling. | Evidence can record cleanup success if readback confirms. |
| Status report creation fails but workflow action succeeds | Use GitHub commit/readback to verify work; flag report failure as separate issue. | Avoid failing the primary task solely because report commit failed unless reporting is mandatory for that workflow. | Work Item gets warning; follow-up if repeated. |
| Status report creation fails and workflow action fails | Use GitHub run/log pointer if available; mark blocked if no readable evidence exists. | Best-effort raw logs/artifacts remain in GitHub Actions. | Work Item blocked; may require operator or workflow repair. |
| Cleanup marker for status report is created | Create cleanup marker only after reading/recording report evidence. | Cleanup removes scoped status report and marker; preserves `.gitkeep` scaffolds. | Evidence records cleanup if material. |
| Cleanup marker malformed | Fix or replace marker. | Fail closed and delete nothing. Write cleanup failure report if possible. | Work Item blocked/waiting if cleanup matters. |
| New session resumes after workflow run | Check active Airtable Work Item, then inspect `status_reports/` before asking operator for screenshots/log uploads. | Existing reports remain until cleanup marker removes them. | SKILLROUTE/decision rows point new sessions to reports. |
| Multiple reports exist | Read newest relevant report by workflow/request/run id; avoid deleting unrelated reports. | Reports are namespaced by workflow and request/run id. | Airtable notes identify which report was consumed. |
| Retry after failure | Read old failure report first, then create a new request/payload/run. Cleanup old report only after retry plan is clear. | Preserve old report until cleanup marker removes it; new run writes separate report. | Failure chain remains traceable until resolved. |

## Stage-out scenarios

| Scenario | ChatGPT action | GitHub action | Airtable / skill state |
|---|---|---|---|
| Stage-out needed | Create `chatgpt_staging/requests/<request_id>.json` with explicit allowed roots and exact paths or bounded search terms. | Detect request, create `out/<request_id>/`, write status report, commit output, and delete consumed request JSON after success. | Work Item remains active/waiting until ChatGPT retrieves output and records evidence. |
| Stage-out succeeds and bundle is needed | Retrieve `manifest.json`, `manifest.md`, `staged_files.zip`, chunks, or copied files as needed. After retrieval, create cleanup marker when safe. | Preserve `out/<request_id>/` and status report until cleanup marker appears. | Record readback/evidence before cleanup. |
| Stage-out fails before output | Inspect `status_reports/chatgpt-stage-out/<request_id>/workflow_report.md` and run logs if needed. | Commit small failure report if possible; do not perform unsafe cleanup. | Mark Work Item blocked or waiting with failure class. |

## Apply-in scenarios

| Scenario | ChatGPT action | GitHub action | Airtable / skill state |
|---|---|---|---|
| Apply-in needed | Create `chatgpt_staging/in/<request_id>/payload.zip.b64` with `apply_manifest.json`, allowed roots, hashes, and explicit targets. | Detect payload, decode ZIP, validate manifest, apply changes, write report, commit target changes, and delete inbound payload only after success. | Work Item remains active until commit/readback succeeds. |
| Apply-in succeeds | Read success report, verify target file commit/readback, then create cleanup marker if retained reports should be removed. | Commit target file changes, apply report, status report, and payload deletion. | Close or advance Work Item only after readback. |
| Apply-in fails | Read failure report and optional artifact pointer; decide retry or repair. | Commit one failure `workflow_report.md`; upload bulky diagnostics as artifact when useful; commit no target changes. | Preserve evidence and failure class before retry. |

## Cleanup scenarios

| Scenario | ChatGPT action | GitHub action | Airtable / skill state |
|---|---|---|---|
| Cleanup marker needed | Create `chatgpt_staging/cleanup_requests/<request_id>.json` only after retrieval/readback. | Detect marker, delete only scoped artifacts, write cleanup report, delete marker after success, preserve scaffolds. | Record cleanup verification if material. |
| Cleanup succeeds | Read cleanup workflow report; verify scoped deletion and retained scaffolds. | Commit cleanup changes and one cleanup `workflow_report.md`. | Validation case can pass after readback confirms no collateral deletion. |
| Cleanup marker malformed | Fix/recreate marker. | Fail closed, delete nothing, write failure report if possible. | Mark cleanup blocked if it affects active plan. |

## Cleanup marker schema

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
