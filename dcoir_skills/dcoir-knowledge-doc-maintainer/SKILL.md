---
name: dcoir-knowledge-doc-maintainer
description: maintain and emit africom_soc_ir / dcoir supporting knowledge docs from the current authoritative github-primary project sources. use when chatgpt needs to regenerate or update knowledge markdown, inventory documentation-impacting source changes, explain local testing versus elastic response-action execution, or keep retained supporting knowledge zips aligned to the current governed readable working set. do not use this skill to decide authority, promotions, or content edits. use only after the control plane settles what is current and when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Knowledge Doc Maintainer

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Core workflow
1. Read the current manifest first, preferring `project_sources/CP-01_DCOIR_Version_Manifest.txt`.
2. Read the current change log second, preferring `project_sources/CP-02_DCOIR_Change_Log.txt`.
3. Treat only files marked current in the manifest as authoritative governed GitHub readable sources.
4. Treat retained ZIP assets such as `supporting_assets/supporting_knowledge_docs.zip` and `supporting_assets/DCOIR_Collector.zip` as supporting inputs or retained delivery assets, not control-plane authority.
5. Run `scripts/scan_project.py` against the current source directory to inventory current sources, current knowledge markdown from `knowledge/`, retained delivery assets, collector or harness parameters, quick-command examples, and Sysinternals tools inside `DCOIR_Collector.zip`. Do not assume the retired extracted folder `knowledge/supporting_knowledge_docs/` is present or current.
6. Review the status report before drafting docs.
7. If code intent is unclear, ask targeted clarification questions or provide a targeted prompt that asks the main project workflow to add clearer in-code documentation.
8. Use project sources first. Prefer current control-plane roles and manifest keys over brittle exact filenames when the workspace naming model changes. Use official vendor documentation only when external truth is needed.
9. Build the document content model.
10. Run `scripts/build_knowledge_docs.py` to create the full current markdown Knowledge-doc set and one ZIP.
11. Open every generated `.md.txt` file directly and inspect the title, source table, section order, bullets, tables, and footer note before delivery.
12. Return the ZIP, operator next steps, and a conditional reinventory prompt when the Knowledge-doc existence set changed.

## Hard rules
- Do not decide authority, promotions, or content edits.
- Do not rewrite control-plane or evergreen files.
- Do not let Knowledge docs become control-plane authority.
- Do not guess unclear code intent.
- Prefer current GitHub-native readable script sources such as `project_sources/DCOIR_Collector.ps1` and `project_sources/run_DCOIR_Tests.ps1` when reasoning about the current project files.
- When documenting execution, testing, or operator usage for a script-like file, keep the current GitHub-readable path for provenance and use the runtime filename the operator will actually run.
- Document CMD wrapper behavior only when the current control plane still carries an explicit wrapper source.
- Keep Windows PowerShell 5.1 compatibility as a hard requirement unless the project changes it.
- Distinguish endpoint response-action syntax from local workstation or local test commands.
- Use authoritative-only external sources: Microsoft Learn / Sysinternals, official PowerShell docs, and Elastic Docs.
- Emit Knowledge docs as markdown stored in `.md.txt`. Do not emit `.docx` files.
- Keep the emitted `.md.txt` extension unchanged in repo and update bundles. Do not strip the final `.txt` from generated Knowledge docs.

## What this skill should document
- Collector and harness purpose when grounded in current sources.
- Runtime filenames for local execution and testing guidance.
- PowerShell parameters, defaults, and comment-based help when present.
- CMD wrapper behavior only when explicit in the current source.
- Sysinternals tools present in `supporting_assets/DCOIR_Collector.zip`, normalized by tool family.
- Local workstation and local test execution guidance.
- Elastic response-action guidance where the project explicitly uses it.
- Related technologies only when directly referenced by the current project sources or supporting assets.

## Required outputs
Every execution must produce:
1. A documentation status report.
2. One ZIP named `supporting_knowledge_docs.zip` containing the full current Knowledge-doc set, including unchanged docs.
3. Exact operator next steps.
4. A reinventory prompt when the Knowledge-doc existence set changed.
