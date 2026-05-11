# Airtable Cache Contract for dcoir-airtable-schema-cache
Purpose: schema-readiness cache and operational table expectation checks; this skill caches schema metadata, not normal row memory.
## Cache scope rule
Routine re-anchor caching is intentionally limited to high-call tables that the skill repeatedly consults. Do not cache every table the skill can touch. Tables listed as conditional/live-read are not part of the normal re-anchor cache; read them from live Airtable only when the active task needs them.
## Routine cached Airtable tables
### Airtable live schema
- Table id/source: `appM4KSwnVf3G3OTK`
- Required cached fields when present: all table ids/names/descriptions, primary fields, field ids/names/types/options/descriptions, and linked-record metadata where present
## Conditional/live-read tables, not routine cache
- `Admin Registry` (`tblFaJW1V2DPc9css`): read live only for schema-governance or object-state evidence when the task needs it.

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
- before task-time Airtable writes, deletes, cleanup/migration/merge work, Delete Queue work, or schema-sensitive filters/sorts/select-option handling when relevant schema has not been checked in the current turn;
- when the operator requests a cache refresh.
If the skill writes to a conditional/live-read table, verify that write by live Airtable readback. Do not add the table to routine cache unless the cache contract is explicitly updated.
## Freshness and authority
Default stale threshold is 60 minutes unless the active task requires fresher data. For cleanup, deletion, migration, schema-sensitive writes, dependency-sensitive work, or authority-conflict decisions, perform live Airtable readback even if the cache is fresh. The cache is advisory/readiness evidence only; live Airtable remains authority.
## Safety exclusions
Never cache secret values, token values, credentials, webhook secrets, hidden local paths that are not safe to display, or raw local environment values. For Local Configuration Registry rows, cache names and safe references only. Respect `safe_to_display=false` and `sensitive_value=true` by excluding value-bearing content and preserving only safety flags and guidance.
