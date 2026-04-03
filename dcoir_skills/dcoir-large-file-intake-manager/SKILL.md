---
name: dcoir-large-file-intake-manager
description: plan bounded intake when dcoir evidence files are too large, missing, or only partially available. use when chatgpt needs to keep working despite upload limits by switching to metadata-first triage, targeted excerpts, staged collection, or narrowed artifact requests. includes living large-file intake playbooks that can evolve as the workflow changes. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Large File Intake Manager

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Use this skill to keep DCOIR work moving when full evidence files cannot be uploaded.

## Core workflow
1. Identify the artifact type and limitation.
2. Read `references/large_file_intake_playbooks.md`.
3. Run `scripts/plan_large_file_intake.py`.
4. Return the best bounded intake path, next requested excerpt, and confidence limits.

## Hard rules
- Do not block the workflow just because the full file is unavailable.
- State the limitation plainly.
- Prefer metadata-first and highest-value targeted excerpts.
- Keep conclusions bounded to the reviewed scope.

## References
- `references/large_file_intake_playbooks.md`
