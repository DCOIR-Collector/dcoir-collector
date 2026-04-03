# GitHub Memory Workflow

## Purpose
Use the GitHub repository as a human-readable helper-memory surface for collector QA state without confusing it with governed control-plane authority.

## Repository path
- Root helper-memory folder: `dcoir_skill_memory/`
- Collector-QA folder: `dcoir_skill_memory/dcoir-collector-qa/`
- Default state file: `dcoir_skill_memory/dcoir-collector-qa/collector_qa_memory.md`

## Execution layer
- Use the GitHub connector directly as the default execution layer for helper-memory reads and writes in `malwaredevil/dcoir-collector`.
- Re-anchor to Project Instructions, then CP-01, then CP-02 before invoking it.
- Prefer connector `fetch_file` readback after every write and prefer the validated existing-file update lane for modifications.

## Rules
- Re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing skill memory.
- Treat the GitHub memory file as helper working state only.
- Keep the file markdown and human-readable.
- Prefer one canonical file per skill unless the operator explicitly wants snapshots or history.
- Preserve known failure lanes, active repair candidates, and recent validation results in separate sections so later QA review remains deterministic.
- Update the file after material QA-state changes through the GitHub connector directly when the available connector action surface can complete the modification safely.

## Recommended first files
- `dcoir_skill_memory/README.md`
- `dcoir_skill_memory/dcoir-collector-qa/collector_qa_memory.md`

## Write pattern
1. Read the current memory file if it exists.
2. Merge the current QA state with any still-relevant memory sections.
3. Render the merged state with `render_collector_qa_memory.py`.
4. Use the GitHub connector directly to create or update the canonical memory file in GitHub, reducing operator burden to the smallest bounded manual GitHub action only when connector limitations prevent safe completion.
5. Report what changed and which lanes still need replay, repair, or deeper regression.
