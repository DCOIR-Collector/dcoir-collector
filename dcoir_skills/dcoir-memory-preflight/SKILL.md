---
name: dcoir-memory-preflight
description: consult canonical dcoir task memory, airtable governance tables, helper-memory rows, dynamic skill-routing rows, and full continuity/checkpoint rules before dcoir task execution and after blocker recovery. use for session startup, re-anchor, resume, active branch recovery, checkpoint/closeout/handoff, starter prompts, task-time skill applicability checks, execution-lane choice, blocker learning, github/github desktop/tooling friction, skill-routing checks, airtable authority/schema-sensitive work, and cases where any specialist dcoir helper skill may apply.
---

<!-- skill-marker: updated-skill|20260507T183500Z|full-continuity-takeover|in-session-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260507T000000Z|session-continuity-owner-fold-in|in-session-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260505T073000Z|task-time-routing-strengthening|in-session-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260504T181500Z|cache-scope-narrowing-stale-reference-scrub|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260504T171500Z|airtable-local-cache-contract|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260504T163500Z|continuity-strengthening|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260504T111000Z|plan-tracker-retirement-direct-airtable|in-session-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T173000Z|reanchor-helper-invocation-rule|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T111500Z|airtable-display-allowed-when-useful|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260501T193500Z|queue-control-cross-check|source-update|dcoir-memory-preflight|SKILL.md -->

# DCOIR Memory Preflight

## Project gate
Use only inside AFRICOM_SOC_IR / DCOIR. This skill is the pre-execution, post-blocker, task-routing, and folded continuity layer. It does not override Airtable or governed GitHub source authority.

## Continuity ownership
`dcoir-memory-preflight` is the primary and active continuity, checkpoint, startup, resume, re-anchor, handoff, and closeout owner for AFRICOM_SOC_IR / DCOIR. This is not fallback behavior. Do not wait for, route to, or depend on a retired standalone session helper for these duties.

