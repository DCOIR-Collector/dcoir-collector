# ChatGPT GitHub Staging Lane Safety Contract

Status: production-safety contract draft for `PLAN-20260501-chatgpt-github-staging-lane` / `T1`.

This folder supports the ChatGPT GitHub staging lane: a controlled path for large-file readback, stage-out bundles, and reviewed apply-in bundles when normal connector edits are too small, fragile, or cumbersome.

This lane is not production-ready merely because a smoke test passes. Production readiness requires the contract below, matching workflow behavior, operator instructions, and captured validation evidence.

## Current proven capability

The current lane has already proven the basic mechanics in test scope:

- stage-out can create a readback bundle from repo files.
- apply-in can apply a staged bundle.
- base64 ZIP apply-in can decode and apply a ZIP payload.
- successful apply-in can delete `payload.zip.b64` after success.
- ZIP readback and sample alpha/beta updates were verified in prior smoke work.

These are capability proofs, not permission to use the lane broadly.

## Authority and ownership

- Airtable remains live queue authority for whether this lane is active and what task owns current work.
- GitHub remains governed source/readback for workflow files, staging-lane code, operator instructions, and promoted history.
- The staging lane must never replace normal review, GitHub Desktop inspection, validation evidence, or operator approval.
- A committed/pushed state is not considered complete until GitHub readback and Airtable validation/closeout records are updated.

## Production safety principles

1. Narrow by default. Each request or apply manifest must explicitly list the roots it may read or write.
2. No broad root writes. Manifests must not allow the repository root, empty strings, `.`, or wildcard-style broad coverage.
3. No path traversal. Absolute paths, drive-letter paths, parent segments, and root escapes are prohibited.
4. No secrets. Payloads must not include API keys, tokens, credentials, `.env` files, private config values, or secret-bearing logs.
5. No workflow mutation by default. `.github/` and especially `.github/workflows/` changes require an explicit workflow-repair branch and operator approval.
6. No stale overwrites. Apply-in must use current-source hash checks or blob SHA checks for existing files whenever overwriting tracked content.
7. No repo bloat. Payloads, ZIPs, extracted work folders, generated logs, and output bundles must be cleaned or explicitly retained as validation evidence.
8. Evidence before readiness. The lane cannot be called production-ready until blocked-path, hash-mismatch, cleanup, and happy-path validation all pass.

## Allowed-root policy

Allowed roots must be supplied per request or per apply manifest. The list below defines classes, not blanket permission.

### Validation-only roots

Use only for smoke tests and fixtures:

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

A workflow may read or clean these surfaces when explicitly designed for that purpose. An arbitrary apply-in payload must not write into `out/`, `work/`, or `apply_reports/`.

### Workflow roots

Default: blocked.

- `.github/`
- `.github/workflows/`

Exception: a bounded workflow-repair branch may permit these paths only when the operator explicitly approves that branch and the manifest names the exact files involved.

## Blocked paths and content

Reject any payload or request that targets or includes:

- `.git/` or Git internals
- parent path segments such as `../`
- absolute paths such as `/tmp/file` or `C:\temp\file`
- `.env`, token, credential, key, certificate, or secret-bearing files
- generated dependency folders such as `node_modules/`, `.venv/`, `dist/`, `build/`, `bin/`, or `obj/`
- binary executables or archives unless the task is explicitly a bounded binary/artifact packaging task
- `.github/` unless an explicit workflow-repair exception exists
- stale staging artifacts not tied to the current request id

## Stage-out contract

A stage-out request must include:

- a safe `request_id`
- an explicit `allowed_roots` list
- exact paths and/or bounded search terms
- a bounded maximum match count when search terms are used
- a mode that preserves a ZIP-first readback with text chunks as fallback

Stage-out output must include:

- a manifest JSON with path, byte count, line count, blob SHA, SHA256, and chunk references
- a human-readable manifest summary
- a ZIP copy when available
- enough evidence for ChatGPT to reason about source freshness without guessing

## Apply-in contract

An apply-in payload must contain:

- `apply_manifest.json`
- a safe `request_id`
- a non-empty `allowed_roots` list
- an explicit `files` list
- each file's repo-relative target path
- each file's payload-relative source path
- current-source verification when overwriting existing tracked files

When overwriting existing files, at least one of these should be present:

- `expected_blob_sha`
- `expected_current_sha256`

When writing new payload content, `expected_new_sha256` should be present for high-value files.

Apply-in must fail closed when:

- no files are applied
- a target is outside allowed roots
- a source path is unsafe or missing
- a current-source hash check fails
- a new-content hash check fails
- a workflow path is requested without an explicit workflow exception

## Cleanup and quarantine contract

Successful apply-in:

- should delete the consumed `payload.zip.b64` when configured to do so
- should not commit `chatgpt_staging/work/`
- should not leave extracted ZIP content in the repo
- should leave only intentional target changes and explicitly retained validation reports

Failed apply-in:

- must not commit partial target changes
- should preserve enough failure evidence to diagnose the issue
- should quarantine failed request material by request id only when the workflow explicitly implements quarantine
- must not silently delete failure evidence before it is captured

Cleanup workflow behavior:

- must preserve scaffold `.gitkeep` files
- must reject unsafe cleanup filters or paths
- should support request-id filtering
- should distinguish consumed requests, inbound payloads, outbound bundles, and apply reports

## Trigger isolation contract

Production use should prefer intentional `workflow_dispatch` runs.

Push-triggered runs are allowed only if all of these remain true:

- the push path is narrowly scoped to staging request or payload files
- the workflow resolves exactly one current request/payload
- the request id is safe
- the workflow exits safely when no matching payload exists
- the workflow cannot be triggered by unrelated repo changes

Workflow changes themselves are blocked through this lane unless a workflow-repair branch is explicitly approved.

## Validation gates before production-ready

The lane is not production-ready until evidence exists for all gates below:

1. Happy-path stage-out readback succeeds for a bounded allowed root.
2. Happy-path apply-in succeeds for a bounded allowed root.
3. Base64 ZIP apply-in succeeds with payload deletion after success.
4. Blocked-path validation rejects `.git/`, parent traversal, absolute paths, and disallowed roots.
5. Workflow path mutation is rejected unless an explicit workflow exception is enabled.
6. Stale-write protection fails closed on an expected hash mismatch.
7. Cleanup preserves scaffold files and removes selected consumed artifacts.
8. Failed-payload behavior preserves diagnostic evidence without committing partial target changes.
9. Repo readback confirms no stale ZIP, base64 payload, extracted work folder, or generated junk remains.
10. Airtable Validation Evidence records the test result and remaining limitations.

## Stop conditions

Stop and ask for operator guidance if:

- a request or manifest needs a broad repo root
- a workflow file must be changed
- a payload contains secrets or suspected secrets
- source hash checks fail
- cleanup would delete scaffold or unrelated files
- generated artifacts are too large or unclear to review
- GitHub Actions behavior differs from the contract

## Current next work

T1 is satisfied when this contract is reviewed and accepted as the governing production-safety contract.

Next implementation tasks should use this contract to complete:

- cleanup and failed-payload quarantine behavior
- source-hash and stale-write protections
- workflow trigger isolation and workflow-mutation boundaries
- repo-bloat mitigation
- operator instructions
- final validation evidence
