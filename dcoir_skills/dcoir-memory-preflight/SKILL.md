---
name: dcoir-memory-preflight
description: >- follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
  consult the canonical dcoir github task-memory bank before high-friction or known-procedure work and again after blocker recovery when a reusable lesson may need staging. after session-start resume bootstrap, also use this skill at the first substantive turn of every new africom_soc_ir or dcoir session to classify the immediate work family, consult airtable queue authority and three-division governance tables, improve skill routing, and avoid rediscovering the right lane later.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-memory-preflight|SKILL.md -->

# DCOIR Memory Preflight

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.


## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Purpose
Use this skill to consult canonical GitHub task memory before execution when the task family is likely to have a validated procedure, limitation, or failure signature already recorded in `knowledge/task_memory`.

This skill is now a closed-loop preflight layer, not only a front-end lookup step.
It should help:
- before high-friction execution so ChatGPT does not rediscover the right lane only after friction
- after blocker recovery so reusable lessons can be classified honestly and staged for later promotion instead of being silently forgotten or silently written into canonical memory

## Invocation modes

### 0. session-start bootstrap mode
Run this mode immediately after `dcoir-session-resume` on the first substantive AFRICOM_SOC_IR / DCOIR turn of every new session.

Use it to:
- classify the immediate work family early
- consult canonical memory before the branch drifts into execution
- surface the best bounded lane, anti-patterns, and likely flush triggers before high-friction work starts
- keep simple resume-status work on the bounded governed GitHub readable-text lane instead of drifting into unnecessary execution paths
- resolve the active queue branch from Airtable `Queue Control`, active `Work Items`, and active `Plans` before old GitHub todo surfaces bias the lane

### 1. pre-execution mode
Run this mode before choosing an execution lane when the task family is likely to have reusable canonical guidance.

### 2. post-blocker mode
Run this mode again after a blocker or failed attempt is successfully overcome when the lesson could improve:
- a repeatable workflow
- a reusable procedure
- a reusable limitation note
- a reusable failure signature
- helper-skill guidance
- governed process documentation

## Canonical memory sources
## Three-division governance preflight
For `session_start_bootstrap`, repo cleanup, skill routing, source-authority review, or governance-boundary work, consult the Airtable three-division tables as part of preflight before relying on older GitHub todo or ad hoc skill-memory assumptions.

Use silent Airtable reads only unless the operator explicitly asks to display a table.

Consult these tables when the task family matches:
- `Governance Control Plane`: authority-order, startup-chain, live queue authority, and GitHub/Airtable/Project role definitions
- `Repo Surface Registry`: major repo-surface keep/delete/move classification and replacement-surface notes
- `Skill State Registry`: available `dcoir-*` skills, startup relevance, invocation priority, and maintenance/parity status
- `Repo File Classification Detail`: optional file-level evidence for cleanup and migration review only

Preflight outcomes should mention these tables when they materially affect the lane. If the tables are missing or inaccessible, proceed bounded and say which table could not be checked rather than silently falling back to stale repo memory.

## Airtable queue-authority readback
When current branch priority or next-work-item order matters, read Airtable `Queue Control` first, then active Airtable `Work Items`, then active Airtable `Plans`.

During session-start bootstrap or re-anchor classification:
- use silent Airtable reads only
- do not use `display_records_for_table`
- prefer `search_records` or other non-display Airtable reads
- if a visible Airtable view might help, ask the operator first instead of displaying it automatically

Use GitHub todo files only as retired or historical context unless the migration explicitly needs them.

Read these in order when relevant:
1. `knowledge/task_memory/00_registry/task_memory_manifest.yaml`
2. `knowledge/task_memory/30_compiled/fast_lookup.json`
3. the specific canonical record files selected from the compiled index

Treat canonical procedure records as higher trust than chat recollection.
Treat compiled indexes as routing aids, not as sources of truth.

## When preflight is mandatory
- At the first substantive DCOIR turn of every new session, run this skill after `dcoir-session-resume` even if the operator did not explicitly ask for preflight.
Run this skill before choosing the execution lane when the task family includes any of these:
- GitHub readable-text create, update, overwrite, grouped edit, or delete work
- multi-file repo changes that should land in one bounded transaction
- branch-safe or branch-first repo work
- control-plane updates or structural repo changes
- bundle generation or packaging work
- skill maintenance, repair, or regression work
- coordinated multi-skill patch campaigns where the same validated procedure may shape several sibling updates
- GitHub Desktop manual repo-update bundle preparation or grouped manual governed-push delivery work
- GitHub Desktop manual repo-update bundle preparation or grouped governed pushes where the same preflight logic should shape the delivery lane
- any task where the operator asks to remove friction from a repeated GitHub workflow

Run this skill again after blocker recovery when the recovered lesson could matter beyond the current one-off fix.

