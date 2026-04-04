# DCOIR governed skill source root

Purpose
- This folder is the governed GitHub readable source root for DCOIR helper-skill source intentionally stored in the repository.

## Root rules
- Per-skill source folders live under `dcoir_skills/<skill-name>/`.
- Preserve the readable package layout for each skill.
- Exclude runtime residue such as `__pycache__/` and temporary outputs.
- Treat the source in this folder as governed readable skill source, not as runtime cache or session memory.

## What a skill folder normally contains
Most skill folders use the readable package layout below:
- `SKILL.md` — core skill contract and routing description
- `agents/openai.yaml` — UI metadata
- `assets/` — icons or other bundled output assets
- `references/` — supporting guidance or static reference material
- `scripts/` — deterministic helper scripts when the workflow benefits from them

## Current governed skill families

For the most current routing inventory and common request mapping, use:
- `knowledge/DCOIR_Helper_Skills_Routing_Note.md`

This README is the local guide to the governed skill-source root. The routing note is the project-side descriptive inventory for the current helper-skill set.

### Continuity and routing
- `dcoir-session-resume` — resume current governed project state from the control plane.
- `dcoir-attention-signaler` — emit conspicuous milestone, review, blocked, action-required, or completion banners.
- `dcoir-source-authority-auditor` — verify current source authority and stop stale or contradictory work.
- `dcoir-decision-policy` — apply the operator’s default branch and delivery decisions when several reasonable paths exist.

### GitHub and repo-change workflow
- `dcoir-memory-preflight` — consult canonical GitHub task memory before high-friction execution and after blocker recovery.
- `dcoir-change-impact-analyzer` — identify downstream refresh sets and related affected files after a change.
- `dcoir-structural-rename-coordinator` — coordinate renames, re-homing, and naming-model changes.
- `dcoir-release-scope-builder` — decide packaging or release class.
- `dcoir-promotion-readiness-reviewer` — judge ready, ready-with-conditions, or not-ready after changed set and packaging posture are known.
- `dcoir-repo-packager` — build strict repo-layout zips and GitHub-primary bootstrap bundles.

### Validation, QA, and remediation
- `dcoir-collector-qa` — validate, troubleshoot, repair, and maintain collector/harness files.
- `dcoir-validation-orchestrator` — build validation plans and test gates.
- `dcoir-skill-regression-auditor` — plan and audit deep regression for helper skills.
- `dcoir-live-test-remediation-planner` — turn live-test findings into ranked remediation work.

### Operator workflow and intake
- `dcoir-operator-workflow-hardener` — normalize operator-facing execution guidance and interpret collector output.
- `dcoir-large-file-intake-manager` — stage intake when evidence files are too large or incomplete.
- `dcoir-session-tracker` — keep session-local notes, unfinished items, exportable handoff artifacts, and continuity buffer state.
- `dcoir-plan-tracker` — maintain governed execution plans, blockers, resume state, and milestone-visible task flow.

### Documentation, prompt, and design work
- `dcoir-readme-maintainer` — maintain root and folder README surfaces and README navigation.
- `dcoir-prompt-pack-assembler` — assemble one combined analyst-facing master prompt from the current validated modular prompt-pack source set.
- `dcoir-knowledge-doc-maintainer` — maintain and regenerate supporting knowledge docs from current authoritative sources.
- `dcoir-triage-to-collector-escalation-designer` — design or revise the alert-triage-to-DCOIR bridge.

## Maintenance note
- When a governed helper skill is added, removed, renamed, materially repurposed, or retired, refresh this README and the routing note together.
- When helper-skill workflow rules change materially, refresh nearby README and routing references so they stay aligned to the approved current process.
