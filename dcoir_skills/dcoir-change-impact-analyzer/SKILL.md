---
name: dcoir-change-impact-analyzer
description: analyze proposed or completed changes in the africom_soc_ir / dcoir project and determine the downstream refresh set, helper-skill impacts, regression requirements, primary delivery recommendation, any secondary skill-delivery recommendation, and stop conditions. use when chatgpt needs to answer what else must change after a file, asset, skill, workflow, packaging, or prompt-pack update; when validating whether a change is safe to promote; or when deciding whether a targeted update or full-refresh bundle is required. prefer the current Airtable-first governance posture plus governed GitHub source/readback surface, current manifest roles, and current gitHub-native collector or harness filenames over older project-mirror assumptions. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-change-impact-analyzer|SKILL.md -->

# DCOIR Change Impact Analyzer

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.



Use this skill to turn a proposed or completed DCOIR change into an explicit downstream work list.

## Core workflow
1. Resolve Airtable-first startup/control-plane authority for startup, queue, administrative, and helper-memory context.
2. Read GitHub `CP-01`/`CP-02` only when the impact analysis requires repository-source role resolution, source-file comparison, packaging scope, promoted-history comparison, or final T99 keep/delete review.
3. Resolve the current working set from Airtable live state plus governed GitHub source files only when those source files are in scope.
4. Identify the changed files, changed assets, changed skills, or changed workflow targets from the user request.
5. Run `scripts/analyze_change_impact.py` with the changed targets.
6. Read the generated markdown and json reports.
7. Return the direct refresh set, conditional review set, deep-regression set, primary delivery recommendation, any secondary skill-delivery recommendation, and stop conditions.

## Inputs this skill supports
- Explicit file list such as `project_sources/PP-03_Baseline_Triage_Prompt_v1_0_0.txt`, `PP-07_Agent_Guardrails_v1_0_0.txt`, or `project_sources/collector/source/DCOIR_Collector.ps1`
- Supporting assets such as `supporting_assets/supporting_knowledge_docs.zip` or `supporting_knowledge_docs.zip`
- Skill names such as `dcoir-repo-packager`
- Short natural-language requests when ChatGPT can confidently map the request to the changed targets before running the script

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Before analyzing impact, verify the task-required authority surface from the workspace.

Preferred current authority surfaces:
- Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST` for startup/admin/current-state authority
- Airtable `Queue Control`, `Work Items`, active `Plans`, and `Plan Tasks` when the active work-line structure changed
- Airtable `Schema Registry`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, `Tracking Registry`, and release tracking tables when downstream impact matters
- GitHub `project_sources/governance/control_plane/CP-01_DCOIR_Version_Manifest.txt` and `project_sources/governance/control_plane/CP-02_DCOIR_Change_Log.txt` only when repository-source role resolution, promoted-history comparison, packaging, or final T99 keep/delete review is in scope
- `README.md` and governed repo source files when the current repo-guide posture or source content is part of the changed set
- retired GitHub todo files only when the migration or retirement path itself is part of the changed set

Stop only when the required authority surface for the current task cannot be resolved. For startup/admin/live-queue tasks, use Airtable authority; for repository-source tasks, use GitHub CP/source files or their Airtable replacement rows if CP files have been detached.

## Hard rules
- Do not decide authority or promotion status.
- Do not silently ignore changed current files.
- Do not silently treat retired GitHub todo files as active authority after Airtable queue-control cutover.
- Do not assume PP-08 is the source of truth over PP-01 through PP-07.
- Do not treat supporting assets as control-plane authority.
- Hard-stop unknown targets that fall outside the current rule set; do not emit a provisional packaging recommendation for them.
- When the change affects a skill, script, packaging path, or runtime behavior, require deep regression before the result is treated as ready for live or production use.
- Prefer GitHub Desktop manual repo-update bundles for current governed repo-readable changes in the GitHub-primary working line unless the change truly belongs to repo-layout local testing, targeted skill-only delivery, a batched skill-update wave, or a full-refresh project-upload class.
- Prefer batched skill-update waves over one-skill-at-a-time delivery when multiple compatible helper-skill fixes are already ready.
- Reserve full-refresh project-upload recommendations for changes that truly require the broader project-upload class rather than ordinary governed GitHub repo updates.
- Prefer manifest role resolution over brittle filename assumptions.

## Deep-regression rule
The operator preference is to catch issues before production impact.

Treat deep regression as the default whenever the changed target is any of these:
- a DCOIR skill
- a script or harness source
- collector logic or packaging
- prompt-pack behavior that affects runtime outputs
- repo or update-bundle generation
- anything else that can be tested reliably

## Output contract
Return these sections in order:
1. Change summary
2. Directly changed targets
3. Required refresh set
4. Conditional review set
5. Deep-regression test set
6. Packaging and delivery recommendation
7. Stop conditions and warnings

## Commands
Analyze explicit changed targets:
```bash
python scripts/analyze_change_impact.py   --source-dir /mnt/data   --output-dir /mnt/data/dcoir_change_impact_out   --changed-target PP-03_Baseline_Triage_Prompt_v1_0_0.txt   --changed-target project_sources/collector/source/DCOIR_Collector.ps1
```

Analyze a skill change:
```bash
python scripts/analyze_change_impact.py   --source-dir /mnt/data   --output-dir /mnt/data/dcoir_change_impact_out   --changed-target dcoir-repo-packager
```

## Output handling
After the script runs:
- Read `dcoir_change_impact_report.md` and `dcoir_change_impact_report.json`.
- If the report says `analysis_status` is `failure`, explain the exact stop reason.
- If the report says `analysis_status` is `success`, summarize the required refresh set, deep-regression set, and the delivery recommendation plainly.
- Call out anti-patterns such as direct PP-08 edits without corresponding modular prompt-pack changes.
- Treat helper-skill refreshes and deep regression as first-class downstream work items when the rules require them.

## References
Use these bundled references when needed:
- `references/impact_rules.json`
- `references/impact_model.md`
