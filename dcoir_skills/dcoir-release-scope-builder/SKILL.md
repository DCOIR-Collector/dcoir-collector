---
name: dcoir-release-scope-builder
description: determine the right dcoir release or packaging class for an already-identified project change.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-release-scope-builder|SKILL.md -->

# DCOIR Release Scope Builder

## Airtable operational schema alignment
Airtable cutover and skill cutover are complete. Use the current Airtable schema as live operational authority, not historical migration or cleanup plans.

Use `references/airtable_operational_schema_contract.md` for durable rules covering:
- current live authority tables
- idea-to-work-item-to-plan promotion
- Delete Queue deletion requests and dependency order
- DCOIR Lifecycle Ledger readback/history events
- Local Configuration Registry secret-safe configuration references

Do not assume retired or absent tables exist. In particular, do not require `Plan Tasks`, `Plan Checkpoints`, `Skill State Registry`, `Schema Registry`, `Tracking Registry`, `Repo File Coverage Detail`, or `Retained Repo Manifest` unless live Airtable schema readback proves the table exists for the current task.

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Work Items for task execution`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, explicit repo cleanup/source-role review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo Surface Registry supporting evidence`, `Repo Surface Registry retained-state evidence`, and active plan state before stopping.


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
