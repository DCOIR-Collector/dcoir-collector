# Startup active-plan recovery workflow

Use this workflow during DCOIR re-anchor or resume when plan state matters.

## Authority order
1. Project Instructions.
2. CP-00 as pointer only when present.
3. Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`.
4. `Session Checkpoints` for the latest resume continuity.
5. `Queue Control` for active branch and resume rule.
6. `Work Items` for executable task rows.
7. Active `Plans` for parent scope and next action.
8. `Operator Preferences`, `Admin Registry`, helper-memory tables, and SKILLROUTE rows when relevant.

## Recovery steps
1. Read the latest active/current checkpoint matching the requested resume branch.
2. Read Queue Control to confirm the active branch and supersession notes.
3. Read active Plans and Work Items that match the checkpoint or queue branch.
4. Prefer Work Items plus Plans for execution hierarchy; do not require a dedicated task/checkpoint table unless live schema readback proves it exists.
5. Report the exact next move and any authority drift before executing changes.

## Stop conditions
- Stop on conflict between Project Instructions, CP-00, Governance Control Plane, and live Airtable state.
- Treat GitHub CP/current-state conflicts as promoted-history drift unless the current task is source-authority comparison.
- Do not infer missing queue rows from old local JSON or GitHub todo files.
