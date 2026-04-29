---
name: dcoir-prompt-pack-assembler
description: assemble and validate combined dcoir analyst-facing master prompts from current validated modular prompt-pack source files.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-prompt-pack-assembler|SKILL.md -->

# DCOIR Prompt Pack Assembler

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


Build one combined analyst-facing master prompt draft and one short assembly report from the current authoritative modular prompt-pack source files.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Preferred authority inputs:
- Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` for startup/admin authority
- active Airtable plan state for current branch context
- GitHub `project_sources/CP-01_DCOIR_Version_Manifest.txt` and `project_sources/CP-02_DCOIR_Change_Log.txt` only when prompt-pack source-role or promoted-history comparison is required

## Required behavior
- resolve Airtable-first authority first for current branch context; resolve GitHub control/source files only when prompt-pack source-role validation requires them
- discover the live modular PP-01 through PP-07 files directly from the current governed GitHub `project_sources/` source line
- ignore PP-08, PP-09, and PP-10 as non-modular assembly inputs
- fail safely when a required module is missing or ambiguous
- emit only neutral draft outputs, never a promoted project filename
