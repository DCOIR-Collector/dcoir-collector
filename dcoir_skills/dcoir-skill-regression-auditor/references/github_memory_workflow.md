# GitHub Memory Workflow

## Purpose
Use the GitHub repository as a human-readable helper-memory surface for skill-regression state without confusing it with governed control-plane authority.

## Repository path
- Root helper-memory folder: use the governed discovery contract helper-memory root
- Skill-regression folder: `helper_memory.root` + `dcoir-skill-regression-auditor/`
- Default state file: `helper_memory.root` + `dcoir-skill-regression-auditor/skill_regression_memory.md`

## Execution layer
- Use the GitHub connector directly as the default execution layer for helper-memory reads and writes in the current governed repository resolved from the governed discovery contract.
- Re-anchor to Project Instructions, then CP-01, then CP-02 before invoking it.
- Prefer connector `fetch_file` readback after every write and prefer the validated existing-file update lane for modifications.

## Rules
- Re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing skill memory.
- Treat the GitHub memory file as helper working state only.
- Keep the file markdown and human-readable.
- Prefer one canonical file per skill unless the operator explicitly wants snapshots or history.
- Preserve tracked skills, fixture baselines, and failure gates in separate sections so later regression review remains deterministic.
- Update the file after material regression-state changes through the GitHub connector directly when the available connector action surface can complete the modification safely.

## Recommended first files
- `helper_memory.readme` from the governed discovery contract
- `helper_memory.root` + `dcoir-skill-regression-auditor/skill_regression_memory.md`

## Write pattern
1. Read the current memory file if it exists.
2. Merge the current regression state with any still-relevant memory sections.
3. Render the merged state with `render_skill_regression_memory.py`.
4. Use the GitHub connector directly to create or update the canonical memory file in GitHub, reducing operator burden to the smallest bounded manual GitHub action only when connector limitations prevent safe completion.
5. Report what changed and which skills, fixtures, or gates still need follow-through.
