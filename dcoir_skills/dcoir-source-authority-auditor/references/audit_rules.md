# Audit Rules

## clear_to_proceed
Use when the control plane resolves, current files exist, and the task does not rely on historical or missing authority.

## proceed_bounded
Use when the control plane is clear but the reviewed evidence or workspace is partial. The task may continue only with bounded claims.

## hard_stop_conflict
Use when any of these are true:
- manifest missing
- change log missing
- current file listed in manifest is missing from workspace
- task depends on non-current file as authority
- manifest/workspace drift would change the authoritative basis
