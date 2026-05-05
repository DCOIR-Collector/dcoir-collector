# ChatGPT Apply-In Core Skill Parity Sync

Status: active procedure for updating governed DCOIR skill source in GitHub from already-installed/verified ChatGPT skills.

## Use this when

Use this procedure when installed DCOIR skills have already been patched, installed in ChatGPT, marker/readback verified, and the remaining job is to sync the matching source files under `dcoir_skills/` in `malwaredevil/dcoir-collector`.

Do not rediscover this lane. Use `chatgpt-apply-in` by staging a validated `payload.zip.b64` through the GitHub connector when the operator authorizes connector staging.

## Required DCOIR gates

Before execution, run compact gates:

1. `dcoir-memory-preflight`: route as GitHub workflow/apply-in skill parity task; check Operator Tools Registry for `DCOIR-CHATGPT-APPLY-IN-PAYLOAD-STAGER`.
2. `dcoir-decision-policy`: lane is GitHub connector staging to `chatgpt-apply-in` unless operator changes it.
3. `dcoir-repo-packager`: payload is one apply-in ZIP, affected files only.
4. `dcoir-validation-orchestrator`: verify workflow report and GitHub readback before claiming parity success.
5. `dcoir-session-manager`: checkpoint before/after material workflow execution or at closeout.

## Build payload

Create one ZIP containing:

```text
apply_manifest.json
files/<repo-relative paths>
```

Manifest schema:

```json
{
  "schema": "dcoir.chatgpt_staging.apply_manifest.v1",
  "request_id": "apply-YYYYMMDD-core-skill-parity-sync-001",
  "allowed_roots": ["dcoir_skills"],
  "files": []
}
```

For existing tracked files include `expected_blob_sha` or `expected_current_sha256`. For new files include `create_only:true` and `expected_new_sha256`.

For each updated skill, include the changed `SKILL.md` and any added/changed reference files. Do not include skill ZIPs, local caches, runtime residue, `.git`, or ChatGPT-only meta files.

## Stage through connector

Base64 encode the ZIP as `payload.zip.b64`. Stage it with the GitHub connector at:

```text
chatgpt_staging/in/<request_id>/payload.zip.b64
```

Optionally stage:

```text
chatgpt_staging/in/<request_id>/payload_staging_report.json
```

Before writing, validate: ZIP opens; `apply_manifest.json` exists at archive root; base64 round trip matches source ZIP SHA256; request id is safe; no truncation marker exists.

Pushing `payload.zip.b64` to `main` triggers `.github/workflows/chatgpt-apply-in.yml`.

## Verify workflow

Do not wait for the operator to provide logs. Check results directly:

1. Fetch workflow report:

```text
chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/workflow_report.md
```

2. If needed, fetch workflow jobs using `github_run_id` from the report.
3. Verify job conclusion is `success` and apply step succeeded.
4. Read back every target file from GitHub `main`.
5. Confirm expected skill markers/reference files are present.
6. Only then claim the source sync succeeded.

## Fallback batching

If the full eight-skill payload fails because of size, connector limits, or workflow validation:

1. Retry with four skills.
2. Then remaining four skills.
3. If still blocked, retry one skill at a time.

A one-skill test already succeeded for `dcoir-session-manager` under request id:

```text
apply-20260505-session-manager-parity-test-001
```

That successful test applied:

```text
dcoir_skills/dcoir-session-manager/SKILL.md
dcoir_skills/dcoir-session-manager/references/session_checkpoint_and_closeout_workflow.md
```

Workflow run:

```text
25369464930
```

## After all skill source syncs

After every updated core skill source is synced and readback verified, run or trigger the skill parity refresh workflow/tooling that regenerates:

```text
dcoir_skills/skill_parity_manifest.json
dcoir_skills/skill_parity_summary.md
```

Then verify those parity documents by GitHub readback. Update Airtable evidence/checkpoints as needed. Clean staging artifacts only after reports/readback are consumed.

## Current remaining skill source targets after the one-skill test

The already-synced test skill is `dcoir-session-manager`. Remaining likely source-sync targets from the 2026-05-05 strengthening pass are:

```text
dcoir-memory-preflight
dcoir-airtable-schema-cache
dcoir-decision-policy
dcoir-local-config-registry-maintainer
dcoir-github-desktop-lane-advisor
dcoir-repo-packager
dcoir-validation-orchestrator
```

Also include their added reference files and then refresh parity surfaces.
