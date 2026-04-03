---
name: dcoir-promotion-readiness-reviewer
description: review whether an africom_soc_ir / dcoir project change is ready, ready with conditions, or not ready after the changed set and packaging posture are already known. use only when working inside the africom_soc_ir / dcoir project context and chatgpt must check authority basis, validation evidence, downstream refresh completion, release instructions, and blocking gaps before anything is treated as live. this skill owns readiness judgment, not general decision branching or release-class selection.
---
# DCOIR Promotion Readiness Reviewer

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Use this skill after work is built, the changed set is known, and the packaging posture is already settled, but before the result is treated as ready.

## Scope boundary
This skill answers one later question only: is the already-scoped change ready, ready with conditions, or not ready.

Use this skill only after the changed set and packaging posture are already known.

It does not choose the release or packaging class for the change. Use `dcoir-release-scope-builder` for that earlier classification step.

It does not own general branching, cadence, or operator-preference application across multiple reasonable paths. Use `dcoir-decision-policy` for those broader control decisions.

## Workflow
1. Confirm the control plane is current.
2. Confirm the changed file set is identified.
3. Confirm required validation evidence exists.
4. Confirm downstream refreshes and packaging posture are settled.
5. Run `scripts/review_promotion_readiness.py` when a deterministic checklist helps.
6. Return `ready`, `ready_with_conditions`, or `not_ready`.

## Hard rules
- Do not call something ready without validation evidence.
- Default to deeper regression for anything testable.
- If release instructions are required but missing, block readiness.
- If downstream refresh obligations are unresolved, block readiness.
