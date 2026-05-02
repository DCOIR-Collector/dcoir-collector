# ChatGPT Staging Lane Scenario Matrix

Status: active planning and implementation matrix for `PLAN-20260501-chatgpt-github-staging-lane`.

Action order is ChatGPT first, GitHub second, Airtable/skill state third. ChatGPT initiates and verifies. GitHub performs bounded automation. Airtable and helper skills preserve durable state and routing.

| Scenario | ChatGPT action | GitHub action | Airtable / skill state |
|---|---|---|---|
| Stage-out needed | Create `chatgpt_staging/requests/<request_id>.json` with explicit allowed roots and exact paths or bounded search terms. | Detect request, create `chatgpt_staging/out/<request_id>/`, commit output bundle, and delete consumed request JSON after success. | Work Item remains active or waiting until ChatGPT retrieves output and records evidence. |
| Stage-out succeeds and bundle is needed | Retrieve `manifest.json`, `manifest.md`, `staged_files.zip`, chunks, or copied files as needed. After retrieval, create a cleanup marker when safe. | Preserve `out/<request_id>/` until a cleanup marker appears. | Record readback/evidence before cleanup. |
| Stage-out succeeds but bundle is no longer needed | Create `chatgpt_staging/cleanup_requests/<request_id>.json` scoped to out bundle cleanup. | Delete only scoped `out/<request_id>/` and the cleanup marker; preserve `.gitkeep`. | Record cleanup verification if material. |
| Stage-out fails before output | Inspect workflow run, logs, and artifacts if available; decide retry or repair. | Preserve failure in run logs/artifacts; do not perform unsafe cleanup. | Mark Work Item blocked or waiting with failure class. |
| Apply-in needed | Create `chatgpt_staging/in/<request_id>/payload.zip.b64` with `apply_manifest.json`, allowed roots, hashes, and explicit targets. | Detect payload, decode ZIP, validate manifest, apply changes, commit target changes, and delete inbound payload only after success. | Work Item remains active until commit/readback succeeds. |
| Apply-in succeeds | Verify target file commit/readback; create cleanup marker if retained reports or outputs should be removed. | Commit target file changes and apply report; delete inbound payload as part of the successful apply commit. | Close or advance Work Item only after readback. |
| Apply-in fails before decode | Read repo-visible failure locator and retrieve artifact/logs if needed; decide retry or cleanup. | Commit minimal `failure_reports/<request_id>/` locator and upload detailed artifact. | Mark blocked or waiting; preserve evidence. |
| Apply-in fails after decode before copy | Inspect manifest/hash/payload context from locator/artifact. | Commit locator with decoded context when available; no target commit. | Update Work Item with failure class. |
| Apply-in fails due to hash mismatch | Decide whether to regenerate payload from current repo source or stop. | Fail closed, commit failure locator naming mismatch, commit no target changes. | Feed T3 stale-write/hash validation. |
| Apply-in fails after partial local copy before commit | Confirm no target commit landed; decide retry after diagnosis. | Upload failure artifact and commit locator only; do not commit partial target changes. | Preserve failure evidence before retry. |
| Cleanup marker needed | Create `chatgpt_staging/cleanup_requests/<request_id>.json` only after retrieval/readback. | Detect marker, delete only scoped staging artifacts, delete marker after success, preserve scaffolds. | Record cleanup verification if material. |
| Cleanup marker malformed | Fix marker or delete/recreate safely. | Fail closed and delete nothing. | Mark cleanup blocked if it affects the active plan. |
| Manual cleanup needed | Recommend `workflow_dispatch` cleanup only for stale or exceptional artifacts. | Run scoped cleanup with selected switches and optional request ID filter. | Record note/evidence if cleanup changes repo. |
| Retrying failed apply-in | Read old failure locator first, generate a new reviewed payload, then later create cleanup marker for old failure if safe. | Keep previous locator until cleanup marker removes it; process new payload independently. | Preserve failure chain until retry succeeds. |

## Required new-session checklist

When a new session sees staging-lane, cleanup, failure-report, large-file readback, or batch-apply work:

1. Read Airtable active Plan, Work Item, and Queue Control.
2. Consult `dcoir-memory-preflight` routing/memory rows for staging-lane guidance.
3. Read `chatgpt_staging/README.md` and this scenario matrix from GitHub when repo-source work is in scope.
4. Check `chatgpt_staging/failure_reports/` before retrying a failed request id.
5. Check `chatgpt_staging/cleanup_requests/` before assuming cleanup was requested or completed.
6. Never claim cleanup, retry safety, or production readiness without GitHub readback and Airtable evidence.

## Cleanup marker schema

Create markers only after ChatGPT has retrieved needed output or read failure evidence.

```json
{
  "schema": "dcoir.chatgpt_staging.cleanup_request.v1",
  "request_id": "request-id",
  "cleanup_requests": true,
  "cleanup_in_payloads": true,
  "cleanup_out_bundles": true,
  "cleanup_apply_reports": false,
  "cleanup_failure_reports": false,
  "delete_marker_after_success": true,
  "reason": "ChatGPT retrieved the stage-out bundle and recorded evidence."
}
```

All booleans must be explicit when ChatGPT creates a marker. GitHub fails closed if the marker is malformed.
