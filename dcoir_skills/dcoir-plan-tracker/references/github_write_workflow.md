# DCOIR Plan Tracker GitHub Write Workflow

## Purpose
This reference maps tracker-file updates to the canonical GitHub task-memory posture.

## Read-first posture
Before high-friction GitHub-family work:
1. re-anchor to Project Instructions, `CP-01`, and `CP-02`
2. use `dcoir-memory-preflight`
3. consult the smallest relevant canonical records

## Key canonical records
- `GH-PROC-007` for memory-preflight routing
- `GH-PROC-006` for grouped multi-file transactions
- `GH-PROC-005` for post-write verification

## Default lane selection
### When creating a new plan folder and its initial files
- prefer the smallest safe create lane when the operation is just new-file creation
- if the root registry and root memory file must also be updated in the same step, treat the full change set as grouped work

### When updating multiple related tracker files
Use grouped work when these belong together, for example:
- `00_index.md`
- `02_execution_table.md`
- `05_resume_state.md`
- `plan_state.json`
- `plan_tracker_registry.json`
- `plan_tracker_memory.md`

In that case, prefer one bounded multi-file transaction instead of one-file-at-a-time updates.

## Verification rules
After any tracker write:
1. fetch each changed path from the live repo state
2. compare fetched content to intended content
3. if the update changed root tracker memory or registry, verify both
4. never stop at apparent write success alone

## Anti-patterns
- do not trust connector success without readback
- do not leave markdown and JSON out of sync
- do not perform one-file-at-a-time writes when a grouped state change belongs together
- do not treat tracker memory as control-plane authority
