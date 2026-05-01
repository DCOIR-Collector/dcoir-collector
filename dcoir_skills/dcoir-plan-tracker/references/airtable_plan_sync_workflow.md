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

## Parent-plan sync gate

Run this gate before any closeout, pause, resume, active-task switch, checkpoint, or Work Item status change.

1. Identify the Work Item row and read `canonical_parent_plan_id`.
2. If a parent plan id exists, find the matching `Plans` row by `plan_id`.
3. Compare parent plan fields against the actual task state:
   - `plan_state`
   - `active_task_id`
   - `active_task_title`
   - `exact_resume_goal`
   - `next_recommended_action`
   - `last_updated_text`
4. If the Work Item is now active, set the parent plan to active and point the active task fields at that Work Item.
5. If the Work Item is complete, move the parent plan to the next unfinished task, pause it with a clear next action, or mark it complete if no work remains.
6. Create or update checkpoint/evidence only after the parent plan row and Work Item row agree.

Never let a Session Checkpoint become the only source of truth for plan progress when a `Plans` row exists.

## Drift repair rule

If Airtable says the plan active task is older than the newest work/checkpoint/evidence, treat that as plan drift. Repair the `Plans` row before giving a final closeout or resume answer. If the correct repair is not clear, state the mismatch plainly and ask the operator to choose the next active task.

