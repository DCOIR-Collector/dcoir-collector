# DCOIR Plan Tracker File Layout

## Purpose
This reference defines the fixed durable layout for `dcoir-plan-tracker` plans stored in GitHub.

## Root layout
- `dcoir_skill_memory/dcoir-plan-tracker/plan_tracker_memory.md`
- `dcoir_skill_memory/dcoir-plan-tracker/plan_tracker_registry.json`
- `dcoir_skill_memory/dcoir-plan-tracker/plans/PLAN-YYYYMMDD-short-slug/`

## Per-plan required files
- `00_index.md`
  - plan id, title, objective, plan status, active task pointer, created date, updated date, next recommended action
- `01_scope_and_constraints.md`
  - authority basis, assumptions, exclusions, constraints, stop conditions
- `02_execution_table.md`
  - hierarchical task table and current status row set
- `03_decisions_and_rationale.md`
  - branch decisions and why they were taken
- `04_call_log.md`
  - load-bearing tool calls, repo actions, validation steps, and noteworthy outputs
- `05_resume_state.md`
  - exact next resume breadcrumb, blockers, pending approvals, next action
- `06_artifacts_and_outputs.md`
  - changed files, produced bundles, related PRs, related docs, related outputs
- `07_closeout.md`
  - completion summary, follow-on tasks, unresolved items, promotion notes
- `plan_state.json`
  - machine-readable mirror for the current plan state

## Naming rules
### Plan id
`PLAN-YYYYMMDD-short-slug`

### Task ids
- top-level: `T1`, `T2`, `T3`
- subtask: `T1.1`, `T1.2`
- subsubtask: `T1.1.1`, `T1.1.2`

## Update rules
- Keep markdown and JSON in sync.
- Keep only one active task per plan.
- Update `00_index.md`, `05_resume_state.md`, and `plan_state.json` whenever the active task changes.
- Update `07_closeout.md` only when the plan is ready for completion or archival.

## Registry expectations
`plan_tracker_registry.json` should stay compact and index-friendly.
Suggested per-plan fields:
- `plan_id`
- `title`
- `status`
- `created_at`
- `updated_at`
- `active_task_id`
- `active_task_title`
- `plan_path`

## Human-readable root memory expectations
`plan_tracker_memory.md` is a continuity surface, not the authority source.
Keep short entries per plan:
- plan id
- one-line objective
- current status
- active task
- last meaningful update
- next recommended action
