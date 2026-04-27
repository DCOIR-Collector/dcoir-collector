---
name: dcoir-release-scope-builder
description: determine the right dcoir release or packaging class for an already-identified africom_soc_ir / dcoir project change. use only when working inside the africom_soc_ir / dcoir project context and chatgpt needs to choose whether the change stays local, becomes a targeted skill update, becomes a batched multi-skill update wave, becomes a github desktop manual repo-update bundle, becomes a repo-layout test bundle, or requires a full-refresh project upload bundle with release instructions. this skill owns packaging-class selection, not general decision branching or promotion-readiness judgment. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-release-scope-builder|SKILL.md -->

# DCOIR Release Scope Builder

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

Use this skill to choose the right release or packaging scope for a DCOIR change.

## Scope boundary
This skill answers one narrow question: what release or packaging class fits the already-identified change.

Use this skill only after the changed targets or change set are already known.

It does not own general proceed-versus-ask-versus-stop branching or operator-preference application. Use `dcoir-decision-policy` for those broader control decisions.

It does not judge whether the built change is ready, conditionally ready, or not ready. Use `dcoir-promotion-readiness-reviewer` for that later readiness check.

## Core workflow
1. Resolve the current control plane.
2. Confirm the changed targets or change set are already identified.
3. Determine whether the identified change affects authority, runtime behavior, packaging, or only one helper skill.
4. Read `references/release_instruction_templates.md`.
5. Run `scripts/build_release_scope.py`.
6. Return the recommended release or packaging class, why it fits, and what release notes or instructions are required.

## Default scope rules
- local-only testing -> repo-layout local testing
- one helper skill with no project-source effect -> targeted skill update
- multiple compatible helper-skill changes with no broader repo-readable source change -> batched skill-update wave
- current governed repo-readable changes in the GitHub-primary line -> GitHub Desktop manual repo-update bundle
- structural, uploaded-project, or broader project-upload class change -> full-refresh project upload
- anything authority-adjacent -> explicit review before release

## References
- `references/release_instruction_templates.md`