This skill must:
- resolve Project Instructions, CP-00 pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` authority order;
- read or request compact Airtable state for Queue Control, active Plans, active/todo Work Items, latest Session Checkpoints, Operator Preferences, Admin Registry skill-state rows, Repo Surface Registry, Local Configuration Registry when relevant, Operator Tools Registry when local tools may apply, and SKILLROUTE rows when routing matters;
- select the active executable Work Item or Plan branch from Airtable rather than stale chat, old GitHub CP files, or older todo files;
- report conflicts instead of guessing when Project Instructions, CP-00, Airtable Governance Control Plane, or live Airtable queue state disagree;
- decide whether a Session Checkpoint is required;
- create the Session Checkpoint when Airtable writes are available and allowed, or emit a checkpoint-ready payload when writes are unavailable or forbidden;
- refresh the Session Checkpoints cache when file access exists after a checkpoint write;
- verify writes by Airtable readback when possible and report any readback/cache gap;
- preserve raw ideas in Idea Inbox, executable tasks in Work Items, parent scope in Plans, queue branch state in Queue Control, and material lifecycle history in DCOIR Lifecycle Ledger.

When asked to resume or report current state, summarize only: stable baseline, Airtable startup authority, governed GitHub source/readback role, retained supporting assets, governance state, validation status, Airtable queue authority, active Airtable plan/work branch, refresh watchlist, and one next move.

## Invocation modes

### 0. startup, resume, re-anchor, and continuity mode
Run on the first substantive DCOIR turn, explicit resume/re-anchor/startup recovery, active branch recovery, closeout, handoff, checkpoint/capture/remember requests, blocker/task/lane transitions, starter prompt generation, or any case where session-continuity behavior is needed.

The current helper chain is:
1. `dcoir-memory-preflight` establishes the authority chain, continuity posture, active branch, and checkpoint need.
2. `dcoir-airtable-schema-cache` validates schema readiness before broad Airtable reads or schema-sensitive writes.
3. `dcoir-decision-policy` resolves source authority, approval, persistence, branch, and stop/proceed choices when material choices exist.
4. Active lane helpers are selected from Airtable state, live installed skills, and `SKILLROUTE-*` rows.
5. `dcoir-validation-orchestrator` gates readiness, install/readback, package-validity, and evidence claims.

Use this mode to classify the immediate work family, recover active branch state, consult durable routing memory, surface installed-skill drift, choose a bounded lane, preserve continuity, and produce a checkpoint-ready payload when needed.

### 1. pre-execution mode
Run before choosing an execution lane when the task family is likely to have reusable guidance, validated procedure, friction pattern, specialist helper skill, or checkpoint implications.

### 2. post-blocker mode
Run after a blocker or failed attempt is recovered when the lesson could improve a repeatable workflow, reusable procedure, limitation note, failure signature, helper skill, process document, or checkpoint/closeout rule.

### 3. compact task-time routing mode
Run as a lightweight applicability check before DCOIR execution whenever it is plausible that any current DCOIR helper skill, Airtable authority surface, local config registry, operator tool, validation gate, continuity trigger, or execution lane matters.

For compact task-time routing, answer only:
1. Which task family is this?
2. Which SKILLROUTE rows, operator preferences, helper-memory rows, active work records, or checkpoint records are relevant?
3. Which skill(s) must fire now before execution?
4. Which lane is safest/effective: in-session Airtable, GitHub connector/workflow, GitHub Desktop, reusable operator tool, manual review, validation-only, or no-execution planning?
5. What preconditions, anti-patterns, and verification apply?
6. Is a Session Checkpoint or checkpoint-ready payload required?
7. Who is the checkpoint writer for this turn?

## Mandatory triggers
Run this skill before execution, not only at startup, when the task involves:
- startup, resume, re-anchor, branch recovery, closeout, handoff, starter prompts, checkpoint/capture/remember/carry-forward language;
- GitHub readable-text create/update/delete work;
- grouped repo edits or packaging;
- control-plane, queue, authority, or source-role changes;
- skill maintenance, repair, regression, install/readback, or packaging;
- GitHub Desktop/manual bundle preparation;
- repeated local tool, connector, or Actions workflow friction;
- artifact intake, validation orchestration, authority review, or Airtable schema-sensitive work;
- any task where a specialist DCOIR helper skill may apply;
- any DCOIR task where the assistant is about to answer from memory without checking whether a current skill, SKILLROUTE row, operator preference, helper-memory row, active plan/work item, local configuration name, validation gate, continuity trigger, or execution lane should influence the result.

Frequent-fire rule: if unsure whether another DCOIR skill applies, run compact task-time routing mode first. Prefer a short routing check over skipping a relevant skill.

## Airtable-first preflight
When branch priority, startup posture, checkpointing, or next work matters:
1. Read Airtable Queue Control first.
2. Cross-check active Plans and active/todo Work Items.
3. Read latest Session Checkpoints when resume, continuity, handoff, closeout, or branch recovery matters.
4. Consult Governance Control Plane when authority/order matters.
5. Consult Operator Preferences when workflow branching or display behavior matters.
6. Consult Admin Registry and helper-memory tables when skill-state, installed-skill awareness, or routing matters.
7. Consult Repo Surface Registry before repo cleanup, source-role changes, or keep/delete claims.
8. Consult Local Configuration Registry when generated code, operator-side tools, workflow scripts, or environment variable names are in scope.

During automatic startup/re-anchor, use compact non-display Airtable reads. During execution/audit/verification, Airtable display views may be used when they materially improve correctness or when operator approval/preference already allows it.

## Session Checkpoint and closeout enforcement
Use `references/session_checkpoint_and_closeout_workflow.md` for trigger details and payload requirements. Use `scripts/build_checkpoint_payload.py` when deterministic checkpoint-ready JSON is useful. Use `scripts/verify_memory_preflight_skill.py` for local package/readback inspection when troubleshooting install exposure. Use `scripts/validate_cache_contract.py` to check local routine-cache JSON shape.

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

At closeout, create the Session Checkpoint automatically before or with the closeout response when Airtable writes are available and allowed. If Airtable is unavailable or the operator forbids writes, emit a checkpoint-ready payload in chat and label it non-durable. A closeout response without either a durable Session Checkpoint or a non-durable checkpoint-ready payload is incomplete unless the operator explicitly says not to checkpoint.

Use `scripts/build_checkpoint_payload.py` when deterministic checkpoint-ready JSON is useful. Use `scripts/validate_cache_contract.py` for local routine-cache JSON checks.

## Checkpoint ownership rule
Only one helper writes or prepares the active Session Checkpoint for a turn. `dcoir-memory-preflight` owns checkpoint-need detection and is the default checkpoint writer/preparer for DCOIR. Do not delegate checkpoint creation, closeout, handoff, starter-prompt continuity, or active branch recovery to retired standalone session helpers. If a future continuity helper is explicitly introduced by the operator, treat that as a new source-authority decision and update Project Instructions, Airtable skill-state rows, SKILLROUTE rows, and this skill source before changing writers.

## Dynamic skill routing
Use Airtable `dcoir-memory-preflight` rows with key prefix `SKILLROUTE-` as the live installed-skill routing catalog. Do not hardcode the installed-skill list into this package.

When skill routing may apply:
1. Search for likely matching `SKILLROUTE-*` rows.
2. Use matching rows to decide whether to invoke, recommend, or pair a specialist skill.
3. If no row exists, say so and continue with the best bounded lane.
4. When a skill is added, removed, renamed, or materially repurposed, update the `SKILLROUTE-*` row set in Airtable rather than repackaging this skill just to refresh the catalog.
5. If a route points at a retired skill, do not invoke it. Use the replacement surface named in the route/registry when present and queue a route cleanup patch.

## Task-time route matrix
During compact task-time routing, default to these pairings unless live SKILLROUTE rows or task evidence say otherwise:
- continuity, starter prompts, checkpoint/closeout, branch transition, remember/capture language -> `dcoir-memory-preflight` as active continuity and checkpoint owner.
- Airtable schema, table/field id, select options, linked records, cleanup/migration/delete planning -> `dcoir-airtable-schema-cache` plus live Airtable readback.
- source authority, branch choice, approval gates, operator preference, proceed/ask/stop, drift, grouping/campaign decisions -> `dcoir-decision-policy`.
- generated code, workflow commands, env vars, secret-safe references, local config names -> `dcoir-local-config-registry-maintainer`.
- local Git, GitHub Desktop, speed lane, reusable PowerShell helpers, operator_tools, repo snapshots -> `dcoir-github-desktop-lane-advisor`.
- repo-layout zips, skill packages, GitHub Desktop bundles, bootstrap bundles, affected-file artifacts -> `dcoir-repo-packager`.
- validation plans, regression gates, readiness claims, evidence thresholds, post-change verification -> `dcoir-validation-orchestrator`.
- skill creation/update/packaging/troubleshooting -> `skill-creator` plus relevant DCOIR skill(s).

If more than one pairing applies, use the safety-critical order: continuity/checkpoint, schema-cache, decision-policy, lane/package specialists, validation-orchestrator.

## Retired-route drift signatures
Treat these exact names only as stale route signatures that require cleanup; never invoke them unless they are explicitly runtime-readable and selected for compatibility:
- `dcoir-session-resume` -> `dcoir-memory-preflight` continuity behavior
- `dcoir-session-tracker` -> `dcoir-memory-preflight` continuity behavior
- `dcoir-plan-tracker` -> direct Airtable Queue Control, Plans, and Work Items discipline
- `dcoir-source-authority-auditor` -> `dcoir-decision-policy`
- `dcoir-parity-verifier` -> GitHub `refresh-skill-parity-surfaces` workflow and `tools/skill_parity/`

## Canonical memory use
For GitHub/repo/tooling/validation task families, consult canonical task-memory only when relevant:
- `knowledge/task_memory/00_registry/task_memory_manifest.yaml`
- `knowledge/task_memory/30_compiled/fast_lookup.json`
- selected procedure or failure-signature files from the compiled index

Treat compiled indexes as routing aids, not sources of truth. Treat canonical procedure records as higher trust than chat recollection, but never stronger than the current control plane.

## Queue Control cross-check
If Queue Control is empty or stale while an active plan exists, classify the condition as `queue-control-drift` and repair or request repair through direct Airtable live-state handling before unrelated work continues. Do not route this to a retired planning helper. Do not let old chat memory, stale checkpoints, or GitHub todo text override Queue Control + Plans + Work Items.

## Re-anchor helper-chain posture
When invoked during startup or re-anchor, explicitly verify or report:
- this skill is the active continuity, resume, checkpoint, closeout, handoff, and starter-prompt owner;
- this preflight has run;
- `dcoir-airtable-schema-cache` is next before broad Airtable reads or schema-sensitive work;
- durable leftovers, ideas, and checkpoint state are carried through Session Checkpoints, Idea Inbox, Plans, Work Items, Queue Control, and this skill's checkpoint-ready payload flow;
- direct Airtable plan-state reconciliation replaces retired plan-tracker use;
- any further helper checks are selected by active lane context and `SKILLROUTE-*` rows, not by loading every full helper skill body.

## Post-blocker classification
Classify recovered lessons as one of:
- `one_off_only`
- `reusable_procedure_candidate`
- `reusable_limitation_candidate`
- `reusable_failure_signature_candidate`
- `reusable_helper_skill_or_process_doc_candidate`

Stage promotion-ready candidates in Session Checkpoints, Idea Inbox, Work Item notes, or the active Airtable branch record instead of silently writing into canonical memory. Do not route promotion capture to retired planning helpers.

## Deletion routing limits
Use Delete Queue for Airtable record/row deletion after dependency checks and approval. Do not use Delete Queue for whole-table/schema deletion. For table deletion, preserve/merge needed data first, have the operator manually delete the table, then verify absence through live schema readback and record evidence.

## Airtable local cache contract
Routine cache scope is intentionally narrow. Read `references/airtable_cache_contract.md` before relying on cached helper-memory, routing, preference, validation, packaging, config-name, queue, or checkpoint state.

On every explicit DCOIR re-anchor/startup recovery/resume-first recovery, refresh or recreate only the routine caches named in the contract. If a routine cache is missing, unreadable, stale, or inconsistent with live schema/table identity, refresh before use. Tables listed as conditional/live-read are not routine caches; read them from live Airtable only when the active task requires them. After this skill writes to a routine cached table or Session Checkpoint, refresh the relevant cache and verify the contract-defined freshness indicator. Local cache is advisory only; live Airtable remains authority for writes, deletes, migrations, and dependency-sensitive decisions.

## Output contract
Return these sections when acting as a full preflight:
1. Invocation mode.
2. Task family or recovered-lesson family.
3. Memory, `SKILLROUTE-*`, queue/checkpoint surfaces consulted.
4. Recommended lane or specialist skill.
5. Preconditions and anti-patterns.
6. Required verification.
7. Checkpoint need and checkpoint writer/preparer.
8. Buffered promotion candidate.
9. Re-anchor helper-chain posture when invoked during startup/re-anchor.
10. Best next move.

For compact task-time routing, return only: invocation mode, task family, consulted routing surfaces, skills to invoke now, lane, hard stops/preconditions, required verification, checkpoint need/writer, best next move.

## Hard rules
- Do not execute the main change by default; route and preflight first.
- Do not invent memory records or skill routes that were not consulted.
- Do not skip `dcoir-airtable-schema-cache` after startup/re-anchor preflight when broad Airtable reads or schema-sensitive work follow.
- Do not silently persist recovered lessons.
- Do not claim session-local buffered state is durable unless flushed to GitHub or Airtable.
- Do not treat UI-installed but unreadable skills as operational dependencies.
- Do not produce a closeout without a durable Session Checkpoint or checkpoint-ready payload unless the operator explicitly says not to checkpoint.
- Do not widen simple resume/status work into repo clone, archive download, raw web fetch, container execution, or local script execution unless the governed readable-text lane fails.
- Do not recreate one-off local scripts before checking `dcoir-github-desktop-lane-advisor` and Operator Tools Registry.

## References
Read these when needed:
- `references/task_time_skill_routing.md`
- `references/session_checkpoint_and_closeout_workflow.md`
- `references/airtable_cache_contract.md`
- `references/preflight_task_families.md`
- `references/post_blocker_classification.md`
- `references/session_buffer_flush_triggers.md`
- `references/github_memory_query_map.md`
- `references/airtable_memory_workflow.md`
- `references/airtable_operational_schema_contract.md`
