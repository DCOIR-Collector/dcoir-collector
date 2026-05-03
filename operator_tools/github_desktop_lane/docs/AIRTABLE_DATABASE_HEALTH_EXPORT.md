# DCOIR Airtable Database Health Export

## Purpose

`New-DcoirAirtableDatabaseHealthExport.ps1` is the reusable local operator tool for exporting the DCOIR Airtable base into a ChatGPT-friendly evidence bundle.

Use it when a session needs Airtable operational state for queue, plan, work item, validation, registry, helper-memory, retention, cleanup, or cross-session handoff analysis.

The tool is read-only against Airtable. Any future cleanup implementation remains governed by DCOIR Delete Queue, dependency order, and compact lifecycle/tombstone preservation.

## Authority and discovery

- Source code: `operator_tools/github_desktop_lane/scripts/New-DcoirAirtableDatabaseHealthExport.ps1`
- Module: `operator_tools/github_desktop_lane/modules/Dcoir.Airtable/Dcoir.Airtable.psm1`
- Machine-readable catalog: `operator_tools/github_desktop_lane/tool_catalog.json`
- Live discovery index: Airtable `Operator Tools Registry`, tool id `DCOIR-AIRTABLE-DB-HEALTH-EXPORT`

## Local configuration

The tool reads local configuration from Machine/System environment variables. It must not print or export environment token values.

Required variables:

```powershell
[Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
```

Use canonical names from Airtable `Local Configuration Registry`. Do not invent alternate token/base-id variable names.

## Scrubbed-data policy

Operator policy as of 2026-05-03: DCOIR Airtable record contents are already scrubbed upstream and should be treated as safe operational state for project database snapshots.

Default DCOIR full exports should not pass `-RedactLikelySecrets`, because record-field redaction hides useful operational values such as repo paths, work surfaces, routing fields, and registry guidance.

Keep these protections:

- never print or export Airtable token values;
- never print or export local secret environment values;
- keep cleanup/deletion actions governed by Delete Queue and dependency order;
- use `-RedactLikelySecrets` only when the operator explicitly requests a redacted sample or when exporting a non-DCOIR/unknown Airtable base.

## Parameters

```powershell
-ExportMode Auto|SchemaOnly|BoundedRecords|FullRecords
-FullRecordDump
-SkipRecords
-MaxRecordsPerTable <int>
-MetadataScope 'BaseSchema,Tables,Fields,Views'   # or 'All'
-ProbeUnsupportedMetadata
-RedactLikelySecrets
-TableList '<comma-separated table names or IDs>'
-NoZip
```

## Recommended launchers

Schema-only smoke:

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -ExportMode SchemaOnly -ProbeUnsupportedMetadata
```

Bounded record sample:

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -ExportMode BoundedRecords -MaxRecordsPerTable 25 -MetadataScope 'All' -ProbeUnsupportedMetadata
```

Full DCOIR database snapshot:

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -ExportMode FullRecords -FullRecordDump -MetadataScope 'All' -ProbeUnsupportedMetadata
```

Redacted sample only when explicitly requested:

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -ExportMode BoundedRecords -MaxRecordsPerTable 25 -MetadataScope 'All' -RedactLikelySecrets -ProbeUnsupportedMetadata
```

If `-TableList` is omitted, the tool exports all tables visible to the token in the configured base.

## Current supported metadata and values

The exporter currently captures:

- base tables schema;
- table id/name/description/primaryFieldId;
- field id/name/type/description/options where Airtable returns them;
- view id/name/type;
- record id/createdTime/fields;
- command context, run summary, export manifest, transcript, run log, captured-files manifest, ZIP manifest, and metadata coverage notes.

The exporter does not currently export automations, extensions/apps, interfaces, scripting extension code, or certain workspace/base admin surfaces unless a supported Airtable API endpoint and token scope are added later.

## Output layout

```text
dcoir_airtable_health_export_<timestamp>/
  diagnostic_index.md
  command_context.json
  run.log.txt
  terminal_transcript.txt
  run_summary.json
  export_manifest.json
  metadata/
    metadata_coverage.json
  schema/
    schema.summary.json
    schema.base_tables.json
    table.<safe_table_name>_<table_id>.schema.json
  records/
    table.<safe_table_name>_<table_id>.records.json
```

A ChatGPT-friendly ZIP is created next to the output folder unless `-NoZip` is passed. On failure, the same ZIP path is used for an uploadable diagnostic package.

## Validation history

2026-05-03 validation sequence:

- schema-only smoke passed;
- bounded live export passed after Dcoir.Airtable URL and offset fixes;
- full-record export passed with `ExportMode FullRecords`, `FullRecordDump true`, `MaxRecordsPerTable 0`, `MetadataScope All`, 24 selected tables, 24 schema files, 24 record files, and 1,132 records exported;
- follow-up policy correction: full DCOIR exports should omit `-RedactLikelySecrets` by default because Airtable records are already scrubbed.

## Future improvement

Add supported metadata probes only when Airtable exposes a documented API endpoint and the configured token has the required scope. Until then, record unsupported surfaces in `metadata/metadata_coverage.json` instead of implying complete automation/extension/interface capture.
