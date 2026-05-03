---
name: dcoir-session-resume
description: resume the africom_soc_ir / dcoir workspace from the current airtable-first operational authority model and current queue state. use on the first substantive dcoir turn, explicit re-anchor/resume/current-state requests, queue recovery, startup authority checks, and live plan/work item selection.
---
<!-- skill-marker: updated-skill|20260503T173000Z|reanchor-helper-invocation-rule|source-update|dcoir-session-resume|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T111500Z|airtable-display-allowed-when-useful|source-update|dcoir-session-resume|SKILL.md -->
<!-- skill-marker: updated-skill|20260501T193500Z|queue-control-drift-gate|source-update|dcoir-session-resume|SKILL.md -->

# DCOIR Session Resume

## Project gate
Use only inside AFRICOM_SOC_IR / DCOIR. Airtable is live operational authority for startup, queue, active Plans, Work Items, Session Checkpoints, Operator Preferences, helper memory, and workflow control. GitHub is governed source/readback, packaging, tool-code, helper-skill source, and promoted history only when the task requires those roles.

## Mandatory startup and re-anchor chain
On the first substantive DCOIR turn of a new session, and on explicit re-anchor/resume requests, run this chain before resuming active execution:
1. Project Instructions.
2. CP-00 only as a bootstrap pointer when present.
3. Airtable Governance Control Plane row `CONTROL-STARTUP-AIRTABLE-FIRST`.
4. Airtable Queue Control, active Plans, Work Items, Session Checkpoints, Operator Preferences, and Admin Registry/helper memory rows needed for the branch.
5. `dcoir-memory-preflight` for task-family classification, SKILLROUTE lookup, reusable memory, blocker/lane guidance, and anti-pattern checks.
6. `dcoir-airtable-schema-cache` for schema readiness before broad Airtable reads, writes, deletes, migration checks, or schema-sensitive work.
7. `dcoir-session-tracker` for durable leftover scan, idea/promote candidates, and session carry-forward state.
8. `dcoir-plan-tracker` when open/active Airtable-backed plan state exists, a Work Item points to a parent plan, or Queue Control needs repair.
9. Additional DCOIR helper checks selected by active lane context and `SKILLROUTE-*` rows. Do not load every full helper-skill body just to prove awareness.

Plain rule: a DCOIR re-anchor is not complete until the required helper chain has run or a specific blocker/conflict is reported.

## Authority order
Use this order unless the operator explicitly overrides it:
1. Project Instructions.
2. CP-00 pointer only.
3. Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`.
4. Airtable live authority tables: Queue Control, Work Items, active Plans, Work Items for task execution, Session Checkpoints, Operator Preferences, Admin Registry, helper-memory tables, and task-specific current tables.
5. GitHub current governed source only for repository-source, packaging, promoted-history, source-code validation, tool-code, helper-skill source, or explicit repo readback.
6. Supporting assets and historical surfaces only as evidence or promoted history.

Do not fetch GitHub CP-01/CP-02 during normal startup when Airtable startup authority is present/current. If GitHub history conflicts with Airtable live state, prefer Airtable and report promoted-history drift unless doing a source-authority comparison.

## Queue Control drift gate
During startup, re-anchor, resume, and “where are we” checks:
- Treat `Queue Control.active_plans` as the first live branch pointer.
- Cross-check Queue Control against active Plans and active/todo Work Items.
- If Queue Control points to a current plan, use that branch unless the operator explicitly overrides it.
- If Queue Control is empty while exactly one active plan exists, report drift and proceed only as a bounded fallback while requesting/performing Queue Control repair through plan-tracker.
- If Queue Control conflicts with active Plans or active Work Items, stop ordinary resume and report the exact mismatch.
- Do not pick an older plan from chat memory, stale checkpoint text, or GitHub todo history when Queue Control and active Plans disagree.

## Airtable display behavior
During automatic startup/re-anchor, use compact non-display Airtable reads by default. During execution, audit, cleanup, duplicate comparison, or verification, Airtable display views may be used when they materially improve correctness or when operator approval/preference already allows visible Airtable display. Always summarize displayed evidence in chat.

## Core workflow
1. Classify the request as `session_start_bootstrap`, explicit resume/re-anchor, status report, or task execution continuation.
2. Read Airtable Governance Control Plane, Queue Control, active Plans, active/todo Work Items, Session Checkpoints, and relevant Operator Preferences.
3. Apply the Queue Control drift gate.
4. Invoke the mandatory startup/re-anchor helper chain in order.
5. Use Airtable queue state as live next-work authority.
6. Read GitHub only when the immediate task requires governed source/readback, promoted-history comparison, package generation, source-code validation, or explicit repo readback.
7. If authority conflict appears, stop and report the exact conflict instead of producing a normal resume summary.
8. If a path is bounded by missing/inaccessible surfaces, say which surfaces were unavailable.
9. Hand off to the active Work Item with one best next move.

## Strong trigger phrases
Use this skill for: `re-anchor`, `resume`, `where are we`, `what is current`, `get me back on track`, `continue from checkpoint`, `close out this session`, and first substantive DCOIR turns.

## Output contract
For status/resume replies, return:
1. Current stable baseline.
2. Airtable startup authority and queue state.
3. Governed GitHub source/readback role.
4. Active Plan and active Work Item.
5. Helper-chain status.
6. Refresh watchlist.
7. One recommended next move.

For execution continuation, keep the chat short: state the selected Work Item, any blocker/conflict, and the next action being executed.

## Hard rules
- Do not skip `dcoir-memory-preflight`, `dcoir-airtable-schema-cache`, session-tracker, and conditional plan-tracker during startup/re-anchor.
- Do not treat old GitHub todo/current-state files as live queue authority.
- Do not assume retired Airtable tables exist unless live schema readback proves they exist.
- Do not use a schema cache as write/delete authority.
- Do not infer missing files or silently resolve authority conflicts.
- Do not ask broad clarification questions when Airtable queue authority already resolves the next work.
- Prefer one best next move over a menu.

## Testing surface default
When the resumed work is collector testing, Gemini testing, live evaluation, or validation follow-through, consult Airtable `Validation Test Cases` as the default durable manual-testing surface after the normal resume/bootstrap chain completes.
