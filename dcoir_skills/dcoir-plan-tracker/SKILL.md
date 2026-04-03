---
name: dcoir-plan-tracker
description: plan, track, resume, and document multi-step africom_soc_ir / dcoir work with durable github-backed state, hierarchical task decomposition, blocker capture, closed-loop blocker recovery, session-local write buffering, decision-aware execution, and operator-visible milestone signaling. use when chatgpt needs to break a dcoir task into tasks, subtasks, and subsubtasks; automatically create or update governed tracker files in github; resume paused work; record blockers and mitigations; classify reusable lessons after blocker recovery; stage promotion-ready candidates; consult decision defaults before pausing for operator input; or export a clean handoff for follow-on execution.
---

# DCOIR Plan Tracker

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.

Before proceeding:
1. Re-anchor to Project Instructions.
2. Read the current `CP-01` manifest.
3. Read the current `CP-02` change log.
4. Confirm the task is inside the current governed DCOIR working line.

If authority is unclear or the control plane conflicts, stop and report the exact conflict.

## Purpose
Use this skill to create, maintain, and resume durable execution plans for DCOIR work.

This skill owns:
- hierarchical task decomposition
- execution-state tracking
- resume breadcrumbs
- blocker and mitigation capture
- blocker-recovery classification
- promotion-candidate staging
- plan-level and task-level status updates
- session-local buffer-state review
- github-backed tracker file creation and updates
- concise user-visible milestone signaling through `dcoir-attention-signaler`

This skill does not replace:
- control-plane authority
- promotion readiness judgment
- release-scope classification
- canonical task-memory authority

## Mandatory companion-skill behavior

### 1. decision control
Use `dcoir-decision-policy` as the default branch-control layer whenever multiple reasonable paths exist.

### 2. task-memory preflight
Use `dcoir-memory-preflight` before execution when the task family includes:
- github readable-text create, update, overwrite, grouped edit, or delete work
- multi-file repo changes
- control-plane changes
- structural repo changes
- packaging or bundle work
- skill maintenance, repair, or regression work
- repeated high-friction workflows with likely canonical memory

Use `dcoir-memory-preflight` again after blocker recovery when the successful mitigation could become a reusable lesson.

### 3. attention signaling
Use `dcoir-attention-signaler` for user-visible progress only at:
- major milestones
- blocked states
- task or plan completions

Do not emit banners for every small state change.

## Durable storage model

### Root path
Use this github-backed durable memory root:
`dcoir_skill_memory/dcoir-plan-tracker/`

### Root files
Maintain:
- `dcoir_skill_memory/dcoir-plan-tracker/plan_tracker_memory.md`
- `dcoir_skill_memory/dcoir-plan-tracker/plan_tracker_registry.json`

### Per-plan folder
Each plan lives under:
`dcoir_skill_memory/dcoir-plan-tracker/plans/PLAN-YYYYMMDD-short-slug/`

### Locked plan files
Create and maintain these files for every plan:
- `00_index.md`
- `01_scope_and_constraints.md`
- `02_execution_table.md`
- `03_decisions_and_rationale.md`
- `04_call_log.md`
- `05_resume_state.md`
- `06_artifacts_and_outputs.md`
- `07_closeout.md`
- `plan_state.json`

Read `references/file_layout.md` when creating or validating plan surfaces.

## Locked id and naming rules

### Plan id
Format: `PLAN-YYYYMMDD-short-slug`

### Task ids
Use:
- top-level task: `T1`, `T2`, `T3`
- subtask: `T1.1`, `T1.2`
- subsubtask: `T1.1.1`, `T1.1.2`

There may be multiple active plans across the workspace.
There must be only one active task per plan.

## Plan lifecycle
Allowed plan states:
- `draft`
- `approved_to_execute`
- `active`
- `blocked`
- `paused`
- `complete`
- `archived`

## Task status model
Allowed task statuses:
- `todo`
- `in_progress`
- `blocked`
- `done`
- `skipped`

Every change to `in_progress`, `blocked`, or `done` must update:
- task `last_update`
- `00_index.md`
- `05_resume_state.md`
- `plan_state.json`

## Execution table row schema
Use this stable row model in `02_execution_table.md` and mirror it in `plan_state.json`:
- `id`
- `parent_id`
- `level`
- `title`
- `status`
- `owner`
- `why_it_matters`
- `next_action`
- `expected_output`
- `validation_gate`
- `touched_paths`
- `blocking_dependency`
- `last_update`

When buffering or blocker recovery is active, also preserve the relevant state in `05_resume_state.md`, `03_decisions_and_rationale.md`, and `plan_state.json`.

## Command surface
Read `references/command_surface.md` when the task requires a specific tracker action.

Supported commands include:
- `create_plan`
- `close_plan`
- `archive_plan`
- `add_task`
- `add_subtask`
- `split_task`
- `mark_todo`
- `mark_in_progress`
- `mark_blocked`
- `mark_done`
- `mark_skipped`
- `set_active_task`
- `resume_plan`
- `pause_plan`
- `update_resume_state`
- `record_blocker`
- `clear_blocker`
- `record_decision`
- `record_assumption`
- `record_constraint`
- `record_stop_condition`
- `record_call`
- `record_validation`
- `record_touched_paths`
- `record_output_artifact`
- `show_plan_summary`
- `show_execution_table`
- `show_active_task`
- `show_blockers`
- `export_handoff`

