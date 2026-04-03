---
artifact_type: dcoir-skill-regression-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-03T10:11:30Z
authority_basis:
  - Project Instructions v15
  - project_sources/CP-01_DCOIR_Version_Manifest.txt v3.9.17
  - project_sources/CP-02_DCOIR_Change_Log.txt v3.9.17
---

# DCOIR Skill Regression Memory

## Current focus
broad `dcoir-*` helper-skill deep scan and patch campaign, with dcoir-skill-regression-auditor patched first so it can be trusted as the test harness for the remaining skills

## Tracked skills
- **dcoir-decision-policy** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: deep-scan after regression-auditor replacement and smoke regression complete
- **dcoir-collector-qa** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: deep-scan after regression-auditor replacement and smoke regression complete
- **dcoir-validation-orchestrator** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: deep-scan after regression-auditor replacement and smoke regression complete
- **dcoir-skill-regression-auditor** (status: patched-and-packaged-validated)
  - why: fixture language and planner output were tightened for the current narrative-manifest control plane and the campaign rule to test the tester first
  - next_action: replace the external skill package with the patched bundle and run a quick post-install invocation or accessibility smoke regression
- **dcoir-live-test-remediation-planner** (status: validated)
  - why: GitHub-memory workflow and renderer added
  - next_action: deep-scan after regression-auditor replacement and smoke regression complete
- **dcoir-knowledge-doc-maintainer** (status: patched-and-locally-validated)
  - why: updated skill text matched the post-delete model but scan_project.py still parsed an older manifest shape; scanner was patched, package validation passed, build-doc artifact generation passed, and the current-control-plane success fixture now recognizes governed readable sources
  - next_action: confirm the installed package matches the patched bundle during the broader helper-skill scan

## Fixture baselines
- current-workspace structure validation
- renderer proof test with representative JSON input
- legacy-drift grep for old pre-GitHub assumptions
- current-control-plane minimal fixture with CP-01 v3.9.17, CP-02 v3.9.17, README, DCOIR_Collector.ps1, run_DCOIR_Tests.ps1, and minimal knowledge/ todo files
- missing-control-plane fixture with no manifest or change log
- representative build-doc spec emitting one Knowledge - 01 - Overview and About.md.txt file and supporting_knowledge_docs.zip
- package replacement smoke fixture for external skill replacement and quick accessibility test

## Failure gates
- packaging must succeed for each updated skill
- new or modified scripts must execute without syntax or runtime failure
- plan or scanner scripts must not ignore the current narrative-manifest control-plane model when that model is part of the skill contract
- missing-control-plane or missing-required-file fixtures must still stop clearly
- emitted files must be verified by presence and content cues rather than exit code alone

## Next actions
- replace the patched dcoir-skill-regression-auditor external skill package
- run a post-install invocation or accessibility smoke regression against the patched regression-auditor package
- use the refreshed regression-auditor package to deep-scan the remaining `dcoir-*` skills in bounded batches
- continue the DOC-04-guided architecture and extracted-folder integration audit after the skill smoke check passes

## Provenance notes
- initialized during the five-skill GitHub-memory rollout
- knowledge-doc-maintainer was previously patched and locally validated against the post-delete GitHub-primary control-plane fixture
- the regression-auditor package validated, its updated planner script executed successfully, and the patched bundle was packaged for external replacement
- operator preference note captured separately in continuity: when optional project-helpful work can be done through ChatGPT Codex, present it as step-by-step, click-by-click learning tasks starting basic before advanced
