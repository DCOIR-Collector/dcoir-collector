# Validation Scenario Library

## Core phases

### pre-live
Use before first live use of a new or materially changed artifact.
Required sections:
- blocking gates
- smoke checks
- deep-regression set
- evidence collection
- readiness criteria

### post-patch
Use after any patch to a testable artifact.
Required sections:
- reproduction of original failure
- patch verification
- rerun of the affected deep-regression set
- regression spillover checks
- restored-readiness criteria

### failed-run
Use after a bad output, runtime error, or packaging defect.
Required sections:
- capture failure evidence
- isolate changed surface
- targeted re-test
- expanded regression around the failed behavior
- recovery gate

### routine
Use for non-emergency health checks.
Required sections:
- drift checks
- representative regression subset
- output artifact verification
- status note

## Scenario overlays

### end-to-end repo workflow
Use when the project needs confidence that the full workflow still hangs together across repo state, governed files, helper skills, and output artifacts.
Add:
- workflow entry points
- handoff boundaries
- generated artifact checks
- representative happy-path execution
- key failure-gate checks

### edge-case and failure-gate
Use when a branch is fragile, failure-prone, or newly repaired.
Add:
- expected failure signatures
- negative fixtures
- stop conditions
- recovery checks

### skill deep dive
Use when a helper skill needs execution, code-hygiene, or capability alignment review.
Add:
- representative trigger coverage
- script execution checks when scripts exist
- stale-instruction or stale-reference review
- governance alignment checks
- code-hygiene follow-ups when needed

### docs/readme/knowledge alignment
Use when README surfaces, routing notes, or knowledge docs need validation against the current repo state.
Add:
- cross-link checks
- inventory alignment checks
- authority-boundary checks
- surface usefulness checks

### packager live-project validation
Use when bundle or packaging behavior must match the current repo posture.
Add:
- required roots and required files
- emitted tree checks
- no-duplicate-readable-source checks
- update-mode bootstrap-safety checks
- GitHub Desktop affected-path bundle checks when manual repo-update delivery is in scope
- installable skill package cleanliness checks for runtime residue such as `__pycache__/`, `*.pyc`, and `.DS_Store`

### session-memory pre-push contract
Use when buffer-capable or GitHub-memory-backed skills should stage their state before a governed push.
Add:
- pre-push flush/manicure checks
- staged governed update checks
- todo synchronization checks
- post-push cleanup checks
- loss-boundary statement: only work since the last push or explicit export may remain at risk

### coordinated multi-skill delivery wave
Use when multiple compatible helper-skill repairs should be surfaced as one bounded manual GitHub/Desktop update instead of many isolated operator actions.
Add:
- batch scope and included skills
- grouped installability checks
- package-cleanliness checks across the whole delivery set
- no-wrapper-root and affected-path bundle checks for manual repo-update zips
- combined readiness criteria for surfacing the batch to the operator
