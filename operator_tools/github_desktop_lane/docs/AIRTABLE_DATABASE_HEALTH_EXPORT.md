# DCOIR Airtable Database Health Export

Reusable operator-side export tool for DCOIR Airtable database health review.

## Purpose

Use this tool when ChatGPT needs an uploadable ZIP containing Airtable schema and selected record data for database engineering analysis, stale or duplicate record review, retention-class review, dependency-order review, and upload-back manicure planning.

The tool is read-only against Airtable. Any future cleanup implementation remains governed by DCOIR Delete Queue, dependency order, and compact lifecycle/tombstone preservation.

## Required Machine/System environment variables

Set these as System environment variables, then open a new PowerShell window:

```powershell
[Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
```

Do not use the older API-token variable name from prior drafts; it is non-canonical for this project.

Optional table limiting should be passed with `-TableList`:

```powershell
& $script -SchemaOnly -RedactLikelySecrets -MaxRecordsPerTable 10 -TableList 'Work Items,Plans,Local Configuration Registry'
```

If `-TableList` is omitted, the tool exports all tables visible to the token in the configured base.

Never paste token values into ChatGPT, Airtable notes, repo files, logs, or bundles.

## First-run smoke test

This launcher shows progress in the terminal and also produces a verbose diagnostic folder and `.chatgpt.zip` in `DCOIR_DOWNLOADS_DIR`. The tool creates diagnostics even when early configuration checks fail, such as a missing Airtable token.

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -SchemaOnly -RedactLikelySecrets -MaxRecordsPerTable 10 2>&1 | Tee-Object -Variable dcoirAirtableRun
```

Upload the resulting `.chatgpt.zip` from `DCOIR_DOWNLOADS_DIR`. If no ZIP exists, upload the newest `dcoir_airtable_health_export_<timestamp>` folder.

### Expected failure behavior

If a required System environment variable is missing, the command should still create:

```text
dcoir_airtable_health_export_<timestamp>/
  diagnostic_index.md
  command_context.json
  run.log.txt
  terminal_transcript.txt
  run_summary.json
  error_report.md
  error_report.json
```

A ChatGPT-friendly ZIP should also be created next to the folder when the ZIP helper exists. The diagnostic files log environment variable presence/absence only; they do not log secret values.

## Full bounded record export

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -RedactLikelySecrets -MaxRecordsPerTable 500
```

Use `-MaxRecordsPerTable 0` only when you intentionally want all records from selected tables.

## Output layout

```text
dcoir_airtable_health_export_<timestamp>/
  diagnostic_index.md
  command_context.json
  run.log.txt
  terminal_transcript.txt
  run_summary.json
  export_manifest.json
  schema/
    schema.summary.json
    schema.base_tables.json
    table.<safe_table_name>_<table_id>.schema.json
  records/
    table.<safe_table_name>_<table_id>.records.json
```

A ChatGPT-friendly ZIP is created next to the output folder unless `-NoZip` is passed. On failure, the same ZIP path is used for an uploadable diagnostic package.

## Safety contract

- Read only from Airtable.
- Do not write the Airtable token value to output.
- Always create a timestamped diagnostic folder and uploadable ZIP on failure when possible.
- Capture terminal context with `Start-Transcript`, `run.log.txt`, and machine-readable error JSON.
- Prefer `-RedactLikelySecrets` for record exports.
- Treat exported record data as operational data; upload only to approved DCOIR ChatGPT workspace.
- Cleanup recommendations require Delete Queue and dependency-safe processing.
