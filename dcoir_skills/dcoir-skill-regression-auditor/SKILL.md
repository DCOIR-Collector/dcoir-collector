---
name: dcoir-skill-regression-auditor
description: plan and audit deeper regression for dcoir skills before live use and after every patch. use when chatgpt needs to define regression fixtures, harness expectations, success and failure paths, output-verification checks for one or more dcoir skills, enforce the mandatory post-create or post-update regression rule, stage regression state in a session-local buffer before a grouped github flush, or manage a bounded coordinated multi-skill patch campaign with explicit self-first validation and one grouped regression bundle.
---

# DCOIR Skill Regression Auditor

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
5. Run `scripts/plan_skill_regression.py`.
6. Produce the regression suites, failure gates, artifact checks, readiness criteria, campaign ordering, and grouped regression-bundle expectations.
7. If regression revealed a blocker that is later overcome, invoke `dcoir-memory-preflight` again when the recovered lesson could improve a reusable procedure, limitation note, failure signature, or helper-skill/process guidance.
8. Keep regression-state changes session-local until the next suitable flush-check trigger when grouped GitHub writes are preferred.
9. When the regression-state changed materially and the write lane is safe, use the GitHub connector directly to read or update the canonical GitHub memory file defined in `references/github_memory_workflow.md`.
10. Return the regression suites, failure gates, artifact checks, readiness criteria, campaign scope, buffer state, and any GitHub-memory change that matters.

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

## GitHub-backed skill memory
Use the GitHub connector directly against repository `malwaredevil/dcoir-collector` when reusable regression-planning state should persist outside the current chat.

GitHub skill-memory layout:
- root folder: `dcoir_skill_memory/`
- per-skill folder: `dcoir_skill_memory/dcoir-skill-regression-auditor/`
- canonical memory file: `dcoir_skill_memory/dcoir-skill-regression-auditor/skill_regression_memory.md`

Use this memory surface for helper working state such as:
- tracked skills with active regression follow-through
- fixture baselines worth reusing after later patches
- failure gates that should remain visible across packaging cycles
- buffered but unflushed regression deltas awaiting a later grouped write
- coordinated campaign coverage summaries when a bounded multi-skill patch cycle is in flight

Rules:
- re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing the memory file
- treat the GitHub memory file as helper working state only, not control-plane authority
- keep one canonical markdown file and update it through the GitHub connector directly when the available connector action surface can complete the modification safely
- if the GitHub connector cannot safely complete the write, say that plainly and reduce the operator burden to the smallest bounded manual GitHub action or surface the markdown content for later commit

When rendering memory content locally, use `scripts/render_skill_regression_memory.py`.

## Hard rules
- do not treat packaging success as sufficient proof of runtime correctness
- include both success-path and failure-gate testing where possible
- verify emitted artifacts and content, not only exit status
- in a broad helper-skill patch campaign, patch and regression-test this skill first before using it to judge other skills
- after a patch, rerun the same failing case that motivated the fix, then expand outward
- after every helper-skill create or update, require regression coverage before claiming readiness
- keep the canonical GitHub memory file human-readable and continuously updated after material regression-state changes when repo persistence is available
- do not claim buffered regression state is durable before GitHub flush or export actually happened
- do not call a coordinated campaign complete unless every materially changed skill has an explicit regression result or a plainly bounded untested reason

## References
- `references/regression_fixture_catalog.md`
- `references/skill_test_harness_definitions.md`
- `references/github_memory_workflow.md`
- `references/session_buffer_workflow.md`
