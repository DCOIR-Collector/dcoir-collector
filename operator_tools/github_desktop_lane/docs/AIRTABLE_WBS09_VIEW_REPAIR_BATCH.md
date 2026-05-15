# DCOIR WBS09 Airtable View Repair Batch

This tool family repairs saved Airtable native-view filter/sort drift discovered by the WBS09 panel-readback verifier.

## Safety model

The tool has two modes:

1. `DryRun`: opens Airtable, reads current filter/sort panel state, compares it to the governed WBS09 manifest, and writes a repair plan. It does not mutate Airtable.
2. `Apply`: re-runs the same live preflight, requires an explicit confirmation token, then attempts only the plan actions that the live preflight says are still required.

The apply path is intentionally guarded:

- It requires `-Mode Apply`.
- It requires `-ConfirmToken APPLY_WBS09_VIEW_REPAIR_BATCH`.
- It prompts for the same token interactively after Airtable login and before any mutation.
- It performs live readback before each target.
- It verifies each target after mutation and after reload.
- It records skipped/unsupported targets instead of blindly clicking.
- It does not create/delete/rename Airtable views.
- It does not delete Airtable records, fields, or tables.

## Inputs

- `-TargetListFile`: JSON file with `target_keys`, or newline-delimited target keys.
- `-AllGapTargets`: use the built-in remaining-gap target list.
- `-ManifestPath`: WBS09 native-view manifest. Defaults to the repo manifest.
- `-Mode DryRun|Apply`.

## Output

Output is written under `DCOIR_DOWNLOADS_DIR`:

- `view_repair_batch_rollup.json`
- `view_repair_batch_plan.json`
- per-target repair reports
- before/after DOM and screenshot evidence when enabled

## Validation order

Recommended flow:

1. Run dry-run against all gap targets.
2. Upload the dry-run evidence ZIP.
3. Review skipped/unsupported/source-intent entries.
4. Run apply only when the plan is approved.
5. Re-run `Invoke-DcoirAirtableWbs09ViewPanelReadback.ps1` for the repaired target list.
6. Persist the outcome to Session Checkpoints and Validation Evidence.

## Notes

This tool is intentionally a batch wrapper around existing readback/discovery behavior. It does not replace the read-only WBS09 panel-readback verifier, which remains the authority for post-repair verification.
