---
name: dcoir-repo-packager
description: build strict dcoir repo-layout zips, github-primary bootstrap bundles, and github desktop manual repo-update patch bundles from the current authoritative dcoir project files. use when chatgpt needs to package the current project workspace for local repo-style testing, prepare a bootstrap refresh that follows the no-duplicate-readable-source rule, or emit a github desktop manual repo-update bundle containing only affected repo-relative files with no wrapper root. this skill is class-prefix aware, prefers control-plane roles over brittle legacy filenames, supports the current github-primary layout, and must stop if the required control-plane roles or requested paths cannot be resolved safely. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-repo-packager|SKILL.md -->

# DCOIR Repo Packager

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.


## Overview
Build strict DCOIR repo-layout ZIPs, GitHub-primary bootstrap/update bundles, and GitHub Desktop manual repo-update patch bundles from the current approved DCOIR file set.

This skill is project-gated and must only act when the current DCOIR control plane is present and the required current roots can be resolved.
Use this skill after authority, promotion, rename, and content decisions are already settled.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Before packaging anything, verify that Airtable-first startup/governance authority and any task-required governed source roles can be resolved. Prefer Airtable governance/registry tables for startup and final cleanup posture; use the governed discovery contract `dcoir_skills/project_discovery_contract.json` and GitHub CP files only when the package depends on repo source roles or promoted-history comparison.

Preferred current authority surfaces:
- Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST` for startup/admin authority
- Airtable `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and `Schema Registry` for final cleanup and retained-surface classification
- GitHub `project_sources/CP-01_DCOIR_Version_Manifest.txt` and `project_sources/CP-02_DCOIR_Change_Log.txt` only when packaging depends on governed repo source roles or promoted-history comparison

Legacy compatibility aliases may be accepted only when the bundled mapping rules explicitly allow them.

Also stop if any of these are true:
- the required control-plane roles cannot be resolved
- a required current root or file is missing from disk for the selected mode
- the current layout drifts beyond what this skill knows how to package safely
- a requested GitHub Desktop manual repo-update path is missing, unsafe, absolute, or escapes the repo root

## What this skill may do
- Build a strict `DCOIR_Project/` repo-layout ZIP for local testing.
- Build a GitHub-primary bootstrap/update bundle with only `Airtable Operator Preferences / governed control-plane references`, retained `supporting_assets/` when present, and Airtable `Release Artifacts` / delivery instructions.
- Build a GitHub Desktop manual repo-update bundle with only the affected repo-relative files and folders, no wrapper root, and a suggested commit summary surfaced in the report.
- Build repo and update outputs in one run when asked.
- Report exactly what it created and where files were emitted.

## What this skill must not do
- Do not decide what files are authoritative.
- Do not promote candidates.
- Do not rewrite file contents.
- Do not infer missing files.
- Do not invent folders or filenames.
- Do not silently continue when the control plane or required roots drift.
- Do not reintroduce duplicate readable governed text files into a Project bootstrap bundle.
- Do not add extra wrapper roots or extra top-level helper files to a GitHub Desktop manual repo-update bundle.

## Packaging modes

1. **Repo mode**
   - Use for local testing downloads.
   - Build the canonical `DCOIR_Project/` tree using the current repo-style layout and preserving current relative paths under the current roots when present:
     - `README.md`
     - `dcoir_skills/`
     - `knowledge/`
     - `project_sources/`
     - `Airtable Operator Preferences / governed control-plane references`
     - `supporting_assets/`
     - optional `release_notes/`

2. **Update mode**
   - Use for a Project bootstrap refresh bundle.
   - Include only bootstrap material that follows the no-duplicate-readable-source rule:
     - `Airtable Operator Preferences / governed control-plane references` when present
     - retained `supporting_assets/` when present
     - Airtable `Release Artifacts` / delivery instructions
   - Do not include readable governed text mirrors from `project_sources/`, `knowledge/`, or `dcoir_skills/` in the bootstrap bundle.

3. **Both mode**
   - Build both repo and update outputs in one run.

4. **GitHub Desktop manual repo-update mode**
   - Use when the operator wants a patch-style ZIP for GitHub Desktop that contains only the affected repo-relative paths.
   - Require one or more `--include-path` values.
   - Preserve the repo-relative paths exactly as provided.
   - Do not add a wrapper root.
   - Surface the suggested commit summary in the JSON report and in the chat response, not as an extra file inside the ZIP.

## Workflow
1. Verify the DCOIR project gate by discovery contract and control-plane role, not just one hard-coded historic filename set.
2. Decide the packaging mode from the user's request.
3. For GitHub Desktop manual repo-update mode, collect the affected repo-relative paths and the suggested commit summary.
4. Run `scripts/create_dcoir_bundle.py`.
5. Read the generated JSON report.
6. Share the ZIP file or files and summarize only the key packaging result.

## Commands
Repo bundle:
```bash
python scripts/create_dcoir_bundle.py --source-dir /mnt/data --output-dir /mnt/data/dcoir_packager_out --mode repo
```

Update bundle:
```bash
python scripts/create_dcoir_bundle.py --source-dir /mnt/data --output-dir /mnt/data/dcoir_packager_out --mode update
```

Both:
```bash
python scripts/create_dcoir_bundle.py --source-dir /mnt/data --output-dir /mnt/data/dcoir_packager_out --mode both
```

GitHub Desktop manual repo-update bundle:
```bash
python scripts/create_dcoir_bundle.py --source-dir /mnt/data --output-dir /mnt/data/dcoir_packager_out --mode github-desktop-manual-update --include-path project_sources/CP-01_DCOIR_Version_Manifest.txt --include-path dcoir_skills/dcoir-repo-packager/SKILL.md --commit-summary "record startup validation and repair github desktop patch-bundle packaging"
```

## Output handling
After the script runs:
- Read the generated `packager_report.json`.
- If `success` is false, explain the failure plainly and do not present the ZIP as valid.
- If `success` is true, provide the resulting ZIP link or links.
- For repo mode, describe it as a strict local-testing repo-layout bundle.
- For update mode, describe it as a GitHub-primary bootstrap bundle and remind the user to follow Airtable `Release Artifacts` / delivery instructions.
- For GitHub Desktop manual repo-update mode, describe it as a patch-style GitHub Desktop bundle containing only the affected repo-relative paths with no wrapper root, and include the suggested commit summary in the response.
- Treat settings content and supporting assets as separate bootstrap-bundle classes.

## References
Use these bundled references when needed:
- `references/layout_rules.md`
- `references/source_mapping.json`
