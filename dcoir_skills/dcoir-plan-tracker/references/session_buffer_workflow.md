# Session Buffer Workflow

Plan-tracker may keep related tracker changes session-local until the next suitable flush point.

## Buffer when
- several related tracker files should land together
- blocker-recovery notes are still settling
- grouped GitHub writes are safer than repeated one-file churn
- the next flush-check trigger is near

## Preferred flush-check trigger points
- before any GitHub write
- when a governed push, GitHub Desktop push, or grouped repo batch is about to happen
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export or handoff
- when the operator asks what remains
- when the skill reports meaningful state drift

## Flush/manicure sequence
1. Inspect the current plan state and active task.
2. Surface buffered plan-state changes, blocker-recovery notes, promotion candidates, and pending flush items.
3. Surface what is safe to flush now.
4. Surface what should remain local or buffered for now.
5. Surface staged governed updates and active-todo changes that should land in the same grouped push when safe.
6. Surface the next flush trigger and one best next move.
6. If the current branch includes a countdown-gated decision, show the remaining count and the trigger condition explicitly.

Truth rule:
- buffered tracker state is session-local only until it is flushed to GitHub or exported in a handoff artifact
- a countdown-gated widening or scope decision must remain deferred until the qualifying validation count reaches zero and the operator reviews the triggered decision
