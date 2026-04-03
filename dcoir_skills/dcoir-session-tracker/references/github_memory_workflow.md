# GitHub Session-State Workflow

## Purpose
Use the GitHub repository as a human-readable session-state surface for durable DCOIR continuity without confusing it with governed control-plane authority.

## Repository path
- Root helper-memory folder: `dcoir_skill_memory/`
- Session-tracker folder: `dcoir_skill_memory/dcoir-session-tracker/`
- Default state file: `dcoir_skill_memory/dcoir-session-tracker/session_tracker_state.md`

## Execution layer
- Use the GitHub connector directly as the default execution layer for session-state reads and writes in `malwaredevil/dcoir-collector`.
- Re-anchor to Project Instructions, then CP-01, then CP-02 before invoking it.
- Prefer connector `fetch_file` readback after every write and prefer the validated existing-file update lane for modifications.

## Rules
- Re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing session state.
- Treat the GitHub session-state file as helper working state only.
- Keep the file markdown and human-readable.
- Prefer one canonical file unless the operator explicitly wants snapshots or history.
- Preserve open items, completed items worth preserving, and promotion candidates in separate sections so later review remains deterministic.
- Update the file through the GitHub connector directly after material session-state changes when the available connector action surface can complete the modification safely.

## Recommended first files
- `dcoir_skill_memory/README.md`
- `dcoir_skill_memory/dcoir-session-tracker/session_tracker_state.md`

## Write pattern
1. Read the current session-state file if it exists.
2. Merge current-chat state with any still-relevant open items and durable preference candidates from the file.
3. Render the merged state with `render_session_state.py`.
4. Use the GitHub connector directly to create or update the canonical session-state file in GitHub, reducing operator burden to the smallest bounded manual GitHub action only when connector limitations prevent safe completion.
5. Report what changed and which items still need promotion, validation, or follow-through.
