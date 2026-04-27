---
name: dcoir-prompt-pack-assembler
description: assemble one combined dcoir analyst-facing master prompt draft from the current validated modular prompt-pack source files in the africom_soc_ir / dcoir project. use when chatgpt needs to build, refresh, validate, or reassemble the combined master prompt from the current modular set after control-plane review has already settled what is current. this skill is project-gated, scans the current github-primary project_sources prompt-pack line directly, requires a current guardrails module, and should tolerate future filename drift when the modular pp-01 through pp-07 pattern remains clear. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-prompt-pack-assembler|SKILL.md -->

# DCOIR Prompt Pack Assembler

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.


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
