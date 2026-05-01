# DCOIR Work Items Schema Cleanup Tool

This local tool helps simplify the DCOIR Airtable `Work Items` table.

It uses environment variables first wherever possible.

## Environment variables

| Variable | Purpose |
|---|---|
| `DCOIR_AIRTABLE_TOKEN` | Preferred Airtable token |
| `AIRTABLE_TOKEN` | Backup Airtable token name |
| `DCOIR_AIRTABLE_BASE_ID` | Preferred Airtable base ID |
| `DCOIR_AIRTABLE_WORK_ITEMS_TABLE_ID` | Preferred Work Items table ID |
| `DCOIR_DOWNLOADS_DIR` | Preferred output root |

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

Run these in order:

| Order | File | What it does |
|---:|---|---|
| 0 | `00_Remove_Legacy_Wrapper_Filenames.cmd` | Optional: removes old long `.cmd` filenames after the numbered wrappers are installed |
| 1 | `01_Dry_Run.cmd` | Reports planned changes only |
| 2 | `02_Apply_Options.cmd` | Creates missing simple select options |
| 3 | `03_Apply_Safe_Cleanup.cmd` | Normalizes record values and prefixes retired fields with `DELETE -` |
| 4 | `04_Verify.cmd` | Checks cleanup state |
| 5 | `05_Generate_Option_Delete_Script.cmd` | Writes Airtable Scripting Extension JavaScript for option deletion |
| 90 | `90_Self_Test.cmd` | Checks the tool files locally; does not call Airtable |
| 91 | `91_Attempt_Api_Option_Delete_DANGEROUS.cmd` | Tries direct API option deletion; expected to fail on normal Airtable API |
| 92 | `92_Attempt_Field_Delete_DANGEROUS.cmd` | Tries direct API field deletion for `DELETE -` fields; expected to fail on normal Airtable API |

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

## Fields marked for deletion by safe apply

The safe apply mode prefixes these fields with `DELETE -`:

```text
Next Action
Branch State
pipeline_stage
canonical_item_type
retirement_action
Owner
Active
Resume First
Queue Control
GitHub Link
Due Date
Blocker
Decision Source
Priority Rationale
Supersedes Item IDs
Superseded By Item ID
source_table
source_record_id
review_after
Last Confirmed Text
```

## Success markers

Look for these in the terminal and log:

```text
DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_DONE
DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_WRAPPER_DONE
```

If the window shows an error, upload the newest `.log`, `.json`, and `.md` from the tool output folder. Do not include your Airtable token.

## v4 wrapper note

The v4 wrapper adds numbered human-readable launchers, dated output folders, and explicit environment-variable source reporting. It also keeps the legacy wrapper cleanup as an operator-run step so file deletions are visible in GitHub Desktop.

## Future generic cleanup mode

This tool is currently tuned for the `Work Items` table. The next major patch should make the cleanup rules config-driven so the same tool can clean other Airtable tables.

See:

```text
GENERIC_TABLE_CLEANUP_DESIGN.md
work_items_cleanup.config.example.json
```

Avoid adding one environment variable per table. Prefer a config file selected once, with general environment variables for token, base, output folder, and config path.
