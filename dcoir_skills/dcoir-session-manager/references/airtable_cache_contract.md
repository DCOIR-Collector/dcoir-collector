# Airtable Cache Contract for dcoir-session-manager

Purpose: session continuity, closeout, idea capture, queue branch selection, plan/work branch selection, and lifecycle evidence.

## Designated Airtable tables

### Session Checkpoints
- Table id/source: `tblTe75HKZOJaPDGn`
- Required cached fields when present: checkpoint_id, session_id, state_summary, current_focus, open_threads, captured_ideas_summary, decisions_constraints, buffered_promotion_candidates, next_recommended_move, local_state_hash, resume_prompt, checkpoint_at, trigger, github_promotion_status, checkpoint_status, retention_class, updated_at

### Queue Control
- Table id/source: `tblf13aCslg6rJBah`
- Required cached fields when present: control_key, active_plans, branch_summary, branch_decision, superseded_github_surfaces, resume_rule, next_revalidation_trigger, last_confirmed_text, status, retention_class, updated_at

### Work Items
- Table id/source: `tblgsQAVWvh8K7gIR`
- Required cached fields when present: Work Item, Item ID, Repo Path or Skill, Evidence / Notes, Queue Rank, canonical_parent_plan_id, Area, Work Type, Status, Priority, Authority Scope, GitHub Promotion Need, retention_class, updated_at

### Plans
- Table id/source: `tblBcp5FyMIfOm7Xe`
- Required cached fields when present: plan_id, plan_title, active_task_id, active_task_title, scope_constraints, exact_resume_goal, resume_detail, carry_forward_note, pending_flush_items, promotion_candidates, next_recommended_action, plan_state, retention_class, updated_at

### Idea Inbox
- Table id/source: `tblWwBxwrjZF6JR3r`
- Required cached fields when present: idea_id, session_id, idea_title, idea_detail, why_it_matters, suggested_promotion_target, notes, promoted_to_github, source_checkpoint_id, captured_at, related_area, status, retention_class, updated_at

### DCOIR Lifecycle Ledger
- Table id/source: `tblNsjkGUUIdRpHuE`
- Required cached fields when present: event_key, source_table, source_record_id, source_primary_key, event_at, event_title, event_summary, payload_json, lifecycle_object_type, lifecycle_stage, migration_status, retention_class

## JSON shape
Each cache file MUST use this JSON object shape:
```json
{
  "schema_version": 1,
  "skill_name": "<skill-name>",
  "generated_at_utc": "<ISO-8601 UTC>",
  "base_id": "appM4KSwnVf3G3OTK",
  "tables": [
    {
      "table_name": "<table>",
      "table_id": "<tbl... or schema source>",
      "primary_key_field": "<field name when known>",
      "record_count": 0,
      "included_fields": ["field names included in records"],
      "excluded_fields": ["secret or unsafe fields excluded"],
      "field_map": {"field_name": "field_id when known"},
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
Use `/mnt/data/dcoir_skill_caches/<skill-name>/<safe-table-name>.json` when file access is available. Use one file per table and optionally an `index.json` with generated_at, table list, and row counts.

## Refresh rules
Refresh or recreate this cache:
- during every explicit DCOIR re-anchor/startup recovery/resume-first recovery;
- when the cache is missing, unreadable, stale, or has a mismatched table name/id;
- before relying on cached rows for routing, preference, validation, packaging, or config-name decisions;
- immediately after this skill successfully writes to any designated Airtable table;
- when live schema readback shows table/field identity drift;
- when the operator requests a cache refresh.

## Freshness and authority
Default stale threshold is 60 minutes unless the active task requires fresher data. For cleanup, deletion, migration, schema-sensitive writes, dependency-sensitive work, or authority-conflict decisions, perform live Airtable readback even if the cache is fresh. The cache is advisory/readiness evidence only; live Airtable remains authority.

## Safety exclusions
Never cache secret values, token values, credentials, webhook secrets, hidden local paths that are not safe to display, or raw local environment values. For Local Configuration Registry rows, cache names and safe references only. Respect `safe_to_display=false` and `sensitive_value=true` by excluding any value-bearing content and preserving only safety flags and guidance.
