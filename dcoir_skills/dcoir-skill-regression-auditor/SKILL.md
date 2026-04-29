---
name: dcoir-skill-regression-auditor
description: plan and audit deeper regression for dcoir skills before live use and after every patch.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-skill-regression-auditor|SKILL.md -->

# DCOIR Skill Regression Auditor

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

Use this skill to define and audit deeper regression for DCOIR skills.

## Mandatory trigger cases
Run this skill:
- after every helper-skill create
- after every helper-skill update or repair
- before treating a patched helper skill as ready for broader use, workflow promotion, or packaging follow-through
- when a bounded coordinated multi-skill patch cycle needs explicit regression coverage for each materially changed skill

In a broad helper-skill patch campaign, regression-test `dcoir-skill-regression-auditor` first before using it as evidence on other skills.

## Core workflow
1. Identify the skill or skills under test.
2. Decide whether self-test-first is required because the current cycle is a broad helper-skill patch campaign.
3. Read `references/regression_fixture_catalog.md`.
4. Read `references/skill_test_harness_definitions.md`.
5. Read `references/package_hygiene_workflow.md`.
6. Run `scripts/plan_skill_regression.py`.
7. Produce the regression suites, failure gates, artifact checks, package-cleanliness checks, preventive bytecode-suppression steps, cleanup steps, readiness criteria, campaign ordering, and grouped regression-bundle expectations.
8. Before packaging or handing back any updated skill zip, run `scripts/clean_skill_runtime_residue.py --clean` against every materially changed skill folder and rerun `scripts/clean_skill_runtime_residue.py --check` so residue prevention is explicit instead of ad hoc.
11. Use the skill editor as primary truth for that marker confirmation when it is available. Treat assistant-side readback as secondary and potentially delayed.
12. If regression revealed a blocker that is later overcome, invoke `dcoir-memory-preflight` again when the recovered lesson could improve a reusable procedure, limitation note, failure signature, or helper-skill/process guidance.
13. Keep regression-state changes session-local until the next suitable flush-check trigger when grouped GitHub writes are preferred.
14. When the regression-state changed materially and the write lane is safe, use the GitHub connector directly to read or update the canonical Airtable memory table defined in `references/airtable_memory_workflow.md`.
15. Return the regression suites, failure gates, artifact checks, readiness criteria, campaign scope, buffer state, and any Airtable-memory change that matters.

## Session-local buffer behavior
This skill may stage regression memory, fixture deltas, follow-through notes, or campaign-scope notes session-locally before GitHub flush time.

Preferred flush-check trigger points:
- before any GitHub write
- after blocker resolution
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift

Truth rule:
- buffered regression state is session-local only until it is flushed to GitHub or exported in a handoff artifact

A valid flush/manicure review for this skill should surface:
- campaign scope or single-skill scope
- what regression state is buffered
- what is safe to flush now
- what should remain buffered for now
- the next flush trigger
- one best next move

## Fast Airtable helper-memory read contract

Use the skill-specific Airtable helper-memory table directly when this skill needs durable helper memory.

- Airtable base id: `appM4KSwnVf3G3OTK`
- Airtable table name: `dcoir-skill-regression-auditor`
- Airtable table id: `tblHAa3e4R6F4LFhb`
- Primary lookup/dedupe field: `regression_entry_id`

Read pattern:
- Use the Airtable connector with `baseId="appM4KSwnVf3G3OTK"` and `tableId="tblHAa3e4R6F4LFhb"` when supported; use the table name only as fallback.
- Use non-display Airtable reads such as `search_records`, direct table reads, or equivalent connector calls. Do not ask the operator whether to display an interactive Airtable view.
- Pull only this skill's own helper-memory table for routine memory lookup. Do not scan a unified helper-memory table and filter by skill.
- Keep helper-memory rows human-readable and update this same table when material reusable state changes.
- If the connector cannot query by tableId, state the limitation and use the table name `dcoir-skill-regression-auditor` without switching to a merged memory table.

## Airtable-backed skill memory
Use Airtable table `dcoir-skill-regression-auditor` when reusable regression-planning state should persist outside the current chat.

Airtable skill-memory layout:
- live table: `dcoir-skill-regression-auditor`
- source-basis history: migrated rows may cite former repo memory paths

Use this memory surface for helper working state such as:
- tracked skills with active regression follow-through
- fixture baselines worth reusing after later patches
- failure gates that should remain visible across packaging cycles
- buffered but unflushed regression deltas awaiting a later grouped write
- coordinated campaign coverage summaries when a bounded multi-skill patch cycle is in flight

Rules:
- re-anchor to Project Instructions, CP-00 as a pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`; read GitHub `CP-01`/`CP-02` only for repository-source tasks before reading or writing Airtable memory rows
- treat the Airtable memory table as helper working state only, not control-plane authority
- keep one canonical Airtable row set for live memory and update it directly when connector access permits
- if Airtable access is blocked, say that plainly and reduce the operator burden to the smallest bounded manual Airtable action

When rendering memory content locally, prefer Airtable memory rows; use migrated source-basis files only for historical comparison.

## Hard rules
- do not treat packaging success as sufficient proof of runtime correctness
- include both success-path and failure-gate testing where possible
- verify emitted artifacts and content, not only exit status
- prevent runtime residue where possible by running python commands with bytecode suppression such as `PYTHONDONTWRITEBYTECODE=1` or `python -B` when practical
- run the shared residue-cleanup script before packaging every materially changed skill and rerun the check after cleanup
- verify that delivered skill packages are free of runtime residue such as `__pycache__/`, `*.pyc`, `.DS_Store`, or equivalent contamination
- in a broad helper-skill patch campaign, patch and regression-test this skill first before using it to judge other skills
- after a patch, rerun the same failing case that motivated the fix, then expand outward
- after every helper-skill create or update, require regression coverage before claiming readiness
- keep the canonical Airtable memory table human-readable and continuously updated after material regression-state changes when Airtable access is available
- do not claim buffered regression state is durable before GitHub flush or export actually happened
- do not call a coordinated campaign complete unless every materially changed skill has an explicit regression result or a plainly bounded untested reason

## References
- `references/regression_fixture_catalog.md`
- `references/skill_test_harness_definitions.md`
- `references/airtable_memory_workflow.md`
- `references/session_buffer_workflow.md`
- `references/package_hygiene_workflow.md`
