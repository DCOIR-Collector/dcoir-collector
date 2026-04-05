# GitHub Memory Workflow

Use the GitHub repository as a human-readable helper-memory surface for live-test remediation state without confusing it with governed control-plane authority.

## Repository path
- Root helper-memory folder: `dcoir_skill_memory/`
- Live-test-remediation folder: `dcoir_skill_memory/dcoir-live-test-remediation-planner/`
- Default state file: `dcoir_skill_memory/dcoir-live-test-remediation-planner/live_test_remediation_memory.md`

## Execution layer
- Use the GitHub connector directly as the default execution layer for helper-memory reads and writes in `malwaredevil/dcoir-collector`.
- Re-anchor to Project Instructions, then `project_sources/CP-01_DCOIR_Version_Manifest.txt`, then `project_sources/CP-02_DCOIR_Change_Log.txt` before invoking it.
- Prefer connector readback after every write and prefer the validated existing-file update lane for modifications.
