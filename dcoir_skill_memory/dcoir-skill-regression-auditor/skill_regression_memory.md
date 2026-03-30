---
artifact_type: dcoir-skill-regression-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-03-30T12:30:01Z
authority_basis:
  - Project Instructions v15
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Skill Regression Memory

## Current focus
GitHub-backed regression-memory continuity for helper-skill maintenance

## Tracked skills
- **dcoir-decision-policy** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement
- **dcoir-collector-qa** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement
- **dcoir-validation-orchestrator** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement
- **dcoir-skill-regression-auditor** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement
- **dcoir-live-test-remediation-planner** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement

## Fixture baselines
- current-workspace structure validation
- renderer proof test with representative JSON input
- legacy-drift grep for old pre-GitHub assumptions

## Failure gates
- packaging must succeed for each updated skill
- new renderer scripts must execute without syntax or runtime failure

## Next actions
- rerun the same regression checks after operator manual install
- extend the same baseline to later GitHub-memory skill conversions

## Provenance notes
- Initialized during the five-skill GitHub-memory rollout.
