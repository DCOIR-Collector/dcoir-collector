# DCOIR Airtable Operational Schema Contract

Airtable cutover and skill cutover are complete. Treat Airtable as the live operational authority for its own schema, queue state, lifecycle state, cleanup state, and helper-memory state.

## Current live authority model
- Use `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST` as startup and authority-order anchor.
- Use `Queue Control`, `Work Items`, and `Plans` for live queue and execution state.
- Use `Session Checkpoints` for resume continuity.
- Use `Idea Inbox` for raw ideas, deferred improvements, and promotion candidates.
- Use `Validation Test Cases` for test catalog state and `Validation Evidence` for proof/readiness evidence.
- Use `Repo Surface Registry` and `Admin Registry` for repo-surface/source-role/schema-governance housekeeping.
- Use helper-specific Airtable memory tables where present.
- Use `Delete Queue` for Airtable deletion requests and deletion processing.
- Use `DCOIR Lifecycle Ledger` as readback/history for object lifecycle events. It is not live task authority.
- Use `Local Configuration Registry` for configuration names, purpose, and safe reference guidance only. Never store token or secret values there.

## Tables no longer assumed by default
Do not assume `Plan Tasks`, `Plan Checkpoints`, `Skill State Registry`, `Schema Registry`, `Tracking Registry`, `Repo File Coverage Detail`, or `Retained Repo Manifest` exist unless current Airtable schema readback proves they exist. Where older instructions mention those names, use the current Airtable schema instead:
- plan execution details live in `Plans` plus executable `Work Items` unless a current task-specific table exists
- skill-state inventory lives in `Admin Registry` skill-state rows and skill-specific helper-memory tables unless a dedicated registry exists
- schema/default-policy state lives in `Admin Registry` plus live schema readback
- repo surface state lives in `Repo Surface Registry` plus source-authority review evidence

## Idea to executable work workflow
1. Capture unapproved or raw ideas in `Idea Inbox`.
2. Promote executable work into `Work Items`.
3. Create or update a `Plans` row when the work is multi-step, governed, or resume-sensitive.
4. Link or cross-reference the Work Item to the parent Plan using current schema fields such as `canonical_parent_plan_id` when available.
5. Update `Queue Control` only after the executable Work Item or Plan exists.
6. Write a `DCOIR Lifecycle Ledger` event for material promotion, migration, retirement, cleanup, or closeout events.

## Delete Queue workflow
Never directly delete Airtable records as a casual cleanup action. Queue deletions through `Delete Queue` unless the operator explicitly directs an immediate connector-level delete and the dependency order is already safe.

Deletion workflow:
1. Identify target table and target record id.
2. Check relational/dependency order before deletion. Children, links, generated evidence, or dependent records may need unlinking, retirement, or separate queue rows before parent deletion.
3. Create or update a `Delete Queue` row with `delete_key`, `target_table`, `target_record_id`, `reason`, `requested_by`, `requested_at`, `review_after`, and `retention_class` when available.
4. Process only rows whose approval gate is satisfied: `approved_to_delete` is checked and `delete_stage` is pending, or the current Airtable schema defines an equivalent approved/pending state.
5. Verify absence after deletion and preserve verification notes in the queue row or Lifecycle Ledger according to the current operator-approved processor behavior.

## Durable lifecycle event requirements
For material lifecycle events, write or prepare a `DCOIR Lifecycle Ledger` row with:
- `event_key`
- `source_table`
- `source_record_id` when known
- `source_primary_key` when useful
- `event_at`
- `event_title`
- `event_summary`
- compact `payload_json` with secrets excluded
- `lifecycle_object_type`
- `lifecycle_stage`
- `migration_status`
- `created_at`
- `retention_class`

## Security and local configuration
Use `Local Configuration Registry` to describe configuration names only. Do not store personal access tokens, API keys, webhook secrets, or credentials in Airtable rows, repo files, logs, generated bundles, or chat-visible output. Use local environment variables or operator-managed secret storage and register only the variable name and safe usage guidance.
