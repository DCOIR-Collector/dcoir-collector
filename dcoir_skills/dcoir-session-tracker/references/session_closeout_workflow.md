# Session close-out workflow

## Purpose
Use this reference when the operator indicates that work is moving to another session and the current session must be safely closed out.

## Required close-out sequence
1. Re-anchor to Project Instructions.
2. Read the current manifest.
3. Read the current change log.
4. Review current session-tracker state.
5. Review known open items from the current conversation.
6. Run a flush check across buffered state.
7. Classify every material item as one of:
   - already durable in governed GitHub
   - exported in handoff only
   - buffered session-local only
   - missing durable capture and needing explicit warning
8. Verify whether the currently relevant continuity surfaces were already updated.
9. If a safe GitHub write is already in progress, batch already-known continuity follow-ons into that grouped write.
10. Otherwise export the handoff artifact and state what remains non-durable.
11. Produce the next-session starter prompt.
12. End with one best next move.

## Required verification questions
At close-out, verify:
- Were learned durable workflow rules captured in governed GitHub sources or explicitly marked as still pending?
- Were all tasks or requests either closed or preserved in the right destination?
- Were session-related logs or continuity notes updated, or explicitly left pending?
- Is the canonical session-tracker state current enough for safe resume?
- Does the next-session starter prompt match the current control plane and current open work?

## Truth rules
- Chat discussion alone is not durable continuity.
- Exported handoff is not the same as governed GitHub promotion.
- Buffered session-local state is not cross-session durable.
- If continuity drift exists, say so plainly.

## Starter prompt requirements
The starter prompt should include:
- project re-anchor instruction
- exact control-plane read order
- current stable baseline
- exact current next work item
- priority open items
- any known buffered-only or exported-only state
- one recommended next move

## Minimum completion statement
A compliant close-out must explicitly say:
- what is durable
- what is exported only
- what is still buffered only
- what the next session should do first
