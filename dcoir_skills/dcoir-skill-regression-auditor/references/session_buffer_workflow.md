# Session Buffer Workflow

Regression-auditor may keep regression-memory deltas, follow-through notes, or recovered blocker lessons session-local until the next safe grouped write point.

## Preferred flush-check trigger points
- before any GitHub write
- after blocker resolution
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift

Truth rule:
- buffered regression state is session-local only until it is flushed to GitHub or exported in a handoff artifact
