---
name: dcoir-collector-qa
description: validate, troubleshoot, regression-test, repair, and maintain the dcoir collector and its harness files inside the africom_soc_ir / dcoir project. use when chatgpt needs to audit or patch the current github-native collector or harness files, validate a collector execution error, generate markdown test reports or repair plans, regenerate targeted maintenance guidance from the current authoritative collector sources, or read and update the dcoir-collector-qa dedicated Airtable memory table in malwaredevil/dcoir-collector. prefer the current Airtable-first governance posture plus governed GitHub source/readback surface and current native filenames over older project-mirror readable-source names. use only when the africom_soc_ir / dcoir project context is present.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-collector-qa|SKILL.md -->

# DCOIR Collector QA

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

## Overview
Use this skill to run a controlled QA / V&V / regression loop for the DCOIR collector line.
The primary scope is the current GitHub-readable collector and harness sources, the emitted runtime filename rules, Airtable validation/test rows, and rollback reference material only when explicit comparison or historical regression context is needed. Use GitHub `CP-01`/`CP-02` only when collector source-role resolution, promoted-history comparison, packaging, or final T99 keep/delete review is in scope.

## Authoritative source set
Re-anchor to Airtable-first startup/control-plane authority first when the task involves live state, queue state, QA follow-through, or test catalog state.
Treat these current GitHub-readable files as the primary collector source scope when collector source inspection or packaging is required:
- `project_sources/DCOIR_Collector.ps1`
- `project_sources/run_DCOIR_Tests.ps1`
- GitHub `CP-01`/`CP-02` only for source-role/promoted-history fallback when needed
- Airtable `Validation Test Cases`, `Plans`, `Plan Tasks`, and `Session Checkpoints` when QA state, test catalog state, or active follow-through matters
- Use `project_sources/RB-01_DCOIR_Collector_refinement_2_1_3.txt` only when explicit rollback comparison, historical regression reference, or bounded rollback analysis is part of the QA question.

## Default posture
Use a hybrid posture by default:
1. always perform analysis and static auditing
2. always emit repeatable local test instructions
3. also execute representative checks in-chat when the environment actually permits
4. mark every check as one of these only:
   - `passed`
   - `failed`
   - `blocked`
   - `planned-not-executed`

## Workflow
1. Read the control plane and confirm the current collector/harness working line.
2. Read `references/test_buckets.md`, `references/execution_modes.md`, `references/maintenance_contract.md`, and `references/repair_mode.md` when repair or documentation refresh is requested.
3. Run `scripts/collector_static_audit.py` against the current readable collector and harness sources.
4. Decide what can be executed in the current environment versus what must remain local/manual.
5. If local execution is possible, run only representative checks that fit the current environment and keep exact command lines lane-correct.
6. Preserve the known-failure lane for the Gemini collector transcript error even if the exact failing excerpt is still pending recovery.
7. If the user asks for code repair or in-code documentation refresh, switch into explicit repair mode using `references/repair_mode.md` and run `scripts/render_repair_plan.py` so the changed targets, documentation targets, validation lanes, and stop conditions are explicit before claiming a fix.
8. Use `scripts/render_collector_qa_report.py` to emit a timestamped markdown report and, when helpful, a companion JSON results file.
9. When the QA state changed materially, use Airtable table `dcoir-collector-qa` to read or update durable helper memory as described in `references/airtable_memory_workflow.md`, reducing operator burden to the smallest bounded manual Airtable action only when the connector cannot safely complete the write.
10. In repair mode, update the readable collector or harness source only for the defect-under-test, refresh targeted in-code documentation when it materially improves future maintenance, regenerate the maintenance code blocks from the current authoritative sources, rerun the motivating failure lane, rerun at least one known-good control lane, and only then report the patch as validated.

## Airtable-backed skill memory

Project preference: prefer the GitHub connector directly for governed readable-text updates and helper-memory persistence whenever the connector can complete the operation safely. Use the smallest bounded manual GitHub action only when connector limitations prevent safe in-chat completion.



Use Airtable table `dcoir-collector-qa` when collector QA state should persist outside the current chat.

Airtable skill-memory layout:
- live table: `dcoir-collector-qa`
- source-basis history: migrated rows may cite former repo memory paths

Use this memory surface for helper working state such as:
- active known-failure lanes and whether they are still placeholders
- active repair candidates and bounded next actions
- recently validated control lanes or repaired paths
- notes about regression scope that should remain visible before later QA passes

Rules:
- re-anchor to Project Instructions, CP-00 as a pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`; read GitHub `CP-01`/`CP-02` only for repository-source tasks before reading or writing Airtable memory rows
- treat the Airtable memory table as helper working state only, not control-plane authority
- keep one canonical Airtable row set for live memory and update it directly when connector access permits
- if Airtable access is blocked, say that plainly and reduce the operator burden to the smallest bounded manual Airtable action

When rendering memory content locally, prefer Airtable rows; use migrated source-basis files only for historical comparison.

## Hard rules
- Do not treat packaging success as proof that the collector works.
- Do not claim a full collector fix without rerunning the motivating regression lane and at least one control lane.
- Do not invent missing runtime results. Mark blocked or planned-not-executed when evidence is not present.
- Do not mix Elastic response-action syntax and local Windows PowerShell 5.1 syntax in one malformed instruction block.
- Preserve the distinction between observed facts, grounded inference, and unresolved gaps.
- Keep the known Gemini collector error as an explicit regression lane from day one, even if the exact transcript excerpt is still a placeholder.
- Keep the canonical Airtable memory table human-readable and continuously updated after material QA-state changes when Airtable access is available.

## Output contract
Default deliverables per run:
1. one combined markdown report
2. one optional JSON companion results file
3. in repair mode, one optional repair-plan JSON file when a deterministic changed-target plan is useful

## References
- `references/test_buckets.md`
- `references/execution_modes.md`
- `references/maintenance_contract.md`
- `references/report_template.md`
- `references/known_failure_lane.md`
- `references/repair_mode.md`
- `references/sample_manual_results.json`
- `references/airtable_memory_workflow.md`

## Airtable test-catalog enforcement

When performing collector QA, repair planning, or live-test interpretation, read and update the relevant Airtable `Validation Test Cases` rows when that table is available.

Use it to:
- confirm whether the branch already has a defined test ID
- mark pass, partial, fail, or blocked status honestly
- record live operator evidence and implementation-boundary notes
- add new collector test rows when a new alias, packaging behavior, or regression class appears
