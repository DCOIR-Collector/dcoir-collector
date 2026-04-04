---
name: dcoir-memory-preflight
description: consult the canonical dcoir github task-memory bank before high-friction or known-procedure work and again after blocker recovery when a reusable lesson may need staging. after the session-start resume bootstrap, also use this skill at the first substantive turn of every new africom_soc_ir or dcoir session to classify the immediate work family and avoid rediscovering the right lane later. use when dcoir work involves github read/write/update/delete operations, grouped repo edits, file removals, control-plane changes, packaging or bundle generation, skill maintenance, structural refactors, repeated high-friction workflows, coordinated multi-skill campaigns, or recovered failures that may justify a reusable procedure, limitation, failure-signature, or helper-skill/process update candidate.
---

# DCOIR Memory Preflight

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
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
- any task where the operator asks to remove friction from a repeated GitHub workflow

Run this skill again after blocker recovery when the recovered lesson could matter beyond the current one-off fix.

## Core workflow
1. Re-anchor to Project Instructions, then CP-01, then CP-02.
2. Determine whether the current use is `session_start_bootstrap`, `pre_execution`, or `post_blocker`.
3. Classify the task family or recovered-lesson family.
4. Identify the likely memory domain, preferring `github` first for repo work.
5. Read the task-memory manifest and compiled lookup.
6. Select the smallest relevant set of canonical records.
7. If the task is GitHub-family lane selection or connector-shape selection, include `GH-PROC-007` and `GH-PROC-008` when relevant.
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

## References
Read when needed:
- `references/preflight_task_families.md`
- `references/github_memory_query_map.md`
- `references/post_blocker_classification.md`
- `references/session_buffer_flush_triggers.md`
