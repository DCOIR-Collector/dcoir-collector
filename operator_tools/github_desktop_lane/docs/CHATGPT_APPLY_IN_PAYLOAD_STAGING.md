# ChatGPT Apply-In Payload Staging

## Purpose

`New-DcoirApplyInPayload.ps1` prepares a local ChatGPT apply-in ZIP payload for the `chatgpt-apply-in` GitHub Actions workflow.

Use this helper instead of pasting or connector-writing long base64 payloads into `chatgpt_staging/in/.../payload.zip.b64`.

## Why this exists

A live test on 2026-05-03 staged `chatgpt_staging/in/airtable-export-policy-20260503/payload.zip.b64` through a long inline write. The `chatgpt-apply-in` workflow run `25280175341` failed in the `Decode ZIP payload and apply bundle` step with:

```text
base64: invalid input
```

Readback showed the staged payload contained a literal truncation marker:

```text
ERROR TRUNCATED
```

That means the workflow lane was structurally sound enough to find the payload and start decoding, but the staged payload file was corrupted before the workflow executed.

## Tool

```text
operator_tools/github_desktop_lane/scripts/New-DcoirApplyInPayload.ps1
```

## Input contract

The input ZIP must contain `apply_manifest.json` at archive root.

The helper:

- resolves `DCOIR_REPO_ROOT` from Machine/System environment when `-RepoRoot` is omitted;
- writes the payload to `chatgpt_staging/in/<request_id>/payload.zip.b64`;
- writes `payload_staging_report.json` next to it;
- rejects unsafe request IDs;
- rejects payload text containing `ERROR TRUNCATED`;
- decodes the written base64 back to a temporary ZIP;
- verifies SHA256 round-trip equality;
- verifies the decoded ZIP still contains `apply_manifest.json`.

## Launcher

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirApplyInPayload.ps1'
$payload = Join-Path ([Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')) 'payload.zip'
& $script -PayloadZip $payload -RequestId 'my-request-id'
```

Then review and commit the two staged files:

```text
chatgpt_staging/in/<request_id>/payload.zip.b64
chatgpt_staging/in/<request_id>/payload_staging_report.json
```

Pushing `payload.zip.b64` under `chatgpt_staging/in/<request_id>/` triggers the `chatgpt-apply-in` workflow. You may also use workflow dispatch with the same repo-relative payload path.

## Safety rule

Do not stage long base64 payloads through chat or connector inline writes. Generate and validate the base64 locally with this helper, then commit/push the generated files from GitHub Desktop or local git.

## Failure triage

If `chatgpt-apply-in` fails, inspect:

```text
chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/workflow_report.md
```

Then inspect the GitHub Actions job log and failure artifact named like:

```text
chatgpt-apply-in-failure-<run_id>
```

The committed report gives the run id, artifact name, payload path, request id, and next action. The job log usually contains the exact failed command.
