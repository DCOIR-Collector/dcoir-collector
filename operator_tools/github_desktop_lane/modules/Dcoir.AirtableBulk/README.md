# Dcoir.AirtableBulk

Reusable PowerShell helpers for safe Airtable bulk insert and readback patterns discovered during the DCOIR database redesign WBS scaffold work.

## Purpose

Use this module when a ChatGPT-staged or operator-side script needs to create Airtable records in batches and verify the result by key before claiming completion.

It is intentionally generic and does not specialize the shared `chatgpt-exec` workflow or harness.

## Solves

- PowerShell root JSON arrays from `ConvertFrom-Json` being treated as one object instead of row-by-row input.
- Airtable field-id readback under `Set-StrictMode`.
- Airtable create-record batching with a maximum batch size of 10.
- Create-missing-by-key behavior to avoid duplicate rows on retry.
- After-readback validation for missing or duplicate expected keys.
- Reusable `planned_payload`, created-record, skipped-existing, missing-after, and duplicate-after data structures.

## Primary functions

- `Read-DcoirAirtableBulkJsonRows`
- `Get-DcoirAirtableBulkRecordsByFieldId`
- `Get-DcoirAirtableFieldValueById`
- `Invoke-DcoirAirtableBulkCreateRecords`
- `Invoke-DcoirAirtableBulkCreateMissingByKey`

## Recommended usage pattern

1. Resolve Airtable schema and field IDs with `Dcoir.Airtable`.
2. Read input rows with `Read-DcoirAirtableBulkJsonRows`.
3. Build a `FieldIdByInputName` hashtable.
4. Run `Invoke-DcoirAirtableBulkCreateMissingByKey` using a stable unique input key.
5. Write artifacts from the returned object:
   - `target_records.json`
   - `planned_payload.json`
   - `execution_summary.json`
   - `after_readback_verification.json`
   - `error_report.json` on failure

## Safety notes

- This module only creates records; it does not update, delete, merge, or enqueue Delete Queue rows.
- It expects caller-owned approval gates before execution.
- It does not hide broad Airtable writes behind generic behavior; callers must supply exact table IDs, field IDs, and target rows.
- Retrying is safe when the same key field is used because existing keys are skipped and reported.

## Origin

Captured after `dcoir-db-redesign-wbs-scaffold-run3-20260508-2025z` successfully created 52 missing WBS scaffold rows and passed after-readback verification.
