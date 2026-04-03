# Session Buffer Workflow

Plan-tracker may keep related tracker changes session-local until the next suitable flush point.

## Buffer when
- several related tracker files should land together
- blocker-recovery notes are still settling
- grouped GitHub writes are safer than repeated one-file churn
- the next flush-check trigger is near

## Preferred flush-check trigger points
- before any GitHub write
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift

Truth rule:
- buffered tracker state is session-local only until it is flushed to GitHub or exported in a handoff artifact