## Core workflow
1. Re-anchor to Project Instructions, `CP-01`, and `CP-02`.
2. Consult `dcoir-decision-policy` when branch choice exists.
3. Consult `dcoir-memory-preflight` when the task family requires canonical memory preflight.
4. Create or open the plan folder.
5. Update `plan_tracker_registry.json` and `plan_tracker_memory.md`.
6. Read `00_index.md`, `05_resume_state.md`, and `plan_state.json` first when resuming.
7. Update markdown and json together whenever the plan changes.
8. Decide whether tracker state should be written immediately or buffered until the next flush-check trigger.
9. Use the github connector directly for safe governed readable-text writes when available.
10. Verify repo state after writes instead of trusting success messages alone.
11. Emit user-visible attention signals only at milestone, blocked, and completion moments.
12. On completion, write `07_closeout.md` and move the plan to `complete` or `archived`.

## GitHub write workflow
Read `references/github_write_workflow.md` when tracker files must be created or updated in GitHub.

Default rules:
- use `GH-PROC-007` logic before high-friction github-family work
- prefer one bounded multi-file transaction when related tracker files change together
- apply `GH-PROC-005` style readback verification after any write
- when a simple new-file create is enough, use the smallest safe lane
- if connector limits prevent safe completion, say so plainly and reduce operator burden to the smallest bounded manual action

## Session-local write-buffer behavior
This skill may accumulate session-local tracker state before GitHub flush time.

Buffer when:
- several related tracker files should land together
- the grouped-write posture is safer than repeated small writes
- blocker-recovery notes are still settling and should not be prematurely promoted
- the current task is moving quickly and the next flush-check trigger is near

Preferred flush-check trigger points:
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift

When buffering is active, `05_resume_state.md` should make the pending flush state obvious.

## Automatic behavior rules

### On `create_plan`
Automatically:
- create the plan folder
- create all locked markdown files
- create `plan_state.json`
- create a first top-level summary in `00_index.md`
- register the plan in `plan_tracker_registry.json`
- add a short entry to `plan_tracker_memory.md`

Use `scripts/init_plan.py` to generate consistent starter contents whenever deterministic scaffolding is useful.

### On `mark_in_progress`
Automatically:
- clear any prior active task in that same plan
- set new `active_task_id` and `active_task_title`
- update `00_index.md`
- update `02_execution_table.md`
- update `05_resume_state.md`
- update `plan_state.json`

Emit an attention signal only if this transition is a major milestone.

### On `mark_done`
Automatically:
- set task status to `done`
- record completion note in `last_update`
- clear active pointer if needed
- suggest the next eligible task
- update markdown and json together

Emit an attention signal when the completed task is milestone-worthy or when a plan completes.

### On `mark_blocked`
Automatically:
- set task status to `blocked`
- record blocker details
- record what was attempted
- record the failure signature when recognizable
- update `05_resume_state.md`
- update `03_decisions_and_rationale.md` when the blocker changed branch choice
- update `plan_state.json`

Always emit a blocked-state attention signal.

### On `clear_blocker`
Automatically:
- record the successful mitigation
- invoke `dcoir-memory-preflight` again when the resolved lesson could be reusable
- classify the result as one-off only or as a reusable promotion candidate
- stage the promotion candidate in the plan rather than silently writing to canonical memory
- update `05_resume_state.md`, `03_decisions_and_rationale.md`, and `plan_state.json`
- surface the next flush-check trigger if buffered state now exists

Use `scripts/update_plan_state.py` when a deterministic local transition render will reduce drift between markdown and json.

## Blocker learning and mitigation capture
Every meaningful blocker or failed attempt must be captured in the active plan.

Capture:
- what happened
- where it happened
- failure signature
- attempted fixes
- successful mitigation if found
- whether it appears reusable across similar tasks or technologies

Default rule:
- store the immediate blocker and mitigation in the current plan
- if the lesson appears reusable, create a promotion-ready candidate for canonical memory, governed docs, or another skill update
- do not silently persist reusable lessons into canonical memory without the correct workflow and approval posture

Read `references/blocker_promotion_workflow.md` when deciding whether a blocker lesson should remain local to the plan or be promoted.

## Relationship to dcoir-memory-preflight
`dcoir-memory-preflight` should play a role before high-friction execution and after blocker resolution.

Use it in two ways:
1. before execution to avoid known friction
2. after a blocker is overcome to evaluate whether the mitigation should be promoted into canonical memory, docs, or a helper-skill update

Do not let this skill silently overwrite canonical task memory.
Surface a bounded promotion candidate instead.

## Reporting style
When using this skill:
- keep the durable files continuity-rich
- keep user-visible chat updates concise and milestone-oriented
- preserve enough rationale that the next session can resume cleanly
- distinguish observed facts, inferred branch logic, unresolved items, and buffered state awaiting flush
- prefer one best next move over broad option lists

## Hard rules
- do not treat plan state as control-plane authority
- do not skip decision-policy when branch choice is unresolved
- do not skip memory-preflight for high-friction github-family work
- do not skip the post-blocker re-check when a recovered lesson appears reusable
- do not emit attention banners for every small task flip
- do not leave markdown and json out of sync
- do not silently promote blocker lessons into canonical memory
- do not allow more than one active task per plan
- do not rename active plan ids casually after work starts

## References
Read when needed:
- `references/file_layout.md`
- `references/command_surface.md`
- `references/github_write_workflow.md`
- `references/blocker_promotion_workflow.md`
- `references/session_buffer_workflow.md`
