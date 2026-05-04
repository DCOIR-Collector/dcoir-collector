# Airtable Cache Contract for dcoir-session-manager
Purpose: session continuity, active queue recovery, closeout, and active plan/work branch selection.
## Cache scope rule
Routine re-anchor caching is intentionally limited to high-call tables that the skill repeatedly consults. Do not cache every table the skill can touch. Tables listed as conditional/live-read are not part of the normal re-anchor cache; read them from live Airtable only when the active task needs them.
## Routine cached Airtable tables
### Session Checkpoints
- Table id/source: `tblTe75HKZOJaPDGn`
- Required cached fields when present: checkpoint_id, session_id, state_summary, current_focus, open_threads, decisions_constraints, next_recommended_move, resume_prompt, checkpoint_at, trigger, checkpoint_status, retention_class, updated_at
### Queue Control
- Table id/source: `tblf13aCslg6rJBah`
- Required cached fields when present: control_key, active_plans, branch_summary, branch_decision, resume_rule, next_revalidation_trigger, last_confirmed_text, status, retention_class, updated_at
### Plans
- Table id/source: `tblBcp5FyMIfOm7Xe`
- Scope limit: Cache only active or recently active plan rows when the connector/query path supports filtering; otherwise keep the compact cache bounded and prefer live reads for broad plan review.
- Required cached fields when present: plan_id, plan_title, active_task_id, active_task_title, exact_resume_goal, resume_detail, carry_forward_note, next_recommended_action, plan_state, retention_class, updated_at
### Work Items
- Table id/source: `tblgsQAVWvh8K7gIR`
- Scope limit: Cache only active/todo/recent rows needed for queue selection when supported; use live Airtable for full backlog analysis, cleanup, or migration.
- Required cached fields when present: Work Item, Item ID, Repo Path or Skill, Evidence / Notes, Queue Rank, canonical_parent_plan_id, Status, Priority, retention_class, updated_at
## Conditional/live-read tables, not routine cache
- `Idea Inbox` (`tblWwBxwrjZF6JR3r`): read live only during idea capture/promotion, session closeout, lifecycle verification, or historical audit.
- `DCOIR Lifecycle Ledger` (`tblNsjkGUUIdRpHuE`): read live only during idea capture/promotion, session closeout, lifecycle verification, or historical audit.

## JSON shape
Each routine cache file MUST use this JSON object shape:
```json
{
  "schema_version": 1,
  "skill_name": "<skill-name>",
  "generated_at_utc": "<ISO-8601 UTC>",
  "base_id": "appM4KSwnVf3G3OTK",
  "tables": [
    {
      "table_name": "<routine table>",
      "table_id": "<tbl... or schema source>",
      "primary_key_field": "<field name when known>",
      "record_count": 0,
      "included_fields": ["field names included in records"],
      "excluded_fields": ["secret or unsafe fields excluded"],
      "field_map": {"field_name": "field_id when known"},
      "scope_filter": "<active/todo/recent filter when bounded caching is required>",
      "records": [
        {"record_id": "rec...", "fields": {}}
      ]
    }
  ],
  "freshness": {
    "max_age_minutes": 60,
    "source": "live Airtable readback",
    "content_hash": "sha256 of normalized table payload when practical"
  }
}
```
## Cache paths
Use `/mnt/data/dcoir_skill_caches/<skill-name>/<safe-table-name>.json` when file access is available. Use one file per routine cached table and optionally an `index.json` with generated_at, table list, row counts, and scope filters.
## Refresh rules
Refresh or recreate routine caches:
- during every explicit DCOIR re-anchor/startup recovery/resume-first recovery;
- when the cache is missing, unreadable, stale, or has a mismatched table name/id;
- before relying on cached rows for routing, preference, validation, packaging, or config-name decisions;
- immediately after this skill successfully writes to a routine cached table;
- when live schema readback shows table/field identity drift;
- when the operator requests a cache refresh.
If the skill writes to a conditional/live-read table, verify that write by live Airtable readback. Do not add the table to routine cache unless the cache contract is explicitly updated.
## Freshness and authority
Default stale threshold is 60 minutes unless the active task requires fresher data. For cleanup, deletion, migration, schema-sensitive writes, dependency-sensitive work, or authority-conflict decisions, perform live Airtable readback even if the cache is fresh. The cache is advisory/readiness evidence only; live Airtable remains authority.
## Safety exclusions
Never cache secret values, token values, credentials, webhook secrets, hidden local paths that are not safe to display, or raw local environment values. For Local Configuration Registry rows, cache names and safe references only. Respect `safe_to_display=false` and `sensitive_value=true` by excluding value-bearing content and preserving only safety flags and guidance.
