---
name: dcoir-knowledge-doc-maintainer
description: maintain and emit africom_soc_ir / dcoir supporting knowledge docs from the current authoritative github-primary project sources. use when chatgpt needs to regenerate or update knowledge markdown, inventory documentation-impacting source changes, explain local testing versus elastic response-action execution, refresh stale knowledge-doc clusters that share the same outdated source-name or removed-wrapper assumptions, or keep retained supporting knowledge zips aligned to the current governed readable working set. do not use this skill to decide authority, promotions, or content edits. use only after the control plane settles what is current and when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-knowledge-doc-maintainer|SKILL.md -->

# DCOIR Knowledge Doc Maintainer

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.


## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Core workflow
1. Resolve Airtable-first startup/control-plane authority first for live state.
2. Read GitHub `CP-01`/`CP-02` only when the documentation task depends on governed repo source roles, promoted-history comparison, or source-file inspection.
3. Treat only files marked current in the manifest as authoritative governed GitHub readable sources.
4. Treat `supporting_assets/supporting_knowledge_docs.zip`, settings mirrors, and `supporting_assets/DCOIR_Collector.zip` as supporting inputs or retained delivery assets, not control-plane authority.
5. Run `scripts/scan_project.py` against the current source directory to inventory current sources, the current root repo guide, the split todo structure, current knowledge markdown from `knowledge/`, retained delivery assets, collector or harness parameters, quick-command examples, and Sysinternals tools inside `DCOIR_Collector.zip`. Do not assume the retired extracted folder `knowledge/supporting_knowledge_docs/` is present or current.
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
- Treat `README.md` and the split todo structure as current human-readable project context when they are present in the current control plane.
- When documenting execution, testing, or operator usage for a script-like file, reference the runtime filename the operator will actually use and keep the current GitHub-readable repo path only as provenance.
- Keep Windows PowerShell 5.1 compatibility as a hard requirement unless the project changes it.
- Distinguish endpoint response-action syntax from local workstation or local test commands.
- Use authoritative-only external sources: Microsoft Learn / Sysinternals, official PowerShell docs, and Elastic Docs.
- Emit Knowledge docs as markdown stored in `.md.txt`. Do not emit `.docx` files.
- Keep the emitted `.md.txt` extension unchanged in repo and update bundles. Do not strip the final `.txt` from Knowledge docs.

## What this skill should document
- Collector and harness purpose when grounded in current sources.
- Runtime filenames for local execution and testing guidance.
- PowerShell parameters, defaults, and comment-based help when present.
- CMD wrapper behavior only when explicit in the current governed source line.
- Sysinternals tools present in `supporting_assets/DCOIR_Collector.zip`, normalized by tool family.
- Local workstation and local test execution guidance.
- Elastic response-action guidance where the project explicitly uses it.
- Related technologies only when directly referenced by the current project sources or supporting assets.

## Knowledge-doc naming and placement
- Every generated doc must use `Knowledge - ## - Title.md.txt`.
- These are supporting human-readable docs only.
- They are not control-plane authority.
- The editable working source for knowledge maintenance is `knowledge/*.md` when a maintained GitHub-readable knowledge-doc markdown working set exists.
- `supporting_assets/supporting_knowledge_docs.zip` may be retained as a delivery or reference asset, but it is not control-plane authority and should not be treated as the preferred editable readable source.
- The retired extracted folder `knowledge/supporting_knowledge_docs/` is not part of the current default maintenance model and should not be recreated unless the control plane explicitly restores it.
- Emit unchanged native `.md.txt` files inside the ZIP.
- Do not version emitted doc filenames.

## Required outputs
Every execution must produce:
1. A documentation status report.
2. One ZIP named `supporting_knowledge_docs.zip` containing the full current Knowledge-doc set, including unchanged docs.
3. Exact operator next steps.
4. A reinventory prompt when the Knowledge-doc existence set changed.

## Required operator steps
Always tell the operator:
- Replace the retained `supporting_assets/supporting_knowledge_docs.zip` asset when Knowledge docs are refreshed and a ZIP delivery artifact is still needed.
- Keep `knowledge/*.md` in GitHub as the editable readable working set when the current control plane uses GitHub-readable knowledge-doc markdown.
- Do not treat the ZIP as the source of truth.
- Do not recreate `knowledge/supporting_knowledge_docs/` unless the control plane explicitly restores that extracted-folder model.
- If the Knowledge-doc existence set changed, refresh any retained delivery asset or downstream packaging workflow that still depends on the ZIP.

## Initial document set
Use the stable initial set from `references/initial_doc_set.md` unless the operator narrows scope.
If a page cannot be generated truthfully from the current sources and authoritative external docs, skip it and explain why instead of inventing content.

## Script usage
Run the scanner:
```bash
python scripts/scan_project.py --source-dir /mnt/data --output-json /mnt/data/knowledge_status.json --state-file /mnt/data/knowledge_state.json --write-state /mnt/data/knowledge_state.json
```

The scanner should prefer current class-prefixed control-plane names and manifest-declared current source roles, while tolerating legacy aliases when older workspaces are still present.

Build docs from a content model:
```bash
python scripts/build_knowledge_docs.py --spec-json /mnt/data/knowledge_docs_spec.json --output-dir /mnt/data/knowledge_docs --zip-path /mnt/data/supporting_knowledge_docs.zip
```

## References
- `references/initial_doc_set.md`
- `references/operator_workflow.md`
- `references/reinventory_prompt_template.md`

## Airtable testing workflow alignment

When knowledge docs describe collector or Gemini testing, include the current operating note that Airtable table `Validation Test Cases` is the standard dynamic manual-testing surface and that GitHub remains the engineering/source/packaging authority.
