# DCOIR Helper Skills Routing Note

## Purpose
This note is a governed descriptive routing aid for the current installed or governed `dcoir-*` helper skills used in the AFRICOM_SOC_IR / DCOIR project.

It exists to make helper-skill selection more predictable and stable during project work by documenting:
- the current helper-skill inventory
- the task families each skill is meant to handle
- preferred routing cues and example trigger phrases
- important boundaries and anti-patterns

## Scope and limits
- This note is descriptive guidance, not control-plane authority.
- Project Instructions, then `project_sources/CP-01_DCOIR_Version_Manifest.txt`, then `project_sources/CP-02_DCOIR_Change_Log.txt` remain the authoritative resume order.
- This note does not guarantee automatic skill invocation. It is a routing aid, not an execution engine.
- Final standalone runtime deliverables should remain self-sufficient and should not depend on helper-skill awareness.
- When a helper skill changes materially, this note should be refreshed.
- After a helper-skill create or update, pass the result through `dcoir-skill-regression-auditor` before treating it as ready for broader workflow use.

## Fast routing matrix

| Task family | Preferred helper skill | Typical routing cues | Notes |
| --- | --- | --- | --- |
| Resume current project state | dcoir-session-resume | resume, where are we, what is current, get me back on track | Start here for continuity-focused restarts |
| Need a visible attention banner | dcoir-attention-signaler | important review, milestone, action required, blocked | Use for high-signal chat responses inside DCOIR |
| Verify source authority or stop stale work | dcoir-source-authority-auditor | verify authority, is this current, stale source risk | Use when control-plane drift is a risk |
| GitHub repo write or grouped update work | dcoir-memory-preflight | update GitHub, grouped repo edit, control-plane change | Consult task memory before execution and after blocker recovery when the lesson looks reusable |
| What else must change after a repo update | dcoir-change-impact-analyzer | downstream impact, what else must change, refresh set | Use after a proposed or completed change |
| Default branch or decision handling | dcoir-decision-policy | what should we do, choose path, operator preference branch | Use when several reasonable paths exist |
| Collector QA, repair, or harness issues | dcoir-collector-qa | collector error, harness failure, repair collector | Collector maintenance aid |
| Validation plan or test sequencing | dcoir-validation-orchestrator | what should we test, validation plan, test order | Default for explicit validation planning |
| Deep regression for helper skills | dcoir-skill-regression-auditor | regression plan for skills, fixtures, output checks | Use before or after skill changes |
| Session-local scratch, follow-ups, and handoff | dcoir-session-tracker | do not forget, what is left, handoff artifact | Session-local continuity aid |
| Deep task decomposition and resume state | dcoir-plan-tracker | plan work, track tasks, resume plan, blocker capture | Durable execution-plan helper |
| Root or folder README maintenance | dcoir-readme-maintainer | improve README, folder README, navigation links | Focused README upkeep, not broad documentation generation |
| Knowledge and supporting docs maintenance | dcoir-knowledge-doc-maintainer | regenerate docs, maintain knowledge docs, inventory doc changes | Knowledge-doc generation and refresh |
| Repo-layout zip or bootstrap bundle creation | dcoir-repo-packager | package repo, build bootstrap bundle | Packaging execution helper |

## Current helper-skill inventory
- dcoir-attention-signaler
- dcoir-change-impact-analyzer
- dcoir-collector-qa
- dcoir-decision-policy
- dcoir-knowledge-doc-maintainer
- dcoir-large-file-intake-manager
- dcoir-live-test-remediation-planner
- dcoir-memory-preflight
- dcoir-operator-workflow-hardener
- dcoir-plan-tracker
- dcoir-prompt-pack-assembler
- dcoir-promotion-readiness-reviewer
- dcoir-readme-maintainer
- dcoir-release-scope-builder
- dcoir-repo-packager
- dcoir-session-resume
- dcoir-session-tracker
- dcoir-skill-regression-auditor
- dcoir-source-authority-auditor
- dcoir-structural-rename-coordinator
- dcoir-triage-to-collector-escalation-designer
- dcoir-validation-orchestrator

## Inventory gap note
- `dcoir-trigger-test` was referenced by older routing content but is not present as a current governed skill source in the repo and should not be treated as part of the current governed helper-skill set unless it is deliberately restored.

## Maintenance rule
When a `dcoir-*` helper skill is added, removed, renamed, materially repurposed, or retired, update this note and nearby routing references in `knowledge/README.md` and `dcoir_skills/README.md`.
