# Audit Rules

## clear_to_proceed
Use when all of these are true:
- the control plane resolves
- current manifest-listed files needed for authority are present
- the task does not rely on historical or missing authority
- the in-scope active enforcement surfaces share the same `current_state_id`
- the Airtable startup/governance authority is present; the `CP-01` / `CP-02` version pair aligns only when those GitHub files are explicitly in repository-source scope

## proceed_bounded
Use when the control plane is clear but the reviewed evidence or workspace is partial and no contradiction is yet proven.

Typical cases:
- the workspace is intentionally partial and one or more non-control active surfaces are unavailable
- one or more supporting assets are missing from the workspace, but the current task does not depend on them for authority
- the active enforcement set cannot be fully checked, but the available surfaces do not contradict each other

The task may continue only with bounded claims and an explicit note about which surfaces or supporting assets were unavailable.

## hard_stop_conflict
Use when any of these are true:
- manifest missing
- task-required authority surface missing; for startup/admin branches, missing GitHub change log is not a blocker when Airtable replacement authority is present
- current authoritative readable source listed in the manifest is missing from the workspace
- task explicitly depends on a missing supporting asset as though it were authoritative current-state basis
- task depends on a non-current file as authority
- `CP-01` / `CP-02` version mismatch only when those files are in source-task scope; otherwise report promoted-history drift and use Airtable live authority
- `current_state_id` mismatch across the in-scope active enforcement surfaces
- a stamped active surface is present but missing its required `current_state_id`
- manifest/workspace drift would change the authoritative basis
