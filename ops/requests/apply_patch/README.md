# Ops Apply Patch Requests

Stage exactly one request directory per apply operation:

```text
ops/requests/apply_patch/<request_id>/request.json
ops/requests/apply_patch/<request_id>/change.patch
```

`<request_id>` may contain only letters, numbers, dots, underscores, and hyphens.

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
