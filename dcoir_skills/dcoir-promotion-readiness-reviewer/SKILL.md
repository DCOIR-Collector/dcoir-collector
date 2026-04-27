---
name: dcoir-promotion-readiness-reviewer
description: review whether an africom_soc_ir / dcoir project change is ready, ready with conditions, or not ready after the changed set and packaging posture are already known. use only when working inside the africom_soc_ir / dcoir project context and chatgpt must check authority basis, validation evidence, downstream refresh completion, release instructions, and blocking gaps before anything is treated as live. this skill owns readiness judgment, not general decision branching or release-class selection. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-promotion-readiness-reviewer|SKILL.md -->

# DCOIR Promotion Readiness Reviewer

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
6. Return `ready`, `ready_with_conditions`, or `not_ready`, with batched-delivery blockers called out explicitly when they apply.

## Hard rules
- Do not call something ready without validation evidence.
- Default to deeper regression for anything testable.
- If release instructions are required but missing, block readiness.
- If the settled packaging posture is a batched skill-update wave, block readiness until every changed skill has explicit regression coverage or a plainly bounded untested reason.
- If the settled packaging posture is a GitHub Desktop manual repo-update wave, block readiness until the repo-update artifact, required delivery instructions, and suggested commit-summary guidance are present when that guidance is required by the current workflow.
- If downstream refresh obligations are unresolved, block readiness.
