---
name: dcoir-session-tracker
description: maintain a session-local dcoir tracker with a real local json state file, presence checks, explicit absence or re-init signaling, verbose continuity capture, derived pre-push review bundles, staged governed updates, todo-sync proposals, and handoff exports. use when chatgpt needs to catch important project thoughts before they are lost, answer what remains, prove local tracker state exists, detect or recover from silent local-state absence, prepare follow-up promotion into governed project files, derive what should land in the next grouped github push, or close out a session safely for later resume inside africom_soc_ir / dcoir work.
---

# DCOIR Session Tracker

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Overview
Use this skill to maintain a session-local tracker that catches spontaneous operator thoughts before they get lost, keeps an explicit and operator-readable inventory of what remains, maintains a real inspectable local session-state file when code execution and file writing are available, prepares promotion-ready follow-up when the operator wants items moved into governed Project files, and honestly tracks what is still only buffered in the current session.

This skill does not claim hidden persistence across chats.
- within the current conversation, it may maintain a live local session-state file and session-local buffer state when code execution and file writing are available
- across future conversations, it only has what is re-imported from an exported markdown artifact or what was promoted into governed Project sources
- do not claim a real local session-state file exists until the inspected local file proves it

## Core capabilities
1. Capture casual "don't forget" statements without waiting for a formal task list.
2. Classify items into the right buckets.
3. At the beginning of each new session that uses this skill, run a startup local-state preflight and maintain a real local session-state file as the primary working state when code execution and file writing are available.
4. Inspect the local session-state file and report its path, filename, size, modified time, checksum, and current item counts.
5. Answer "what do we still have left" with a deduplicated, priority-ordered inventory grounded in the current local state when that state exists.
6. Preserve and render tracker items verbosely enough that the operator can understand the carried state without reconstructing prior chat context.
7. Merge an uploaded markdown tracker artifact with the current chat state.
8. Export a standardized markdown handoff artifact for later upload into a new session.
9. Hold session-local buffered continuity, promotion-candidate, and flush-check state until the right governed Project update or export moment.
10. Stage governed follow-up actions when session items should be promoted into Project files or skill updates.
11. Stage governed-update entries explicitly when a grouped GitHub push or repo batch is about to happen so promotion candidates can land in the same governed update instead of waiting for later chat memory.
12. Derive a pre-push review bundle from the current local state, including staged todo additions, updates, removals, and post-push cleanup.
13. When an item is marked governed-written after a grouped push, automatically clear staged governed-update entries, staged todo actions, and post-push cleanup notes that still reference that same item.
14. Give an immediate operator-visible confirmation when a materially important item is captured, including whether it is preserved session-locally only or already staged for the next governed push.
15. Surface an explicit absence or re-init warning when a tracker write path had to initialize a new local session-state file because no pre-existing file was present.

## Local session-state file
When code execution and file writing are available, use a real local JSON file as the primary working-state surface.

Default local state path:
- `/mnt/data/dcoir_session_tracker/session_state.json`

Primary implementation:
- use `scripts/session_state_store.py` to ensure-state, initialize, upsert, complete, remove, inspect, derive the pre-push review, stage explicit governed updates or todo actions, and update summary fields
- use `scripts/render_session_state.py` only to render a markdown export from the local JSON state file

Required local-state workflow:
1. At the beginning of each new session that uses this skill, run `scripts/session_state_store.py ensure-state` before other substantive tracker actions so the operator can see whether a real local session-state file was already present or had to be initialized for the current branch.
2. Initialize the local file before claiming that a maintained session-state file exists.
3. Use the local file as the primary working state during the chat when code execution and file writing are available.
4. If the startup preflight or a later write path had to initialize a new local file because no pre-existing file was present, say that plainly and do not imply that the missing interval was still protected by the local file.
5. After material tracker changes, inspect the file when the operator asks whether the local session state is real or when governed Project flush time is approaching.
6. Before any GitHub write that depends on tracker state, inspect the file and derive the pre-push review from current state.
7. When a governed push, grouped repo batch, or GitHub Desktop push is about to happen, run the derived pre-push review instead of leaving the tracker silent.
8. Before session close-out, inspect the file again and classify durable, exported-only, buffered-only, and any unresolved local-state absence risk explicitly.

Inspection requirement:
- do not claim a real local session-state file exists unless `scripts/session_state_store.py inspect` confirms its path, filename, size, modified time, checksum, and counts
- use `scripts/session_state_store.py ensure-state` as the first-use preflight so the operator can see whether the local file was already present or had to be initialized in the current branch
- when the operator questions whether the local session state is real, show the inspection result instead of paraphrasing intent

If code execution or file writing is unavailable:
- say plainly that a real local session-state file cannot be proven in the current branch
- keep reasoning bounded and do not imply that a real maintained local file exists

Read `references/local_session_state_workflow.md` when local-state implementation or inspection details are needed.

