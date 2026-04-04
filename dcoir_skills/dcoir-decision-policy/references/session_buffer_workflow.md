# Session Buffer Workflow

Use session-local buffering when staging related GitHub-readable updates or helper-memory updates that should land together.

## Default rules
- prefer staging content in-session and using as few GitHub operations as possible
- prefer one bounded grouped transaction when multiple related existing-file updates belong together and the connector lane can do so safely
- keep grouped-write intent explicit when the safe grouped lane is not yet available
- buffered state is session-local only until it is flushed to GitHub or exported in a handoff artifact
- when a coordinated campaign is active, keep the campaign scope explicit rather than pretending the remaining work is already done
- when a deferred governance review is intentionally waiting on a countdown, keep the countdown visible and decrement it only after the qualifying validation event actually happens

## Preferred flush-check trigger points
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when a helper skill reports meaningful state drift

## Valid flush-check output
A valid buffer or flush review for this skill should surface:
- current decision branch or campaign scope
- buffered learning or persistence candidates
- what is safe to flush now
- what should remain local for now
- any deferred review countdown that still gates a future decision
- the next flush trigger
- one best next move
