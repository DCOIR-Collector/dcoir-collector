# Airtable Checkpoint Workflow

Use this reference when `dcoir-session-tracker` needs durable checkpointed working state in Airtable.

## Truth model
- local JSON remains the hot working state
- Airtable is the durable checkpointed working-state layer
- GitHub remains the authoritative promoted state

## Base and table targets
- Airtable base id: `appM4KSwnVf3G3OTK`
- `Session Checkpoints` table id: `tblTe75HKZOJaPDGn`
- `Idea Inbox` table id: `tblWwBxwrjZF6JR3r`
- `Tracking Registry` table id: `tblohiMxxVbDUnN77`
- `Schema Registry` table id: `tblwsD43VhzmjWNbc`

Prefer direct table-id writes against the known base instead of querying Airtable for table discovery every time. Only fall back to table-name discovery if the direct table-id write fails.

## Write posture
Write sparsely.
Do not create a checkpoint row for every small local-state mutation.

Checkpoint triggers:
- after session bootstrap completes
- at major milestones
- when a blocker appears
- when a blocker is resolved
- before any GitHub write that depends on tracker state
- when switching major tasks
- when the operator explicitly says to remember, capture, or park an idea
- before handoff or close-out
- when local state had to be reinitialized because a pre-existing file was missing

## Tables and responsibilities
### Session Checkpoints
Use for durable checkpoint snapshots with one record per meaningful checkpoint event.

Required fields to populate:
- `checkpoint_id`
- `session_id`
- `checkpoint_time_text`
- `trigger`
- `state_summary`
- `current_focus`
- `open_threads`
- `captured_ideas_summary`
- `decisions_constraints`
- `buffered_promotion_candidates`
- `next_recommended_move`
- `github_promotion_status`
- `local_state_hash`
- `resume_prompt`
- `checkpoint_status`

### Idea Inbox
Use for scatter-brain ideas and later queue items that should not rely on chat memory.

Required fields to populate:
- `idea_id`
- `session_id`
- `captured_time_text`
- `idea_title`
- `idea_detail`
- `why_it_matters`
- `related_area`
- `suggested_promotion_target`
- `status`
- `notes`
- `promoted_to_github`
- `source_checkpoint_id`

### Tracking Registry
Use only as a metadata index when a durable Airtable record already exists.
Do not make registry writes the only persistence action.

## Call minimization rules
- Prefer one checkpoint write per flush event.
- Prefer one idea write only when an idea is materially capture-worthy.
- Prefer using the local JSON state plus rendered payload scripts instead of multiple Airtable reads.
- Prefer direct known base and table ids to avoid discovery calls.
- Prefer upsert-by-id behavior when the connector surface safely supports it; otherwise create only at the checkpoint moments above.

## Payload rendering helper
Use `scripts/render_airtable_session_bundle.py` to turn the current local JSON state into Airtable-ready payloads.

Typical uses:
- render a `Session Checkpoints` payload from the current state
- render an `Idea Inbox` payload from a known tracked item id
- render the matching `Tracking Registry` metadata payload

## Promotion rule
Airtable checkpoint state is durable working memory only.
Promote to GitHub when the item becomes an approved durable queue item, a control-plane relevant decision, a validated completion worth preserving, or another governed artifact candidate.
