# DCOIR Helper Skills Routing Note

## Purpose
This note is a governed descriptive routing aid for the current installed `dcoir-*` helper skills used in the AFRICOM_SOC_IR / DCOIR project.

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

## High-level routing rules
1. Confirm the task is actually inside the AFRICOM_SOC_IR / DCOIR project context.
2. Re-anchor to Project Instructions, then `CP-01`, then `CP-02`.
3. Prefer the most specific matching `dcoir-*` skill over broader helpers.
4. Use helper skills for project-side authoring, QA, packaging, maintenance, routing, and workflow support.
5. If no helper skill cleanly fits, proceed directly with a bounded explanation rather than forcing a bad match.

## Fast routing matrix

| Task family | Preferred helper skill | Typical routing cues | Notes |
| --- | --- | --- | --- |
| Resume current project state | `dcoir-session-resume` | resume, where are we, what is current, get me back on track | Start here for continuity-focused restarts |
| Need a visible attention banner | `dcoir-attention-signaler` | important review, milestone, action required, blocked | Use for high-signal chat responses inside DCOIR |
| Verify source authority or stop stale work | `dcoir-source-authority-auditor` | verify authority, is this current, stale source risk, should we stop | Use when control-plane drift is a risk |
| GitHub repo write or grouped update work | `dcoir-memory-preflight` | update GitHub, delete files, grouped repo edit, control-plane change | Consult task memory before execution |
| What else must change after a repo update | `dcoir-change-impact-analyzer` | downstream impact, what else must change, refresh set | Use after a proposed or completed change |
| Default branch/decision handling | `dcoir-decision-policy` | what should we do, choose path, operator preference branch | Use when several reasonable paths exist |
| Collector QA, repair, or harness issues | `dcoir-collector-qa` | collector error, harness failure, repair collector, QA report | Project-gated collector maintenance aid |
| Validation plan or test sequencing | `dcoir-validation-orchestrator` | what should we test, validation plan, test order, evidence gates | Default for explicit validation planning |
| Deep regression for helper skills | `dcoir-skill-regression-auditor` | regression plan for skills, fixtures, output checks | Use before or after skill changes |
| Remediation plan after live-test findings | `dcoir-live-test-remediation-planner` | what to fix first, ranked remediation, live-test findings | For ordered post-test repair planning |
| Operator-facing endpoint or local workflow guidance | `dcoir-operator-workflow-hardener` | exact next step, endpoint step, cleanup handling, interpret collector output | Use for operator runtime instructions |
| Large or partial evidence intake | `dcoir-large-file-intake-manager` | files too big, upload limits, staged intake, targeted excerpts | Use when evidence cannot be handled in one pass |
| Session-local scratch, follow-ups, and handoff | `dcoir-session-tracker` | don't forget, what is left, session notes, handoff artifact | Session-local continuity aid |
| Prompt-pack assembly into one combined prompt | `dcoir-prompt-pack-assembler` | assemble master prompt, rebuild combined prompt, prompt-pack refresh | Use only after authority is settled |
| Knowledge and supporting docs maintenance | `dcoir-knowledge-doc-maintainer` | regenerate docs, maintain knowledge docs, inventory doc changes | For knowledge-doc generation and refresh |
| Triage-to-collector bridge design | `dcoir-triage-to-collector-escalation-designer` | alert triage handoff, routing language, escalation triggers | Use for Elastic-style bridge design |
| Structural renames or re-homing | `dcoir-structural-rename-coordinator` | rename file, rename class, move path, re-home assets | Use before partial rename work |
| Packaging or release-class choice | `dcoir-release-scope-builder` | local only or bundle, targeted update or full refresh, packaging class | Picks packaging class, not readiness |
| Readiness judgment before treating work as live | `dcoir-promotion-readiness-reviewer` | is this ready, ready with conditions, blocking gaps | Use after changed set and packaging posture are known |
| Repo-layout zip or bootstrap bundle creation | `dcoir-repo-packager` | package repo, build bootstrap bundle, strict repo-layout zip | Packaging execution helper |
| Trigger-test only | `dcoir-trigger-test` | run dcoir trigger test | Use only to verify visible skill auto-invocation |

## Detailed helper-skill inventory

### Continuity and routing
- `dcoir-session-resume`
  - Use when the operator asks where the project stands, what changed, or how to resume the governed work line.
- `dcoir-attention-signaler`
  - Use to add conspicuous milestone, review, action-required, blocked, or completion banners in DCOIR chats.
- `dcoir-source-authority-auditor`
  - Use to verify current authority, detect stale assumptions, and stop when source drift makes work unsafe.
- `dcoir-decision-policy`
  - Use to apply the operator's default decision matrix when multiple reasonable execution branches exist.

