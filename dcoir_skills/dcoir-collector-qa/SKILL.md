---
name: dcoir-collector-qa
description: validate, troubleshoot, regression-test, repair, and maintain the dcoir collector and its harness files inside the africom_soc_ir / dcoir project. use when chatgpt needs to audit or patch the current github-native collector or harness files, validate a collector execution error, generate markdown test reports or repair plans, regenerate targeted maintenance guidance from the current authoritative collector sources, or read and update the dcoir-collector-qa GitHub skill-memory file in malwaredevil/dcoir-collector. prefer the current github-primary control plane and current native filenames over older project-mirror readable-source names. use only when the africom_soc_ir / dcoir project context is present.
---

# DCOIR Collector QA

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Overview
Use this skill to run a controlled QA / V&V / regression loop for the DCOIR collector line.
The primary scope is the current GitHub-readable collector and harness sources, the emitted runtime filename rules, the maintained documentation surface for those files, and rollback reference material only when explicit comparison or historical regression context is needed.

## Authoritative source set
Re-anchor to the current control plane first.
Treat these current GitHub-readable files as the primary collector QA scope unless the manifest changes:
- `project_sources/DCOIR_Collector.ps1`
- `project_sources/run_DCOIR_Tests.ps1`
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- `project_sources/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt`
- `project_sources/LOG-01_DCOIR_Todo_Log.txt`
- `project_sources/LOG-01_DCOIR_Todo_Index.txt` and `project_sources/todo/*.txt` when the active work-line split matters to current QA follow-through
- `project_sources/LOG-02_DCOIR_Lessons_Learned_Log.txt` when lessons or failing cases need preservation
- `project_sources/LOG-03_DCOIR_Session_Handoff_Brief.txt` when validating against the current phase handoff
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
9. When the QA state changed materially, use the GitHub connector directly to read or update the canonical GitHub memory file defined in `references/github_memory_workflow.md`, reducing operator burden to the smallest bounded manual GitHub action only when the connector cannot safely complete the write.
10. In repair mode, update the readable collector or harness source only for the defect-under-test, refresh targeted in-code documentation when it materially improves future maintenance, regenerate the maintenance code blocks from the current authoritative sources, rerun the motivating failure lane, rerun at least one known-good control lane, and only then report the patch as validated.

## GitHub-backed skill memory

Project preference: prefer the GitHub connector directly for governed readable-text updates and helper-memory persistence whenever the connector can complete the operation safely. Use the smallest bounded manual GitHub action only when connector limitations prevent safe in-chat completion.



Use the GitHub connector directly against repository `malwaredevil/dcoir-collector` when collector QA state should persist outside the current chat.

GitHub skill-memory layout:
- root folder: `dcoir_skill_memory/`
- per-skill folder: `dcoir_skill_memory/dcoir-collector-qa/`
- canonical memory file: `dcoir_skill_memory/dcoir-collector-qa/collector_qa_memory.md`

Use this memory surface for helper working state such as:
- active known-failure lanes and whether they are still placeholders
- active repair candidates and bounded next actions
- recently validated control lanes or repaired paths
- notes about regression scope that should remain visible before later QA passes

Rules:
- re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing the memory file
- treat the GitHub memory file as helper working state only, not control-plane authority
- keep one canonical markdown file and update it through the GitHub connector directly when the available connector action surface can complete the modification safely
- if the GitHub connector cannot safely complete the write, say that plainly and reduce the operator burden to the smallest bounded manual GitHub action or surface the markdown content for later commit

When rendering memory content locally, use `scripts/render_collector_qa_memory.py`.

## Hard rules
- Do not treat packaging success as proof that the collector works.
- Do not claim a full collector fix without rerunning the motivating regression lane and at least one control lane.
- Do not invent missing runtime results. Mark blocked or planned-not-executed when evidence is not present.
- Do not mix Elastic response-action syntax and local Windows PowerShell 5.1 syntax in one malformed instruction block.
- Preserve the distinction between observed facts, grounded inference, and unresolved gaps.
- Keep the known Gemini collector error as an explicit regression lane from day one, even if the exact transcript excerpt is still a placeholder.
- Keep the canonical GitHub memory file human-readable and continuously updated after material QA-state changes when repo persistence is available.

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
- `references/github_memory_workflow.md`
