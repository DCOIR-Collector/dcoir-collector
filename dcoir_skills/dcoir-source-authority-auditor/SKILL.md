---
name: dcoir-source-authority-auditor
description: audit whether a requested dcoir task is grounded in the current authoritative source set and stop when control-plane, current_state_id, or continuity drift would make the result unsafe or misleading. use when chatgpt must verify current authority, compare active continuity surfaces for alignment, detect stale or contradictory current-state signals, flag historical-versus-current confusion, or decide whether work can proceed, must stay bounded, or must stop for an exact conflict report. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Source Authority Auditor

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Overview

Use this skill before or during DCOIR work when source authority or current-state alignment might be in doubt.

This skill verifies the control plane, checks current-versus-historical file handling, compares the active continuity surfaces for the shared `current_state_id` and the `CP-01` / `CP-02` version pair when those surfaces are in scope, and tells ChatGPT whether it can proceed, proceed in a bounded way, or must stop.

## Workflow

1. Resolve the current manifest and change log from the current GitHub-primary control plane.
2. Parse the manifest current governed GitHub readable source set, current knowledge working set, current settings mirrors, and current supporting assets.
3. Treat the current repo guide `README.md`, the split todo structure (`LOG-01_DCOIR_Todo_Log.txt`, `LOG-01_DCOIR_Todo_Index.txt`, and `project_sources/todo/*.txt`), and the task-memory bank as part of current state when the control plane names them explicitly.
4. Resolve the initial active enforcement surface set when those files are present in the workspace:
   - `CP-01`
   - `CP-02`
   - `LOG-03`
   - `LOG-05`
   - `LOG-01_DCOIR_Todo_Log.txt`
   - `LOG-01_DCOIR_Todo_Index.txt`
   - `todo/01_Active_Now.txt`
5. Compare the shared `current_state_id` across that set and compare the `CP-01` / `CP-02` version pair.
6. Compare the manifest-defined current source set with the workspace state.
7. Check whether the task is trying to rely on non-current files or Project-space mirror assumptions.
8. Run `scripts/audit_source_authority.py` when a deterministic audit will help.
9. Emit one of these outcomes:
   - `clear_to_proceed`
   - `proceed_bounded`
   - `hard_stop_conflict`

## Output contract

Return:
- audit outcome
- authoritative basis used
- exact conflict or drift if any
- affected active surfaces when drift is found
- smallest remediation set when a conflict is clear enough to name it
- best next move

## Hard rules

- Treat only files or patterns marked current in the manifest as authoritative readable working sources.
- Treat supporting assets as supporting, not control-plane authority.
- Treat rollback or historical files as non-authoritative unless explicitly requested.
- Stop if the manifest or change log is missing.
- Stop if the task depends on a non-current file as though it were authoritative.
- Stop if the shared `current_state_id` mismatches across the in-scope active enforcement set.
- Stop if the `CP-01` / `CP-02` version pair mismatches.
- Do not let a superficially familiar work line override an explicit current-state conflict.
- Prefer control-plane role and manifest section over brittle filename assumptions.
- Treat Project space as bootstrap/runtime anchor, not as a duplicate readable text repository.
- Detect and report drift; do not silently rewrite governed files from this skill.
