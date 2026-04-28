<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-repo-packager|layout_rules.md -->

# DCOIR Repo Layout Rules

## Project gate
Resolve Airtable-first authority and task-required governed source roles by role.

Preferred current authority surfaces:
- Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST` for startup/admin authority
- Airtable `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and `Schema Registry` for final cleanup and retained-surface classification
- GitHub `project_sources/governance/control_plane/CP-01_DCOIR_Version_Manifest.txt` and `project_sources/governance/control_plane/CP-02_DCOIR_Change_Log.txt` only when packaging depends on governed repo source roles or promoted-history comparison

Legacy aliases may be accepted only when the bundled mapping rules explicitly include them.
Stop only if the task-required authority/source roles cannot be resolved. Missing GitHub CP files are not a startup blocker when Airtable replacement rows are present.

## Canonical repo-mode bundle tree
Repo mode should preserve the current repo-style layout under:
- `DCOIR_Project/README.md`
- `DCOIR_Project/dcoir_skills/` when present
- `DCOIR_Project/knowledge/` when present
- `DCOIR_Project/project_sources/` when present
- `DCOIR_Project/Airtable Operator Preferences / governed control-plane references` when present
- `DCOIR_Project/supporting_assets/` when present
- `DCOIR_Project/Airtable Release Artifacts / repo release-note source basis` when present

## Canonical update-mode bundle tree
Update mode should include only bootstrap-safe roots:
- `Airtable Operator Preferences / governed control-plane references` when present
- `supporting_assets/` when present
- `Airtable Release Artifacts / repo release-note source basisRELEASE_INSTRUCTIONS.txt`

## Canonical GitHub Desktop manual repo-update bundle tree
GitHub Desktop manual repo-update mode should include only the affected repo-relative files or folders requested for the current patch set:
- preserve the requested repo-relative paths exactly
- do not add a wrapper root
- do not add helper files such as commit-summary text files inside the ZIP
- surface the suggested commit summary in the report and chat output instead

## Hard rules
- Preserve current relative paths in repo mode instead of remapping into stale legacy trees.
- Do not include readable governed text from `project_sources/`, `knowledge/`, or `dcoir_skills/` in update mode.
- Keep package assets such as `.zip` unchanged.
- Keep Knowledge docs unchanged as `.md` or `.md.txt` when those are the native files present in the source tree.
- Do not emit extra files.
- Do not guess where unknown files belong.
- If required control-plane roles or required current roots are missing, stop and require a skill update or source repair.
- If a GitHub Desktop manual repo-update include path is missing, unsafe, absolute, or escapes the repo root, stop instead of guessing.
