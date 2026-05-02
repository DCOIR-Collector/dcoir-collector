# ChatGPT Staging Lane Operator Guide

This guide explains when to use the ChatGPT GitHub Staging Lane, when not to use it, and what evidence to preserve.

Use this lane only when normal ChatGPT/GitHub connector edits or readback are too small, fragile, or awkward for the current task.

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

## Hash and stale-write expectations

For existing files, include either `expected_blob_sha` or `expected_current_sha256` whenever possible.

For high-value new content, include `expected_new_sha256`.

If a hash check fails, stop. Do not bypass the check unless the operator explicitly confirms that the source changed and provides a new reviewed payload.

## Cleanup expectations

After success, the consumed base64 payload should be removed when `delete_payload_after_success` is enabled.

The repo should not retain:

- extracted work folders
- stale ZIP payloads
- stale base64 payloads
- unrelated staging outputs
- temporary logs not selected as validation evidence

Scaffold `.gitkeep` files should remain.

## Stop conditions

Stop and ask for guidance if:

- allowed roots are broad or ambiguous
- a payload includes `.github/` or workflow files
- a payload includes secrets or local config values
- source hash checks fail
- cleanup proposes deleting scaffold or unrelated files
- output artifacts are too large or unclear to review
- the workflow behavior differs from the safety contract

## Completion evidence

Before closing staging-lane work, preserve:

- GitHub run or commit readback
- staging manifest or apply report
- cleanup proof where relevant
- validation evidence in Airtable
- notes about what was not tested
