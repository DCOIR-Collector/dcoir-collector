---
name: dcoir-memory-preflight
description: consult canonical dcoir task memory, airtable governance tables, helper-memory rows, and dynamic skill-routing rows before dcoir task execution and after blocker recovery. use for session-start preflight, re-anchor helper-chain checks, task-time skill applicability checks, execution-lane choice, blocker learning, github/github desktop/tooling friction, skill-routing checks, airtable authority/schema-sensitive work, and cases where any specialist dcoir helper skill may apply.
---

<!-- skill-marker: updated-skill|20260505T073000Z|task-time-routing-strengthening|in-session-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260504T181500Z|cache-scope-narrowing-stale-reference-scrub|source-update|dcoir-memory-preflight|SKILL.md -->

<!-- skill-marker: updated-skill|20260504T171500Z|airtable-local-cache-contract|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260504T163500Z|session-manager-strengthening|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260504T111000Z|plan-tracker-retirement-direct-airtable|in-session-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T173000Z|reanchor-helper-invocation-rule|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T111500Z|airtable-display-allowed-when-useful|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260501T193500Z|queue-control-cross-check|source-update|dcoir-memory-preflight|SKILL.md -->

# DCOIR Memory Preflight

## Project gate
Use only inside AFRICOM_SOC_IR / DCOIR. This skill is a pre-execution and post-blocker routing layer. It does not execute the main change by default and does not override Airtable or source authority.

## Invocation modes

### 0. session-start bootstrap and re-anchor mode
Run as the required preflight step in the `dcoir-session-manager` startup/re-anchor chain on the first substantive DCOIR turn and during explicit DCOIR re-anchor requests.

The current helper chain is:
1. `dcoir-session-manager` establishes Project Instructions, CP-00 pointer, Governance Control Plane, and active session branch posture.
2. `dcoir-memory-preflight` classifies the work family, consults durable routing memory, and checks `SKILLROUTE-*` rows.
3. `dcoir-airtable-schema-cache` validates schema readiness before broad Airtable reads or schema-sensitive writes.
4. Active lane helpers are selected from Airtable state, live installed skills, and `SKILLROUTE-*` rows.

Use this mode to:
- classify the immediate work family;
- consult relevant canonical memory before execution starts;
- resolve branch priority from Airtable Queue Control, active Plans, and Work Items;
- search dynamic `SKILLROUTE-*` rows for specialist helper routing;
- identify stale routes for retired skills and route them to current replacements;
- surface the best bounded lane, anti-patterns, preconditions, and required verification;
- report the re-anchor helper-chain posture.

### 1. pre-execution mode
Run before choosing an execution lane when the task family is likely to have reusable guidance, validated procedure, friction pattern, or specialist helper skill.

### 2. post-blocker mode
Run after a blocker or failed attempt is recovered when the lesson could improve a repeatable workflow, reusable procedure, limitation note, failure signature, helper skill, or process document.


### 3. compact task-time routing mode
Run as a lightweight applicability check before DCOIR execution whenever it is plausible that any current DCOIR helper skill, Airtable authority surface, local config registry, operator tool, validation gate, or execution lane matters.

Use compact task-time routing mode to answer only:
1. Which task family is this?
2. Which SKILLROUTE rows, operator preferences, helper-memory rows, or active work records are relevant?
3. Which skill(s) must fire now before execution?
4. Which lane is safest/effective: in-session Airtable, GitHub connector/workflow, GitHub Desktop, reusable operator tool, manual review, validation-only, or no-execution planning?
5. What preconditions, anti-patterns, and verification apply?
6. Should `dcoir-session-manager` create/prepare a checkpoint because the task changes branch/lane/state, crosses a milestone, resolves a blocker, or approaches closeout?

Do not load every full helper skill body by default. Select specialists from live SKILLROUTE rows, installed skill descriptions, Admin Registry skill_state rows, Operator Preferences, active Plans/Work Items, and task context.

## Mandatory triggers
Run this skill before execution, not only at startup, when the task involves:
- GitHub readable-text create/update/delete work;
- grouped repo edits or packaging;
- control-plane, startup, queue, or authority changes;
- skill maintenance, repair, regression, or packaging;
- GitHub Desktop/manual bundle preparation;
- repeated local tool, connector, or Actions workflow friction;
- artifact intake, validation orchestration, authority review, or Airtable schema-sensitive work;
- any task where a specialist DCOIR helper skill may apply;
- any DCOIR task where the assistant is about to answer from memory without checking whether a current skill, SKILLROUTE row, operator preference, helper-memory row, active plan/work item, local configuration name, validation gate, or execution lane should influence the result.

Frequent-fire rule: if unsure whether another DCOIR skill applies, run compact task-time routing mode first. Prefer a short routing check over skipping a relevant skill.

Run this skill again after blocker recovery when the recovered lesson could matter beyond the current one-off fix.

## Airtable-first preflight
When branch priority, startup posture, or next work matters:
1. Read Airtable Queue Control first.
2. Cross-check active Plans and active/todo Work Items.
3. Consult Governance Control Plane when authority/order matters.
4. Consult Operator Preferences when workflow branching or display behavior matters.
5. Consult Admin Registry and helper-memory tables when skill-state, installed-skill awareness, or routing matters.
6. Consult Repo Surface Registry before repo cleanup, source-role changes, or keep/delete claims.
7. Consult Local Configuration Registry when generated code, operator-side tools, workflow scripts, or environment variable names are in scope.

