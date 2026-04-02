---
artifact_type: dcoir-session-followup
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
captured_at_utc: 2026-04-01T16:05:00Z
authority_basis:
  - Project Instructions v15
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
provenance:
  - current_chat
---

# DCOIR Session Follow-up Queue

## Highest priority active item
- Audit and update affected helper skills for the collector split and connector-first GitHub execution model.

## Current durable memory location
- Root: `knowledge/task_memory`
- Manifest: `knowledge/task_memory/00_registry/task_memory_manifest.yaml`
- Compiled lookup: `knowledge/task_memory/30_compiled/fast_lookup.json`

## Next item after the skill audit
- Maintain and extend the GitHub task-memory bank with new validated procedures, limits, failure signatures, and promoted session lessons as future connector or workflow issues are solved.

## Affected skills already identified for post-split audit
- `dcoir-collector-qa`
- `dcoir-live-test-remediation-planner`
- `dcoir-decision-policy`
- `dcoir-change-impact-analyzer`
- `dcoir-repo-packager`
- `dcoir-knowledge-doc-maintainer`
- `dcoir-operator-workflow-hardener`

## Audit rationale
These skills or their helper scripts currently reference `project_sources/DCOIR_Collector.ps1`, `run_DCOIR_Tests.ps1`, or current collector-source assumptions and should be checked after the split before any cleanup or retirement decisions are made.
