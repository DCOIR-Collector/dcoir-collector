# Local session-state workflow

## Purpose
Use a real local JSON file as the primary session-tracker working-state surface when code execution and file writing are available.

## Default path
- `/mnt/data/dcoir_session_tracker/session_state.json`

## Primary script
- `scripts/session_state_store.py`

## Core commands
Initialize the file:
```bash
python scripts/session_state_store.py init
```

Inspect the file:
```bash
python scripts/session_state_store.py inspect
```

Upsert or update one verbose item:
```bash
python scripts/session_state_store.py upsert --item-json '{"id":"S-001","bucket":"session_only","title":"example title","detail":"full context line that makes the item understandable in isolation","why":"why this matters","next_action":"next action to take","carry_forward_note":"what the next session should remember if this is still open","promotion_target":"project_sources/LOG-01_DCOIR_Todo_Log.txt"}'
```

Mark one item done and move it to completed:
```bash
python scripts/session_state_store.py complete --id S-001
```

Remove an item entirely:
```bash
python scripts/session_state_store.py remove --id S-001
```

Update summary fields:
```bash
python scripts/session_state_store.py set-summary --current-phase "example phase" --best-next-move "example next move"
```

## Verbosity requirement
The local JSON file is allowed to preserve concise helper metadata, but materially important operator-facing items should carry enough context to be understood in isolation.

Minimum recommended item fields:
- `title`
- `detail`
- `why`
- `next_action`
- `carry_forward_note` when later resume clarity would benefit
- `promotion_target` when the likely governed destination is already known

Preferred additional fields when useful:
- `operator_language`
- `impact_if_missed`
- `desired_outcome`
- `flush_trigger`
- `related`

## Inspection output requirements
A valid inspection should surface:
- absolute path
- filename
- file size in bytes
- modified time
- sha256 checksum
- counts by open bucket
- completed item count
- optional state excerpt when requested

## Truth rules
- Do not claim a real local session-state file exists until `inspect` proves it.
- Do not treat a merely described buffer as equivalent to a file-backed local state.
- The local JSON file is the primary working state when it exists.
- GitHub-backed tracker-memory snapshots are not used for this skill.
- Cross-session continuity for this skill should come from an exported handoff artifact or promotion into governed Project files.

## Governed-write requirement
Before any governed Project update that depends on session-tracker state:
1. inspect the local file
2. surface pending promotion candidates
3. surface what should remain local
4. use verbose item detail by default for materially important buffered items
5. only then propose or execute the Project-file update path
