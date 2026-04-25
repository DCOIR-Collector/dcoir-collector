<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-plan-tracker|SKILL.md -->


# DCOIR Plan Tracker

<!-- skill-marker: updated-skill|20260417T064500Z|dcoir-plan-tracker|SKILL.md|R02 -->

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
- airtable-first durable plan state plus local `plan_state.json` cache checks and explicit missing-state warnings for local plan folders
- Airtable `Work Items` lifecycle ownership for plan-tracker-created implementation rows so verified completions auto-close the same rows
- Airtable `Queue Control` ownership when an active plan becomes the live queue branch
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

## Storage model

### Airtable-first durable working state
Use Airtable as the primary durable execution-state surface for live plan continuity.

### Governed repo surfaces
Use this github-backed promoted memory root:
Airtable `Plans`, `Plan Tasks`, `Plan Checkpoints`, and `Session Checkpoints`

### Root files
Maintain:
- Airtable `Plans` / `Plan Tasks`
- Airtable `Tracking Registry`

### Per-plan folder
Each plan lives under:
Airtable plan/task hierarchy records

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
Read `references/local_plan_state_workflow.md` when a local plan cache or `plan_state.json` proof check is in scope.
Read `references/airtable_plan_sync_workflow.md` when Airtable-first plan persistence or recovery is in scope.


## Conditional session-start active-plan recovery
After `dcoir-session-resume`, `dcoir-memory-preflight`, and `dcoir-session-tracker` startup leftover recovery, use this skill when Airtable shows open or active plan state or when the leftover scan indicates unfinished plan work.

Startup recovery workflow:
1. Read `Plans` rows whose `plan_state` is still open enough to matter: `draft`, `approved_to_execute`, `active`, `blocked`, or `paused`. Use silent Airtable reads only.
2. If multiple open plans exist, prefer the most recently updated plan unless the control plane or session-tracker leftover scan points to a different plan explicitly.
3. Read matching `Plan Tasks` rows and the newest relevant `Plan Checkpoints` rows for the candidate plan.
4. Surface the active task, blockers, buffered promotion candidates, and best next move from Airtable-backed plan state before trusting a missing or stale local `plan_state.json` cache.
5. During automatic startup plan recovery, do not use `display_records_for_table`; prefer `search_records` or other non-display Airtable reads.
6. If a visible Airtable view might help, ask the operator first instead of displaying it automatically.
7. If no open Airtable-backed plan state exists, say so plainly and do not force plan recovery unnecessarily.

Read `references/startup_active_plan_recovery_workflow.md` when startup plan recovery details are needed.

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

In addition, preserve these verbose plan-resume fields whenever they are known:
- `resume_state.exact_resume_goal`
- `resume_state.resume_detail`
- `resume_state.why_current_task_matters`
- `resume_state.carry_forward_note`
- `resume_state.flush_trigger`
- `resume_state.pending_flush_items`
- `resume_state.promotion_candidates`
- `resume_state.remain_local_notes`
- `resume_state.validation_counters`

When the active task changes to `in_progress` and `resume_state.exact_resume_goal` is blank, auto-populate it from the strongest available next-action field rather than leaving operator-facing resume state empty.

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
6. At the beginning of each new session that uses a plan, prefer Airtable-backed plan state first and then run `scripts/ensure_plan_state.py` only when a local plan cache is useful for deterministic rendering or local proof.
7. Read `00_index.md`, `05_resume_state.md`, Airtable-backed plan state, and `plan_state.json` when available before resuming.
8. Update Airtable durable state first and refresh markdown or local JSON mirrors as needed whenever the plan changes.
9. During startup recovery or re-anchor-related plan reads, keep Airtable retrieval silent and do not render Airtable UI unless the operator explicitly asked for it or explicitly approved it after being asked.
10. During startup recovery or re-anchor-related plan reads, do not use `display_records_for_table`; prefer `search_records` or other non-display Airtable reads.
11. Before any GitHub write that depends on buffered plan state, run a bounded flush/manicure check that surfaces Airtable-backed durable state, promotion candidates, what should remain local, the next flush trigger, one best next move, and any staged governed updates that should land in the same grouped push.
12. Decide whether tracker state should be written immediately or buffered until the next flush-check trigger, but do not rely on local JSON alone when continuity really matters.
13. When the active plan becomes the live execution branch, update Airtable `Work Items` and the active Airtable `Queue Control` record in the same bounded Airtable pass.
14. Use the github connector directly for safe governed readable-text writes when available.
15. Verify repo state after writes instead of trusting success messages alone.
16. Emit user-visible attention signals only at milestone, blocked, and completion moments.
17. On completion, write `07_closeout.md` and move the plan to `complete` or `archived`.


