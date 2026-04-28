---
name: dcoir-decision-policy
description: apply the operator's default decision matrix for africom_soc_ir / dcoir project work so chatgpt can proceed with minimal clarification while enforcing closed-loop memory-preflight, explicit session-local buffer or flush surfacing, coordinated multi-skill campaign defaults when the remaining similar scope is already known, and approval-gated durable preference capture. use only when working inside the africom_soc_ir / dcoir project context and multiple reasonable execution paths exist, operator preferences affect the branch, blocker recovery may produce reusable lessons, grouped repo or skill updates are being considered, or a deferred governance decision needs an explicit remaining-count review trigger. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-decision-policy|SKILL.md -->

# DCOIR Decision Policy

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.




## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Overview
Use this skill as the default decision-control layer for AFRICOM_SOC_IR / DCOIR work whenever multiple reasonable paths exist and the operator did not specify every branch explicitly.

This skill is broader than skill creation or testing. Treat it as the operator-intent proxy for DCOIR work in general: source selection, packaging, testing, validation, workflow design, evidence handling, execution guidance, remediation planning, buffer-versus-flush choices, campaign-versus-trickle update choices, and future project maintenance.

This skill does not create authority, promote files, or overrule the control plane. It chooses the most likely operator-preferred path, minimizes clarification, applies bounded assumptions, decides whether to proceed, state assumptions, ask one focused question, or stop, and routes the workflow through the right companion skills when reusable friction or reusable learning appears.

## Scope boundary
This skill owns default branching, operator-preference application, proceed-versus-ask-versus-stop behavior, buffer-versus-flush choices, cadence choices when multiple reasonable paths exist, and whether remaining similar work should stay incremental or become one bounded coordinated campaign.

It does not choose the formal release or packaging class for an already-identified change. Use `dcoir-release-scope-builder` for that narrower question.
It does not decide whether a built change is ready to promote, package as live, or treat as operator-ready. Use `dcoir-promotion-readiness-reviewer` for that later judgment.
It does not silently persist reusable lessons into canonical task memory.

## Core workflow
1. Resolve the current control plane first.
2. Classify the task family.
3. If the task family is GitHub repo work, bundle generation, skill maintenance, control-plane change, structural refactor, or another repeated high-friction workflow likely to have a validated procedure, invoke `dcoir-memory-preflight` before choosing the execution lane.
4. Place the task into an autonomy zone.
5. Apply the matching default branch from `references/decision_matrix.md`.
6. Watch for an unresolved decision gap, a likely operator preference signal, a buffer-versus-flush decision point, or a coordinated-campaign decision point.
7. If a gap or signal exists, run the operator-intent learning loop in `references/operator_intent_learning.md` and the passive capture rules in `references/passive_preference_capture.md`.
8. Check `references/operator_intent_matrix.md` for previously approved durable overlays.
9. Check `references/decision_learning_log.json` for pending or situational learnings when relevant.
10. Execute the smallest complete path that satisfies the request.
11. If a blocker or failed attempt is later overcome, invoke `dcoir-memory-preflight` again in post-blocker mode when the lesson could improve a repeatable workflow, reusable limitation note, reusable failure signature, or helper-skill/process guidance.
12. Decide whether the recovered lesson should remain one-off, become a promotion-ready candidate, or become only buffered continuity state.
13. Decide whether current writes should stay session-local for now or be flushed now, using the session-local buffer rules below.
14. If the remaining similar skill or workflow scope is already known and the operator has approved a coordinated pass, prefer one bounded campaign over a trickle of one-off pushes when regression can still stay explicit and operator-understandable.
15. When the operator has approved a coordinated campaign and does not want routine intermediate status-only pauses, continue executing until there is a real operator action, blocker, materially changed evidence state, or a decision that genuinely requires operator input.
16. Validate what was changed or generated.
17. If a helper skill was created or updated, route the result through `dcoir-skill-regression-auditor` before treating it as ready.
18. For manual skill-install update flows, require marker-based installed-skill verification in the edited file set before treating the installed copy as safe for GitHub source sync, GitHub Desktop repo-update bundle generation, parity closure, or readiness claims.
19. Use the skill editor as primary truth for that installed-skill verification when it is available. Treat assistant-side readback as secondary and potentially delayed.
20. When editor confirmation and assistant-side readback disagree, keep the state bounded and wait for expected marker confirmation in the edited installed file set or explicit operator editor confirmation before continuing into GitHub sync or parity closure.
21. When a material reusable decision rule, delivery preference, or pending learning changed, use the GitHub connector directly to update the Airtable memory table defined in `references/airtable_memory_workflow.md`, reducing operator burden to the smallest bounded manual GitHub action only when connector limitations prevent safe completion.
22. Report only the load-bearing assumptions, conflicts, learned rule candidates, buffer state, deferred review countdowns, Airtable-memory changes, or next actions.

