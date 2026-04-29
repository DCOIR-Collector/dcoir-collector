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
