# DCOIR Airtable schema cache contract

The cache is a local accelerator. It is allowed to answer read-only questions such as table names, field IDs, field types, select options, and linked-record targets. It is not allowed to replace live Airtable readback for writes, deletes, migrations, or dependency-sensitive workflows.

## Cache JSON shape
- `generated_at`: UTC timestamp
- `source`: human-readable source marker
- `base_id`: Airtable base id when known
- `tables`: map by table name with table id, primary field id, description, and fields
- `tables_by_id`: map table id to name
- `operational_expectations`: required and retired-by-default table expectations
- `warnings`: normalization warnings

## Freshness policy
Fresh cache is normally acceptable for read-only lookup during the same session. For destructive or schema-sensitive operations, call Airtable live schema readback again.

## Delete Queue special rule
Before queueing or processing deletions, verify current fields for approval and stage. The known current model includes `approved_to_delete` and `delete_stage`, but live schema wins.

## Startup readiness contract

During DCOIR startup or re-anchor, this skill should be invoked after `dcoir-session-resume` and `dcoir-memory-preflight`. Its job is to refresh or validate a local schema cache, confirm current operational tables, and make table/field metadata available before other skills perform repeated Airtable reads. The cache remains advisory and must not replace live schema readback for writes, deletes, migrations, linked-record changes, or any destructive action.

Startup reports must stay compact and must not render Airtable UI.
