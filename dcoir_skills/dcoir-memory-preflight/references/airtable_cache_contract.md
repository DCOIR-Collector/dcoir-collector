# Airtable Cache Contract for dcoir-memory-preflight

Purpose: SKILLROUTE lookup, routing preconditions, anti-patterns, operator preferences, skill-state, blocker recovery, and task-family selection.

## Designated Airtable tables

### dcoir-memory-preflight
- Table id/source: `tblcNNuKqi8IkFsSQ`
- Required cached fields when present: memory_entry_id, consulted_records, selected_lane, preconditions, anti_patterns, required_verification, buffered_candidate, last_confirmed_text, invocation_mode, status, retention_class, task_family, updated_at

### Operator Preferences
- Table id/source: `tblnxZ3eLPT3W38wl`
- Required cached fields when present: preference_key, preference_statement, effective_behavior, source_session_id, last_confirmed_text, notes, status, scope, retention_class, curation_decision, updated_at

### Admin Registry
- Table id/source: `tblFaJW1V2DPc9css`
- Required cached fields when present: registry_key, object_name, owning_table, object_type, status, retention_class, notes, last_reviewed_at, updated_at

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
