# GitHub Memory Workflow

## Purpose
Use Airtable `Operator Preferences` as the durable working-state preference surface and use the GitHub repository as the human-readable promoted helper-memory surface for decision-policy state without confusing either with governed control-plane authority.

## Repository path
- Root helper-memory folder: use the governed discovery contract helper-memory root
- Decision-policy folder: `helper_memory.root` + `dcoir-decision-policy/`
- Default state file: `helper_memory.root` + `dcoir-decision-policy/decision_policy_memory.md`

## Execution layer
- Use the GitHub connector directly as the default execution layer for helper-memory reads and writes in the current governed repository resolved from the governed discovery contract.
- Re-anchor to Project Instructions, then CP-01, then CP-02 before invoking it.
- Prefer connector `fetch_file` readback after every write and prefer the validated existing-file update lane for modifications.

## Rules
- Re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing skill memory.
- Treat the GitHub memory file as helper working state only.
- Keep the file markdown and human-readable.
- Prefer one canonical file per skill unless the operator explicitly wants snapshots or history.
- Preserve durable overlays, pending candidates, and delivery preferences in separate sections so later review remains deterministic.
- Update the file after material decision-state changes through the GitHub connector directly when the available connector action surface can complete the modification safely.

## Recommended first surfaces
- Airtable `Operator Preferences` when the current branch is preference-sensitive
- `helper_memory.readme` from the governed discovery contract
- `helper_memory.root` + `dcoir-decision-policy/decision_policy_memory.md`

## Write pattern
1. Read Airtable `Operator Preferences` when the current branch depends on operator preference.
2. Read the current GitHub memory file if it exists.
3. Merge current-chat learning with Airtable-held implemented preferences, approved overlays, and pending candidates from the GitHub file.
4. Render the merged state with `render_decision_policy_memory.py`.
5. Use the GitHub connector directly to create or update the canonical memory file in GitHub, reducing operator burden to the smallest bounded manual GitHub action only when connector limitations prevent safe completion.
6. Report what changed, what remains Airtable-only, and whether any candidate still needs GitHub promotion.
