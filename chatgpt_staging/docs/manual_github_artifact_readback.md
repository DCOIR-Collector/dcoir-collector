# Manual GitHub Artifact Readback

Use this workflow when ChatGPT needs connector-readable access to a GitHub Actions artifact without asking the operator to download and re-upload the ZIP manually.

## Workflow

- workflow name: `manual-github-artifact-readback`
- workflow file: `.github/workflows/manual-github-artifact-readback.yml`

## Inputs

- `source_run_id`: GitHub Actions run id that owns the artifact
- `artifact_name` or `artifact_id`: bounded artifact selector
- `request_id`: optional safe override for the staged output folder
- `artifact_subpath`: optional relative path inside the extracted artifact when only one file or folder should be staged

## Readback paths

Successful runs write:

```text
chatgpt_staging/status_reports/manual-github-artifact-readback/<request_id>/workflow_report.md
chatgpt_staging/out/<request_id>/artifact_manifest.json
chatgpt_staging/out/<request_id>/artifact_manifest.md
chatgpt_staging/out/<request_id>/...
```

The staged output under `chatgpt_staging/out/<request_id>/` is the primary ChatGPT-readable surface.

## Use pattern

1. Read the source workflow report first.
2. Confirm the source run id and artifact name or id.
3. Run `manual-github-artifact-readback` with bounded inputs.
4. Read `artifact_manifest.md` and the staged files under `chatgpt_staging/out/<request_id>/`.
5. After evidence is recorded, clean the bundle with `chatgpt-staging-cleanup` using `cleanup_out_bundles=true` and `cleanup_status_reports=true`.

## Safety notes

- Do not use absolute paths or parent traversal in `artifact_subpath`.
- Do not use this workflow as a substitute for heartbeat-first readback when the source workflow already commits the answer directly.
- Keep the staged bundle only as long as needed for readback and validation evidence.
