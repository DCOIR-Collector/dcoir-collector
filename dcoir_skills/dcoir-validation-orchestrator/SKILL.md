---
name: dcoir-validation-orchestrator
description: build explicit validation plans, task-time validation gates, regression gates, evidence thresholds, readiness claims, write gate checks, post-change verification, install/readback checks, and live/readback validation for dcoir changes, skill updates, packages, airtable cleanup, github workflows, and operational workflows. use before declaring readiness, after patches, when evidence is incomplete, when validation planning/execution applies, or when a proposed airtable/governance write needs pass/fail/conditional-pass/stop-escalate review before execution.
---
<!-- skill-marker: updated-skill|20260507T081800Z|write-gate-temporary-fold-in|in-session-update|dcoir-validation-orchestrator|SKILL.md -->
<!-- skill-marker: updated-skill|20260505T090000Z|task-time-validation-gate-strengthening|in-session-update|dcoir-validation-orchestrator|SKILL.md -->


<!-- skill-marker: updated-skill|20260504T181500Z|cache-scope-narrowing-stale-reference-scrub|source-update|dcoir-validation-orchestrator|SKILL.md -->

<!-- skill-marker: updated-skill|20260504T171500Z|airtable-local-cache-contract|source-update|dcoir-validation-orchestrator|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T111500Z|airtable-display-allowed-when-useful|source-update|dcoir-validation-orchestrator|SKILL.md -->
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-validation-orchestrator|SKILL.md -->

# DCOIR Validation Orchestrator

## Airtable operational schema alignment
Airtable cutover and skill cutover are complete. Use the current Airtable schema as live operational authority, not historical migration or cleanup plans.

Use `references/airtable_operational_schema_contract.md` for durable rules covering:
- current live authority tables
- idea-to-work-item-to-plan promotion
- Delete Queue deletion requests and dependency order
- DCOIR Lifecycle Ledger readback/history events
- Local Configuration Registry secret-safe configuration references

Do not assume retired or absent tables exist. In particular, do not require `Plan Tasks`, `Plan Checkpoints`, `Skill State Registry`, `Schema Registry`, `Tracking Registry`, `Repo File Coverage Detail`, or `Retained Repo Manifest` unless live Airtable schema readback proves the table exists for the current task.

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Work Items for task execution`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, explicit repo cleanup/source-role review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo Surface Registry supporting evidence`, `Repo Surface Registry retained-state evidence`, and active plan state before stopping.


## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Use this skill to turn a DCOIR change, workflow, campaign, or inventory-derived gap area into an explicit validation plan.


## Task-time validation gate
Use this skill at task time, not only when the operator explicitly asks for a validation plan, whenever DCOIR work will make or imply a readiness, correctness, installability, package-validity, regression, evidence, or verification claim.

Frequent-fire rule: if a DCOIR response will say that something is valid, installed, ready, verified, complete, safe to use, regression-covered, package-clean, schema-safe, or successfully changed, run a compact validation gate first. Prefer a small validation gate over unsupported readiness language.

Hard triggers:
- after any helper-skill patch, package, marker/readback check, install confirmation, or source/parity update;
- before claiming live readiness, package validity, installability, no-wrapper-root compliance, affected-file-only compliance, Airtable write success, GitHub readback success, workflow success, or schema-cleanup success;
- before or after GitHub workflow/chatgpt-exec execution, GitHub Desktop/manual bundle use, reusable operator-tool use, or local execution guidance when evidence will be required;
- when a task touches validation evidence, validation test cases, regression gates, acceptance criteria, evidence thresholds, or readiness status;
- when a blocker/failure is recovered and the recovery should become a repeatable test, guardrail, or evidence requirement;
- when the operator reports an install/package/readback problem, malformed ZIP, missing marker, stale skill readback, or incomplete verification.

Compact validation gate output should identify: validation target; phase (`pre-live`, `post-patch`, `failed-run`, `routine`, `install-readback`, or `evidence-gap`); evidence available; evidence missing; minimum tests/checks; companion skills; whether Airtable Validation Evidence/Test Cases or helper-memory should be updated; and the safest readiness statement allowed.

