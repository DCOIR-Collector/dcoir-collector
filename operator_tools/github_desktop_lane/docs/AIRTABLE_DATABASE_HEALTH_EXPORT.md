# DCOIR Airtable Database Health Export

Reusable operator-side export tool for DCOIR Airtable database health review.

## Purpose

Use this tool when ChatGPT needs a ZIP containing Airtable schema and selected record data for database engineering analysis, stale or duplicate record review, retention-class review, dependency-order review, and upload-back manicure planning.

The tool is read-only against Airtable. Any future cleanup implementation remains governed by DCOIR Delete Queue, dependency order, and compact lifecycle/tombstone preservation.

## Required Machine/System environment variables

Set these as System environment variables, then open a new PowerShell window:

```powershell
[Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_API_TOKEN','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
```

Optional:

```powershell
[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TABLES','Machine')
```

`DCOIR_AIRTABLE_TABLES` is a comma-separated list of table names or table IDs. If unset, the tool exports all tables visible to the token in the configured base.

Never paste token values into ChatGPT, Airtable notes, repo files, logs, or bundles.

## First-run smoke test

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -SchemaOnly -RedactLikelySecrets -MaxRecordsPerTable 10
```

Upload the resulting `.chatgpt.zip` from `DCOIR_DOWNLOADS_DIR`.

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
  export_manifest.json
  schema/
    schema.summary.json
    schema.base_tables.json
    table.<safe_table_name>_<table_id>.schema.json
  records/
    table.<safe_table_name>_<table_id>.records.json
```

A ChatGPT-friendly ZIP is created next to the output folder unless `-NoZip` is passed.

## Safety contract

- Read only from Airtable.
- Do not write the API token value to output.
- Prefer `-RedactLikelySecrets` for record exports.
- Treat exported record data as operational data; upload only to approved DCOIR ChatGPT workspace.
- Cleanup recommendations require Delete Queue and dependency-safe processing.
