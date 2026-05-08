# Dcoir.AirtableBulkUpdate

Reusable PowerShell helpers for safe Airtable update patterns that require before-value gates and after-readback verification.

## Purpose

Use this module when a ChatGPT-staged or operator-side script needs to update Airtable records in bounded batches and verify exact target records before and after mutation.

It is intentionally generic and does not specialize the shared `chatgpt-exec` workflow or harness.

## Solves

- Airtable record updates with explicit before-value gates.
- Single-select alias normalization using select choice names for record values.
- Airtable field-id readback under `Set-StrictMode`.
- Airtable PATCH batching with a maximum batch size of 10.
- After-readback verification for exact target records.
- Reusable `planned_payload`, `before_readback`, `after_readback`, and mismatch structures.

## Primary functions

- `Get-DcoirAirtableBulkUpdateVersion`
- `Get-DcoirAirtableUpdateFieldValueById`
- `Get-DcoirAirtableBulkUpdateRecordById`
- `Invoke-DcoirAirtableBulkPatchRecords`
- `Invoke-DcoirAirtableSelectAliasUpdateWithBeforeGates`

## Select value contract

For Airtable single-select record values, this module compares and writes by **choice name**. Choice IDs may be carried in approval packets as schema/audit metadata, but record readback and PATCH payloads use names.

This avoids the failure mode where schema choice IDs are compared against record readback names.

## Recommended usage pattern

1. Build an exact approval packet with table IDs, record IDs, field IDs, old choice names, and new choice names.
2. Include choice IDs as optional metadata if useful for schema audit.
3. Run `Invoke-DcoirAirtableSelectAliasUpdateWithBeforeGates`.
4. Write artifacts from the returned object:
   - `target_records.json`
   - `planned_payload.json`
   - `execution_summary.json`
   - `after_readback_verification.json`
   - `error_report.json` on failure
5. Do not claim completion until after-readback passes.

## Safety notes

- This module updates existing records only.
- It does not create, delete, merge, or enqueue Delete Queue rows.
- It expects caller-owned approval gates before execution.
- It stops on the first before-value mismatch.
- It should be used only with exact target records and exact fields, not broad unreviewed table updates.

## Origin

Captured after the first `dcoir-alias-normalization-20260508-2105z` run exposed the reusable select-value contract: Airtable record values for single-select fields were read as choice names, not schema choice IDs. Version `2026-05-08.2` fixes the helper to compare/write by choice name.
