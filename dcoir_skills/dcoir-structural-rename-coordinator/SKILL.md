---
name: dcoir-structural-rename-coordinator
description: coordinate dcoir structural renames and naming-model changes so dependent files, mappings, skills, and bundles stay aligned. use when a file, source class, asset class, or layout rule is being renamed or re-homed and chatgpt must identify every downstream touchpoint, stop unsafe partial updates, and stage the correct refresh set before promotion. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---
# DCOIR Structural Rename Coordinator

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Use this skill for renames, source-class transitions, and layout-structure changes.

## Workflow
1. Confirm the rename is intentional and identify old and new names.
2. Build the downstream touchpoint list.
3. Use the script to normalize impacted areas.
4. Default to full-refresh bundle posture for structural changes.
5. Require deeper regression after the rename patch set is applied.
