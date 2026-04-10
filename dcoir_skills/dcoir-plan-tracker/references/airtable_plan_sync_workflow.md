# Airtable-First Plan Sync Workflow

Use this reference when `dcoir-plan-tracker` needs durable execution state that must survive fragile local container continuity.

## Truth model
- Airtable is the primary durable execution-state surface
- local `plan_state.json` is an optional cache or render mirror
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
Primary durable row per plan. Upsert on plan creation and material plan-state changes only.

### Plan Tasks
Primary durable normalized task rows for hierarchical execution state. Batch writes when task structure or task statuses materially change.

### Plan Checkpoints
Sparse durable checkpoint history for blockers, mitigations, flush reviews, resume moments, and handoff or close-out transitions.

### Tracking Registry
Metadata index only. Use after the durable domain record already exists.

## Trigger rules
Write Airtable state when:
- a plan is created
- the active task changes materially
- a blocker is recorded or resolved
- a flush/manicure review occurs
- a before-GitHub-write checkpoint is needed
- a handoff or close-out checkpoint is needed
- local cache continuity is missing but durable plan continuity still matters

## Call minimization rules
- Prefer one `Plans` upsert plus one batched `Plan Tasks` write when a plan materially changes.
- Prefer one `Plan Checkpoints` record per meaningful checkpoint event.
- Prefer direct known base and table ids to avoid discovery calls.
- Prefer text foreign keys like `plan_id` and `parent_task_id` over Airtable-native relationship dependence in the skill logic.

## Local cache interaction
- If the local cache exists and is current, use `scripts/render_airtable_plan_bundle.py` to render Airtable-ready payloads from it.
- If the local cache is missing, reconstruct the Airtable payload from the current plan reasoning and write Airtable first.
- Refresh or reinitialize the local cache only when deterministic export, local proof, or render parity is useful.

## Promotion rule
Airtable holds primary durable execution state for live plan continuity.
GitHub plan surfaces remain the authoritative promoted record when the workflow decides the current plan state or learned lesson should become governed text.
