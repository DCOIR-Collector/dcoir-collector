---
name: dcoir-session-tracker
description: session-local task, note, and continuity tracker for africom_soc_ir / dcoir work. use when chatgpt needs to capture "don't forget" items, answer what is left, merge an uploaded markdown session log with current-session notes, classify items into session-only scratch versus candidate log-01/log-02/log-03 updates, preserve durable preference candidates, hold session-local buffer state until the right flush-check trigger, classify reusable lessons after blocker recovery, or export a downloadable markdown handoff artifact.
---

# DCOIR Session Tracker

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Overview
Use this skill to maintain a session-local tracker that catches spontaneous operator thoughts before they get lost, keeps a clean inventory of what remains, merges an uploaded markdown handoff artifact into the current session state, prepares promotion-ready follow-up when the operator wants items moved into governed Project files, and honestly tracks what is still only buffered in the current session.

This skill does not claim hidden persistence across chats.
- within the current conversation, it can maintain a live tracker and session-local buffer state
- across future conversations, it only has what is re-imported from an exported markdown artifact or what was promoted into governed Project sources

## Core capabilities
1. Capture casual "don't forget" statements without waiting for a formal task list.
2. Classify items into the right buckets.
3. Answer "what do we still have left" with a deduplicated, priority-ordered inventory.
4. Merge an uploaded markdown tracker artifact with the current chat state.
5. Export a standardized markdown handoff artifact for later upload into a new session.
6. Hold session-local buffered continuity, promotion-candidate, and flush-check state until the right GitHub or export moment.
7. Use the GitHub connector directly to read or update the canonical session-tracker state file in `malwaredevil/dcoir-collector` when durable project continuity is needed.
8. Stage governed follow-up actions when session items should be promoted into Project files or skill updates.

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
- says "don't forget", "later we need to", "when we get back to", "from now on", "super important to remember", or equivalent language
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
- why it matters
- next useful action
- related files, skills, or artifacts when known
- `buffer_state`: `not_buffered`, `buffered_session_local`, `flushed_to_github`, or `exported_in_handoff`
- `persistence_status`: `session_only`, `promotion_candidate`, `governed_written`, or `needs_export`
- `flush_trigger` when a later review point is already known

Prefer the operator's latest wording when the same item appears multiple times.
Preserve older wording only when it adds useful rationale or provenance.

## Closed-loop blocker recovery behavior
When a blocker or failed attempt is successfully overcome and the lesson may be reusable:
1. keep the immediate notes in session state
2. invoke `dcoir-memory-preflight` again when the lesson could improve a repeatable workflow, limitation note, failure signature, or helper-skill/process guidance
3. record whether the lesson is one-off or a promotion-ready candidate
4. keep that state buffered until the next suitable flush-check trigger unless the workflow is already performing a safe GitHub write

## Import and merge workflow
When the operator uploads a markdown session artifact or asks to resume from one:
1. Read `references/import_merge_rules.md`.
2. Treat the uploaded markdown as mergeable session state, not control-plane authority.
3. Re-anchor to the current control plane first.
4. Merge imported items with:
   - current-session captured items
   - current Project todo/handoff context when relevant
5. Deduplicate semantically similar items.
6. Keep imported provenance visible.
7. Report the merged open items, newly completed items, buffer state, and any conflicts.

If an imported item conflicts with the current control plane, do not silently carry it forward as authoritative. Mark it `blocked_or_needs_authority` and say why.

## Flush-check workflow
Relevant DCOIR helper-skill workflows may accumulate session-local buffer content during the chat and flush it into GitHub in grouped updates at the next suitable write point instead of writing every small change immediately.

Preferred flush-check trigger points:
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift

When a flush-check occurs, surface:
- what is still buffered
- what is safe to flush now
- what should remain session-local for now
- one best next move

## Inventory workflow
When the operator asks what remains:
1. group by status and priority
2. show gating items first
3. keep session-only items separate from promotion candidates
4. surface durable preference candidates separately from one-off notes
5. surface buffered but unflushed items explicitly
6. end with one best next move

## Export workflow
When the operator asks to export, hand off, or save the session state:
1. Read `references/session_state_schema.md`.
2. Build a structured state object that matches the schema.
3. If code execution and file writing are available, use `scripts/render_session_state.py` to create a markdown artifact.
4. When durable continuity in GitHub is requested, use the GitHub connector directly to create or update the canonical GitHub session-state file, reducing operator burden to the smallest bounded manual GitHub action only when connector limitations prevent safe completion.
5. If file writing is not available, emit the same artifact as one markdown block.
6. Use the default filename pattern `YYYYMMDDTHHMMSSZ_dcoir_session_state.md` unless the operator explicitly asks for another name.

The exported markdown artifact must contain:
- YAML frontmatter with machine-friendly metadata
- current open items
- completed items worth preserving
- candidate LOG-01 / LOG-02 / LOG-03 promotions
- durable preference candidates and their persistence status
- buffer state and pending flush items when relevant
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

## GitHub-backed session state
Use the GitHub connector directly against repository `malwaredevil/dcoir-collector` when session-tracker state should persist outside the current chat.

GitHub session-state layout:
- root folder: `dcoir_skill_memory/`
- per-skill folder: `dcoir_skill_memory/dcoir-session-tracker/`
- canonical state file: `dcoir_skill_memory/dcoir-session-tracker/session_tracker_state.md`

Rules:
- re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing the state file
- treat the GitHub session-state file as helper working state only, not control-plane authority
- keep one canonical markdown file unless the operator explicitly wants snapshots
- update it through the GitHub connector directly when the available connector action surface can complete the modification safely
- if the GitHub connector cannot safely complete the write, say that plainly and reduce the operator burden to the smallest bounded manual GitHub action or surface the markdown content for later commit

## Truth rules
- do not claim cross-session memory unless the state was exported and later re-imported, or the contents were promoted into governed Project files
- do not treat an imported markdown artifact as control-plane authority
- do not let session notes overwrite CP, DOC, LOG, PP, ST, or RB authority rules
- do not silently convert a user preference into a durable rule without surfacing its persistence status
- do not lose operator-stated rationale when it materially explains why the item matters
- do not claim buffered state is durable before GitHub flush or handoff export actually happened

## Output contract
When acting under this skill:
- keep the tracker concise but stateful
- separate session-only items from governed-promotion candidates
- distinguish captured facts, grounded inferences, imported context, and buffered state
- preserve durable preference candidates explicitly
- prefer one best next move over a broad menu
- when exporting, produce a markdown artifact that can be re-uploaded and merged later

## References
Read these when needed:
- `references/classification_rules.md`
- `references/session_state_schema.md`
- `references/import_merge_rules.md`
- `references/promotion_handoff.md`
- `references/sample_cases.md`
- `references/session_buffer_workflow.md`
