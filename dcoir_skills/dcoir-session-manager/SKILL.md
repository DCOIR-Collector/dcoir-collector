---
name: dcoir-session-manager
description: manage africom_soc_ir / dcoir Airtable-first session startup, re-anchor, resume, checkpointing, closeout, handoff, and continuity. Use on the first substantive DCOIR turn, explicit resume or re-anchor requests, active queue recovery, session closeout, handoff export, idea capture/promotion, active plan/work item selection, and former resume/tracker helper behavior now consolidated into this skill.
---

<!-- skill-marker: updated-skill|20260504T181500Z|cache-scope-narrowing-stale-reference-scrub|source-update|dcoir-session-manager|SKILL.md -->

<!-- skill-marker: updated-skill|20260504T171500Z|airtable-local-cache-contract|source-update|dcoir-session-manager|SKILL.md -->
<!-- skill-marker: updated-skill|20260504T163500Z|core-strengthening|source-update|dcoir-session-manager|SKILL.md -->

# DCOIR Session Manager

Use this skill as the consolidated Airtable-first session startup, resume, checkpoint, and closeout authority.

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
5. Include Local Configuration Registry in the compact read set when the session involves generated code, operator-side tools, workflow scripts, GitHub Actions, environment variable names, or local/system configuration names.
6. Select the active executable Work Item or Plan branch from Airtable, not from stale chat, GitHub CP files, or older todo files.
7. Report conflicts instead of guessing when Project Instructions, CP-00, Airtable Governance Control Plane, or live Airtable queue state disagree.
8. Treat any live route to a retired session resume/tracker helper as route drift. Repair the route to `dcoir-session-manager` or report the cleanup gate before continuing if it affects startup behavior.

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
6. source/readback artifacts that must be rechecked,
7. skill install/removal state that changed this session,
8. parity/schema refreshes that still need to be run.

## Idea capture and promotion
Do not silently promote rough ideas into execution state.
- Put raw or unapproved ideas in Idea Inbox.
- Promote executable work into Work Items only when it is approved or clearly actionable.
- Create/update Plans for governed, multi-step, or resume-sensitive work.
- Record material lifecycle events in DCOIR Lifecycle Ledger.

## Skill lifecycle and parity awareness
When a helper skill is created, merged, retired, or strengthened:
1. Preserve required behavior into the replacement skill or workflow before retirement.
2. Require operator confirmation for marketplace/editor deletion when deletion is involved.
3. Remove GitHub source through the approved repo-update lane.
4. Refresh skill parity surfaces and verify the manifest excludes retired source and includes updated source.
5. Update SKILLROUTE rows, Admin Registry skill-state rows, Repo Surface Registry, and DCOIR Lifecycle Ledger.
6. Check for helper-specific Airtable tables. If table data exists, merge/preserve it first; table deletion is manual and must be verified by schema readback.

## Deletion and cleanup discipline
- Use Delete Queue for Airtable record/row deletion unless the operator explicitly authorizes immediate connector-level deletion and dependency order is safe.
- Do not use Delete Queue for whole-table/schema deletion. Airtable table deletion is manual; after deletion, verify absence through live schema readback and record evidence.
- Do not delete repo files, helper-skill source, Airtable records, or tables solely because they look stale.
- Verify source/readback and live dependency status before deletion.
- For helper-skill retirement, preserve replacement behavior, confirm marketplace/editor deletion when required, remove GitHub source through the approved lane, refresh parity, and update Airtable evidence.

## Output discipline
- Do not narrate tool-by-tool intent.
- Stop only for operator decisions, blockers, conflicts, approval gates, or completed checkpoints.
- When a governed action changes Airtable or GitHub, report the result, evidence, and any remaining gate.

## Airtable local cache contract
Routine cache scope is intentionally narrow: cache only the high-call tables named as routine in the contract; use live Airtable reads for conditional tables.

This skill is Airtable-backed only for the high-call routine tables named in `references/airtable_cache_contract.md`. Read that contract before relying on cached helper-memory, routing, preference, validation, packaging, or configuration-name state.

On every explicit DCOIR re-anchor/startup recovery/resume-first recovery, refresh or recreate only the routine caches named in the contract. If a routine cache is missing, unreadable, stale, or inconsistent with live schema/table identity, refresh before use. Tables listed as conditional/live-read are not routine caches; read them from live Airtable only when the active task requires them. After this skill writes to a routine cached table, refresh the cache and verify the contract-defined freshness indicator. Local cache is advisory only; live Airtable remains authority for writes, deletes, migrations, and dependency-sensitive decisions.
