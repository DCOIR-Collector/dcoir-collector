# DCOIR Plan Tracker Command Surface

## Supported commands

### Plan creation and closure
- `create_plan`
- `clone_plan`
- `close_plan`
- `archive_plan`

### Structure management
- `add_task`
- `add_subtask`
- `add_subsubtask`
- `split_task`
- `reorder_task`
- `remove_task`
- `merge_tasks`

### State transitions
- `mark_todo`
- `mark_in_progress`
- `mark_blocked`
- `mark_done`
- `mark_skipped`
- `set_active_task`

### Resume and continuity
- `resume_plan`
- `pause_plan`
- `update_resume_state`
- `record_blocker`
- `clear_blocker`

### Context and rationale
- `record_decision`
- `record_assumption`
- `record_constraint`
- `record_stop_condition`

### Execution evidence
- `record_call`
- `record_validation`
- `record_touched_paths`
- `record_output_artifact`

### Views and exports
- `show_plan_summary`
- `show_execution_table`
- `show_active_task`
- `show_blockers`
- `export_handoff`

## Default behavior notes
### `create_plan`
Create the full file set, register the plan, and set the initial plan status.

### `mark_in_progress`
- clear the previous active task in that plan
- set the new active task
- update index, execution table, resume state, and JSON
- emit milestone signaling only when materially useful

### `mark_done`
- mark the task done
- write last update note
- clear active pointer if needed
- suggest the next eligible task

### `mark_blocked`
- capture the blocker
- capture what was attempted
- capture the mitigation if the blocker is later resolved
- emit blocked-state signaling

### `resume_plan`
Read in this order:
1. `00_index.md`
2. `05_resume_state.md`
3. `plan_state.json`
4. `02_execution_table.md`
5. other files only when needed

## Ask threshold
Do not ask the operator for routine branch choices if `dcoir-decision-policy` can resolve the path safely.
Ask only when authority, safety, released file set, or a hard stop requires it.
