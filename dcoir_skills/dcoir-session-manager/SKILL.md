---
name: dcoir-session-manager
description: manage africom_soc_ir / dcoir Airtable-first session startup, re-anchor, resume, checkpointing, closeout, handoff, and continuity. Use on the first substantive DCOIR turn, explicit resume or re-anchor requests, active queue recovery, session closeout, handoff export, idea capture/promotion, active plan/work item selection, and cases where dcoir-session-resume or dcoir-session-tracker behavior would previously have applied.
---

# DCOIR Session Manager

Use this skill as the consolidated replacement for `dcoir-session-resume` and `dcoir-session-tracker`.

## Authority order
1. Project Instructions are the first anchor.
2. Read `CP-00_DCOIR_Airtable_First_Bootstrap.txt` when present as a pointer only.
3. Use Airtable Governance Control Plane row `CONTROL-STARTUP-AIRTABLE-FIRST` as active startup/load-sequence authority.
4. Treat Airtable as live authority for Queue Control, Plans, Work Items, Session Checkpoints, Idea Inbox, Operator Preferences, Validation Test Cases, Validation Evidence, Delete Queue, DCOIR Lifecycle Ledger, Admin Registry, Repo Surface Registry, Local Configuration Registry, Operator Tools Registry, and helper-memory tables where present.
5. Treat GitHub `malwaredevil/dcoir-collector` as governed source/readback, packaging source, reusable tool-code source, helper-skill source parity target, and promoted history only when repo-source work requires it.
6. Do not fetch GitHub CP-01/CP-02 during normal startup when Airtable startup authority is present/current.

## Startup and re-anchor workflow
On the first substantive DCOIR turn, or when the operator asks to resume, re-anchor, recover queue state, or report current state:

1. Confirm the active authority chain from Project Instructions, CP-00 pointer, and Airtable Governance Control Plane.
2. Invoke `dcoir-memory-preflight` to recover durable task memory, SKILLROUTE rows, operator preferences, helper-memory state, and blocker-routing guidance.
3. Invoke `dcoir-airtable-schema-cache` to refresh or validate schema readiness before broad Airtable reads.
4. Use compact Airtable reads for Queue Control, active Plans, Work Items, Session Checkpoints, Operator Preferences, Admin Registry skill-state rows, SKILLROUTE rows when routing may apply, Operator Tools Registry when local tools may apply, and task-specific tables.
5. Select the active executable Work Item or Plan branch from Airtable, not from stale chat, GitHub CP files, or older todo files.
6. Report conflicts instead of guessing when Project Instructions, CP-00, Airtable Governance Control Plane, or live Airtable queue state disagree.

## Resume response shape
When asked to resume or report state, summarize only:
- stable baseline,
- Airtable startup authority,
- governed GitHub source/readback role,
- retained supporting assets,
- governance state,
- validation status,
- Airtable queue authority,
- active Airtable plan/work branch,
- refresh watchlist,
- one next move.

## Session continuity and closeout
Use Airtable durable surfaces for session carry-forward:

- Use Session Checkpoints for resume notes, closeout summaries, active state, blockers, and next move.
- Use Idea Inbox for unapproved ideas, rough improvements, deferred decisions, and promotion candidates.
- Use Work Items for executable task rows.
- Use Plans for multi-step parent scope.
- Use Queue Control only after an executable Work Item or Plan state exists.
- Use DCOIR Lifecycle Ledger for material promotion, migration, retirement, deletion, closeout, or cleanup history.

At closeout, preserve enough detail for the next re-anchor to continue without relying on chat memory:
1. active plan/work item,
2. completed changes and verification evidence,
3. blockers and unresolved conflicts,
4. pending operator actions,
5. next executable step,
6. source/readback artifacts that must be rechecked.

## Idea capture and promotion
Do not silently promote rough ideas into execution state.
- Put raw or unapproved ideas in Idea Inbox.
- Promote executable work into Work Items only when it is approved or clearly actionable.
- Create/update Plans for governed, multi-step, or resume-sensitive work.
- Record material lifecycle events in DCOIR Lifecycle Ledger.

## Deletion and cleanup discipline
- Use Delete Queue for Airtable record deletion unless the operator explicitly authorizes immediate connector-level deletion and dependency order is safe.
- Do not delete repo files, helper-skill source, Airtable records, or tables solely because they look stale.
- Verify source/readback and live dependency status before deletion.
- For helper-skill retirement, preserve replacement behavior, confirm marketplace/editor deletion when required, remove GitHub source through the approved lane, refresh parity, and update Airtable evidence.

## Output discipline
- Do not narrate tool-by-tool intent.
- Stop only for operator decisions, blockers, conflicts, approval gates, or completed checkpoints.
- When a governed action changes Airtable or GitHub, report the result, evidence, and any remaining gate.