Do not claim readiness from inspection alone when execution, generated output, installed-skill readback, package inspection, Airtable readback, GitHub readback, or workflow logs can reasonably be checked. If full validation is blocked, state the bounded validation actually performed and the remaining evidence gap.

Read `references/task_time_validation_gate.md` for compact trigger/output rules.


## Temporary Airtable Write Gate fold-in
During the DCOIR cleanup/restructure plan, this skill temporarily owns the validation-only Airtable Write Gate because the standalone `dcoir-airtable-write-gate` skill may not be runtime-readable when the session skill budget is constrained.

Use this fold-in before any proposed DCOIR Airtable or governance mutation needs a safety decision. It returns one of: `PASS`, `CONDITIONAL_PASS`, `FAIL`, or `STOP_ESCALATE`. It does not execute writes, cleanup, deletion, merge, schema, repo, skill, workflow, automation, or Delete Queue actions.

Use `references/airtable_write_gate.md` for the manual contract. When a structured proposed-action JSON is available, run:

```bash
python scripts/evaluate_write_gate.py --input proposed_action.json --output gate_report.json
```

Treat this as a temporary scaffold responsibility. At plan conclusion, remove or split this Write Gate fold-in during scaffold cleanup after the final Write Gate architecture is chosen.

## Core workflow
1. Resolve the current control plane first.
2. Identify the changed targets, workflow area, or campaign scope.
3. Classify the validation phase: `pre-live`, `post-patch`, `failed-run`, or `routine`.
4. Read `references/validation_scenario_library.md`.
5. Run `scripts/emit_validation_plan.py`.
6. If the current branch includes session-memory-enabled or buffer-capable skills and a governed push is likely, include pre-push flush and post-push cleanup validation in the plan.
7. When the operator prefers batched manual GitHub/Desktop updates, group compatible skill changes into bounded delivery waves and include package-cleanliness plus installability checks for the whole batch before surfacing the manual update step.
8. When the validation state changed materially, use Airtable table `dcoir-validation-orchestrator` to read or update durable helper memory as described in `references/airtable_memory_workflow.md`, reducing operator burden to the smallest bounded manual Airtable action only when the connector cannot safely complete the write.
9. Return the gates, smoke tests, deep-regression set, evidence requirements, live-readiness criteria, buffered validation state, and any Airtable-memory change that matters.

## Validation regime ownership
This skill now owns:
- end-to-end validation planning
- edge-case and failure-gate planning
- skill deep-dive validation planning
- docs/readme/knowledge alignment validation planning
- packager live-project validation planning
- session-memory pre-push contract validation planning
- coordinated multi-skill delivery-wave validation planning

## Fast Airtable helper-memory read contract

Use the skill-specific Airtable helper-memory table directly when this skill needs durable helper memory.

- Airtable base id: `appM4KSwnVf3G3OTK`
- Airtable table name: `dcoir-validation-orchestrator`
- Airtable table id: `tbls9O1B0Rs8YvTAj`
- Primary lookup/dedupe field: `validation_entry_id`

Read pattern:
- Use the Airtable connector with `baseId="appM4KSwnVf3G3OTK"` and `tableId="tbls9O1B0Rs8YvTAj"` when supported; use the table name only as fallback.
- Prefer non-display Airtable reads such as `search_records` or direct reads for routine lookup and automatic startup. Use `display_records_for_table` when field completeness, duplicate comparison, or verification materially benefits from a grid view, or when the operator has already approved visible Airtable display; summarize displayed evidence in chat.
- Pull only this skill's own helper-memory table for routine memory lookup. Do not scan a unified helper-memory table and filter by skill.
- Keep helper-memory rows human-readable and update this same table when material reusable state changes.
- If the connector cannot query by tableId, state the limitation and use the table name `dcoir-validation-orchestrator` without switching to a merged memory table.

