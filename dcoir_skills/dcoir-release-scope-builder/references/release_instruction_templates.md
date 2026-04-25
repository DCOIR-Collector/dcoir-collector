<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-release-scope-builder|release_instruction_templates.md -->

# Release Instruction Templates

## targeted skill update
Use when only one helper skill changes and no project-readable source file set changes.
Template cues:
- replace only the updated skill package
- rerun skill-specific deep regression after the patch
- no project-source full refresh required unless later analysis expands scope

## repo-layout local testing
Use when the operator needs a local runnable tree.
Template cues:
- build strict repo-layout bundle
- verify runtime filenames
- keep this separate from project upload instructions

## full-refresh project upload
Use when current project sources, supporting assets, or structural mappings changed.
Template cues:
- delete/replace the current uploaded project source set as directed
- upload all required current classes from the bundle
- follow Airtable Release Artifacts / repo release-note source-basis filesRELEASE_INSTRUCTIONS.txt

## github desktop manual repo-update
Use when governed repo-readable files changed in the GitHub-primary working line and the operator is applying a repo patch through GitHub Desktop.
Template cues:
- provide one repo-update zip with only the affected repo-relative files and folders
- include a suggested GitHub commit `Summary` in the response, not inside the zip
- keep repo-update steps separate from skill-install steps

## batched skill-update wave
Use when multiple compatible helper skills changed and the operator prefers fewer one-skill-at-a-time installs.
Template cues:
- provide one outer zip whose top level contains only the affected per-skill zip files
- require per-skill regression coverage before the batch is treated as ready
- pair with a repo-update bundle when governed repo-readable files changed in the same wave
