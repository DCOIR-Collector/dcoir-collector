---
name: dcoir-skill-regression-auditor
description: plan and audit deeper regression for dcoir skills before live use and after every patch. use when chatgpt needs to define regression fixtures, harness expectations, success and failure paths, output-verification checks for one or more dcoir skills, enforce the mandatory post-create or post-update regression rule, stage regression state in a session-local buffer before a grouped github flush, or manage a bounded coordinated multi-skill patch campaign with explicit self-first validation and one grouped regression bundle.
---

<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-skill-regression-auditor|SKILL.md -->

# DCOIR Skill Regression Auditor

<!-- skill-marker: updated-skill|20260415T135556Z|dcoir-skill-regression-auditor|SKILL.md|R01 -->

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
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
9. For helper-skill update flows that use manual install, remove older `skill-marker:` lines or comments from the edited files, add one fresh `skill-marker:` entry to each edited file before packaging, and record the expected marker list as part of regression readiness.
10. After the operator saves the installed skill update, verify the expected current `skill-marker:` entries in the edited installed file set before treating the result as ready for GitHub sync, GitHub Desktop repo-update bundle generation, parity closure, or broader readiness claims.
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
- re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing Airtable memory rows
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
- do not treat a manually installed updated skill as ready for GitHub sync, repo-bundle generation, parity closure, or broader rollout until the expected current `skill-marker:` entries are confirmed in the edited installed file set
- keep the canonical Airtable memory table human-readable and continuously updated after material regression-state changes when Airtable access is available
- do not claim buffered regression state is durable before GitHub flush or export actually happened
- do not call a coordinated campaign complete unless every materially changed skill has an explicit regression result or a plainly bounded untested reason

## References
- `references/regression_fixture_catalog.md`
- `references/skill_test_harness_definitions.md`
- `references/airtable_memory_workflow.md`
- `references/session_buffer_workflow.md`
- `references/package_hygiene_workflow.md`
