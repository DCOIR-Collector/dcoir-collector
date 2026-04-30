# Airtable plan sync workflow

Use this workflow when dcoir-plan-tracker needs to render or prepare Airtable-ready plan state. Airtable is the live execution authority; local JSON is only a render buffer.

## Current target tables
- `Plans` (`tblBcp5FyMIfOm7Xe`) holds multi-step parent scope, active task context, resume detail, and next action.
- `Work Items` (`tblgsQAVWvh8K7gIR`) holds executable task rows. Use it instead of retired `Plan Tasks` unless live schema readback proves a dedicated task table exists for the current job.
- `Session Checkpoints` (`tblTe75HKZOJaPDGn`) holds resume/checkpoint continuity. Use it instead of retired `Plan Checkpoints` unless live schema readback proves otherwise.
- `Queue Control` (`tblf13aCslg6rJBah`) is updated only after executable Work Item or Plan state exists.
- `Admin Registry` may carry skill-state or schema-governance housekeeping. It is not a live task queue.

## Sync order
1. Read live schema before writing or migrating records.
2. Render or upsert the `Plans` row first when parent scope changed.
3. Render task-level rows to `Work Items`, preserving `canonical_parent_plan_id` when present.
4. Render meaningful checkpoints to `Session Checkpoints`.
5. Update `Queue Control` only after the Plan/Work Item rows exist and the operator-authorized queue branch is clear.
6. Record material promotion, migration, retirement, or closeout in `DCOIR Lifecycle Ledger` when appropriate.

## Safety rules
- Do not require retired tables by name during normal startup or plan recovery.
- Do not write directly from stale hard-coded table ids when live schema readback disagrees.
- Do not treat GitHub CP/todo files as live queue authority.
- Keep generated Airtable payloads secret-safe and operator-readable.
