# ChatGPT GitHub Staging Lane Safety Contract

Status: production-safety contract for `PLAN-20260501-chatgpt-github-staging-lane`.

This folder supports the ChatGPT GitHub staging lane: a controlled path for large-file readback, stage-out bundles, and reviewed apply-in bundles when normal connector edits are too small, fragile, or cumbersome.

This lane is not production-ready merely because a smoke test passes. Production readiness requires this contract, matching workflow behavior, operator instructions, scenario validation, and Airtable evidence.

## New-session entrypoint

When a new ChatGPT session sees staging-lane, cleanup, failure-report, large-file readback, or batch-apply work, it must:

1. Read Airtable Queue Control, active Plan, and Work Item first.
2. Consult `dcoir-memory-preflight` routing/memory rows for staging-lane guidance.
3. Read this file and `chatgpt_staging/SCENARIO_MATRIX.md` from GitHub when repo-source work is in scope.
4. Check `chatgpt_staging/failure_reports/` before retrying a failed request id.
5. Check `chatgpt_staging/cleanup_requests/` before assuming cleanup was requested.
6. Record validation evidence before claiming production readiness.

## Durable folders

```text
chatgpt_staging/
  requests/           # ChatGPT-created stage-out request JSON files
  in/                 # ChatGPT-created apply-in payload folders
  out/                # GitHub-created stage-out bundles retained until cleanup marker
  apply_reports/      # GitHub-created apply reports
  failure_reports/    # GitHub-created minimal failure locators
  cleanup_requests/   # ChatGPT-created cleanup marker JSON files
  work/               # transient GitHub Actions work area; never committed
  testdata/           # validation fixtures
```

## Current proven capability

The lane has proven these mechanics in test scope:

- stage-out can create a readback bundle from repo files.
- apply-in can apply a staged bundle.
- base64 ZIP apply-in can decode and apply a ZIP payload.
- successful apply-in can delete `payload.zip.b64` after success.
- ZIP readback and sample alpha/beta updates were verified in prior smoke work.

These are capability proofs, not permission to use the lane broadly.

## Authority and ownership

- ChatGPT initiates requests, payloads, cleanup markers, and verification.
- GitHub Actions performs bounded automation.
- Airtable remains live queue authority and validation state authority.
- GitHub remains governed source/readback for workflow files, staging-lane code, operator instructions, and promoted history.
- A committed/pushed state is not complete until GitHub readback and Airtable validation/closeout records are updated.

## Production safety principles

1. Narrow by default. Each request or apply manifest must explicitly list the roots it may read or write.
2. No broad root writes. Manifests must not allow the repository root, empty strings, `.`, or wildcard-style broad coverage.
3. No path traversal. Absolute paths, drive-letter paths, parent segments, and root escapes are prohibited.
4. No secrets. Payloads must not include API keys, tokens, credentials, `.env` files, private config values, or secret-bearing logs.
5. No workflow mutation by default. `.github/` and especially `.github/workflows/` changes require an explicit workflow-repair branch and operator approval.
6. No stale overwrites. Apply-in must use current-source hash checks or blob SHA checks for existing files whenever overwriting tracked content.
7. No repo bloat. Payloads, ZIPs, extracted work folders, generated logs, and output bundles must be cleaned or explicitly retained as validation evidence.
8. Evidence before readiness. The lane cannot be called production-ready until blocked-path, hash-mismatch, cleanup, failure, and happy-path validation all pass.

## Allowed-root policy

Allowed roots must be supplied per request or per apply manifest. The list below defines classes, not blanket permission.

### Validation-only roots

- `chatgpt_staging/testdata/`

### Normal documentation/source roots

These may be allowed only when the task explicitly requires them:

- `knowledge/`
- `project_sources/`
- `operator_tools/`
- `dcoir_skills/`
- `project_settings/`
- `release_notes/`
- `README.md`
- `DCOIR_KNOWLEDGE_INDEX.md`

### Staging infrastructure roots

