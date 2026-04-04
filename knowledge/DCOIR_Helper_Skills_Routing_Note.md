# DCOIR Helper Skills Routing Note

## Purpose
This note is a governed descriptive routing aid for the current installed dcoir-* helper skills used in the AFRICOM_SOC_IR / DCOIR project.

It exists to make helper-skill selection more predictable and stable during project work by documenting:
- the current helper-skill inventory
- the task families each skill is meant to handle
- preferred routing cues and example trigger phrases
- important boundaries and anti-patterns

## Scope and limits
- This note is descriptive guidance, not control-plane authority.
- Project Instructions, then project_sources/CP-01_DCOIR_Version_Manifest.txt, then project_sources/CP-02_DCOIR_Change_Log.txt remain the authoritative resume order.
- This note does not guarantee automatic skill invocation. It is a routing aid, not an execution engine.
- Final standalone runtime deliverables should remain self-sufficient and should not depend on helper-skill awareness.
- When a helper skill changes materially, this note should be refreshed.
- After a helper-skill create or update, pass the result through dcoir-skill-regression-auditor before treating it as ready for broader workflow use.

## High-level routing rules
1. Confirm the task is actually inside the AFRICOM_SOC_IR / DCOIR project context.
2. Re-anchor to Project Instructions, then CP-01, then CP-02.
3. Prefer the most specific matching dcoir-* skill over broader helpers.
4. Use helper skills for project-side authoring, QA, packaging, maintenance, routing, and workflow support.
5. Use dcoir-memory-preflight before high-friction GitHub-family execution work and again after blocker recovery when the lesson may be reusable.
6. If no helper skill cleanly fits, proceed directly with a bounded explanation rather than forcing a bad match.

## Fast routing matrix

| Task family | Preferred helper skill | Typical routing cues | Notes |
| --- | --- | --- | --- |
| Resume current project state | dcoir-session-resume | resume, where are we, what is current, get me back on track | Start here for continuity-focused restarts |
| Need a visible attention banner | dcoir-attention-signaler | important review, milestone, action required, blocked | Use for high-signal chat responses inside DCOIR |
| Verify source authority or stop stale work | dcoir-source-authority-auditor | verify authority, is this current, stale source risk, should we stop | Use when control-plane drift is a risk |
| GitHub repo write or grouped update work | dcoir-memory-preflight | update GitHub, delete files, grouped repo edit, control-plane change | Consult task memory before execution and after blocker recovery when the lesson looks reusable |
| What else must change after a repo update | dcoir-change-impact-analyzer | downstream impact, what else must change, refresh set | Use after a proposed or completed change |
| Default branch or decision handling | dcoir-decision-policy | what should we do, choose path, operator preference branch | Use when several reasonable paths exist |
| Collector QA, repair, or harness issues | dcoir-collector-qa | collector error, harness failure, repair collector, QA report | Project-gated collector maintenance aid |
| Validation plan or test sequencing | dcoir-validation-orchestrator | what should we test, validation plan, test order, evidence gates | Default for explicit validation planning |
| Deep regression for helper skills | dcoir-skill-regression-auditor | regression plan for skills, fixtures, output checks | Use before or after skill changes |
| Remediation plan after live-test findings | dcoir-live-test-remediation-planner | what to fix first, ranked remediation, live-test findings | For ordered post-test repair planning |
| Operator-facing endpoint or local workflow guidance | dcoir-operator-workflow-hardener | exact next step, endpoint step, cleanup handling, interpret collector output | Use for operator runtime instructions |
| Large or partial evidence intake | dcoir-large-file-intake-manager | files too big, upload limits, staged intake, targeted excerpts | Use when evidence cannot be handled in one pass |
| Session-local scratch, follow-ups, and handoff | dcoir-session-tracker | don't forget, what is left, session notes, handoff artifact | Session-local continuity aid |
| Plan decomposition, blocker capture, and resume-state persistence | dcoir-plan-tracker | break this into tasks, plan, blocker, resume state, what is the active task | Use for durable governed plan work |
| Root or folder README maintenance | dcoir-readme-maintainer | improve README, folder README, navigation links, stale README references | Use for focused README upkeep rather than broad documentation generation |
| Prompt-pack assembly into one combined prompt | dcoir-prompt-pack-assembler | assemble master prompt, rebuild combined prompt, prompt-pack refresh | Use only after authority is settled |
| Knowledge and supporting docs maintenance | dcoir-knowledge-doc-maintainer | regenerate docs, maintain knowledge docs, inventory doc changes | For knowledge-doc generation and refresh |
| Triage-to-collector bridge design | dcoir-triage-to-collector-escalation-designer | alert triage handoff, routing language, escalation triggers | Use for Elastic-style bridge design |
| Structural renames or re-homing | dcoir-structural-rename-coordinator | rename file, rename class, move path, re-home assets | Use before partial rename work |
| Packaging or release-class choice | dcoir-release-scope-builder | local only or bundle, targeted update or full refresh, packaging class | Picks packaging class, not readiness |
| Readiness judgment before treating work as live | dcoir-promotion-readiness-reviewer | is this ready, ready with conditions, blocking gaps | Use after changed set and packaging posture are known |
| Repo-layout zip or bootstrap bundle creation | dcoir-repo-packager | package repo, build bootstrap bundle, strict repo-layout zip | Packaging execution helper |

## Anti-patterns
- Do not treat this note as a guarantee that a helper skill will always auto-invoke.
- Do not override Project Instructions, CP-01, or CP-02 with this note.
- Do not use a broad helper when a more specific project helper clearly matches.
- Do not mention helper skills or hidden workflow machinery inside final standalone runtime deliverables.
- Do not keep this note stale after the installed helper-skill set changes materially.

## Maintenance rule
When a dcoir-* helper skill is added, removed, renamed, materially repurposed, or retired, update this note and any nearby routing references in knowledge/README.md or related project guidance.
When helper-skill workflow rules change materially, refresh this note so routing remains aligned to the current approved process.

## Related files
- knowledge/README.md
- dcoir_skills/README.md
- project_sources/CP-01_DCOIR_Version_Manifest.txt
- project_sources/CP-02_DCOIR_Change_Log.txt
- project_sources/todo/03_Documentation_And_Knowledge_Lane.txt
- project_sources/LOG-03_DCOIR_Session_Handoff_Brief.txt
- project_sources/DOC-05_DCOIR_Helper_Skill_Workflow_And_GitHub_Source_Rules.txt

## Out of scope
- Generic non-DCOIR skills such as skill-creator are not part of this project-specific helper-skill routing note unless later promoted into a governed project workflow.