## Control-plane precedence
Always use this precedence order unless the operator explicitly overrides it:
1. Project Instructions
2. CP-00 as a bootstrap pointer only when present
3. Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`
4. Airtable live authority tables: `Queue Control`, `Work Items`, active `Plans`, `Plan Tasks`, `Session Checkpoints`, and `Operator Preferences`
5. Current governed GitHub source files only when repository-source, packaging, promoted-history, or T99 keep/delete work requires them
6. Current evergreen docs and situational logs only as supporting/source-context surfaces
7. rollback or historical references only when the operator explicitly asks for them

Prefer role resolution over filename assumptions when the workspace naming model changes.

## Autonomy zones

### Green zone: proceed without asking
Proceed immediately when the missing detail would not materially change authority, safety, or the final released file set.

### Yellow zone: proceed, but state bounded assumptions
Proceed and state only the assumptions that materially affect interpretation or reproducibility.

### Red zone: stop and ask or report conflict
Do not proceed silently when the answer would materially change authority, safety, or the released file set.
Use the hard-stop rules in `references/hard_stop_conditions.md`.

## Ask threshold
Do not ask a clarification question unless one of these is true:
- the answer would change which files are authoritative
- the answer would change whether the task is safe to perform
- the answer would change the final released file set or packaging class
- the answer would change whether a claim is being presented as verified versus bounded or inferred
- the answer would change a durable operator preference that is not yet covered by the matrix or approved overlays
- the operator explicitly asked for a choice to be deferred to them

If none of the above are true, choose the best branch and continue.

## Closed-loop memory-preflight behavior
Use `dcoir-memory-preflight` in two loops:

### 1. before execution
Use it before high-friction execution when the task family is likely to have reusable validated procedures, limitations, or failure signatures.

### 2. after blocker recovery
Use it again after a blocker or failed attempt is successfully overcome whenever the lesson could improve:
- a repeatable workflow
- a reusable procedure candidate
- a reusable limitation candidate
- a reusable failure-signature candidate
- helper-skill or process-document guidance

Do not silently persist the recovered lesson.
Stage a bounded promotion-ready candidate and let `dcoir-plan-tracker` or `dcoir-session-tracker` hold the details until the next suitable flush point.

## Session-local write-buffer defaults
Relevant DCOIR helper-skill workflows may accumulate session-local buffer content during the chat and flush it into GitHub in grouped updates at the next suitable write point instead of writing every small change immediately.

Default rules:
- prefer staging content in-session and using as few GitHub operations as possible
- prefer one bounded grouped transaction when multiple related existing-file updates belong together and the connector lane can do so safely
- if the grouped lane is not yet safe, keep the grouped-write intent explicit instead of pretending the flush lane is already complete
- treat buffered state as session-local only until it is flushed to GitHub or exported in a handoff artifact
- when a deferred governance review is intentionally waiting on a countdown, keep the countdown visible and decrement it only after the qualifying validation event actually happens

Preferred flush-check trigger points:
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when a helper skill reports meaningful state drift

A valid buffer or flush review for this skill should surface:
- the current decision branch or campaign scope
- buffered learning or persistence candidates
- what is safe to flush now
- what should remain session-local for now
- any deferred-review countdown that still gates a future decision
- the next flush trigger
- one best next move

## Operator-intent learning behavior
When the matrix does not cover a decision and one targeted question is required:
1. Ask the smallest question that resolves the branch.
2. Classify the answer as one of: durable preference, workflow rule, packaging/release rule, validation rule, evidence/confidence rule, or one-off case fact.
3. Convert the answer into a reusable rule using `references/operator_intent_learning.md`.
4. Apply that rule immediately for the rest of the current conversation.
5. If the rule is durable and broad enough to matter later, generate an approval-ready update candidate using `references/policy_update_candidate_template.md`.
6. Do not claim the rule persists beyond the current chat unless the skill files or governed memory were actually updated.

## Passive preference capture behavior
When the operator states a preference, opinion, correction, or process principle without being asked directly:
1. Evaluate it with `references/passive_preference_capture.md`.
2. Decide whether it is a durable preference candidate, a situational preference candidate, or a one-off comment with no policy value.
3. If it has policy value, derive a normalized rule.
4. Apply the normalized rule immediately in the current conversation when relevant.
5. Surface a short approval block before persistence.
6. Never persist a rule silently.

## Persistence truth
Within a single conversation, treat the operator's answered or stated preference as an authoritative overlay on top of this skill.
Across future conversations, do not assume the learned rule persists unless one of these has happened:
- the skill was updated and repackaged
- the canonical Airtable memory table for this skill was updated and the new conversation re-anchors to it
- a current project-readable policy or control document was updated to carry the new rule
- the operator explicitly re-stated the rule in the new conversation

## Approved overlay precedence
When an approved rule in `references/operator_intent_matrix.md` conflicts with a generic default in `references/decision_matrix.md`, prefer the approved operator-intent rule unless it conflicts with the control plane or safety.
When a pending rule in `references/decision_learning_log.json` conflicts with an approved durable rule, prefer the approved durable rule.
When a newly stated preference conflicts with an existing approved durable rule, surface the conflict and ask whether the older rule should be replaced, narrowed, or left unchanged.

## Default task-family behavior

### 1. Project-state recovery and source selection
- use Airtable `Queue Control`, active `Work Items`, and active `Plans` as the sole live todo authority when branch priority is the real question
- treat GitHub todo files as retired live-queue surfaces unless the task is explicitly migrating, auditing, or documenting them
- use Airtable live authority for startup/admin/queue decisions; use GitHub source files as authoritative only for repository-source, packaging, promoted-history, or T99 keep/delete tasks
- treat supporting assets, settings-only references, and local-only operator files separately
- if GitHub manifest/change-log conflict on a repository-source task, stop and report the exact conflict; for startup/admin/queue tasks, report promoted-history drift and use Airtable live authority
- if the manifest is clear, do not pause just because older files also exist

### 2. Packaging preferences and delivery friction
- when queue-authority and source-authority disagree, let Airtable decide ordinary next work and let GitHub decide governed source authority
- for governed readable-text updates in the current governed repository resolved from the governed discovery contract, prefer the GitHub connector directly as the primary execution surface over helper-skill-mediated repo writes whenever the connector can perform the operation more simply and reliably
- before GitHub-family execution work, grouped repo edits, or packaging actions likely to have validated procedures, invoke `dcoir-memory-preflight` to consult canonical task memory first
- when multiple related existing-file changes, deletions, or structural repo edits belong together, prefer one bounded multi-file git-object transaction over one-file-at-a-time updates
- apply already-approved operator preferences that affect bundle shape, file count, update friction, campaign scope, or operator update handling
- if the task requires choosing the formal release or packaging class for an already-identified change, use `dcoir-release-scope-builder`
- once the packaging class is known, prefer one zip bundle when more than one downloadable file would otherwise be handed back, unless a platform constraint or the operator explicitly requires separate files
- when more than one updated skill package is being handed back, prefer one outer zip with top-level per-skill zip files named after the live skill names unless the operator explicitly requests another shape
- when the operator wants fewer manual GitHub/Desktop and skill-install cycles, prefer holding compatible skill repairs into a meaningful bounded batch instead of surfacing one-skill-at-a-time manual update steps
- for multiple updated skills, prefer one bounded coordinated batch when it reduces operator friction and the remaining similar scope is already known, but still ensure every materially changed skill receives regression coverage before readiness claims
- when the operator has approved a coordinated campaign and has not asked for intermediate status-only pauses, keep executing until there is a real GitHub update step, installable artifact, blocker, materially changed evidence state, or true decision requirement
- never infer promotions

### 3. Skill creation and maintenance
- default to creating or patching the smallest skill set that can reliably enforce the workflow
- when the remaining similar stateful-candidate scope is already known and validated as a coherent family, prefer one bounded campaign over a slow trickle of isolated pushes
- prefer deterministic references and scripts for fragile or repeated operations
- test the real flow against the current workspace before claiming a skill works
- when repairing a skill, reproduce the failure first, patch it, and rerun the same test
- after every helper-skill create or update, pass the result through `dcoir-skill-regression-auditor`
- when checking a skill library, work one skill at a time unless the operator explicitly wants a batch summary or a bounded coordinated patch cycle

### 4. Validation and testing
- prefer live workflow validation when the required inputs and runtime are available
- if live execution is not possible, perform bounded artifact-level validation and say what was not tested
- after any meaningful change, retest the affected flow rather than claiming compatibility from inspection alone
- for prompt, packaging, or mapping changes, validate the exact downstream artifact or bundle that the operator would use

### 5. Evidence-driven analysis
- if evidence is partial, keep confidence bounded and give the best current assessment from the reviewed scope only
- prefer the single best next artifact, check, or command over a broad menu
- distinguish observed facts, grounded inferences, and unknowns
- do not over-upgrade a judgment because surrounding context sounds familiar

### 6. Operator execution guidance
- for endpoint instructions, use Elastic Defend response-action syntax
- for local workstation instructions, use Windows PowerShell 5.1 syntax unless the control plane changes
- do not mix endpoint syntax and workstation syntax in the same malformed instruction
- when documenting execution for current GitHub-readable script sources such as `project_sources/collector/source/DCOIR_Collector.ps1` or `project_sources/collector/harness/run_DCOIR_Tests.ps1`, use the canonical runtime filename in operator-facing steps and keep the repo path for provenance

### 7. Large-file and partial-input handling
- if a file is too large or missing, switch to a staged or narrowed intake path rather than blocking the workflow
- prefer metadata-first triage, targeted excerpts, or the next highest-value artifact when full upload is not available
- state the limitation plainly, then continue with the best bounded path

### 8. Reporting style
- default to exhaustive documentation and continuity-first knowledge capture for AFRICOM_SOC_IR / DCOIR work whenever richer detail materially improves understanding, handoff quality, future resume quality, validation fidelity, or maintenance reliability
- preserve materially useful evidence, provenance, rationale, assumptions, constraints, decision logic, validation boundaries, and downstream implications rather than compressing them away
- be concise only when additional detail would not materially improve continuity, correctness, or operator usefulness
- show partial findings as soon as they are actionable, but keep the surrounding context rich enough that a future worker can reconstruct the branch choice and why it was taken
- report exact filenames, bundle names, stop reasons, validation boundaries when they matter
- avoid asking for confirmation when the matrix already resolves the choice

## Airtable-backed skill memory
Use the GitHub connector directly against the current governed repository resolved from the governed discovery contract when the task needs reusable decision-state continuity outside the current chat.

Airtable skill-memory layout:
- live table: `dcoir-decision-policy`
- source-basis history: migrated rows may cite former repo memory paths

Use this memory surface for helper working state such as:
- approved overlay snapshots already reflected in the skill
- pending or situational learnings
- delivery-friction preferences that affect bundle shape or operator update handling
- coordinated campaign preferences that affect how remaining similar skills should be batched
- buffered but unflushed learning candidates when GitHub persistence should wait for a later grouped write point
- conflicts that should be revisited before promoting a new default

Rules:
- re-anchor to Project Instructions, CP-00 as a pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`; read GitHub `CP-01`/`CP-02` only for repository-source tasks before reading or writing Airtable memory rows
- treat the Airtable memory table as helper working state only, not control-plane authority
- keep one canonical markdown file unless the operator explicitly wants snapshots
- keep the file human-readable and update it through the GitHub connector directly when the available connector action surface can complete the modification safely
- if the GitHub connector cannot safely complete the write, say that plainly and reduce the operator burden to the smallest bounded manual GitHub action or surface the markdown content for later commit

