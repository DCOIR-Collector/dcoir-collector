---
name: dcoir-prompt-pack-assembler
description: assemble one combined dcoir analyst-facing master prompt draft from the current validated modular prompt-pack source files in the africom_soc_ir / dcoir project. use when chatgpt needs to build, refresh, validate, or reassemble the combined master prompt from the current modular set after control-plane review has already settled what is current. this skill is project-gated, scans the current github-primary project_sources prompt-pack line directly, requires a current guardrails module, and should tolerate future filename drift when the modular pp-01 through pp-07 pattern remains clear. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-prompt-pack-assembler|SKILL.md -->

# DCOIR Prompt Pack Assembler

Build one combined analyst-facing master prompt draft and one short assembly report from the current authoritative modular prompt-pack source files.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Preferred current control-plane files:
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- `project_sources/CP-01_DCOIR_Version_Manifest.txt` and `project_sources/CP-02_DCOIR_Change_Log.txt`

## Required behavior
- resolve the current control files first
- discover the live modular PP-01 through PP-07 files directly from the current GitHub-primary `project_sources/` line
- ignore PP-08, PP-09, and PP-10 as non-modular assembly inputs
- fail safely when a required module is missing or ambiguous
- emit only neutral draft outputs, never a promoted project filename
