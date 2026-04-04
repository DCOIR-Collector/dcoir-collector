---
name: dcoir-validation-orchestrator
description: build explicit validation plans for dcoir changes and workflows, with deep regression as the default for anything testable before live use and after every patch. use when chatgpt needs to decide what to test, in what order, with what evidence thresholds, what gates must pass before a skill, script, prompt-pack flow, bundle generator, documentation alignment batch, session-memory workflow, or other dcoir change is considered ready, or when the workflow should read and update the dcoir-validation-orchestrator GitHub skill-memory file in the current governed repository resolved through the project discovery contract. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

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
7. When the validation state changed materially, use the GitHub connector directly to read or update the canonical GitHub memory file defined in `references/github_memory_workflow.md`, reducing operator burden to the smallest bounded manual GitHub action only when the connector cannot safely complete the write.
8. Return the gates, smoke tests, deep-regression set, evidence requirements, live-readiness criteria, buffered validation state, and any GitHub-memory change that matters.

## Validation regime ownership
This skill now owns:
- end-to-end validation planning
- edge-case and failure-gate planning
- skill deep-dive validation planning
- docs/readme/knowledge alignment validation planning
- packager live-project validation planning
- session-memory pre-push contract validation planning

## GitHub-backed skill memory
Use the GitHub connector directly against the current governed repository resolved through `dcoir_skills/project_discovery_contract.json` when reusable validation-plan state should persist outside the current chat.

GitHub skill-memory layout (resolved from the governed discovery contract plus the current skill name):
- root folder: `dcoir_skill_memory/`
- per-skill folder: `dcoir_skill_memory/dcoir-validation-orchestrator/`
- canonical memory file: `dcoir_skill_memory/dcoir-validation-orchestrator/validation_orchestrator_memory.md`

Use this memory surface for helper working state such as:
- active validation plans that are still in flight
- reusable gates or evidence thresholds worth carrying into the next pass
- unresolved evidence gaps that should remain visible before live-use claims
- campaign coverage notes for broad validation branches
- buffered validation deltas that should land in the next suitable grouped write
- deferred review counters or countdown-gated decisions that affect later validation timing

Rules:
- re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing the memory file
- treat the GitHub memory file as helper working state only, not control-plane authority
- keep one canonical markdown file and update it through the GitHub connector directly when the available connector action surface can complete the modification safely
- if the GitHub connector cannot safely complete the write, say that plainly and reduce the operator burden to the smallest bounded manual GitHub action or surface the markdown content for later commit

When rendering memory content locally, use `scripts/render_validation_memory.py`.

## Hard rules
- Default to deep regression for anything testable before live use and after every patch.
- Do not claim live readiness from inspection alone when execution or generated outputs can be tested.
- Keep the plan bounded to the affected area when the scope is narrow.
- Expand to cross-skill or cross-bundle regression when the change is structural, runtime-affecting, authority-adjacent, or inventory-wide.
- When session-memory-enabled or buffer-capable skills are in scope, include pre-push flush and post-push cleanup checks instead of assuming that state will promote itself.
- Keep the canonical GitHub memory file human-readable and continuously updated after material validation-state changes when repo persistence is available.

## References
- `references/validation_scenario_library.md`
- `references/github_memory_workflow.md`
- `../project_discovery_contract.json` when current repository or helper-memory naming assumptions matter
