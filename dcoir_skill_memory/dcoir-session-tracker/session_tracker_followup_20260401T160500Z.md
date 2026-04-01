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
- Collector split implementation for `project_sources/DCOIR_Collector.ps1`
  - intent: break the large collector source into no more than 10 smaller governed source files that can be reassembled into the full collector.
  - constraints: preserve `DCOIR_Collector.ps1` as the canonical runtime filename; update control-plane references if the readable-source model changes.
  - required follow-on immediately after split: verify and update any affected skills that rely on the collector readable-source path or assumptions.

## Next item after the split and skill audit
- GitHub connector permanent-memory workflow capture
  - intent: preserve the validated GitHub connector write/update process in a durable GitHub-readable location so it is not lost again.
  - notes: this is the operator-designated emergency task and should be the next queued item after the collector split and affected-skill refresh.

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
