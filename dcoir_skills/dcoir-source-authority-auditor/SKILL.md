---
name: dcoir-source-authority-auditor
description: audit whether a requested dcoir task is grounded in current authoritative source sets and stop on unsafe authority drift.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-source-authority-auditor|SKILL.md -->

# DCOIR Source Authority Auditor

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

## Overview

Use this skill before or during DCOIR work when source authority or current-state alignment might be in doubt.

This skill verifies the control plane, checks current-versus-historical file handling, compares the active continuity surfaces for the shared `current_state_id` and the `CP-01` / `CP-02` version pair when those surfaces are in scope, and tells ChatGPT whether it can proceed, proceed in a bounded way, or must stop.

## Three-division Airtable authority surfaces
When a source-authority audit touches current-state boundaries, repo cleanup, skill-source governance, startup behavior, or migration from GitHub-readable state into Airtable, include Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo Surface Registry supporting evidence`, `Repo Surface Registry retained-state evidence`, Queue Control, Work Items, active Plans, and Work Items for task execution before any GitHub CP fallback.

Use silent Airtable reads only unless the operator explicitly asks for visible tables.

Table roles:
- `Governance Control Plane`: durable Airtable governance reference for the GitHub / Airtable / ChatGPT Project authority split
- `Repo Surface Registry`: major repo-surface classification and keep/delete/replacement decisions
- `Admin Registry skill-state rows`: governed `dcoir-*` skill inventory, startup relevance, parity status, and maintenance state
- `Repo File Classification Detail`: supporting snapshot-level file evidence only; never a replacement for GitHub source authority

Audit posture:
- Treat Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` and live Airtable governance tables as the startup/admin re-anchor before consulting GitHub. Treat GitHub `CP-01` and `CP-02` as repository-source/promoted-history inputs only when the audit scope requires source-file authority or explicit repo cleanup/source-role review.
- Treat Airtable `Queue Control`, `Work Items`, and active `Plans` as live queue authority.
- Treat `Governance Control Plane`, `Repo Surface Registry`, and `Admin Registry skill-state rows` as durable Airtable governance and registry surfaces.
- Treat `Repo File Classification Detail` as supporting evidence for cleanup or classification, not as a hard-stop authority surface.
- If a three-division table contradicts a stale GitHub todo or retired helper-memory claim, prefer Airtable for live governance and report the stale GitHub surface as historical or promoted history unless the GitHub control plane explicitly says otherwise.

## Workflow

1. Resolve the current manifest and change log from the current Airtable-first governance posture plus governed GitHub source/readback surface.
2. Parse the manifest current governed GitHub readable source set, current knowledge working set, current settings mirrors, and current supporting assets.
3. Treat the current repo guide `README.md`, the task-memory bank, and the Airtable queue-authority surfaces as part of current state when the active workflow depends on ordinary queue priority.
4. Resolve the initial active enforcement surface set when those files or records are present in the workspace:
   - `CP-01`
   - `CP-02`
   - `Airtable Session Checkpoints`
   - `Airtable Queue Control / Work Items / Work Items for task execution`
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

## Fast Airtable helper-memory read contract

Use the skill-specific Airtable helper-memory table directly when this skill needs durable helper memory.

- Airtable base id: `appM4KSwnVf3G3OTK`
- Airtable table name: `dcoir-source-authority-auditor`
- Airtable table id: `tblggXJoCuDK6cHg5`
- Primary lookup/dedupe field: `authority_audit_entry_id`

Read pattern:
- Use the Airtable connector with `baseId="appM4KSwnVf3G3OTK"` and `tableId="tblggXJoCuDK6cHg5"` when supported; use the table name only as fallback.
- Use non-display Airtable reads such as `search_records`, direct table reads, or equivalent connector calls. Do not ask the operator whether to display an interactive Airtable view.
- Pull only this skill's own helper-memory table for routine memory lookup. Do not scan a unified helper-memory table and filter by skill.
- Keep helper-memory rows human-readable and update this same table when material reusable state changes.
- If the connector cannot query by tableId, state the limitation and use the table name `dcoir-source-authority-auditor` without switching to a merged memory table.

## Hard rules

- Treat only files or patterns marked current in the manifest as authoritative readable working sources.
- Treat supporting assets as supporting, not control-plane authority.
- Treat rollback or historical files as non-authoritative unless explicitly requested.
- Stop if the task-required authority surface is missing. For startup/admin/live-queue tasks, missing GitHub CP files are not a stop condition when Airtable startup/governance rows are present.
- Stop if the task depends on a non-current file as though it were authoritative.
- Stop if the task depends on retired GitHub todo files as though they were still the live queue authority after Airtable operational queue-control model.
- Stop if the shared `current_state_id` mismatches across the in-scope GitHub control-plane enforcement set.
- Stop on `CP-01` / `CP-02` mismatch only when those GitHub files are explicitly in source-task scope. For Airtable-first startup/admin branches, report the mismatch as promoted-history drift and use Airtable live authority.
- Do not let a superficially familiar work line override an explicit current-state conflict.
- Prefer control-plane role and manifest section over brittle filename assumptions.
- Treat Project space as bootstrap/runtime anchor, not as a duplicate readable text repository.
- Detect and report drift; do not silently rewrite governed files from this skill.
- Do not hard-stop only because a supporting asset is absent unless the current task explicitly depends on that asset as authority.
