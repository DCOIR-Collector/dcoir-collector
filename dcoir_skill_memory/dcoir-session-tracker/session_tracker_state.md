---
artifact_type: dcoir-session-state
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-03-30T13:50:00Z
authority_basis:
  - Project Instructions v15
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
merge_mode: merge
imports_merged:
  - current_chat
  - github_skill_memory
---

# DCOIR Session State

## Current phase
Design the project-scoped GitHub super-skill after helper-memory rollout, with broader GitHub control surfaces deferred behind the MVP.

## Best next move
Finalize the phased build spec for the project-scoped GitHub super-skill with explicit MVP support for updating readable governed repo text files.

## Open items
### session_only
- [ST-010] Design the project-scoped GitHub super-skill (status: in_progress; provenance: current_chat)
  - why: This is now the active next line of work.
  - next_action: Finalize the phased MVP and later-phase capability map.
  - related: skill-creator, malwaredevil/dcoir-collector

### durable_preference_candidate
- [ST-002] Keep helper-skill memory separate in GitHub (status: open; provenance: current_chat)
  - why: Helper memory should remain separate from governed project files.
  - next_action: Continue using dcoir_skill_memory/ as the helper-memory root.
  - related: dcoir_skill_memory/
- [ST-003] Bundle multi-skill updates into one zip (status: open; provenance: current_chat)
  - why: The operator prefers one download for grouped manual skill updates.
  - next_action: Keep providing one bundle zip when multiple skills are updated together.
  - related: dcoir-decision-policy
- [ST-013] Defer broader GitHub project-control and management surfaces to later phases while keeping full GitHub coverage as the ideal endstate (status: open; provenance: current_chat)
  - why: The MVP should stay focused, but the long-term goal is a full GitHub interface.
  - next_action: Keep wiki, projects, and other broader GitHub control surfaces in the later-phase map, not the MVP.
  - related: dcoir-github-operator
- [ST-014] Ensure the GitHub super-skill MVP can update readable governed repo text files across the project, excluding zip and other binary assets (status: open; provenance: current_chat)
  - why: The MVP must be able to update all relevant readable project sources without waiting for a later release.
  - next_action: Treat readable text updates in project_sources/, knowledge/, project_settings/, and release_notes/ as MVP scope, while keeping zip/binary assets out of MVP write scope.
  - related: dcoir-github-operator, project_sources/, knowledge/, project_settings/, release_notes/

### follow_on_validation
- [ST-011] Update dependent skills to use the GitHub super-skill after it is designed, tested, and implemented (status: open; provenance: current_chat)
  - why: The super-skill will not deliver full value unless the dependent helper skills adopt it where appropriate.
  - next_action: After the super-skill is complete, review and update the skills that should use it.
  - related: dcoir-*
- [ST-012] Update project sources, workflows, controls, and instructions to use the GitHub super-skill after it is designed, tested, and implemented (status: open; provenance: current_chat)
  - why: The governed project documentation and workflow surface must reflect the new capability once it becomes real.
  - next_action: After the super-skill is complete, refresh the affected project sources, workflow docs, control-plane references, and instructions.
  - related: project_sources/, project_settings/

## Completed or resolved this session
- [ST-005] Implement GitHub-backed memory for the current high-value five-skill set (status: done; provenance: current_chat)
  - why: The requested rollout was completed and packaged.
  - next_action: Proceed to the next todo item.
  - related: dcoir-decision-policy, dcoir-collector-qa, dcoir-validation-orchestrator, dcoir-skill-regression-auditor, dcoir-live-test-remediation-planner

## Provenance notes
- Updated after clarifying the GitHub super-skill MVP write scope.
