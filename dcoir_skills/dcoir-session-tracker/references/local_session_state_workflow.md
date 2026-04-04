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

Stage one governed update entry:
```bash
python scripts/session_state_store.py stage-governed-update --entry-json '{"title":"promote tracker items into LOG-01 and todo/01","target_paths":["project_sources/LOG-01_DCOIR_Todo_Log.txt","project_sources/todo/01_Active_Now.txt"],"action":"update","why":"same grouped push is already happening","source_item_ids":["S-101","S-102"]}'
```

Derive a pre-push review and todo-sync proposal from the current local state:
```bash
python scripts/session_state_store.py derive-pre-push-review --output-md /mnt/data/dcoir_session_tracker/pre_push_review.md --output-json /mnt/data/dcoir_session_tracker/pre_push_review.json --update-state
```

Mark one item complete and move it to completed:
```bash
python scripts/session_state_store.py complete --id S-001
```

Mark one item as governed-written after the push lands:
```bash
python scripts/session_state_store.py mark-governed-written --id S-001 --note 'promoted in same grouped push as LOG-01 update'
```

Clear staged governed updates after post-push cleanup:
```bash
python scripts/session_state_store.py clear-staged-governed-updates
```

Clear staged todo actions after post-push cleanup:
```bash
python scripts/session_state_store.py clear-staged-todo-actions
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
- staged governed update count
- staged todo-action count
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
2. derive a pre-push review from the current state
3. surface pending promotion candidates
4. surface what should remain local
5. surface staged governed updates that should land in the same grouped transaction
6. surface staged todo additions, updates, or removals for the same grouped transaction
7. use verbose item detail by default for materially important buffered items
8. only then propose or execute the Project-file update path
9. after the governed push lands, mark the promoted items governed-written and clear the completed staged-update and staged-todo entries
