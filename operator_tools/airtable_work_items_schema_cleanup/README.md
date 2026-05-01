# DCOIR Work Items Schema Cleanup Tool

This local tool helps simplify the DCOIR Airtable `Work Items` table.

It uses your local Airtable token from:

```text
DCOIR_AIRTABLE_TOKEN
```

or:

```text
AIRTABLE_TOKEN
```

It uses base `appM4KSwnVf3G3OTK` and table `tblgsQAVWvh8K7gIR` by default.

## Modes

| Mode | File | What it does |
|---|---|---|
| Dry run | `Run_DCOIR_WorkItemsSchemaCleanup_DryRun.cmd` | Reports planned changes only |
| Apply options | `Run_DCOIR_WorkItemsSchemaCleanup_ApplyOptions.cmd` | Creates missing canonical select options by temporary scratch record |
| Apply safe | `Run_DCOIR_WorkItemsSchemaCleanup_ApplySafe.cmd` | Normalizes record values and prefixes retired fields with `DELETE -` |
| Verify | `Run_DCOIR_WorkItemsSchemaCleanup_Verify.cmd` | Confirms old values are no longer used |
| Generate option delete script | `Run_DCOIR_WorkItemsSchemaCleanup_GenerateOptionDeleteScript.cmd` | Writes Airtable Scripting Extension JavaScript for option deletion |
| Attempt API option delete | `Run_DCOIR_WorkItemsSchemaCleanup_AttemptApiOptionDelete_DANGEROUS.cmd` | Tries direct API option deletion; expected to fail on normal Airtable Web API |
| Attempt field delete | `Run_DCOIR_WorkItemsSchemaCleanup_AttemptFieldDelete_DANGEROUS.cmd` | Tries direct API deletion of fields prefixed `DELETE -`; expected to fail on normal Airtable Web API |

## Recommended order

1. Run dry run.
2. Run apply options.
3. Run apply safe.
4. Run verify.
5. Run generate option delete script.
6. Paste the generated JavaScript into Airtable Scripting Extension if option deletion is needed.
7. Try dangerous API attempts only if you explicitly want to test whether your Airtable account/API currently supports them.

## Canonical Status values

```text
todo
active
blocked
waiting
done
dropped
```

## Fields marked for deletion

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

## Logs and reports

The PowerShell wrapper tees terminal output to a timestamped log in `DCOIR_DOWNLOADS_DIR` when that environment variable exists. Otherwise it writes to this tool's local `out` folder.

The Python tool also writes JSON and Markdown reports.

## Safety

The dangerous modes require explicit confirmation words in the wrapper:

```text
DELETE_FIELDS
DELETE_OPTIONS
```

The normal Web API is expected to reject direct field deletion and direct option deletion. Those modes exist only to test capability and capture proof.
