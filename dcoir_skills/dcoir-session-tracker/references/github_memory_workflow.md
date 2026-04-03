# GitHub Session-State Workflow

## Purpose
Use the GitHub repository as an optional human-readable helper-state snapshot surface for durable DCOIR continuity when the operator explicitly wants persistence outside the current chat, without confusing it with governed control-plane authority or the primary local working-state file.

## Repository path
- Root helper-memory folder: `dcoir_skill_memory/`
- Session-tracker folder: `dcoir_skill_memory/dcoir-session-tracker/`
- Default snapshot file: `dcoir_skill_memory/dcoir-session-tracker/session_tracker_state.md`

## Execution layer
- Use the GitHub connector directly when a GitHub-backed helper-state snapshot is explicitly requested or when a safe GitHub write is already occurring and a snapshot is intentionally part of the grouped update.
- Re-anchor to Project Instructions, then CP-01, then CP-02 before invoking it.
- Prefer connector `fetch_file` readback after every write and prefer the validated existing-file update lane for modifications.

## Rules
- Re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing session state.
- Treat the GitHub session-state file as optional helper working state only.
- Do not treat the GitHub file as the default primary working state when a local session-state file exists.
- Keep the file markdown and human-readable.
- Prefer one canonical file unless the operator explicitly wants snapshots or history.
- Preserve open items, completed items worth preserving, and promotion candidates in separate sections so later review remains deterministic.
- Update the file through the GitHub connector directly only after the local file and pending promotion state have been inspected when the local file exists.

## Recommended first files
- `dcoir_skill_memory/README.md`
- `dcoir_skill_memory/dcoir-session-tracker/session_tracker_state.md`

## Write pattern
1. Inspect the local session-state file if it exists.
2. Decide whether a GitHub-backed helper-state snapshot is actually needed.
3. Merge current-chat state with any still-relevant open items and durable preference candidates from the GitHub file when the snapshot is being refreshed intentionally.
4. Render the merged state with `render_session_state.py`.
5. Use the GitHub connector directly to create or update the canonical GitHub session-state file, reducing operator burden to the smallest bounded manual GitHub action only when connector limitations prevent safe completion.
6. Report what changed and which items still need promotion, validation, or follow-through.
