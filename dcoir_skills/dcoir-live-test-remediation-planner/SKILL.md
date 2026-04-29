---
name: dcoir-live-test-remediation-planner
description: turn dcoir live-test findings into ranked remediation plans with impacted files, helper-skill refreshes, regression requirements, delivery posture, and stop conditions.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-live-test-remediation-planner|SKILL.md -->

# DCOIR Live Test Remediation Planner

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


Use this skill to convert live-test findings into an explicit remediation queue and verification plan.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Before planning remediation, verify the current authoritative control-plane files from the workspace.

Preferred current files:
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- Airtable `Work Items` / `Work Items for task execution`
- Airtable `Session Checkpoints`

Stop only when the required authority surface for the current task cannot be resolved. For startup/admin/live-queue tasks, use Airtable authority; for repository-source tasks, use GitHub CP/source files or their Airtable replacement rows if CP files have been detached.

## Core workflow
1. Resolve Airtable-first startup/control-plane authority first for live state and queue context.
2. Read GitHub `CP-01`/`CP-02` only when the remediation analysis requires repository-source role resolution, promoted-history comparison, or source-file inspection.
3. Use the current todo log and current handoff brief as supporting context for active remediation themes.
4. Identify the live-test findings, defects, or operator-friction notes from the user request.
5. Run `scripts/plan_live_test_remediation.py` with the findings.
6. Read the generated markdown and json reports.
7. When the remediation state changed materially, use Airtable table `dcoir-live-test-remediation-planner` to read or update durable helper memory as described in `references/airtable_memory_workflow.md`, reducing operator burden to the smallest bounded manual Airtable action only when the connector cannot safely complete the write.
8. Return the ranked remediation order, impacted sources, deep-regression requirements, recommended delivery posture, and any Airtable-memory change that matters.

## Fast Airtable helper-memory read contract

Use the skill-specific Airtable helper-memory table directly when this skill needs durable helper memory.

- Airtable base id: `appM4KSwnVf3G3OTK`
- Airtable table name: `dcoir-live-test-remediation-planner`
- Airtable table id: `tbltsNeLytMKgmJft`
- Primary lookup/dedupe field: `remediation_entry_id`

Read pattern:
- Use the Airtable connector with `baseId="appM4KSwnVf3G3OTK"` and `tableId="tbltsNeLytMKgmJft"` when supported; use the table name only as fallback.
- Use non-display Airtable reads such as `search_records`, direct table reads, or equivalent connector calls. Do not ask the operator whether to display an interactive Airtable view.
- Pull only this skill's own helper-memory table for routine memory lookup. Do not scan a unified helper-memory table and filter by skill.
- Keep helper-memory rows human-readable and update this same table when material reusable state changes.
- If the connector cannot query by tableId, state the limitation and use the table name `dcoir-live-test-remediation-planner` without switching to a merged memory table.

## Hard rules
- Do not treat live-test findings as fixed until the repaired path is re-tested.
- Default to deep regression for any remediation affecting a skill, script, packaging path, operator guidance, or generated workflow artifact that can be tested reliably.
- Prefer the active work line from the todo log and handoff brief over stale historical assumptions.
- Prefer the smallest truthful remediation slice first, unless the findings indicate a structural change requiring coordinated multi-file work.
- Use the current delivery classes, not the retired targeted-versus-full-refresh split alone.
- Treat `project_sources/DCOIR_Collector.ps1` as the current readable collector source and `DCOIR_Collector.ps1` as the canonical runtime filename.
- Keep the canonical Airtable memory table human-readable and continuously updated after material remediation-state changes when Airtable access is available.

## Delivery posture classes
Use these delivery classes when they fit the repaired change set:
- `targeted_skill_update`
- `batched_skill_update_wave`
- `github_desktop_manual_repo_update_bundle`
- `full_refresh_project_upload`

## Output contract
Return these sections in order:
1. Live-test finding summary
2. Ranked remediation queue
3. Impacted files and skills
4. Deep-regression requirements
5. Delivery recommendation
6. Stop conditions and warnings

## Commands
Build a remediation plan from explicit findings:
```bash
python scripts/plan_live_test_remediation.py \
  --source-dir /mnt/data \
  --output-dir /mnt/data/dcoir_live_test_remediation_out \
  --finding "collector output interpretation was unclear" \
  --finding "large-file fallback was not explained"
```

## References
- `references/remediation_rules.json`
- `references/remediation_model.md`
- `references/airtable_memory_workflow.md`

## Airtable remediation traceability

When live-test findings map to existing collector or Gemini test rows, update or reference the Airtable `Validation Test Cases` catalog alongside the remediation queue.

Prefer this pattern:
- failed or blocked live finding -> update matching test row evidence/status
- new failure shape or missing coverage -> add a new test row
- remediation plan -> link the finding to an Airtable Work Item and the affected test IDs
