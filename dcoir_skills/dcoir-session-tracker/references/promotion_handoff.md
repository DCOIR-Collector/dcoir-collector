<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-session-tracker|promotion_handoff.md -->

# Promotion handoff

## Purpose
Use this reference when a session-tracker item needs to become a real Project update.

## Default promotion sequence
1. Confirm the operator wants promotion rather than session-local tracking only.
2. Re-anchor to the control plane.
3. Identify which files or skills are implicated.
4. Use the existing DCOIR helper skills in this order when relevant:
   - `dcoir-decision-policy`
   - `dcoir-source-authority-auditor`
   - `dcoir-change-impact-analyzer`
   - `dcoir-release-scope-builder`
   - `dcoir-promotion-readiness-reviewer`
   - `dcoir-repo-packager`
5. Produce the smallest correct update set that matches the control plane and the operator's approved path.

## Promotion-ready text blocks
When useful, prepare ready-to-drop candidate text for:
- `Airtable Work Items / Plan Tasks`
- `Airtable skill-memory or Session Checkpoints`
- `Airtable Session Checkpoints`

Do not imply these candidate blocks are already promoted.

## Session close-out promotion sequence
Use this sequence when the operator is moving to another session and the current session contains material that should not remain chat-only.

1. Confirm whether a safe governed Project write is already happening in the current workflow.
2. Re-anchor to the control plane.
3. Identify the smallest correct continuity update set.
4. Prefer batching already-known continuity follow-ons into one grouped transaction when the lane is safe.
5. If no safe GitHub write is happening, export the handoff artifact and state the remaining non-durable items plainly.
6. Prepare starter-prompt text for the next session.
7. Do not imply session close-out is complete until durability state is explicitly reported.

## Close-out candidate destinations
When relevant, prepare ready-to-drop candidate text for:
- `Airtable Work Items / Plan Tasks`
- `Airtable skill-memory or Session Checkpoints`
- `Airtable Session Checkpoints`

Do not imply these candidate blocks are already promoted unless they were actually written.
