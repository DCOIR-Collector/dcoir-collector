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
