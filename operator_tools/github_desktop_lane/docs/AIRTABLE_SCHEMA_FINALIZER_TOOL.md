# DCOIR Airtable Schema Finalizer Tool

## Purpose

`Invoke-DcoirAirtableSchemaFinalizer.ps1` is a reusable, parameterized Airtable schema/readback tool for DCOIR operator work.

It is designed for schema-finalization passes where ChatGPT or an operator needs to:

- verify that a table exists;
- create missing API-supported fields;
- validate readback-only native fields such as formula and autonumber fields;
- validate expected records by a stable key;
- validate generated-key parity across two fields when a manifest defines `key_match_checks`;
- produce readback evidence for field presence, row count, missing keys, duplicate keys, and key mismatches;
- emit precise follow-up tasks only when native Airtable work remains outside the safe API/connector lane.

The first consumer is `GitHub Workflow Inventory`, but the manifest-driven design is table-agnostic.

## Authority and limits

Airtable remains the live schema and record authority. GitHub remains the source of truth for this tool code and sample manifests.

The tool intentionally does not delete tables, fields, or records.

Native formula and autonumber fields should be represented as `readback_only_fields` once created in Airtable UI. The tool verifies they exist and can validate their computed output through record readback. Native field defaults may be represented as `field_defaults` only while they are still pending review; completed defaults should not stay in the manifest as perpetual tasks.

## Required local configuration

The tool reads configuration names only; it never stores or prints secret values.

Required environment variables:

- `DCOIR_AIRTABLE_TOKEN` — Airtable personal access token with schema and records permissions for the target base.
- `DCOIR_AIRTABLE_BASE_ID` — target Airtable base id, for example the DCOIR base.
- `DCOIR_DOWNLOADS_DIR` — optional output root for logs and diagnostic ZIPs.

Environment lookup order is Machine, User, then Process. This supports local operator-side PowerShell and GitHub Actions/check harnesses where secrets are injected as process environment variables.

## Launcher examples

Plan/readback only:

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableSchemaFinalizer.ps1'
$manifest = Join-Path $repo 'operator_tools\github_desktop_lane\manifests\airtable_schema_finalizer.github_workflow_inventory.sample.json'
& $script -ManifestJson $manifest -Mode Plan
```

Apply missing API-supported fields only:

```powershell
& $script -ManifestJson $manifest -Mode Apply -AllowCreateFields
```

Validate only, with no writes:

```powershell
& $script -ManifestJson $manifest -Mode Validate
```

## Output

Each run writes:

- terminal output;
- a single uploadable log file;
- `schema_finalizer_report.json`;
- `schema_finalizer_report.md`;
- a diagnostic ZIP containing the report files when `Compress-Archive` is available.

## Safety posture

- `Plan` and `Validate` modes do not create, update, or delete Airtable objects.
- `Apply` mode still requires explicit switches for write classes.
- Duplicate key records are reported rather than mutated.
- Missing readback-only native fields fail validation instead of being silently recreated as a weaker field type.
- Unsupported native field work is reported as a task only while it is actually pending.

## GitHub Workflow Inventory current design

For the current `GitHub Workflow Inventory` table, the final key fields are:

- `workflow_key` — stable primary lookup key.
- `workflow_seq_auto` — Airtable-native autonumber sequence.
- `workflow_key_native` — Airtable-native formula key.

Current `workflow_key_native` formula:

```text
"workflow-" & {workflow_family} & "-" & {workflow_file_stem} & "-" & RIGHT("0000" & {workflow_seq_auto}, 4)
```

The transitional bridge fields `workflow_seq` and `workflow_key_formula_preview` were intentionally removed after validation. Do not reintroduce them.

The current manifest validates:

- all API-supported workflow inventory fields exist;
- `workflow_seq_auto` and `workflow_key_native` exist as readback-only native fields;
- all 24 expected workflow keys exist;
- `workflow_key` equals `workflow_key_native` for every record;
- no duplicate expected workflow keys are present.
