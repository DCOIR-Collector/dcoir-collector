# Generic Airtable Table Cleanup Design

This tool started as a Work Items cleanup helper. The next patch line should make it config-driven so it can clean other Airtable tables without adding table-specific environment variables.

## Goal

A local operator should be able to pick a table and a cleanup config once, then run the same safe flow:

1. dry run
2. create missing options
3. apply safe value cleanup and `DELETE -` field prefixes
4. verify
5. generate an Airtable Scripting Extension option-delete script
6. optionally test direct API deletion

## Recommended approach

Use a config file instead of one environment variable per table.

Environment variables should stay general:

| Variable | Purpose |
|---|---|
| `DCOIR_AIRTABLE_TOKEN` | Preferred Airtable token |
| `AIRTABLE_TOKEN` | Backup Airtable token |
| `DCOIR_AIRTABLE_BASE_ID` | Default Airtable base |
| `DCOIR_DOWNLOADS_DIR` | Output root |
| `DCOIR_AIRTABLE_CLEANUP_CONFIG` | Optional path to the cleanup config file |

Do not require table-specific variables like `DCOIR_AIRTABLE_WORK_ITEMS_TABLE_ID` for every table. A config file should carry table-specific IDs and cleanup rules.

## Config should define

- base ID or use `DCOIR_AIRTABLE_BASE_ID`
- table ID
- table name
- primary field name
- keep-visible fields
- fields to prefix with `DELETE -`
- select fields to normalize
- canonical select options
- old-to-new value mappings
- recommended defaults
- dangerous delete behavior settings

## Future launcher idea

A future `00_Select_Table_And_Config.cmd` can:

1. ask for a config file path, or use `DCOIR_AIRTABLE_CLEANUP_CONFIG`
2. read the base and table metadata
3. write a small local `.selected-config.json`
4. have the numbered launchers reuse that selected config

This avoids hard-coding one table per script while keeping the operator flow simple.


## Current Work Items cleanup state

The Work Items-specific cleanup has already removed retired fields and old select options. For the current `work_items_cleanup.config.example.json`, `prefix_delete_fields` should remain empty. Future table cleanups may still use the generic `prefix_delete_fields` concept when a new table has approved field-retirement targets.
