# Airtable Plan Sync Workflow

Use this reference when `dcoir-plan-tracker` needs durable checkpointed execution state in Airtable.

## Truth model
- local `plan_state.json` remains the hot working state
- Airtable is the durable checkpointed execution-state layer
- GitHub remains the authoritative promoted state

## Base and table targets
- Airtable base id: `appM4KSwnVf3G3OTK`
- `Plans` table id: `tblBcp5FyMIfOm7Xe`
- `Plan Tasks` table id: `tblsATLIDeh6gtcoM`
- `Plan Checkpoints` table id: `tbl6z4Lyai2RABMyw`
- `Tracking Registry` table id: `tblohiMxxVbDUnN77`
- `Schema Registry` table id: `tblwsD43VhzmjWNbc`

Prefer direct table-id writes against the known base instead of querying Airtable for discovery every time. Only fall back to table-name discovery if the direct table-id write fails.

## Table responsibilities
### Plans
One durable checkpointed row per plan.
Update on plan creation and material plan-state changes only.

### Plan Tasks
Normalized task rows for hierarchical execution state.
Batch writes when task structure or task statuses materially change.
Do not write task rows on every tiny chat turn.

### Plan Checkpoints
Sparse checkpoint history for blockers, mitigations, flush reviews, resume moments, and handoff/close-out transitions.

### Tracking Registry
Metadata index only. Use after the durable domain record already exists.

## Trigger rules
Write plan Airtable state when:
- a plan is created
- the active task changes materially
- a blocker is recorded
- a blocker is resolved
- a flush/manicure review occurs
- a before-GitHub-write checkpoint is needed
- a handoff or close-out checkpoint is needed

## Call minimization rules
- Prefer one `Plans` upsert plus one batched `Plan Tasks` write when a plan materially changes.
- Prefer one `Plan Checkpoints` record per meaningful checkpoint event.
- Prefer direct known base and table ids to avoid discovery calls.
- Prefer text foreign keys like `plan_id` and `parent_task_id` over Airtable-native relationship dependence in the skill logic.

## Payload rendering helper
Use `scripts/render_airtable_plan_bundle.py` to render Airtable-ready payloads from a local plan folder.

Typical uses:
- render the `Plans` record from `plan_state.json`
- render the full `Plan Tasks` row set from the normalized task tree
- render a `Plan Checkpoints` payload from a blocker, milestone, or flush moment
- render the matching `Tracking Registry` metadata payloads

## Promotion rule
Airtable holds durable checkpointed execution state only.
GitHub plan surfaces remain the promoted durable record when the workflow decides the current plan state or learned lesson should become governed text.
