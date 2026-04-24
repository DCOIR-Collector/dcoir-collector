
# DCOIR Source Authority Auditor

<!-- skill-marker: updated-skill|20260415T170500Z|dcoir-source-authority-auditor|SKILL.md|R02 -->

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
3. Treat the current repo guide `README.md`, the task-memory bank, and the Airtable queue-authority surfaces as part of current state when the active workflow depends on ordinary queue priority.
4. Resolve the initial active enforcement surface set when those files or records are present in the workspace:
   - `CP-01`
   - `CP-02`
   - `LOG-03`
   - `LOG-05`
   - active Airtable `Queue Control`
   - active Airtable `Work Items` rows that define the live branch
   - active Airtable `Plans` rows when a plan owns the live branch
5. Compare the `CP-01` / `CP-02` version pair and verify that Airtable queue authority is not being contradicted by a stale GitHub todo claim.
6. Compare the manifest-defined current source set with the workspace state.
7. Check whether the task is trying to rely on retired GitHub todo files as though they were still authoritative for live queue priority.
8. Treat missing authoritative readable sources as a hard-stop conflict, but treat missing supporting assets as a bounded-state note unless the current task explicitly depends on those assets as authority. Treat missing Airtable queue-authority records as a bounded-state note when the control plane is still otherwise intact.
9. Run `scripts/audit_source_authority.py` when a deterministic audit will help.
10. Emit one of these outcomes:
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
- Stop if the task depends on retired GitHub todo files as though they were still the live queue authority after Airtable queue-control cutover.
- Stop if the shared `current_state_id` mismatches across the in-scope GitHub control-plane enforcement set.
- Stop if the `CP-01` / `CP-02` version pair mismatches.
- Do not let a superficially familiar work line override an explicit current-state conflict.
- Prefer control-plane role and manifest section over brittle filename assumptions.
- Treat Project space as bootstrap/runtime anchor, not as a duplicate readable text repository.
- Detect and report drift; do not silently rewrite governed files from this skill.
- Do not hard-stop only because a supporting asset is absent unless the current task explicitly depends on that asset as authority.
