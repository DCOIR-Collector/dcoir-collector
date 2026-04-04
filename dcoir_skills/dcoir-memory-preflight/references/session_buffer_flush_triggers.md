# Session Buffer Flush Triggers

Preferred flush-check trigger points:
- before GitHub writes
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when a helper skill reports meaningful state drift

Truth rule:
- buffered state is session-local only until it is flushed to GitHub or exported in a handoff artifact

## Valid flush/manicure review
A valid flush/manicure review for this skill should surface:
- blocker signature or task family
- failed attempt summary
- successful mitigation
- lesson classification
- whether the lesson stays one-off, promotion-ready, or only buffered for now
- the next flush trigger
- one best next move

## Pre-push contract note
When a suitable governed push is already happening in the same branch, surface what should land in that same grouped push instead of silently leaving the state buffered for later.
