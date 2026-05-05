# Task-time schema gate

Use this reference when dcoir-airtable-schema-cache is invoked outside startup/re-anchor.

## Purpose
Make the schema check frequent and cheap enough that DCOIR Airtable work does not proceed from stale memory. The gate is not a full cleanup plan and does not authorize writes.

## Invoke before
- Airtable record create/update/delete, Delete Queue creation/processing, cleanup, merge, dedupe, migration, schema redesign, taxonomy/controlled-vocabulary design, naming/id convention work, searchability repair, or validation evidence work.
- Airtable connector calls that require field IDs, filter operands, sort fields, select choice IDs, linked-record targets, primary-field assumptions, formula/id generation, or table names.
- Code/scripts/workflows that reference Airtable fields or table IDs.
- Any recovery after a failed Airtable query where schema drift could be the cause.

## Compact output
Return only what is needed:
1. Target table(s) and table id(s).
2. Needed field ids/types/select choices/linked-record targets.
3. Cache status or live-readback status.
4. Schema drift or retired-table assumptions.
5. Whether fresh live schema readback is required before the next action.
6. Safest next Airtable action or stop condition.

## Hard limits
Do not treat cache as authority for writes, deletes, migrations, dependency checks, or schema changes. Do not continue after schema conflict when the conflict changes safety, target records, field IDs, or approval gates.
