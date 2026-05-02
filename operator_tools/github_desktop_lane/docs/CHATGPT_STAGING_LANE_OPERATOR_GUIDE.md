# ChatGPT Staging Lane Operator Guide

This guide explains when to use the ChatGPT GitHub Staging Lane, when not to use it, what files to look for, and how cleanup works.

Use this lane only when normal ChatGPT/GitHub connector edits or readback are too small, fragile, or awkward for the current task.

## Action order

1. ChatGPT initiates the request, payload, cleanup marker, or verification.
2. GitHub Actions performs bounded automation.
3. ChatGPT verifies GitHub readback and updates Airtable plan/work/evidence state.

## When to use this lane

Use it for:

- large-file readback from governed repo paths
- bounded multi-file readback bundles
- reviewed batch apply of repo-relative files
- recovery from connector size or edit limits
- validation fixtures for the staging workflow itself

Do not use it for routine one-file edits, secrets, broad repo sync, unreviewed workflow mutation, or anything that should be handled by the normal GitHub connector or GitHub Desktop update bundle.

## Before use

Confirm:

1. Airtable says the staging-lane plan or a specific Work Item owns the work.
2. The request has a clear purpose and bounded repo paths.
3. The manifest has explicit allowed roots.
4. No payload contains secrets, tokens, credentials, or local-only values.
5. Workflow paths are not included unless the operator explicitly approved a workflow-repair branch.
6. There is a defined validation/evidence target.
7. `chatgpt_staging/README.md` and `chatgpt_staging/SCENARIO_MATRIX.md` have been considered for scenario handling.

## Folder map

```text
chatgpt_staging/
  requests/           # stage-out request JSON files ChatGPT creates
  in/                 # apply-in payload folders ChatGPT creates
  out/                # stage-out bundles GitHub creates and preserves until cleanup marker
  apply_reports/      # apply-in reports GitHub creates after success
  failure_reports/    # minimal failure locators GitHub creates after apply-in failure
  cleanup_requests/   # cleanup marker JSON files ChatGPT creates after retrieval/evidence review
  work/               # transient GitHub Actions work area; never committed
```

## Stage-out request checklist

A stage-out request should include:

- safe `request_id`
- explicit `allowed_roots`
- exact paths where possible
- bounded search terms only when exact paths are not enough
- reasonable match and chunk limits

Expected evidence:

- generated manifest JSON
- generated manifest Markdown
- staged ZIP when available
- text chunks with path, blob SHA, SHA256, and line spans

Do not create a cleanup marker for `out/<request_id>/` until ChatGPT has retrieved whatever it needs.

## Apply-in payload checklist

An apply-in ZIP should contain:

- `apply_manifest.json`
- source files under payload-relative paths
- explicit target paths
- explicit allowed roots
- expected source hashes for overwrites
- expected new hashes for high-value content

Review before use:

- every target path
- every allowed root
- every file source path
- whether workflow mutation is being attempted
- whether cleanup is expected after success

## Failure report handling

When apply-in fails, look first in:

```text
chatgpt_staging/failure_reports/<request_id>/
```

Expected files:

```text
failure_summary.md
artifact_locator.json
cleanup_hint.json
```

The failure locator is intentionally small and committed so a new ChatGPT session can find it. Detailed diagnostics should be in the GitHub Actions artifact named in `artifact_locator.json`.

Before retrying:

1. Read `failure_summary.md`.
2. Read `artifact_locator.json` and inspect the GitHub Actions run or artifact when needed.
3. Decide whether to regenerate the payload, use a new request id, or stop.
4. Create a cleanup marker only after evidence is no longer needed.

## Cleanup marker handling

ChatGPT may create:

```text
chatgpt_staging/cleanup_requests/<request_id>.json
```

Recommended marker shape:

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
  "reason": "ChatGPT retrieved needed evidence and requested scoped cleanup."
}
```

GitHub cleanup should delete only scoped staging artifacts and preserve `.gitkeep` files. Malformed markers must fail closed.

## Hash and stale-write expectations

For existing files, include either `expected_blob_sha` or `expected_current_sha256` whenever possible.

For high-value new content, include `expected_new_sha256`.

If a hash check fails, stop. Do not bypass the check unless the operator explicitly confirms that the source changed and provides a new reviewed payload.

## Completion evidence

Before closing staging-lane work, preserve or record:

- GitHub commit or run readback
- stage-out manifest or apply report
- failure locator and artifact reference when failure occurred
- cleanup proof where relevant
- validation evidence in Airtable
- notes about what was not tested

## Stop conditions

Stop and ask for guidance if allowed roots are broad or ambiguous, a payload includes workflow files without approval, a payload includes secrets or local config values, source hash checks fail, cleanup proposes deleting scaffold or unrelated files, output artifacts are too large or unclear to review, or workflow behavior differs from the safety contract.
