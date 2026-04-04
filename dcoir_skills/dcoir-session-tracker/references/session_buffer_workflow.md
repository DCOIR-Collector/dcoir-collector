# Session Buffer Workflow

Session-tracker may hold notes, promotion candidates, and continuity state locally until the next flush-check trigger.

## Primary local surface
When code execution and file writing are available, the primary buffer surface is the real local JSON file at `/mnt/data/dcoir_session_tracker/session_state.json` unless the operator explicitly chose another path.
Run the first-use `ensure-state` preflight so the operator can see whether that file was already present or had to be initialized in the current branch.
Inspect that file instead of merely paraphrasing the intended state when the operator questions whether the buffer is real.
If a write path had to initialize a new file because no pre-existing file was present, surface that absence or re-init fact explicitly instead of silently continuing.

## Preferred flush-check trigger points
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift
- when the operator signals that work is moving to another session
- when a governed push, GitHub Desktop push, or grouped repo batch is about to happen

## Surface at each flush check
- what is still buffered
- what is safe to flush now
- what should remain session-local for now
- what staged governed updates should land in the same grouped push
- what staged todo additions, updates, or removals should land in the same grouped push
- what post-push cleanup should occur once the governed update lands
- what must be exported for handoff if a safe governed Project write is not happening
- the local session-state inspection result when the file exists
- one best next move

## Derivation rule
When a governed push is approaching, derive the pre-push review from the current state instead of relying only on manually entered staged entries.
The derived review should preserve existing manually staged entries and add the missing governed-update or todo-sync proposals needed for the same grouped push.

## Close-out-specific rule
When the operator is moving to another session, a flush check is mandatory.
Do not treat session transition as a casual summary moment.
Classify durable state, exported-only state, buffered-only state, and the inspected local-file state explicitly.

Truth rule:
- buffered state is session-local only until it is promoted into governed Project files or exported in a handoff artifact
- a claimed local file is not proven until the inspection command confirms it