These are infrastructure/control surfaces and should not be regular apply targets:

- `chatgpt_staging/requests/`
- `chatgpt_staging/in/`
- `chatgpt_staging/out/`
- `chatgpt_staging/work/`
- `chatgpt_staging/apply_reports/`
- `chatgpt_staging/failure_reports/`
- `chatgpt_staging/cleanup_requests/`

A workflow may read or clean these surfaces when explicitly designed for that purpose. An arbitrary apply-in payload must not write into `out/`, `work/`, `apply_reports/`, `failure_reports/`, or `cleanup_requests/`.

### Workflow roots

Default: blocked.

- `.github/`
- `.github/workflows/`

Exception: a bounded workflow-repair branch may permit these paths only when the operator explicitly approves that branch and the manifest names the exact files involved.

## Stage-out contract

A stage-out request must include a safe `request_id`, explicit `allowed_roots`, exact paths and/or bounded search terms, bounded match counts, and a ZIP-first readback mode with text chunks as fallback.

Stage-out output must include a manifest JSON, a human-readable manifest, ZIP copy when available, blob SHA/SHA256 metadata, and enough evidence for ChatGPT to reason about source freshness without guessing.

Stage-out must retain `out/<request_id>/` until ChatGPT confirms retrieval and creates a cleanup marker.

## Apply-in contract

An apply-in payload must contain `apply_manifest.json`, a safe `request_id`, non-empty `allowed_roots`, an explicit `files` list, repo-relative target paths, payload-relative source paths, and current-source verification when overwriting tracked files.

When overwriting existing files, include at least one of:

- `expected_blob_sha`
- `expected_current_sha256`

When writing high-value new content, include `expected_new_sha256`.

Apply-in must fail closed when no files apply, target paths are outside allowed roots, source paths are unsafe or missing, hash checks fail, new-content hash checks fail, or workflow paths are requested without an explicit workflow exception.

## Failure locator contract

On apply-in failure, GitHub should create a minimal committed failure locator:

```text
chatgpt_staging/failure_reports/<request_id>/
  failure_summary.md
  artifact_locator.json
  cleanup_hint.json
```

The locator is intentionally small and safe for repo readback. Detailed diagnostics belong in the GitHub Actions artifact named by `artifact_locator.json`.

Before retrying a failed request id, ChatGPT must read the failure locator and decide whether to regenerate payload, use a new request id, or create a cleanup marker.

## Cleanup marker contract

ChatGPT creates cleanup markers only after it has retrieved needed output or read failure evidence:

```text
chatgpt_staging/cleanup_requests/<request_id>.json
```

The cleanup workflow deletes only scoped staging artifacts selected by the marker and then deletes the marker after success. It must preserve `.gitkeep` scaffold files and fail closed on malformed markers.

## Scenario matrix

The action-order scenario matrix lives in `chatgpt_staging/SCENARIO_MATRIX.md` and is part of this contract.

## Validation gates before production-ready

The lane is not production-ready until evidence exists for:

1. Happy-path stage-out readback for a bounded allowed root.
2. Happy-path apply-in for a bounded allowed root.
3. Base64 ZIP apply-in with payload deletion after success.
4. Blocked-path rejection for `.git/`, parent traversal, absolute paths, and disallowed roots.
5. Workflow path rejection unless an explicit workflow exception is enabled.
6. Stale-write/hash mismatch failure closed with a failure locator and no target commit.
7. Cleanup marker removes only scoped artifacts and preserves scaffolds.
8. Malformed cleanup marker fails closed.
9. Stage-out bundle remains until ChatGPT retrieval and cleanup marker.
10. Airtable Validation Evidence records results and limitations.

## Stop conditions

Stop and ask for operator guidance if a request needs a broad repo root, a workflow file must be changed outside an approved branch, a payload contains secrets, source hash checks fail, cleanup would delete unrelated files, generated artifacts are too large or unclear to review, or GitHub Actions behavior differs from this contract.
