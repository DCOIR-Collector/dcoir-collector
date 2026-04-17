# Startup Airtable Recovery Workflow

Use this workflow after `dcoir-session-resume` and `dcoir-memory-preflight` on the first substantive DCOIR turn of a new session.

## Purpose
Recover Airtable-backed leftovers before fresh execution starts so session continuity does not depend on fragile local cache presence or chat memory.

## Tables
- base id: `appM4KSwnVf3G3OTK`
- `Session Checkpoints`: `tblTe75HKZOJaPDGn`
- `Idea Inbox`: `tblWwBxwrjZF6JR3r`
- optional `Work Items`: `tblgsQAVWvh8K7gIR`

## Recovery sequence
1. Read the newest relevant `Session Checkpoints` rows first.
2. Prefer rows with active carry-forward value and without final promotion already complete.
3. Read `Idea Inbox` rows that are not `done`, `dropped`, or already promoted.
4. When the operational board exists and is relevant, read open active `Work Items` rows too.
5. Deduplicate against current governed GitHub todo or control-plane surfaces.
6. Classify leftovers as already durable, Airtable-only and still open, or stale/superseded.
7. Surface one best next move plus any Airtable-only items that still need promotion or closure.

## Truth rules
- Do not surface an Airtable item as unresolved if the same item is already durably represented in governed GitHub state.
- Do not treat local cache absence as durable-state loss when Airtable is current.
- Do not silently skip Airtable-only leftovers just because the governed resume summary looked stable.


## Airtable display posture
- Automatic startup recovery must stay silent by default.
- Do not use `display_records_for_table` during automatic startup recovery.
- Prefer `search_records` or other non-display Airtable reads during automatic startup recovery.
- If a visible Airtable view might help, ask the operator first and show Airtable only after explicit approval.
