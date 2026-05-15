# DCOIR WBS09 Airtable View Repair Batch

This tool family creates saved Airtable native-view filter/sort repair plans for WBS09 view drift discovered by the panel-readback verifier.

## Current status

**DryRun remains available. Apply mode is disabled.**

The v1 broad Apply path failed validation on 2026-05-15. It was able to create a dry-run plan, but the broad mutation path did not reliably discover/click Airtable filter/sort controls during live execution. The failed Apply run produced 0 verified repairs across the 25 remaining WBS09 gap targets. A post-failed-apply readback confirmed the 25 gaps remained.

Do not use `APPLY_WBS09_VIEW_REPAIR_BATCH` with this v1 tool. The PowerShell launcher and Node engine both hard-block Apply mode.

## Supported mode

`DryRun`:

- opens Airtable;
- reads current filter/sort panel state;
- compares the live UI state against the governed WBS09 manifest;
- writes a per-target repair plan;
- does not mutate Airtable.

## Disabled mode

`Apply` is blocked until replaced by a validated v2 operation-class-specific apply tool.

The next apply architecture must split work into smaller supported operation classes, such as:

1. sort-direction-only repairs;
2. add-missing-filter-only repairs;
3. replace-sort-field repairs;
4. source-intent/manual-review cases.

A future Apply path must discover exact controls and prove they are clickable before removing or replacing any existing filter/sort row.

## Inputs

- `-TargetListFile`: JSON file with `target_keys`, JSON array, or newline-delimited target keys.
- `-AllGapTargets`: use the built-in remaining-gap target list.
- `-ManifestPath`: WBS09 native-view manifest. Defaults to the repo manifest.
- `-Mode DryRun` only.

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
4. Use a separate validated v2 apply tool for a single operation class only after explicit approval.
5. Re-run `Invoke-DcoirAirtableWbs09ViewPanelReadback.ps1` for repaired targets.
6. Persist the outcome to Session Checkpoints and Validation Evidence.

## Failed validation note

On 2026-05-15, v1 Apply was run against the remaining 25 WBS09 gap targets. Result: 23 `apply_failed`, 1 `apply_gap_after_reload`, and 1 `skipped_apply_unsupported`. Primary failure signature: `Could not find sort direction control`. Follow-up readback showed 0 repairs verified and all 25 gaps still present.

This v1.1 containment patch preserves DryRun and prevents accidental reuse of the failed broad Apply path.
