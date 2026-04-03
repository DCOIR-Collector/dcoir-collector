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
- follow release_notes/RELEASE_INSTRUCTIONS.txt