### GitHub and repo-change workflow
- `dcoir-memory-preflight`
  - Use before GitHub read/write/update/delete or grouped repo work that may already have a validated procedure in task memory.
- `dcoir-change-impact-analyzer`
  - Use to identify the direct refresh set, conditional review set, packaging recommendation, and stop conditions after a proposed or completed change.
- `dcoir-structural-rename-coordinator`
  - Use when a rename, re-home, or naming-model change could break downstream mappings or dependent files.
- `dcoir-release-scope-builder`
  - Use to decide whether a change is local-only, a targeted update, a repo-layout test bundle, or a full-refresh bundle.
- `dcoir-promotion-readiness-reviewer`
  - Use to decide whether a changed set is ready, ready with conditions, or not ready after packaging posture is known.
- `dcoir-repo-packager`
  - Use to generate strict repo-layout zips or GitHub-primary bootstrap bundles from the current authoritative file set.

### Validation, QA, and remediation
- `dcoir-collector-qa`
  - Use to validate, troubleshoot, regression-test, repair, and maintain the governed collector and harness files.
- `dcoir-validation-orchestrator`
  - Use to build explicit validation plans and test gates for scripts, prompt-pack flows, skills, and workflow changes.
- `dcoir-skill-regression-auditor`
  - Use to plan and audit deep regression for helper skills before live use and after every patch.
- `dcoir-live-test-remediation-planner`
  - Use to turn live-test findings into a ranked remediation plan with impacted files and refresh requirements.

### Operator workflow and intake
- `dcoir-operator-workflow-hardener`
  - Use to normalize operator-facing execution guidance, choose between endpoint and local lanes, and interpret collector output.
- `dcoir-large-file-intake-manager`
  - Use when evidence files are too large, incomplete, or partially available and the workflow needs staged intake.
- `dcoir-session-tracker`
  - Use for session-local notes, unfinished items, and exportable handoff artifacts.

### Documentation, prompt, and design work
- `dcoir-prompt-pack-assembler`
  - Use to assemble one combined analyst-facing master prompt from the current validated modular prompt-pack source set.
- `dcoir-knowledge-doc-maintainer`
  - Use to maintain or regenerate supporting knowledge docs from the authoritative GitHub-primary source set.
- `dcoir-triage-to-collector-escalation-designer`
  - Use to design or revise the handoff from alert triage into DCOIR collection and analyst follow-through.

### Special-purpose and test-only helpers
- `dcoir-trigger-test`
  - Trigger-test helper for visible skill invocation checks only. Do not use it for normal project work.

## Preferred routing cues by common request type
- “Where are we?” or “Resume where we left off.”
  - Route to `dcoir-session-resume`.
- “Is this still current?” or “Should we trust this source?”
  - Route to `dcoir-source-authority-auditor`.
- “Update these GitHub files,” “delete these repo files,” or “what is the safe write lane?”
  - Route to `dcoir-memory-preflight` first.
- “What else must change if we edit this?”
  - Route to `dcoir-change-impact-analyzer`.
- “Which packaging class applies?”
  - Route to `dcoir-release-scope-builder`.
- “Is this ready to treat as live?”
  - Route to `dcoir-promotion-readiness-reviewer`.
- “Collector test failed” or “repair the collector or harness.”
  - Route to `dcoir-collector-qa`.
- “What should we test before live use?”
  - Route to `dcoir-validation-orchestrator`.
- “Tell the operator the exact next step.”
  - Route to `dcoir-operator-workflow-hardener`.
- “These uploads are too big.”
  - Route to `dcoir-large-file-intake-manager`.
- “Assemble the combined DCOIR prompt.”
  - Route to `dcoir-prompt-pack-assembler`.
- “Regenerate or improve knowledge docs.”
  - Route to `dcoir-knowledge-doc-maintainer`.

## Anti-patterns
- Do not treat this note as a guarantee that a helper skill will always auto-invoke.
- Do not override Project Instructions, `CP-01`, or `CP-02` with this note.
- Do not use a broad helper when a more specific project helper clearly matches.
- Do not mention helper skills or hidden workflow machinery inside final standalone runtime deliverables.
- Do not keep this note stale after the installed helper-skill set changes materially.

## Maintenance rule
When a `dcoir-*` helper skill is added, removed, renamed, materially repurposed, or retired, update this note and any nearby routing references in `knowledge/README.md` or related project guidance.

## Related files
- `knowledge/README.md`
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- `project_sources/todo/03_Documentation_And_Knowledge_Lane.txt`
- `project_sources/LOG-03_DCOIR_Session_Handoff_Brief.txt`

## Out of scope
- Generic non-DCOIR skills such as `skill-creator` are not part of this project-specific helper-skill routing note unless later promoted into a governed project workflow.
