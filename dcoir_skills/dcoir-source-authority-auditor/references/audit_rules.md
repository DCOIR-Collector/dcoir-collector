# Audit Rules

## clear_to_proceed
Use when all of these are true:
- the control plane resolves
- current manifest-listed files needed for authority are present
- the task does not rely on historical or missing authority
- the in-scope active enforcement surfaces share the same `current_state_id`
- the `CP-01` / `CP-02` version pair aligns

## proceed_bounded
Use when the control plane is clear but the reviewed evidence or workspace is partial and no contradiction is yet proven.

Typical cases:
- the workspace is intentionally partial and one or more non-control active surfaces are unavailable
- the active enforcement set cannot be fully checked, but the available surfaces do not contradict each other

The task may continue only with bounded claims and an explicit note about which surfaces were unavailable.

## hard_stop_conflict
Use when any of these are true:
- manifest missing
- change log missing
- current file listed in the manifest is missing from the workspace
- task depends on a non-current file as authority
- `CP-01` / `CP-02` version mismatch
- `current_state_id` mismatch across the in-scope active enforcement surfaces
- a stamped active surface is present but missing its required `current_state_id`
- manifest/workspace drift would change the authoritative basis
