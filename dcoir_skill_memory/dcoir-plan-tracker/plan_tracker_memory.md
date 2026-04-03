# DCOIR Plan Tracker Memory

Purpose
- Human-readable registry and continuity surface for active and archived DCOIR execution plans.
- GitHub-backed companion surface for the `dcoir-plan-tracker` helper skill.

Current active plans
- `PLAN-20260403-dcoir-readme-maintainer-skill-build`
  - title: build `dcoir-readme-maintainer` skill
  - state: active
  - active task: `T1`
  - created: 2026-04-03
  - why it matters: README maintenance is tracked as a recurring enough workflow that it may deserve a dedicated helper skill instead of broader documentation maintenance.

Rules
- GitHub is the durable readable source of truth for tracker state.
- `plan_tracker_registry.json` is the machine-readable registry.
- Per-plan markdown plus `plan_state.json` hold the authoritative execution details for each plan.
- Only one active task may exist per plan.
- Multiple plans may be active across the workspace.
