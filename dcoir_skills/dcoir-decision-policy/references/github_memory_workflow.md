# GitHub Memory Workflow

## Purpose
Use the GitHub repository as a human-readable helper-memory surface for decision-policy state without confusing it with governed control-plane authority.

## Repository path
- Root helper-memory folder: `dcoir_skill_memory/`
- Decision-policy folder: `dcoir_skill_memory/dcoir-decision-policy/`
- Default state file: `dcoir_skill_memory/dcoir-decision-policy/decision_policy_memory.md`

## Execution layer
- Use the GitHub connector directly as the default execution layer for helper-memory reads and writes in `malwaredevil/dcoir-collector`.
- Re-anchor to Project Instructions, then CP-01, then CP-02 before invoking it.
- Prefer connector `fetch_file` readback after every write and prefer the validated existing-file update lane for modifications.

## Rules
- Re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing skill memory.
- Treat the GitHub memory file as helper working state only.
- Keep the file markdown and human-readable.
- Prefer one canonical file per skill unless the operator explicitly wants snapshots or history.
- Preserve durable overlays, pending candidates, and delivery preferences in separate sections so later review remains deterministic.
- Update the file after material decision-state changes through the GitHub connector directly when the available connector action surface can complete the modification safely.

## Recommended first files
- `dcoir_skill_memory/README.md`
- `dcoir_skill_memory/dcoir-decision-policy/decision_policy_memory.md`

## Write pattern
1. Read the current memory file if it exists.
2. Merge current-chat learning with approved overlays and pending candidates from the file.
3. Render the merged state with `render_decision_policy_memory.py`.
4. Use the GitHub connector directly to create or update the canonical memory file in GitHub, reducing operator burden to the smallest bounded manual GitHub action only when connector limitations prevent safe completion.
5. Report what changed and whether any candidate still needs approval or promotion.
