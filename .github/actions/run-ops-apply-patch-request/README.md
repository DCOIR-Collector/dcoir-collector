# Run ops apply-patch request

Composite action for the `ops-apply-patch` workflow family.

## Purpose

This action keeps the high-risk apply-patch implementation out of the reusable
workflow body while preserving caller-visible evidence and outputs.

It supports two operations:

- `apply`: resolve one staged request from `ops/requests/apply_patch/<request_id>/`,
  run `ops/tools/apply_patch_request.py`, and write `result.json` plus
  `workflow_report.md` under the caller-provided report root.
- `cleanup`: after the report artifact is uploaded, remove the staged request
  directory from the request source branch only when `result.json` shows a
  successful `mode: "apply"` run.

## Surfaces

- Entry workflow: `.github/workflows/ops-apply-patch.yml`
- Reusable workflow: `.github/workflows/reusable-ops-apply-patch.yml`
- Composite action: `.github/actions/run-ops-apply-patch-request/action.yml`
- Patch validator/apply script: `ops/tools/apply_patch_request.py`
- Request folder: `ops/requests/apply_patch/<request_id>/`

Failed apply requests and dry-run requests leave staged files in place for
operator review. Successful apply requests are cleaned after report artifact
upload using a `[skip ci]` cleanup commit.
