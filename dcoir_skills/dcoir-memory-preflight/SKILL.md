---
name: dcoir-memory-preflight
description: consult canonical dcoir task memory, airtable governance tables, helper-memory rows, and dynamic skill-routing rows before high-friction work and after blocker recovery. use for dcoir session-start preflight, re-anchor helper-chain checks, execution-lane choice, blocker learning, github desktop workflow friction, skill-routing checks, and cases where a specialist dcoir helper skill may apply.
---
<!-- skill-marker: updated-skill|20260503T173000Z|reanchor-helper-invocation-rule|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T111500Z|airtable-display-allowed-when-useful|source-update|dcoir-memory-preflight|SKILL.md -->
<!-- skill-marker: updated-skill|20260501T193500Z|queue-control-cross-check|source-update|dcoir-memory-preflight|SKILL.md -->

# DCOIR Memory Preflight

## Project gate
Use only inside AFRICOM_SOC_IR / DCOIR. This skill is a pre-execution and post-blocker routing layer. It does not execute the main change by default and does not override Airtable or source authority.

## Invocation modes

### 0. session-start bootstrap and re-anchor mode
Run immediately after `dcoir-session-resume` on the first substantive DCOIR turn and during explicit DCOIR re-anchor requests.

This is one required step in the re-anchor helper chain. It must be followed by `dcoir-airtable-schema-cache` schema readiness before broad Airtable reads or schema-sensitive work, then by session/plan recovery and additional helper checks selected from active lane context and `SKILLROUTE-*` rows.

Use this mode to:
- classify the immediate work family;
- consult relevant canonical memory before execution starts;
- resolve branch priority from Airtable Queue Control, active Plans, and Work Items;
- search dynamic `SKILLROUTE-*` rows for specialist helper routing;
- surface the best bounded lane, anti-patterns, preconditions, and required verification;
- report the re-anchor helper-chain posture.

### 1. pre-execution mode
Run before choosing an execution lane when the task family is likely to have reusable guidance, validated procedure, friction pattern, or specialist helper skill.

### 2. post-blocker mode
Run after a blocker or failed attempt is recovered when the lesson could improve a repeatable workflow, reusable procedure, limitation note, failure signature, helper skill, or process document.

## Mandatory triggers
Run this skill before execution when the task involves:
- GitHub readable-text create/update/delete work;
- grouped repo edits or packaging;
- control-plane, startup, queue, or authority changes;
- skill maintenance, repair, regression, or packaging;
- GitHub Desktop/manual bundle preparation;
- repeated local tool, connector, or Actions workflow friction;
- artifact intake, validation orchestration, source authority review, or Airtable schema-sensitive work;
- any task where a specialist DCOIR helper skill may apply.

Run this skill again after blocker recovery when the recovered lesson could matter beyond the current one-off fix.

## Airtable-first preflight
When branch priority, startup posture, or next work matters:
1. Read Airtable Queue Control first.
2. Cross-check active Plans and active/todo Work Items.
3. Consult Governance Control Plane when authority/order matters.
4. Consult Operator Preferences when workflow branching or display behavior matters.
5. Consult Admin Registry and helper-memory tables when skill-state, installed-skill awareness, or routing matters.
6. Consult Repo Surface Registry before repo cleanup, source-role changes, or keep/delete claims.

During automatic startup/re-anchor, use compact non-display Airtable reads. During execution/audit/verification, Airtable display views may be used when they materially improve correctness or when operator approval/preference already allows it.

## Dynamic skill routing
Use Airtable `dcoir-memory-preflight` rows with key prefix `SKILLROUTE-` as the live installed-skill routing catalog. Do not hardcode the installed-skill list into this package.

When skill routing may apply:
1. Search for likely matching `SKILLROUTE-*` rows.
2. Use matching rows to decide whether to invoke, recommend, or pair a specialist skill.
3. If no row exists, say so and continue with the best bounded lane.
4. When a skill is added, removed, renamed, or materially repurposed, update the `SKILLROUTE-*` row set in Airtable rather than repackaging this skill just to refresh the catalog.

## Canonical memory use
For GitHub/repo/tooling/validation task families, consult canonical task-memory only when relevant:
- `knowledge/task_memory/00_registry/task_memory_manifest.yaml`
- `knowledge/task_memory/30_compiled/fast_lookup.json`
- selected procedure or failure-signature files from the compiled index

Treat compiled indexes as routing aids, not sources of truth. Treat canonical procedure records as higher trust than chat recollection, but never stronger than the current control plane.

## Queue Control cross-check
If Queue Control is empty or stale while an active plan exists, classify the condition as `queue-control-drift` and recommend/route repair by `dcoir-plan-tracker` before unrelated work continues. Do not let old chat memory, stale checkpoints, or GitHub todo text override Queue Control + Plans + Work Items.

## Re-anchor helper-chain posture
When invoked during startup or re-anchor, explicitly verify or report:
- `dcoir-session-resume` has run or is the immediately preceding step;
- this preflight has run;
- `dcoir-airtable-schema-cache` is next before broad Airtable reads or schema-sensitive work;
- session-tracker and conditional plan-tracker remain part of the chain;
- any further helper checks are selected by active lane context and `SKILLROUTE-*` rows, not by loading every full helper skill body.

## Post-blocker classification
Classify recovered lessons as one of:
- `one_off_only`
- `reusable_procedure_candidate`
- `reusable_limitation_candidate`
- `reusable_failure_signature_candidate`
- `reusable_helper_skill_or_process_doc_candidate`

Stage promotion-ready candidates for plan-tracker or session-tracker instead of silently writing into canonical memory.

## Output contract
Return these sections when acting as a preflight:
1. Invocation mode.
2. Task family or recovered-lesson family.
3. Memory and `SKILLROUTE-*` rows consulted.
4. Recommended lane or specialist skill.
5. Preconditions and anti-patterns.
6. Required verification.
7. Buffered promotion candidate.
8. Re-anchor helper-chain posture when invoked during startup/re-anchor.
9. Best next move.

## Hard rules
- Do not execute the main change by default; route and preflight first.
- Do not invent memory records or skill routes that were not consulted.
- Do not skip `dcoir-airtable-schema-cache` after startup/re-anchor preflight.
- Do not silently persist recovered lessons.
- Do not claim session-local buffered state is durable unless flushed to GitHub or Airtable.
- Do not widen simple resume/status work into repo clone, archive download, raw web fetch, container execution, or local script execution unless the governed readable-text lane fails.
- Do not recreate one-off local scripts before checking `dcoir-github-desktop-lane-advisor` and Operator Tools Registry.
