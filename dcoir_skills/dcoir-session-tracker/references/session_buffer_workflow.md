# Session Buffer Workflow

Session-tracker may hold notes, promotion candidates, and continuity state locally until the next flush-check trigger.

## Preferred flush-check trigger points
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift
- when the operator signals that work is moving to another session

## Surface at each flush check
- what is still buffered
- what is safe to flush now
- what should remain session-local for now
- what must be exported for handoff if a safe GitHub write is not happening
- one best next move

## Close-out-specific rule
When the operator is moving to another session, a flush check is mandatory.
Do not treat session transition as a casual summary moment.
Classify durable state, exported-only state, and buffered-only state explicitly.

Truth rule:
- buffered state is session-local only until it is flushed to GitHub or exported in a handoff artifact
