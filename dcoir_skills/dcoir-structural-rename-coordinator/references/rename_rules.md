# Rename Rules

Structural renames must update every dependent mapping, skill, test, README, routing note, and delivery instruction that still points to the retired name.

## Delivery posture intent
- helper-skill-only rename -> `targeted_skill_update` or `batched_skill_update_wave`
- governed repo-readable rename with no broader project-upload effect -> `github_desktop_manual_repo_update_bundle`
- control-plane, layout-root, or source-class transition -> `full_refresh_project_upload`

## Stop conditions
- stop if the rename touches control-plane files and the new name is not reflected everywhere current state is resolved
- stop if a generated artifact is being renamed while its modular source of truth is left unchanged
- stop if README and routing surfaces would continue to point at the retired name after the patch
