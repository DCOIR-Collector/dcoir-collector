# DCOIR Work Items Schema Cleanup Tool

This local tool verifies and maintains the simplified DCOIR Airtable `Work Items` table.

The original cleanup is complete. Current runs should no longer expect retired `DELETE -` fields.

It uses environment variables first wherever possible.

## Environment variables

| Variable | Purpose |
|---|---|
| `DCOIR_AIRTABLE_TOKEN` | Preferred Airtable token |
| `AIRTABLE_TOKEN` | Backup Airtable token name |
| `DCOIR_AIRTABLE_BASE_ID` | Preferred Airtable base ID |
| `DCOIR_DOWNLOADS_DIR` | Preferred output root |
| `DCOIR_AIRTABLE_WORK_ITEMS_DEFAULT_TABLE_ID` | Optional compatibility override for the Work Items table ID |

Do not create one environment variable per table. Future generic cleanup should use a config file selected once.

If `DCOIR_DOWNLOADS_DIR` is set, output goes under:

```text
%DCOIR_DOWNLOADS_DIR%\DCOIR_WorkItemsSchemaCleanup\YYYYMMDD\
```

If it is not set, output falls back to:

```text
%USERPROFILE%\Downloads\DCOIR_WorkItemsSchemaCleanup\YYYYMMDD\
```

The terminal and log show which source was used for base ID, table ID, and output folder.

## Double-click files

Run these in order when checking the current table state:

| Order | File | What it does |
|---:|---|---|
| 1 | `01_Dry_Run.cmd` | Reports current cleanup state only |
| 2 | `02_Apply_Options.cmd` | Creates missing canonical select options if any are missing |
| 3 | `03_Apply_Safe_Cleanup.cmd` | Normalizes record values; no retired Work Items fields are currently expected |
| 4 | `04_Verify.cmd` | Confirms the table is clean |
| 5 | `05_Generate_Option_Delete_Script.cmd` | Writes Airtable Scripting Extension JavaScript if obsolete select options are detected |
| 90 | `90_Self_Test.cmd` | Checks the tool files locally; does not call Airtable |
| 91 | `91_Attempt_Api_Option_Delete_DANGEROUS.cmd` | Tries direct API option deletion; expected to fail on normal Airtable API |
| 92 | `92_Attempt_Field_Delete_DANGEROUS.cmd` | Legacy diagnostic only; current Work Items cleanup should not need field deletion |

## Logs and reports

Every launcher pauses before closing and writes a timestamped log.

Expected folder pattern:

```text
DCOIR_WorkItemsSchemaCleanup\YYYYMMDD\
```

Expected file names look like:

```text
work_items_schema_cleanup_01_dry_run_20260501T132500Z.log
work_items_schema_cleanup_01_dry_run_20260501T132500Z.json
work_items_schema_cleanup_01_dry_run_20260501T132500Z.md
```

## Canonical Status values

```text
todo
active
blocked
waiting
done
dropped
```

## Current expected Work Items fields

```text
Queue Rank
Status
Work Item
Item ID
canonical_parent_plan_id
Area
Priority
Work Type
Repo Path or Skill
Evidence / Notes
created_at
updated_at
```

## Completed cleanup state

The retired Work Items fields and the old `Queue Control.active_work_items` link have been removed. Current verify reports should show:

```text
fields_to_prefix_delete: 0
records_needing_value_normalization: 0
missing_canonical_select_options: {}
obsolete_option_usage: {}
warnings: []
```

## Success markers

Look for these in the terminal and log:

```text
DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_DONE
DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_WRAPPER_DONE
```

If the window shows an error, upload the newest `.log`, `.json`, and `.md` from the tool output folder. Do not include your Airtable token.

## Future generic cleanup mode

This tool is currently tuned for the `Work Items` table. The next major patch should make cleanup rules config-driven so the same tool can clean other Airtable tables.

See:

```text
GENERIC_TABLE_CLEANUP_DESIGN.md
work_items_cleanup.config.example.json
```

Avoid adding one environment variable per table. Prefer a config file selected once, with general environment variables for token, base, output folder, and config path.

## v7 cleanup-state note

The v7 patch updates the tool and docs after final manual field deletion. The tool no longer expects deleted Work Items fields and the example config carries an empty `prefix_delete_fields` list for the current table.
