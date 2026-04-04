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
- `ensure_plan_state`
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

### `ensure_plan_state`
- run this at the beginning of each new session that uses a local plan folder
- prove whether `plan_state.json` is already present and inspectable
- initialize a brand-new local plan folder only when the branch is intentionally starting one and the minimum metadata is available
- do not silently pretend continuity remained file-backed if an expected local `plan_state.json` file is missing

### `resume_plan`
Read in this order:
1. run `ensure_plan_state` when a local plan folder is in scope
2. `00_index.md`
3. `05_resume_state.md`
4. `plan_state.json`
5. `02_execution_table.md`
6. other files only when needed

## Ask threshold
Do not ask the operator for routine branch choices if `dcoir-decision-policy` can resolve the path safely.
Ask only when authority, safety, released file set, or a hard stop requires it.
