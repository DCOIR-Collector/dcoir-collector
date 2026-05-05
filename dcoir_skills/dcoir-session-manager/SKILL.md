---
name: dcoir-session-manager
description: manage africom_soc_ir / dcoir Airtable-first session startup, re-anchor, resume, automatic periodic/checkpoint-trigger continuity, closeout checkpointing, handoff, and active branch recovery. Use on first substantive DCOIR turns, resume/re-anchor/startup recovery, closeout/handoff, checkpoint/capture/remember requests, blocker or task/lane transitions, idea promotion, active plan/work selection, and former resume/tracker behavior now consolidated here.
---

<!-- skill-marker: updated-skill|20260505T071500Z|automatic-checkpoint-closeout-restoration|in-session-update|dcoir-session-manager|SKILL.md -->

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

- Use Session Checkpoints for resume notes, periodic checkpoints, closeout summaries, active state, blockers, starter prompts, and next move.
- Use Idea Inbox for unapproved ideas, rough improvements, deferred decisions, and promotion candidates.
- Use Work Items for executable task rows.
- Use Plans for multi-step parent scope.
- Use Queue Control only after an executable Work Item or Plan state exists.
- Use DCOIR Lifecycle Ledger for material promotion, migration, retirement, deletion, closeout, or cleanup history.

## Automatic checkpoint and closeout enforcement
This skill owns all behavior formerly split across `dcoir-session-resume` and `dcoir-session-tracker`. Do not treat checkpointing or closeout as a chat-only summary when Airtable write access is available and the operator has not forbidden writes.

Automatically create or prepare a Session Checkpoint when any trigger occurs:
1. a substantive startup, resume, or re-anchor establishes or changes active branch state;
2. a major milestone is reached or a bounded task completes;
3. the active task, active plan, execution lane, or source-authority branch changes;
4. a blocker appears, changes, is resolved, or creates a reusable lesson;
5. before GitHub writes, GitHub Desktop bundles, skill package delivery, or workflow execution when current session state matters;
6. the operator says remember, capture, checkpoint, park this, carry this forward, do not forget, close out, handoff, resume later, or equivalent language;
7. before starter-prompt generation, handoff, session closeout, or moving work to another session;
8. session-local cache/checkpoint state is missing, stale, reinitialized, or uncertain;
9. every long or multi-step DCOIR session after one or two bounded tasks, even without an explicit closeout request.

Checkpoint payloads must preserve: active plan/work item or branch; session mode; completed work; pending work; decisions and operator preferences; blockers/conflicts; artifacts delivered or needing verification; skill/source/parity/cache changes; lane used; validation/evidence status; next recommended move; and starter prompt when closing or handing off.

At closeout, create the Session Checkpoint automatically before or with the closeout response. If Airtable is unavailable or the operator forbids writes, emit a checkpoint-ready payload in chat and state that it is not durable. If the operator asks to close out after a checkpoint-worthy session and no checkpoint has been created, stop the closeout summary until the checkpoint is created or the operator explicitly says not to write one.

After any Session Checkpoint write, refresh the session-manager local cache for Session Checkpoints when file access exists, then verify the written record by Airtable readback or clearly state the verification gap.

See `references/session_checkpoint_and_closeout_workflow.md` for the compact payload template and trigger checklist.

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
