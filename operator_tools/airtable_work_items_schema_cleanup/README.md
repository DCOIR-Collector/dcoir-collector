# DCOIR Work Items Schema Cleanup Tool

This local tool helps simplify the DCOIR Airtable `Work Items` table.

It uses your local Airtable token from one of these environment variables:

```text
DCOIR_AIRTABLE_TOKEN
AIRTABLE_TOKEN
```

It uses base `appM4KSwnVf3G3OTK` and table `tblgsQAVWvh8K7gIR` by default.

## Important safety rule

Start with dry run. Do not use dangerous modes unless the dry run and safe apply modes look correct.

## Double-click files

| File | What it does |
|---|---|
| `Run_DCOIR_WorkItemsSchemaCleanup_SelfTest.cmd` | Checks the tool files locally; does not call Airtable |
| `Run_DCOIR_WorkItemsSchemaCleanup_DryRun.cmd` | Reports planned changes only |
| `Run_DCOIR_WorkItemsSchemaCleanup_ApplyOptions.cmd` | Creates missing simple select options |
| `Run_DCOIR_WorkItemsSchemaCleanup_ApplySafe.cmd` | Normalizes record values and prefixes retired fields with `DELETE -` |
| `Run_DCOIR_WorkItemsSchemaCleanup_Verify.cmd` | Checks cleanup state |
| `Run_DCOIR_WorkItemsSchemaCleanup_GenerateOptionDeleteScript.cmd` | Writes Airtable Scripting Extension JavaScript for option deletion |
| `Run_DCOIR_WorkItemsSchemaCleanup_AttemptApiOptionDelete_DANGEROUS.cmd` | Tries direct API option deletion; expected to fail on normal Airtable API |
| `Run_DCOIR_WorkItemsSchemaCleanup_AttemptFieldDelete_DANGEROUS.cmd` | Tries direct API field deletion for `DELETE -` fields; expected to fail on normal Airtable API |

## Logs

Every `.cmd` launcher now pauses before closing and writes a timestamped log to:

```text
%USERPROFILE%\Downloads\DCOIR
```

If `DCOIR_DOWNLOADS_DIR` is set, it writes there instead.

The log name looks like:

```text
work_items_schema_cleanup_dry-run_20260501T132500Z.log
```

JSON and Markdown reports are written to the same folder.

## Recommended run order

1. Double-click `Run_DCOIR_WorkItemsSchemaCleanup_SelfTest.cmd`.
2. Double-click `Run_DCOIR_WorkItemsSchemaCleanup_DryRun.cmd`.
3. Review the log and report in `Downloads\DCOIR`.
4. Double-click `Run_DCOIR_WorkItemsSchemaCleanup_ApplyOptions.cmd`.
5. Double-click `Run_DCOIR_WorkItemsSchemaCleanup_ApplySafe.cmd`.
6. Double-click `Run_DCOIR_WorkItemsSchemaCleanup_Verify.cmd`.
7. Double-click `Run_DCOIR_WorkItemsSchemaCleanup_GenerateOptionDeleteScript.cmd` if select-option cleanup is needed.
8. Use dangerous API delete launchers only if you explicitly want to test whether Airtable supports those API delete calls.

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

If the window shows an error, copy the text or upload the log. Do not include your Airtable token.

## v3 wrapper note

The wrapper suppresses Python deprecation warnings and does not treat harmless stderr text as failure. Success is based on the Python process exit code and generated report files.
