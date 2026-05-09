# WBS09 Airtable UI View Creation Validation

## Validation gates

1. Install gate
   - `Install-DcoirAirtableWbs09UiViewPrereqs.ps1` completes successfully.
   - `install_result.json` exists under `DCOIR_DOWNLOADS_DIR`.

2. Dry-run gate
   - `dry_run_report.json` exists.
   - `manifest_view_count` is 65.
   - `manifest_table_count` is 21.
   - `selected_view_count` is 65 for full dry-run.

3. Calibration gate
   - `calibration_report.json` exists.
   - The report URL/title match Airtable/DCOIR base context.
   - No create-click action is attempted.

4. One-view smoke gate
   - Run with `-TableName 'Work Items' -MaxViews 1`.
   - Airtable shows the expected new view name.
   - `execution_report.json` has one result.
   - No unexpected modal, wrong table, duplicate view, or partial-name issue appears.

5. Bulk gate
   - Only after one-view smoke passes.
   - Verify total target views after run.
   - Record evidence in Validation Evidence before marking WBS09.04 complete.

## Evidence to upload or report back

- Install output directory path.
- Dry-run output directory path.
- Calibration output directory path.
- One-view smoke `execution_report.json` and screenshot if enabled.
- Bulk `execution_report.json` after full run.