## Visible capture behavior
When a materially important item is captured:
- say that it was captured and preserved in the local session-state file when that file is real and current
- say whether it remains session-local for now or is already staged for the next governed push
- if the capture path had to initialize a new local file because no pre-existing file was present, say that plainly in the same response instead of silently treating the capture as uninterrupted continuity
- prefer one short but explicit reassurance line over silent capture when the operator would otherwise be unsure whether the tracker actually preserved the item

## Verbosity standard
Tracker items should be understandable in isolation.
Do not reduce a materially important item to a short opaque phrase when the operator would need more context to know what it means.

Minimum operator-facing tracker content for a materially important item:
- title
- full detail or context line
- why it matters
- next action
- carry-forward or promotion note when relevant
- related files, skills, or artifacts when known

Preferred additional fields when they materially help:
- operator wording
- impact if missed
- desired outcome
- promotion target
- flush trigger

Truth rules for verbosity:
- terse summaries may exist internally, but they should not be the primary operator-facing representation for important items
- when a user says the tracker is too terse, treat that as both a durable preference candidate and a tracker-improvement task when appropriate
- prefer explicit context over stylistic brevity when the tracker is being used for continuity, handoff, or resume quality

## Session close-out mode
Use this mode when the operator signals that work is about to move to another chat or session.

Strong trigger phrases include:
- `go to another session`
- `move this to a new session`
- `before we switch sessions`
- `close out this session`
- `wrap this session`
- `give me a starter prompt for the next session`
- equivalent language that clearly means session transition or handoff

When session close-out mode is triggered, do not treat it as a normal export only.
Run the full close-out routine below and distinguish:
- what is already durable in governed GitHub sources
- what is only buffered in the current session
- what was exported but not yet promoted
- what is still open and must be carried forward

Required close-out checks:
1. Re-anchor to Project Instructions, then CP-01, then CP-02.
2. Run a flush check against all known buffered session-tracker state.
3. Inspect the local session-state file when it exists and surface the inspection result.
4. If no local session-state file exists at close-out time, say so plainly and warn that any interval since the last proven local-state inspection cannot be treated as file-backed continuity.
5. Verify whether materially learned workflow rules, preferences, blocker recoveries, and reusable lessons were already written to governed GitHub sources, intentionally kept as session-local buffered state, exported into a handoff artifact, or still missing durable capture.
5. Verify that all tasks and requests mentioned in the session are either closed as done, preserved in the correct governed destination, or explicitly carried as open items in the handoff state.
6. Verify that session-related continuity surfaces are updated when the current workflow is already performing a safe GitHub write for governed Project updates.
7. Produce a next-session starter prompt grounded in the current control plane and current open items.
8. Report any close-out gap plainly instead of implying the next session can safely resume from unstored chat-only state.

## Classification buckets
Every tracked item should land in one primary bucket:
- `session_only`
- `candidate_log01`
- `candidate_log02`
- `candidate_log03`
- `durable_preference_candidate`
- `new_skill_idea`
- `follow_on_validation`
- `blocked_or_needs_authority`

These are primary buckets only. Any item may also carry buffer-state, persistence-state, or post-blocker classification metadata.

## Capture rules
Capture an item when the operator does any of the following, even if they do not say "add this to the tracker":
- says `don't forget`, `later we need to`, `when we get back to`, `from now on`, `super important to remember`, or equivalent language
- states a durable preference, workflow rule, naming rule, packaging rule, or validation standard
- says something has been forgotten multiple times and wants it codified
- proposes a new skill, test workflow, or governed change
- points out a miss in an existing skill and expects it to be fixed later
- explains how a blocker was overcome and the lesson may be reusable later

Do not capture trivial back-and-forth comments with no future task value.

## Working-state rules
For each tracked item, preserve:
- short title
- normalized bucket
- status: `open`, `in_progress`, `blocked`, `deferred`, or `done`
- provenance: `current_chat`, `imported_artifact`, `project_log`, or `grounded_inference`
- detail or context line that makes the item understandable in isolation
- why it matters
- next useful action
- related files, skills, or artifacts when known
- `operator_language` when the exact operator wording is especially useful
- `impact_if_missed` when the item guards against likely workflow loss or drift
- `desired_outcome` when the item is steering toward a concrete future state
- `promotion_target` when the likely governed destination is already known
- `carry_forward_note` when the next session will need a bounded reminder or handoff cue
- `buffer_state`: `not_buffered`, `buffered_session_local`, `promoted_to_governed`, or `exported_in_handoff`
- `persistence_status`: `session_only`, `promotion_candidate`, `governed_written`, or `needs_export`
- `flush_trigger` when a later review point is already known

Prefer the operator's latest wording when the same item appears multiple times.
Preserve older wording only when it adds useful rationale or provenance.

## Flush-check workflow
Relevant DCOIR helper-skill workflows may accumulate session-local buffer content during the chat and promote it into governed Project files in grouped updates at the next suitable write point instead of writing every small change immediately.

Preferred flush-check trigger points:
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift
- when the operator signals that work is moving to another session
- when a governed push, GitHub Desktop push, or grouped repo batch is about to happen

