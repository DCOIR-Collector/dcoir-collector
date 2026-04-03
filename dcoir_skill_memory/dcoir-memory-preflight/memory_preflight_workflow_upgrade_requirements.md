# DCOIR Memory Preflight Workflow Upgrade Requirements

## Purpose
Capture the approved upgrade requirements for `dcoir-memory-preflight` so the skill and surrounding workflow can enforce closed-loop process learning rather than acting only as a front-end lookup step.

## Approved standing rule
`dcoir-memory-preflight` should help before high-friction execution and also after blockers are overcome so reusable lessons can be promoted appropriately.

## Required trigger classes

### 1. Pre-execution trigger
Run before high-friction execution when the task family is likely to have reusable validated procedures, limitations, or failure signatures.

### 2. Post-blocker trigger
Run again after a blocker or failed attempt is successfully overcome when the lesson could improve:
- a repeatable workflow
- a reusable procedure
- a reusable limitation note
- a reusable failure signature
- helper-skill or process-document guidance

## Required classification behavior
After blocker recovery, classify the lesson as one of:
- one-off only
- reusable procedure candidate
- reusable limitation candidate
- reusable failure-signature candidate
- reusable helper-skill or process-document candidate

## Promotion behavior
- Do not silently write every recovered lesson into canonical task memory.
- Stage a promotion-ready candidate instead.
- Preserve enough detail to support later promotion into:
  - canonical task memory
  - helper-skill guidance
  - governed project workflow docs
  - or an appropriate combination

## Required companion routing
The surrounding workflow should use:
- `dcoir-decision-policy` to invoke memory-preflight when branch choice or post-blocker learning requires it
- `dcoir-plan-tracker` and `dcoir-session-tracker` to preserve blocker signature, failed attempt summary, successful mitigation, and reusability notes until GitHub flush time

## Session-local buffer expectations
- `dcoir-memory-preflight` should be able to participate in session-local write buffering.
- Buffered state is session-local only until flushed to GitHub or exported in a handoff artifact.
- Preferred flush-check trigger points are:
  - before GitHub writes
  - after blocker resolution
  - at major milestones
  - before session export or handoff
  - when the operator asks what remains

## Known limitation to preserve honestly
- The project prefers grouped GitHub writes and minimal operation count.
- Existing-file grouped updates still depend on a safe, reliable in-chat base-tree recovery path.
- Until that path is fully reliable, the skill should preserve the grouped-write intent and keep the limitation explicit rather than pretending the buffer-flush lane is already complete.

## Next implementation sequence
1. Update the skill instructions so post-blocker classification is explicit.
2. Update the decision-policy workflow so the post-blocker trigger actually fires.
3. Update stateful helper skills so blocker-recovery details can be buffered and surfaced for promotion.
4. After implementation, pass the updated skill through `dcoir-skill-regression-auditor`.
