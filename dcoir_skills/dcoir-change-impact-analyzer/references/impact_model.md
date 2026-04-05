# Impact Model

## Purpose
This skill determines what else must be refreshed, reviewed, regression-tested, or repackaged when a DCOIR file, asset, workflow, or skill changes.

## Decision hierarchy
1. Resolve the current GitHub-primary control plane from the workspace.
2. Classify the changed target by current role, stable naming pattern, current repo-relative path, or known skill name.
3. Apply direct refresh rules.
4. Apply cross-cutting review rules.
5. Apply the deep-regression default for anything testable that could affect production behavior.
6. Pick the strongest packaging recommendation among all matched rules.

## Packaging strength order
- none
- targeted_skill_update
- batched_skill_update_wave
- github_desktop_manual_repo_update
- full_refresh_project_upload

## Anti-pattern handling
- Direct edits to `PP-08_Combined_Analyst_Facing_Master_Prompt_*` without corresponding modular prompt changes should trigger a warning because PP-08 is a generated runtime artifact, not the modular source of truth.
- Structural or naming-model changes should push packaging at least to `github_desktop_manual_repo_update`, and to `full_refresh_project_upload` only when the broader project-upload class is actually required.
- Current-supporting-asset changes should never be treated as control-plane changes unless the manifest also changes.
- Old Project-mirror filenames should not be treated as current when the manifest has already moved the working set to GitHub-native readable sources.

## Deep-regression baseline
Default to deep regression for:
- all DCOIR skills before live use and after every patch
- scripts, harnesses, repo generators, and bundle generators
- collector-adjacent workflow changes
- prompt-pack behavior changes that affect runtime or generated artifacts

## Output intent
The report should be specific enough that ChatGPT can answer:
- what must be regenerated now
- what only needs review
- what must be deep-regression tested
- whether a targeted skill update, batched skill-update wave, GitHub Desktop manual repo-update bundle, or full-refresh project-upload bundle is the right next delivery class
