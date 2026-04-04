# DCOIR Repo Layout Rules

## Project gate
Resolve the current control plane by role.

Preferred current control-plane files:
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- `project_sources/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt`
- `project_sources/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt`

Legacy aliases may be accepted only when the bundled mapping rules explicitly include them.
Stop if the control-plane roles cannot be resolved.

## Canonical repo-mode bundle tree
Repo mode should preserve the current repo-style layout under:
- `DCOIR_Project/README.md`
- `DCOIR_Project/dcoir_skills/` when present
- `DCOIR_Project/knowledge/` when present
- `DCOIR_Project/project_sources/` when present
- `DCOIR_Project/project_settings/` when present
- `DCOIR_Project/supporting_assets/` when present
- `DCOIR_Project/release_notes/` when present

## Canonical update-mode bundle tree
Update mode should include only bootstrap-safe roots:
- `project_settings/` when present
- `supporting_assets/` when present
- `release_notes/RELEASE_INSTRUCTIONS.txt`

## Hard rules
- Preserve current relative paths in repo mode instead of remapping into stale legacy trees.
- Do not include readable governed text from `project_sources/`, `knowledge/`, or `dcoir_skills/` in update mode.
- Keep package assets such as `.zip` unchanged.
- Keep Knowledge docs unchanged as `.md` or `.md.txt` when those are the native files present in the source tree.
- Do not emit extra files.
- Do not guess where unknown files belong.
- If required control-plane roles or required current roots are missing, stop and require a skill update or source repair.