When a flush-check occurs:
- inspect the local session-state file when it exists
- derive the pre-push review from current state
- surface what is still buffered
- surface what is safe to flush now
- surface what should remain session-local for now
- surface staged governed updates that should land in the same grouped push
- surface active-todo items that should be added, updated, or removed in the same grouped push
- stage post-push cleanup actions
- after the grouped push lands, use `mark-governed-written` for promoted items so related staged entries and cleanup notes are cleared automatically for those items
- use the verbose tracker-entry standard by default for materially important buffered items
- end with one best next move

Read `references/session_buffer_workflow.md` when flush-check details are needed.

## Session close-out workflow
When the operator is moving to another session, read `references/session_closeout_workflow.md` and perform this close-out sequence in order:
1. Inventory all active tracked items, including session-only notes, durable preference candidates, new skill ideas, follow-on validation items, blocked items, and promotion-ready LOG-01 / LOG-02 / LOG-03 candidates.
2. Run a flush check and inspect the local session-state file when it exists.
3. Classify each item as safe to flush now, should remain session-local for now, must be exported in handoff, or already durable and only needs verification.
4. Verify whether known continuity surfaces are current enough for safe resume.
5. If the surrounding workflow is already doing a safe governed Project write, batch the already-known follow-on continuity updates into that grouped transaction.
6. If no safe GitHub write is occurring, export the handoff artifact and state plainly what remains non-durable.
7. Produce a starter prompt for the next session.
8. End with one best next move.

## Export workflow
When the operator asks to export, hand off, or save the session state:
1. Read `references/session_state_schema.md`.
2. Ensure the local JSON state file exists when code execution and file writing are available.
3. Use `scripts/render_session_state.py` to create a markdown artifact from the local JSON state file.
4. If code execution or file writing is not available, emit the same artifact as one markdown block and say the local file was not available for proof.
5. Use the default export filename pattern `YYYYMMDDTHHMMSSZ_dcoir_session_state.md` unless the operator explicitly asks for another name.

The exported markdown artifact must contain:
- YAML frontmatter with machine-friendly metadata
- current open items
- completed items worth preserving
- candidate LOG-01 / LOG-02 / LOG-03 promotions
- durable preference candidates and their persistence status
- buffer state and pending flush items when relevant
- staged governed updates when relevant
- staged todo actions when relevant
- post-push cleanup items when relevant
- verbose item detail for materially important carried-forward items
- new skill ideas and validation follow-ons
- one best next move

## Promotion and governed follow-up
This skill can prepare promotion-ready follow-up, but it does not silently promote anything.

When the operator wants one or more session items promoted into governed Project files or skill updates:
1. Use `dcoir-decision-policy` for branch/default handling if preference or sequencing choices remain.
2. Use `dcoir-source-authority-auditor` if authority scope is unclear.
3. Use `dcoir-change-impact-analyzer` to determine the downstream refresh set.
4. Use `dcoir-release-scope-builder` to determine the formal release or packaging class.
5. Use `dcoir-promotion-readiness-reviewer` to judge whether the change set is ready.
6. Use `dcoir-repo-packager` only after the scope and readiness questions are settled.
7. Keep session tracker items separate from promoted Project truth until the operator approves the promotion path.

## No GitHub-backed tracker memory
This skill no longer uses `dcoir_skill_memory/dcoir-session-tracker/session_tracker_state.md` as a working-state or snapshot branch.

Rules:
- treat the local JSON file as the only tracker working-state surface for this skill when code execution and file writing are available
- use exported handoff artifacts or governed Project-file promotion for cross-session continuity
- do not create or refresh GitHub-backed helper-state snapshots for `dcoir-session-tracker`

## Truth rules
- do not claim cross-session memory unless the state was exported and later re-imported, or the contents were promoted into governed Project files
- do not treat an imported markdown artifact as control-plane authority
- do not let session notes overwrite CP, DOC, LOG, PP, ST, or RB authority rules
- do not silently convert a user preference into a durable rule without surfacing its persistence status
- do not lose operator-stated rationale when it materially explains why the item matters
- do not claim buffered state is durable before governed promotion or handoff export actually happened
- do not claim a real local session-state file exists until the inspection command proves it
- do not silently reinitialize a missing local state file during a write path without telling the operator that no pre-existing file was present at that step

## Output contract
When acting under this skill:
- keep the tracker explicit, continuity-rich, and easy for the operator to understand without reconstructing prior chat history
- separate session-only items from governed-promotion candidates
- distinguish captured facts, grounded inferences, imported context, local-file state, and buffered state
- preserve durable preference candidates explicitly
- prefer one best next move over a broad menu
- when exporting, produce a markdown artifact that can be re-uploaded and merged later

## References
Read these when needed:
- `references/local_session_state_workflow.md`
- `references/classification_rules.md`
- `references/session_state_schema.md`
- `references/import_merge_rules.md`
- `references/promotion_handoff.md`
- `references/sample_cases.md`
- `references/session_buffer_workflow.md`
- `references/session_closeout_workflow.md`
