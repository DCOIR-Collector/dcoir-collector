---
name: dcoir-structural-rename-coordinator
description: coordinate dcoir structural renames and naming-model changes so dependent files, mappings, skills, delivery bundles, and release posture stay aligned. use when a file, source class, asset class, skill name, or layout rule is being renamed or re-homed and chatgpt must identify every downstream touchpoint, stop unsafe partial updates, and stage the correct refresh set before promotion. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-structural-rename-coordinator|SKILL.md -->

# DCOIR Structural Rename Coordinator

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

Use this skill for renames, source-class transitions, and layout-structure changes.

## Workflow
1. Confirm the rename is intentional and identify old and new names.
2. Classify the rename as one of these: helper-skill rename, governed repo-readable rename, supporting-asset rename, control-plane or layout rename, or broad source-class transition.
3. Build the downstream touchpoint list.
4. Run the script to normalize impacted areas and recommended delivery posture.
5. Default to deeper regression after the rename patch set is applied.
6. Stop unsafe partial updates when the rename touches control-plane, layout, or multiple delivery classes.

## Delivery posture classes
Use these current classes when they fit the rename:
- `targeted_skill_update`
- `batched_skill_update_wave`
- `github_desktop_manual_repo_update_bundle`
- `full_refresh_project_upload`

## Hard rules
- Do not treat a structural rename as documentation-only if runtime, routing, or bundle mappings still point at the retired name.
- Prefer the GitHub-primary repo-readable line as the source of truth for current names.
- Escalate to the strongest truthful delivery posture when a rename changes control-plane, layout, or current supporting-asset expectations.
- Require deeper regression after any rename that changes a helper skill, prompt-pack source, collector guidance, packaging rule, or maintained documentation surface.

## References
- `references/rename_rules.md`