## Airtable-backed skill memory
Use Airtable table `dcoir-validation-orchestrator` when reusable validation-plan state should persist outside the current chat.

Airtable skill-memory layout:
- live table: `dcoir-validation-orchestrator`
- source_basis history: migrated GitHub memory rows may cite former repo paths

Use this memory surface for helper working state such as:
- active validation plans that are still in flight
- reusable gates or evidence thresholds worth carrying into the next pass
- unresolved evidence gaps that should remain visible before live-use claims
- campaign coverage notes for broad validation branches
- buffered validation deltas that should land in the next suitable grouped write
- deferred review counters or countdown-gated decisions that affect later validation timing

Rules:
- re-anchor to Project Instructions, CP-00 as a pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`; read GitHub `CP-01`/`CP-02` only for repository-source tasks before reading or writing Airtable memory rows
- treat the Airtable memory table as helper working state only, not control-plane authority
- keep one canonical Airtable row set for live memory and update it directly when connector access permits
- if Airtable access is blocked, say that plainly and reduce the operator burden to the smallest bounded manual Airtable action

When rendering memory content locally, prefer Airtable memory rows; use migrated source-basis files only for historical comparison.

## Hard rules
- Default to deep regression for anything testable before live use and after every patch.
- Do not claim live readiness from inspection alone when execution or generated outputs can be tested.
- Keep the plan bounded to the affected area when the scope is narrow.
- Expand to cross-skill or cross-bundle regression when the change is structural, runtime-affecting, authority-adjacent, or inventory-wide.
- When session-memory-enabled or buffer-capable skills are in scope, include pre-push flush and post-push cleanup checks instead of assuming that state will promote itself.
- When a bounded multi-skill batch is being prepared for manual GitHub/Desktop application, include grouped installability, package-cleanliness, and no-wrapper-root delivery checks instead of validating each changed skill in isolation only.
- Keep the canonical Airtable memory table human-readable and continuously updated after material validation-state changes when Airtable access is available.


- After operator confirmation of a skill install, verify installed `SKILL.md` marker readback and any added reference/resource files before proceeding to the next skill or task.
- Treat malformed ZIP/package reports, missing markers, stale readback, and unsupported readiness claims as validation triggers, not as chat-only notes.

## Airtable local cache contract
Routine cache scope is intentionally narrow: cache only the high-call tables named as routine in the contract; use live Airtable reads for conditional tables.

This skill is Airtable-backed only for the high-call routine tables named in `references/airtable_cache_contract.md`. Read that contract before relying on cached helper-memory, routing, preference, validation, packaging, or configuration-name state.

On every explicit DCOIR re-anchor/startup recovery/resume-first recovery, refresh or recreate only the routine caches named in the contract. If a routine cache is missing, unreadable, stale, or inconsistent with live schema/table identity, refresh before use. Tables listed as conditional/live-read are not routine caches; read them from live Airtable only when the active task requires them. After this skill writes to a routine cached table, refresh the cache and verify the contract-defined freshness indicator. Local cache is advisory only; live Airtable remains authority for writes, deletes, migrations, and dependency-sensitive decisions.

## References
- `references/validation_scenario_library.md`
- `references/task_time_validation_gate.md`
- `references/airtable_write_gate.md` for temporary validation-only Write Gate checks
- `references/airtable_memory_workflow.md`
- `../project_discovery_contract.json` when current repository or helper-memory naming assumptions matter

## Airtable validation catalog default

For collector and Gemini manual validation branches, use Airtable table `Validation Test Cases` as the default dynamic test catalog.

When this table is available:
- start by mapping the current validation branch to existing test IDs
- update observed status and evidence as tests are executed
- add new rows when the branch introduces new feature coverage, new regressions, or new mandatory comparison methods
- retire or narrow stale rows when the implementation surface changes materially

Keep GitHub as the authority for executable source, packaging files, workflows, and governed readable docs. Airtable owns the dynamic manual-testing workflow state.