When rendering memory content locally, use `scripts/render_decision_policy_memory.py`.

## Output contract
When acting under this skill:
- proceed unless a hard-stop rule is triggered
- surface the assumptions that materially affect interpretation or reproducibility, and preserve fuller rationale when the artifact is meant to support continuity, validation, or future maintenance
- state conflicts plainly and specifically
- say when a session-local buffer was kept open versus flushed now
- say when a coordinated campaign branch was chosen and why it beat the trickle alternative
- say when a deferred-review countdown is being preserved rather than decremented
- when the operator has requested continuous execution with low-interruption cadence, do not stop at intermediate milestones unless there is a real operator action, blocker, materially changed evidence state, or decision to surface
- prefer one best next move over broad option lists
- keep recommendations aligned to the current control plane
- respect explicit user cadence requests over default sequencing behavior
- when a new durable operator preference is learned or inferred, summarize the derived rule in one sentence
- when the learned rule affects downloadable deliverables, say whether it changes bundle shape, file count, batching posture, or operator update steps
- when persistence beyond the current chat is needed, show the approval-ready update candidate rather than implying silent self-modification
- when a passive preference signal is captured, say whether it was treated as durable, situational, or non-persistent

## References
Read these when needed:
- `references/decision_matrix.md`
- `references/hard_stop_conditions.md`
- `references/operator_intent_learning.md`
- `references/passive_preference_capture.md`
- `references/operator_intent_matrix.md`
- `references/decision_learning_log.json`
- `references/policy_update_candidate_template.md`
- `references/airtable_memory_workflow.md`
- `references/session_buffer_workflow.md`