## Airtable-first durable execution state
This skill now uses Airtable as the primary durable execution-state layer and keeps local `plan_state.json` only as an optional cache or render mirror.

Truth model:
- Airtable is the primary durable execution-state layer
- local `plan_state.json` is an optional transient cache or render mirror
- GitHub remains the authoritative promoted state

Known Airtable targets for this project:
- base id: `appM4KSwnVf3G3OTK`
- `Plans` table id: `tblBcp5FyMIfOm7Xe`
- `Plan Tasks` table id: `tblsATLIDeh6gtcoM`
- `Plan Checkpoints` table id: `tbl6z4Lyai2RABMyw`
- `Tracking Registry` table id: `tblohiMxxVbDUnN77`
- `Queue Control` table id: `tblf13aCslg6rJBah`

Prefer direct table-id writes against the known base instead of querying Airtable for discovery every time. Only fall back to table-name discovery if the direct table-id write fails.

Airtable write posture:
- when a plan is the live execution branch, keep `Queue Control` and queue-ranked `Work Items` aligned to that fact
- upsert `Plans` first on material plan-state changes
- batch `Plan Tasks` writes when task structure or statuses materially change
- create sparse `Plan Checkpoints` rows for blockers, flush reviews, milestones, before-GitHub-write checkpoints, and handoff moments
- use `Tracking Registry` only as metadata after the durable domain record already exists

Use `scripts/render_airtable_plan_bundle.py` to render Airtable-ready payloads from a local plan cache when one exists.
If the local cache is missing, reconstruct the needed Airtable payload from the current plan reasoning and write Airtable first rather than blocking on local file recovery.
Typical modes:
- `plan`
- `tasks`
- `checkpoint`

Read `references/airtable_plan_sync_workflow.md` when Airtable sync details are needed.

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

At the beginning of each new session that uses a local plan cache, prefer Airtable-backed durable state first and run the local `plan_state.json` preflight only when a cache proof or deterministic rendering is useful.

A valid flush/manicure check for this skill must:
- inspect the current plan state and active task
- surface buffered or unsettled plan state
- surface what is safe to flush now
- surface what should remain local or plan-buffered for now
- surface the next flush trigger
- end with one best next move

When the current workflow includes a deferred governance decision with a countdown, preserve the countdown in operator-facing plan state and decrement it only after the qualifying validation event actually happens. Do not silently widen scope just because a countdown reached zero; surface the review trigger instead.

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
- auto-populate `resume_state.exact_resume_goal` from the active task `next_action` or plan `next_recommended_action` when that field is still blank

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
- default the operator-facing plan summary and `05_resume_state.md` to a verbose form when the current branch is materially important
- distinguish observed facts, inferred branch logic, unresolved items, buffered state awaiting flush, and countdown-gated follow-up decisions
- prefer one best next move over broad option lists

## Hard rules
- during automatic startup plan recovery, do not render Airtable UI unless the operator explicitly asked for it or explicitly approved it after being asked
- during automatic startup plan recovery, do not use `display_records_for_table`
- prefer `search_records` or other non-display Airtable reads during automatic startup plan recovery
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
- `references/airtable_plan_sync_workflow.md`
- `references/startup_active_plan_recovery_workflow.md`


## Local plan-state proof rules
When a local plan folder is being used before a GitHub write:
- run `scripts/ensure_plan_state.py` at the beginning of each new session that uses that local plan folder
- do not claim a real local `plan_state.json` cache exists until the preflight proves it
- if the expected local plan cache is missing `plan_state.json`, say that plainly and do not silently treat the missing interval as uninterrupted local-cache continuity
- only initialize a new local plan-state cache automatically when the branch is actually creating a brand-new local plan cache folder
