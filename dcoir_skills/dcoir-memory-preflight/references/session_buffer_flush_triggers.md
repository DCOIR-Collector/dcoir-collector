# Session Buffer Flush Triggers

Preferred flush-check trigger points:
- before GitHub writes
- when a GitHub Desktop push or manual repo-update delivery is about to happen
- after blocker resolution
- when switching major tasks
- at major milestones
- before session export, handoff, closeout, or starter-prompt generation
- after Session Checkpoint creation or checkpoint-ready payload preparation
- when the operator asks what remains
- when a helper skill reports meaningful state drift
- when a GitHub Desktop manual repo-update delivery or grouped governed push is about to happen

Truth rule:
- buffered state is session-local only until it is flushed to GitHub, written to Airtable, or exported in a handoff artifact
- checkpoint-ready payloads emitted in chat are non-durable unless they are written to Airtable Session Checkpoints or another governed durable surface

## Valid flush/manicure review
A valid flush/manicure review for this skill should surface:
- blocker signature or task family
- failed attempt summary
- successful mitigation
- lesson classification
- whether the lesson stays one-off, promotion-ready, or only buffered for now
- checkpoint/write status and readback gap when relevant
- the next flush trigger
- one best next move

## Pre-push contract note
When a suitable governed push or GitHub Desktop manual repo-update delivery is already happening in the same branch, surface what should land in that same grouped push instead of silently leaving the state buffered for later.

## Coordinated-campaign note
When a compatible multi-skill batch is already being staged for a bounded manual GitHub/Desktop update, surface what should land in that same grouped batch instead of treating each skill fix as an isolated later flush.
