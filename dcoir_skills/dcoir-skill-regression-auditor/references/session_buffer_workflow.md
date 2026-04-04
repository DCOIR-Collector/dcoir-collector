# Session Buffer Workflow

Regression-auditor may keep regression-memory deltas, follow-through notes, recovered blocker lessons, or coordinated campaign coverage notes session-local until the next safe grouped write point.

## Preferred flush-check trigger points
- before any GitHub write
- after blocker resolution
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift

Truth rule:
- buffered regression state is session-local only until it is flushed to GitHub or exported in a handoff artifact

## Valid flush/manicure review
A valid flush/manicure review for this skill should surface:
- campaign scope or single-skill scope
- what regression state is buffered
- what is safe to flush now
- what should remain buffered for now
- the next flush trigger
- one best next move
