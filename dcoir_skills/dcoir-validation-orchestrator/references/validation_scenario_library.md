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

### routine
Use for non-emergency health checks.
Required sections:
- drift checks
- representative regression subset
- output artifact verification
