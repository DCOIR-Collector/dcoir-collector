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

Upsert or update one item:
```bash
python scripts/session_state_store.py upsert --item-json '{"id":"S-001","bucket":"session_only","title":"example","why":"example","next_action":"example"}'
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
- GitHub-backed helper-state snapshots are optional and secondary to the local file.

## GitHub-write requirement
Before any GitHub update that depends on session-tracker state:
1. inspect the local file
2. surface pending promotion candidates
3. surface what should remain local
4. only then propose or execute the GitHub update path
