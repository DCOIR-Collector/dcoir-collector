# Airtable checkpoint workflow

Use this workflow when dcoir-session-tracker writes or renders durable session state.

## Current target tables
- `Session Checkpoints` (`tblTe75HKZOJaPDGn`) stores resume continuity and closeout state.
- `Idea Inbox` (`tblWwBxwrjZF6JR3r`) stores raw ideas, deferred improvements, and promotion candidates.
- `Work Items` and `Plans` store executable work and parent scope after promotion.
- `Admin Registry` stores administrative skill-state or schema-governance housekeeping when no dedicated current table exists.
- `DCOIR Lifecycle Ledger` stores material lifecycle/readback events.

## Write order
1. Prefer Airtable readback first during startup or leftover recovery.
2. Write Session Checkpoints for closeout/resume continuity.
3. Write Idea Inbox only for unapproved ideas or deferred improvements.
4. Promote executable work into Work Items, then Plans when multi-step parent scope is needed.
5. Update Queue Control only after executable Work Item or Plan rows exist.
6. Use Admin Registry only for administrative state; it is not the live task queue.

## Safety rules
- Do not require retired Tracking Registry or Schema Registry tables.
- Do not treat local JSON cache as durable authority when Airtable has current state.
- Do not silently persist a durable preference or queue change without surfacing it for operator approval.
