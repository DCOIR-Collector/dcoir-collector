---
artifact_type: dcoir-skill-regression-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-03T09:43:51Z
authority_basis:
  - Project Instructions v15
  - project_sources/CP-01_DCOIR_Version_Manifest.txt v3.9.15
  - project_sources/CP-02_DCOIR_Change_Log.txt v3.9.15
---

# DCOIR Skill Regression Memory

## Current focus
post-delete GitHub-primary regression continuity for DCOIR helper skills, with dcoir-knowledge-doc-maintainer patched and ready for package replacement plus post-install smoke regression

## Tracked skills
- **dcoir-decision-policy** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement when the package changes again
- **dcoir-collector-qa** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement when the package changes again
- **dcoir-validation-orchestrator** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement when the package changes again
- **dcoir-skill-regression-auditor** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement when the package changes again
- **dcoir-live-test-remediation-planner** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: retest after manual skill replacement when the package changes again
- **dcoir-knowledge-doc-maintainer** (status: patched-and-locally-validated)
  - why: updated skill text matched the post-delete model but scan_project.py still parsed an older manifest shape; scanner was patched, package validation passed, build-doc artifact generation passed, and the current-control-plane success fixture now recognizes governed readable sources
  - next_action: replace the external skill package with the patched bundle and run a quick post-install invocation or accessibility smoke regression

## Fixture baselines
- current-workspace structure validation
- renderer proof test with representative JSON input
- legacy-drift grep for old pre-GitHub assumptions
- current-control-plane minimal fixture with CP-01 v3.9.15, CP-02 v3.9.15, README, DCOIR_Collector.ps1, run_DCOIR_Tests.ps1, and minimal knowledge/ todo files
- missing-control-plane fixture with no manifest or change log
- representative build-doc spec emitting one Knowledge - 01 - Overview and About.md.txt file and supporting_knowledge_docs.zip

## Failure gates
- packaging must succeed for each updated skill
- new renderer scripts must execute without syntax or runtime failure
- scan_project.py must not return zero recognized_governed_github_readable_sources on a current-control-plane fixture
- scan_project.py must still fail clearly when the control plane is missing
- build_knowledge_docs.py output presence and content cues must remain correct after any patch

## Next actions
- replace the patched dcoir-knowledge-doc-maintainer external skill package
- run a post-install invocation or accessibility smoke regression against the post-delete GitHub-primary knowledge-doc workflow
- continue the DOC-04-guided architecture and extracted-folder integration audit after the skill smoke check passes

## Provenance notes
- initialized during the five-skill GitHub-memory rollout
- local regression run on the updated dcoir-knowledge-doc-maintainer-skill.zip uploaded in chat
- quick_validate.py returned Skill is valid
- build_knowledge_docs.py emitted the expected md.txt file and zip
- the original updated package scanner exited 0 on the success fixture but returned recognized_governed_github_readable_sources count 0
- after patching scan_project.py, the same success fixture returned recognized_governed_github_readable_sources count 15
- scan_project.py still exited 1 with FileNotFoundError on the missing-control-plane fixture, preserving the clear failure gate
