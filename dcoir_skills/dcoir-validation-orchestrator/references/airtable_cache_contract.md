# Airtable Cache Contract for dcoir-validation-orchestrator

Purpose: validation plan memory, test catalog mapping, evidence thresholds, readiness gates, and post-patch validation state.

## Designated Airtable tables

### dcoir-validation-orchestrator
- Table id/source: `tbls9O1B0Rs8YvTAj`
- Required cached fields when present: validation_entry_id, active_validation_plan, evidence_threshold, unresolved_gap, live_readiness_gate, next_action, last_confirmed_text, validation_scope, status, retention_class, updated_at

### Validation Test Cases
- Table id/source: `tblRnMpQUomIGyFVL`
- Required cached fields when present: Test Case, Test ID, Feature or Behavior, Command or Method, Pass Criteria, Fail Criteria, Evidence / Notes, Source Basis, Active, Area, Execution Lane, Observed Status, retention_class, updated_at

### Validation Evidence
- Table id/source: `tblrPFQH2uZEYBYE9`
- Required cached fields when present: evidence_key, validation_case_key, work_item_key, release_key, repo_surface_key, evidence_summary, source_locator, result, retention_class, updated_at

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
