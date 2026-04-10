# Airtable-First Session Tracker Workflow

Use this reference when `dcoir-session-tracker` needs durable working state that must survive fragile local container continuity.

## Truth model
- Airtable is the primary durable working-state surface
- local `session_state.json` is an optional cache or render buffer
- GitHub remains the authoritative promoted state

## Base and table targets
- Airtable base id: `appM4KSwnVf3G3OTK`
- `Session Checkpoints` table id: `tblTe75HKZOJaPDGn`
- `Idea Inbox` table id: `tblWwBxwrjZF6JR3r`
- `Tracking Registry` table id: `tblohiMxxVbDUnN77`
- `Schema Registry` table id: `tblwsD43VhzmjWNbc`
- `Work Items` table id: `tblgsQAVWvh8K7gIR`

Prefer direct table-id writes against the known base instead of querying Airtable for discovery every time. Only fall back to table-name discovery if the direct table-id write fails.

## Table responsibilities
### Session Checkpoints
Primary durable checkpoint history for session continuity, milestones, blockers, task switches, before-GitHub-write checkpoints, and handoff moments.

### Idea Inbox
Primary durable capture surface for scattered ideas, later work items, and things the operator explicitly does not want forgotten.

### Tracking Registry
Metadata index only. Use after the durable domain record already exists.

## Trigger rules
Write Airtable state when:
- session bootstrap settles the lane
- a major milestone occurs
- a blocker appears or is resolved
- a before-GitHub-write checkpoint is needed
- the operator explicitly says to remember, capture, or park an idea
- a handoff or close-out checkpoint is needed
- a local cache is missing and durable state still needs to survive

## Call minimization rules
- Prefer one `Session Checkpoints` write per meaningful checkpoint event.
- Prefer one `Idea Inbox` write only when an idea is explicitly capture-worthy.
- Prefer direct known base and table ids to avoid discovery calls.
- Use `Tracking Registry` only after the durable domain record already exists.

## Local cache interaction
- If the local cache exists and is current, use `scripts/render_airtable_session_bundle.py` to render Airtable-ready payloads from it.
- If the local cache is missing, reconstruct the Airtable payload from the current session reasoning and write Airtable first.
- Refresh or reinitialize the local cache only when deterministic export or inspection is useful.

## Promotion rule
Airtable holds primary durable working state for live session continuity.
GitHub remains the authoritative promoted state when the workflow decides a learned lesson, decision, or queued item should become governed text.

## Work-item lifecycle ownership
When `dcoir-session-tracker` opens or stages a `Work Items` row for tracker-owned implementation work, it owns the full row lifecycle.

Default completion behavior after success is verified:
- update the same row to `Status = Done`
- set `Active = false`
- leave the row in place for history
- avoid deleting rows unless they were clearly scratch-only or duplicate

Do not require a second operator reminder just to close a row that this skill created.

## Default interactive Work Items field set
When rendering `Work Items` in chat for this workflow, prefer these fields by default unless the operator asked for a narrower view:
- `Work Item`
- `Item ID`
- `Area`
- `Work Type`
- `Status`
- `Priority`
- `Owner`
- `Repo Path or Skill`
- `Next Action`
- `Evidence / Notes`
- `Blocker`
- `Active`

When the operator asked to see one specific row only, filter to that one row instead of rendering the whole table.
