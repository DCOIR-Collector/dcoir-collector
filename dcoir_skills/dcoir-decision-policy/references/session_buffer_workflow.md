# Session Buffer Workflow

Use session-local buffering when staging related GitHub-readable updates or helper-memory updates that should land together.

## Default rules
- prefer staging content in-session and using as few GitHub operations as possible
- prefer one bounded grouped transaction when multiple related existing-file updates belong together and the connector lane can do so safely
- keep grouped-write intent explicit when the safe grouped lane is not yet available
- buffered state is session-local only until it is flushed to GitHub or exported in a handoff artifact

## Preferred flush-check trigger points
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when a helper skill reports meaningful state drift
