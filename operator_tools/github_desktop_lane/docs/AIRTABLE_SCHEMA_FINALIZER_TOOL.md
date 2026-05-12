# DCOIR Airtable Schema Finalizer Tool

## Purpose

`Invoke-DcoirAirtableSchemaFinalizer.ps1` is a reusable, parameterized Airtable schema/readback tool for DCOIR operator work.

It is designed for schema-finalization passes where ChatGPT or an operator needs to:

- verify that a table exists;
- create missing API-supported fields;
- validate expected records by a stable key;
- produce readback evidence for field presence, row count, missing keys, and duplicate keys;
- emit precise follow-up tasks for native Airtable features that are not safely creatable through the public API or connector lane.

The first consumer is `GitHub Workflow Inventory`, but the manifest-driven design is table-agnostic.

## Authority and limits

Airtable remains the live schema and record authority. GitHub remains the source of truth for this tool code and sample manifests.

The tool intentionally does not delete tables, fields, or records.

Native formula fields, autonumber fields, and native field defaults are handled as `ui_only_fields` / `field_defaults` tasks in the manifest. The tool does not fake those features or silently downgrade them.

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
- Unsupported native field work is reported as a UI/default task instead of attempted through an unsafe workaround.

## GitHub Workflow Inventory native follow-up

For the current `GitHub Workflow Inventory` table, the remaining native Airtable UI/default tasks are:

1. Add optional `workflow_seq_auto` as an Airtable Autonumber field.
2. Add optional `workflow_key_native` as a Formula field:

```text
"workflow-" & {workflow_family} & "-" & {workflow_file_stem} & "-" & RIGHT("0000" & IF({workflow_seq}, {workflow_seq}, {workflow_seq_auto}), 4)
```

3. Compare `workflow_key_native` to `workflow_key` and `workflow_key_formula_preview` before promoting it as the generated key reference.
4. Configure native defaults where Airtable UI supports them:
   - `status`: `active`
   - `active`: checked
   - `routing_owner_skill`: `dcoir-memory-preflight`
   - `cache_scope`: `workflow_task_routing`
   - `retention_class`: `operational`

Until those UI/default tasks are complete, the current table remains usable because `workflow_key`, `workflow_seq`, and `workflow_key_formula_preview` are already populated explicitly.