During automatic startup/re-anchor, use compact non-display Airtable reads. During execution/audit/verification, Airtable display views may be used when they materially improve correctness or when operator approval/preference already allows it.

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
- session continuity, starter prompts, checkpoint/closeout, branch transition, remember/capture language -> `dcoir-session-manager`.
- Airtable schema, table/field id, select options, linked records, cleanup/migration/delete planning -> `dcoir-airtable-schema-cache` plus live Airtable readback.
- source authority, branch choice, approval gates, operator preference, proceed/ask/stop, drift, grouping/campaign decisions -> `dcoir-decision-policy`.
- generated code, workflow commands, env vars, secret-safe references, local config names -> `dcoir-local-config-registry-maintainer`.
- local Git, GitHub Desktop, speed lane, reusable PowerShell helpers, operator_tools, repo snapshots -> `dcoir-github-desktop-lane-advisor`.
- repo-layout zips, skill packages, GitHub Desktop bundles, bootstrap bundles, affected-file artifacts -> `dcoir-repo-packager`.
- validation plans, regression gates, readiness claims, evidence thresholds, post-change verification -> `dcoir-validation-orchestrator`.
- skill creation/update/packaging/troubleshooting -> `skill-creator` plus relevant DCOIR skill(s).

If more than one pairing applies, invoke the most safety-critical skill first: session-manager for continuity, schema-cache for Airtable structure, decision-policy for gates/authority, then lane/package/validation specialists.

## Retired-route drift signatures
Treat these exact names only as stale route signatures that require cleanup; never invoke them. Prefer live `SKILLROUTE-*` rows when available.
- `dcoir-session-resume` -> `dcoir-session-manager`
- `dcoir-session-tracker` -> `dcoir-session-manager`
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
- `dcoir-session-manager` has run or is the immediately preceding step;
- this preflight has run;
- `dcoir-airtable-schema-cache` is next before broad Airtable reads or schema-sensitive work;
- durable leftovers, ideas, and checkpoint state are carried through `dcoir-session-manager`, Session Checkpoints, Idea Inbox, Plans, Work Items, and Queue Control;
- direct Airtable plan-state reconciliation replaces conditional plan-tracker use;
- any further helper checks are selected by active lane context and `SKILLROUTE-*` rows, not by loading every full helper skill body.

## Post-blocker classification
Classify recovered lessons as one of:
- `one_off_only`
- `reusable_procedure_candidate`
- `reusable_limitation_candidate`
- `reusable_failure_signature_candidate`
- `reusable_helper_skill_or_process_doc_candidate`

Stage promotion-ready candidates in `dcoir-session-manager` closeout flow, Session Checkpoints, Idea Inbox, Work Item notes, or the active Airtable branch record instead of silently writing into canonical memory. Do not route promotion capture to retired planning helpers.

## Deletion routing limits
Use Delete Queue for Airtable record/row deletion after dependency checks and approval. Do not use Delete Queue for whole-table/schema deletion. For table deletion, preserve/merge needed data first, have the operator manually delete the table, then verify absence through live schema readback and record evidence.

## Retired planning-helper handling
Retired planning helpers are no longer specialist routing targets. Preserve only direct Airtable live-state discipline here:
- Use `Queue Control`, `Plans`, and `Work Items` as the live branch/task authority.
- For queue-control drift, repair or request repair directly in Airtable rather than routing to a standalone plan-tracker skill.
- For Work Item or active-task changes, require verification against the parent Plan and Queue Control before moving to unrelated work.
- For recovered blocker or continuity lessons, stage the carry-forward through `dcoir-session-manager`, Session Checkpoints, Idea Inbox, Work Item notes, or another active Airtable authority surface.
- Treat stale GitHub planning-helper memory as promoted-history/source-basis only, not live task authority.

## Airtable local cache contract
Routine cache scope is intentionally narrow: cache only the high-call tables named as routine in the contract; use live Airtable reads for conditional tables.

This skill is Airtable-backed only for the high-call routine tables named in `references/airtable_cache_contract.md`. Read that contract before relying on cached helper-memory, routing, preference, validation, packaging, or configuration-name state.

On every explicit DCOIR re-anchor/startup recovery/resume-first recovery, refresh or recreate only the routine caches named in the contract. If a routine cache is missing, unreadable, stale, or inconsistent with live schema/table identity, refresh before use. Tables listed as conditional/live-read are not routine caches; read them from live Airtable only when the active task requires them. After this skill writes to a routine cached table, refresh the cache and verify the contract-defined freshness indicator. Local cache is advisory only; live Airtable remains authority for writes, deletes, migrations, and dependency-sensitive decisions.

## Output contract
Return these sections when acting as a full preflight:
1. Invocation mode.
2. Task family or recovered-lesson family.
3. Memory and `SKILLROUTE-*` rows consulted.
4. Recommended lane or specialist skill.
5. Preconditions and anti-patterns.
6. Required verification.
7. Buffered promotion candidate.
8. Re-anchor helper-chain posture when invoked during startup/re-anchor.
9. Best next move.

For compact task-time routing, return only: invocation mode, task family, consulted routing surfaces, skills to invoke now, lane, hard stops/preconditions, required verification, checkpoint need, best next move.

## Hard rules
- Do not execute the main change by default; route and preflight first.
- Do not invent memory records or skill routes that were not consulted.
- Do not skip `dcoir-airtable-schema-cache` after startup/re-anchor preflight.
- Do not silently persist recovered lessons.
- Do not claim session-local buffered state is durable unless flushed to GitHub or Airtable.
- Do not widen simple resume/status work into repo clone, archive download, raw web fetch, container execution, or local script execution unless the governed readable-text lane fails.
- Do not recreate one-off local scripts before checking `dcoir-github-desktop-lane-advisor` and Operator Tools Registry.
