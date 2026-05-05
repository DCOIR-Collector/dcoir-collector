# ChatGPT Apply-In Core Skill Parity Sync

Status: active procedure for updating governed DCOIR skill source in GitHub from already-installed/verified ChatGPT skills.

## Non-negotiable staging rule

Use exactly one base64 ZIP file:

```text
chatgpt_staging/in/<request_id>/payload.zip.b64
```

Do **not** use parts, chunks, chunk manifests, `payload.zip.b64.parts/`, `part-*.b64`, or any marker such as `# dcoir-payload-b64-parts-v1`.

If the payload is too large for connector staging, reduce the batch size and rebuild a new single `payload.zip.b64`. Do not split the file.

The workflow now rejects chunk/parts staging explicitly. The canonical staging contract is documented at:

```text
chatgpt_staging/in/README.md
```

The preferred repo-side helper for building this payload is:

```text
tools/chatgpt_apply_in/build_payload_zip_b64.py
```

## Use this when

Use this procedure when installed DCOIR skills have already been patched, installed in ChatGPT, marker/readback verified, and the remaining job is to sync the matching source files under `dcoir_skills/` in `malwaredevil/dcoir-collector`.

Do not rediscover this lane. Use `chatgpt-apply-in` by staging a validated single `payload.zip.b64` through the GitHub connector when the operator authorizes connector staging.

## Required DCOIR gates

Before execution, run compact gates:

1. `dcoir-memory-preflight`: route as GitHub workflow/apply-in skill parity task; check Operator Tools Registry for `DCOIR-CHATGPT-APPLY-IN-SINGLE-PAYLOAD-BUILDER`.
2. `dcoir-decision-policy`: lane is GitHub connector staging to `chatgpt-apply-in` unless operator changes it. If parts/chunks are proposed, stop and replace with the single `payload.zip.b64` lane.
3. `dcoir-repo-packager`: payload is one apply-in ZIP, affected files only, `apply_manifest.json` at archive root, and `files/` at archive root.
4. `dcoir-validation-orchestrator`: verify workflow report and GitHub readback before claiming parity success.
5. `dcoir-session-manager`: checkpoint before/after material workflow execution or at closeout.

## Batch-size rule

For core skill source parity sync payloads, keep ZIP sizes manageable and reduce connector/workflow friction:

- update a maximum of 4 skills per apply-in payload;
- use a minimum batch size of 2 skills when more than one skill remains;
- do not fall below 2 skills unless only 1 skill remains naturally after prior successful batches;
- if a planned or retry batch would contain fewer than 2 skills while more skills remain, stop and ask the operator for direction;
- if drift, uncertainty, repeated rediscovery, or lane confusion appears, stop and ask for help instead of improvising.

Recommended for seven skills: first payload = 4 skills, second payload = 3 skills. If the four-skill batch fails from size or validation, retry 2+2, then continue with the remaining 3 as 2+1 only if the 1 is the final natural remainder; otherwise stop and ask.

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

Preferred builder command pattern from a local repo checkout:

```bash
python tools/chatgpt_apply_in/build_payload_zip_b64.py \
  --repo-root . \
  --request-id apply-YYYYMMDD-core-skill-parity-sync-001 \
  --allowed-root dcoir_skills \
  --include dcoir_skills/<skill>/SKILL.md \
  --include dcoir_skills/<skill>/references/<reference>.md \
  --output-dir /tmp/dcoir_apply_in
```

The builder emits:

```text
payload.zip
payload.zip.b64
payload_report.json
```

The report records the ZIP SHA256, base64 SHA256, exact staging path, manifest, included files, and confirms `parts_mode:false`.

## Stage through connector

Base64 encode the ZIP as exactly:

```text
payload.zip.b64
```

Stage it with the GitHub connector at:

```text
chatgpt_staging/in/<request_id>/payload.zip.b64
```

Before writing, validate:

- ZIP opens;
- `apply_manifest.json` exists at archive root;
- `files/` exists at archive root;
- base64 round trip matches source ZIP SHA256;
- request id is safe;
- no truncation marker exists;
- no parts/chunk artifacts exist.

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

If a maximum-size four-skill payload fails because of size, connector limits, or workflow validation:

1. Retry as two-skill payloads.
2. Continue in two-to-four skill batches whenever possible.
3. A one-skill payload is allowed only as a final natural remainder after successful prior batches, or if the operator explicitly approves a one-skill retry/test.
4. If troubleshooting starts to become process rediscovery, stop and ask for help.
5. Never use chunking/parts as a fallback.

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
