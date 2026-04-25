---
name: dcoir-validation-orchestrator
description: build explicit validation plans for dcoir changes and workflows, with deep regression as the default for anything testable before live use and after every patch. use when chatgpt needs to decide what to test, in what order, with what evidence thresholds, what gates must pass before a skill, script, prompt-pack flow, bundle generator, documentation alignment batch, session-memory workflow, or other dcoir change is considered ready, or when the workflow should read and update the dcoir-validation-orchestrator dedicated Airtable memory table in the current governed repository resolved through the project discovery contract. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-validation-orchestrator|SKILL.md -->

# DCOIR Validation Orchestrator

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Use this skill to turn a DCOIR change, workflow, campaign, or inventory-derived gap area into an explicit validation plan.

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
- re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing Airtable memory rows
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

## References
- `references/validation_scenario_library.md`
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
