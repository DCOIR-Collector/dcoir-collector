# Ops Apply Patch Requests

Stage exactly one request directory per apply operation:

```text
ops/requests/apply_patch/<request_id>/request.json
ops/requests/apply_patch/<request_id>/change.patch
```

`<request_id>` may contain only letters, numbers, dots, underscores, and hyphens.
The workflow only looks for requests under `ops/requests/apply_patch/<request_id>/`.

This lane is for connector-staged patch requests, not connector-staged full-file
replacement payloads. To use it through the GitHub connector, create both
`request.json` and the referenced `.patch` or `.diff` file on the default branch
under one request directory. A push to the default branch triggers the workflow,
which validates the request and applies the patch to `target_branch`.

The workflow does not scan arbitrary staging folders, does not ingest replacement
files, and does not apply multi-file patch sets. Use `chatgpt-apply-in` for
reviewed full-file ZIP payloads until a separate full-file ops request lane is
implemented.

## Implementation Surfaces

The apply-patch lane follows the repo workflow/module/script pattern:

- Entry workflow: `.github/workflows/ops-apply-patch.yml`
- Reusable workflow: `.github/workflows/reusable-ops-apply-patch.yml`
- Patch validation/apply script: `ops/tools/apply_patch_request.py`
- Request lookup folder: `ops/requests/apply_patch/<request_id>/`

The workflow and reusable workflow are tracked in the GitHub workflow inventory
and modularization contract under the `ops-apply-patch` family.

## Request Schema

```json
{
  "schema": "dcoir.ops.apply_patch_request.v1",
  "request_id": "example-request",
  "mode": "apply",
  "target_branch": "feature/example-branch",
  "target_path": "project_sources/example/large-file.txt",
  "allowed_roots": ["project_sources/example"],
  "patch_path": "ops/requests/apply_patch/example-request/change.patch",
  "expected_patch_sha256": "<sha256 of change.patch>",
  "expected_target_blob_sha": "<current git blob sha on target branch>",
  "expected_current_sha256": "<current file sha256 on target branch>",
  "expected_new_sha256": "<optional expected file sha256 after patch>",
  "commit_message": "Apply reviewed ops patch example-request"
}
```

Use `mode: "dry-run"` to validate and run `git apply --check` without committing.

Default-branch writes are blocked unless the request sets `allow_default_branch: true`
and includes a non-empty `default_branch_reason`.

Workflow-file targets are blocked unless the request sets
`allow_workflow_changes: true` and includes a non-empty
`workflow_change_reason`.

The v1 lane accepts only one text patch for one existing tracked file. It rejects
multi-file patches, binary patches, renames, copies, deletes, mode changes,
unsafe paths, missing stale-base hashes, and unexpected changed paths.

## Cleanup Lifecycle

Request files are staging inputs, not durable repo records.

- Successful `mode: "apply"` runs upload the report artifact first, then remove
  `ops/requests/apply_patch/<request_id>/` from the branch that staged the
  request using a `[skip ci]` cleanup commit.
- Before deletion, cleanup hashes the current staged request directory and
  compares it with the triggering request input. If the directory changed, such
  as from a reused request id, cleanup refuses deletion and leaves the current
  request files for review.
- Failed `mode: "apply"` runs leave the request directory in place so the
  operator can inspect and fix the request.
- Successful `mode: "dry-run"` requests leave the request directory in place
  because no target-branch change was implemented.
- Report files are uploaded as GitHub Actions artifacts, not committed under the
  repo tree. The workflow uses 14-day artifact retention for the apply report.
- If a cleanup-only deletion push is evaluated by the workflow trigger, the
  reusable workflow treats it as a no-op cleanup run instead of failing because
  the deleted `request.json` is no longer present.