## Core workflow
1. Re-anchor to Project Instructions, CP-00 as a pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`; read GitHub `CP-01`/`CP-02` only for repository-source tasks.
2. Determine whether the current use is `session_start_bootstrap`, `pre_execution`, or `post_blocker`.
3. Classify the task family or recovered-lesson family.
4. Identify the likely memory domain, preferring `github` first for repo work.
5. Read the task-memory manifest and compiled lookup.
6. Select the smallest relevant set of canonical records.
7. If the task is GitHub-family lane selection or connector-shape selection, include `GH-PROC-007` and `GH-PROC-008` when relevant. For GitHub Desktop manual repo-update deliveries or grouped governed pushes, also pair the grouped-transaction and post-write-verification records so the delivery lane stays aligned to the same governed write posture.
8. For `pre_execution`, summarize the recommended lane, preconditions, anti-patterns, and required verification.
9. For `post_blocker`, classify the recovered lesson as one of:
   - `one_off_only`
   - `reusable_procedure_candidate`
   - `reusable_limitation_candidate`
   - `reusable_failure_signature_candidate`
   - `reusable_helper_skill_or_process_doc_candidate`
10. Stage a promotion-ready candidate instead of silently writing into canonical memory.
11. When stateful helper skills are active, tell `dcoir-plan-tracker` and `dcoir-session-tracker` what blocker signature, failed attempt summary, successful mitigation, lesson classification, reusability notes, and flush trigger should stay buffered until flush time.
12. Surface the next flush-check trigger when buffered state exists.
13. Return one best next move and the consulted records that justify it.
14. For `session_start_bootstrap`, resolve the live queue branch from Airtable before suggesting the next execution lane, using silent Airtable reads only.
15. During `session_start_bootstrap`, do not use `display_records_for_table`; prefer `search_records` or other non-display Airtable reads.
16. If a visible Airtable view might help during startup classification, ask the operator first instead of displaying it automatically.
17. For `session_start_bootstrap` when the immediate task is simple resume-status or current-state reporting, keep the lane bounded to governed GitHub readable-text fetches for source authority, but let Airtable queue state decide ordinary next-work-item priority.

## GitHub-family defaults
For GitHub governed-readable-text work:
- prefer canonical GitHub procedures from `knowledge/task_memory/10_domains/github/procedures/`
- prefer the low-level git-object transaction lane for existing-file updates
- prefer one bounded multi-file transaction when multiple related existing-file changes or deletions belong together
- do not treat one-file-at-a-time writes as the default for grouped repo changes
- read the post-write verification procedure before claiming success
- when choosing a connector function shape or candidate lane, use the governed connector reference pack through `GH-PROC-008` but still treat the live connector surface as final authority

## Required companion routing
The surrounding workflow should use:
- `dcoir-decision-policy` to invoke this skill before high-friction execution and after blocker recovery when branch choice or reusable learning requires it
- `dcoir-plan-tracker` to preserve blocker signature, failed attempt summary, successful mitigation, promotion-ready candidate state, and deferred review counters for active plan work
- `dcoir-session-tracker` to preserve the same state in session-local continuity when no plan is active or when session export and later resume matter

## Session-local buffering and flush checks
This skill may participate in session-local write buffering, but buffered state is session-local only until it is flushed to GitHub or exported in a handoff artifact.

Preferred flush-check trigger points:
- before GitHub writes
- when a GitHub Desktop push or manual repo-update delivery is about to happen
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when a helper skill reports meaningful state drift

A valid flush/manicure review for this skill should surface:
- blocker signature or task family
- failed attempt summary
- successful mitigation
- lesson classification
- whether the lesson stays one-off, promotion-ready, or only buffered for now
- the next flush trigger
- one best next move

## Output contract
Return sections in this order:
1. Invocation mode
2. Task family or recovered-lesson family
3. Memory records consulted
4. Recommended lane or lesson classification
5. Preconditions and anti-patterns
6. Required verification
7. Buffered promotion candidate
8. Best next move

For one-off recoveries, say plainly that no reusable promotion candidate is recommended.
When a promotion candidate is recommended, preserve these fields explicitly whenever they are known:
- blocker signature
- failed attempt summary
- successful mitigation
- why the lesson appears reusable
- remain-local note when full promotion should wait
- next flush trigger

## Hard rules
- Do not execute the change by default; this skill is for preflight reasoning.
- Do not invent memory records that were not consulted.
- Do not skip canonical records when a matching task family exists.
- Do not let memory override the control plane.
- Do not silently write every recovered lesson into canonical memory.
- Do not claim buffered state is cross-session durable unless it was flushed to GitHub or exported in a handoff artifact.
- If no relevant canonical record exists, say that plainly and recommend the best bounded path.
- Do not widen simple resume-status work into repo clone, archive download, raw web fetch, container execution, or local script execution unless the primary governed readable-text lane actually fails or cannot resolve the drift gate.

## References
Read when needed:
- `references/preflight_task_families.md`
- `references/github_memory_query_map.md`
- `references/post_blocker_classification.md`
- `references/session_buffer_flush_triggers.md`

## Airtable collector and Gemini testing lane

When the immediate work family is collector testing, Gemini testing, live evaluation, or validation follow-through, classify the lane as `airtable-test-catalog-first`.

For that lane:
- consult Airtable table `Validation Test Cases` before proposing the test sequence
- use the table to identify existing test IDs, commands or methods, pass criteria, fail criteria, and known partial/failing areas
- avoid rebuilding the test plan from chat memory when the Airtable catalog already covers the branch
