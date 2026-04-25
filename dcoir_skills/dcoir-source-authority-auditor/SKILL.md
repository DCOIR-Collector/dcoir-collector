---
name: dcoir-source-authority-auditor
description: >-
  audit whether a requested dcoir task is grounded in the current authoritative source set and stop when control-plane, current_state_id, or continuity drift would make the result unsafe or misleading. use when chatgpt must verify current authority, compare active continuity surfaces, detect stale or contradictory current-state signals, or include three-division airtable governance and registry tables in source-authority review.
---

<!-- skill-marker: updated-skill|20260425T092546Z|T2.4-install-frontmatter-repair|frontmatter-fix|dcoir-source-authority-auditor|SKILL.md -->

# DCOIR Source Authority Auditor

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Overview

Use this skill before or during DCOIR work when source authority or current-state alignment might be in doubt.

This skill verifies the control plane, checks current-versus-historical file handling, compares the active continuity surfaces for the shared `current_state_id` and the `CP-01` / `CP-02` version pair when those surfaces are in scope, and tells ChatGPT whether it can proceed, proceed in a bounded way, or must stop.

## Three-division Airtable authority surfaces
When a source-authority audit touches current-state boundaries, repo cleanup, skill-source governance, startup behavior, or migration from GitHub-readable state into Airtable, include the Airtable three-division tables in the audit context after GitHub `CP-01` / `CP-02` are resolved.

Use silent Airtable reads only unless the operator explicitly asks for visible tables.

Table roles:
- `Governance Control Plane`: durable Airtable governance reference for the GitHub / Airtable / ChatGPT Project authority split
- `Repo Surface Registry`: major repo-surface classification and keep/delete/replacement decisions
- `Skill State Registry`: governed `dcoir-*` skill inventory, startup relevance, parity status, and maintenance state
- `Repo File Classification Detail`: supporting snapshot-level file evidence only; never a replacement for GitHub source authority

Audit posture:
- Treat GitHub `CP-01` and `CP-02` as the source-authority re-anchor before consulting Airtable.
- Treat Airtable `Queue Control`, `Work Items`, and active `Plans` as live queue authority.
- Treat `Governance Control Plane`, `Repo Surface Registry`, and `Skill State Registry` as durable Airtable governance and registry surfaces.
- Treat `Repo File Classification Detail` as supporting evidence for cleanup or classification, not as a hard-stop authority surface.
- If a three-division table contradicts a stale GitHub todo or retired helper-memory claim, prefer Airtable for live governance and report the stale GitHub surface as historical or promoted history unless the GitHub control plane explicitly says otherwise.

## Workflow

1. Resolve the current manifest and change log from the current GitHub-primary control plane.
2. Parse the manifest current governed GitHub readable source set, current knowledge working set, current settings mirrors, and current supporting assets.
3. Treat the current repo guide `README.md`, the task-memory bank, and the Airtable queue-authority surfaces as part of current state when the active workflow depends on ordinary queue priority.
4. Resolve the initial active enforcement surface set when those files or records are present in the workspace:
   - `CP-01`
   - `CP-02`
   - `Airtable Session Checkpoints`
   - `Airtable Queue Control / Work Items / Plan Tasks`
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
