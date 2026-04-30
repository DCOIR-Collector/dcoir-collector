---
name: dcoir-authority-drift-reporter
description: detect, structure, and report africom_soc_ir / dcoir source-authority confusion, stale workflow assumptions, missing airtable schema surfaces, github versus airtable drift, project attachment drift, helper-skill memory drift, repeated connector roundtrips, or uncertainty about where information should come from. use when chatgpt or a dcoir skill loops, hesitates, contradicts itself, relies on retired tables/files, or needs a paste-ready repair report for another session.
---

<!-- skill-marker: updated-skill|20260430T214500Z|skill-pass-maintenance|source-update|dcoir-authority-drift-reporter|SKILL.md -->
# DCOIR Authority Drift Reporter

## Project gate
Use this skill only for AFRICOM_SOC_IR / DCOIR work. The current model is Airtable-first operational authority, with GitHub as governed source/readback and promoted history only when repository-source tasks require it.

## Purpose
Use this skill when the assistant, a helper skill, or the workflow has trouble determining the correct authority source. The skill turns the confusion into a durable, paste-ready drift report that another session can use to repair Project Instructions, attachments, skills, GitHub source, Airtable tables, or execution rules.

## Trigger patterns
Invoke this skill when any of these happen:
- repeated Airtable/GitHub/Project attachment roundtrips without a clear source-of-truth decision
- stale references to completed cutovers, retired T99-style cleanup lanes, or detached GitHub todo authority
- assumptions that `Plan Tasks`, `Plan Checkpoints`, `Skill State Registry`, `Schema Registry`, `Tracking Registry`, `Repo File Coverage Detail`, or `Retained Repo Manifest` exist without live schema readback
- conflict between Project Instructions, CP-00, Airtable Governance Control Plane, live Airtable state, helper skill instructions, GitHub source files, or chat-state assumptions
- a helper skill hard-stops, times out, or uses old authority language
- the assistant needs to hand off a clear fix prompt to a later session

## Hard rules
- Do not silently fix authority drift from this skill alone unless the operator explicitly asks for a repair package.
- Prefer reporting precise evidence over broad speculation.
- If live Airtable state and GitHub promoted-history conflict on startup/live queue behavior, prefer Airtable and report GitHub as promoted-history drift unless the task is source-authority comparison.
- If Project Instructions, CP-00, Airtable Governance Control Plane, or live Airtable state conflict on startup/live queue behavior, stop and report the exact conflict.
- Do not create duplicate Work Items or Plans while reporting drift unless the operator requests durable Airtable updates.
- Never include secrets, token values, or hidden credentials in reports.

## Workflow
1. State the task that triggered confusion.
2. List sources consulted or attempted: Project Instructions, CP-00, attachments, Airtable tables/records, GitHub paths, skills, scripts, or uploaded files.
3. Classify the drift using `references/drift_taxonomy.md`.
4. Identify the expected current authority under the v22/v4 operational model.
5. Identify what contradicted or obscured that authority.
6. Run `scripts/authority_drift_report.py` when a deterministic JSON/Markdown report will help.
7. Return a concise chat summary plus a paste-ready repair prompt.

## Command
Create a report from CLI fields:
```bash
python scripts/authority_drift_report.py create   --task "schema alignment review"   --symptom "skill referenced Skill State Registry but live schema did not contain it"   --source "dcoir-source-authority-auditor/SKILL.md"   --source "Airtable list_tables_for_base"   --expected-authority "live Airtable schema readback and Admin Registry skill-state rows"   --observed-drift "old dedicated Skill State Registry assumption"   --recommended-fix "patch skill instructions to use Admin Registry unless live schema proves dedicated registry exists"   --output-dir /mnt/data/dcoir_authority_drift
```

Create a report from JSON:
```bash
python scripts/authority_drift_report.py create --input-json /mnt/data/drift_input.json --output-dir /mnt/data/dcoir_authority_drift
```

## Output contract
Return:
- drift report status
- severity and drift family
- expected authority
- observed conflicting source or missing source
- affected skills/files/tables
- recommended repair lane
- paste-ready prompt for a future DCOIR session
- whether a skill update, Project attachment update, Airtable data update, GitHub source update, or operator decision is needed

## References
Read `references/drift_taxonomy.md` for classification.
Read `references/report_template.md` for report format.
Read `references/repair_prompt_contract.md` for paste-ready repair prompt standards.
