# WBS09 Manifest Schema Audit Tool

## Purpose

`Invoke-DcoirWbs09ManifestSchemaAudit.ps1` is a reusable preflight gate for WBS09 Airtable native-view automation.

It checks the WBS09 view manifest against a live or freshly exported Airtable schema JSON before browser automation configures filters, sorts, or field visibility.

The tool does **not** mutate Airtable. It only reads local JSON files and writes audit evidence.

## Ownership and stale-data controls

- Source/tool-code ownership: GitHub repo `operator_tools/github_desktop_lane/`, routed by `dcoir-github-desktop-lane-advisor`.
- Schema freshness ownership: `dcoir-airtable-schema-cache` and live Airtable schema readback.
- Readiness/evidence gate: `dcoir-validation-orchestrator`.

Do not treat an old audit output as approval for a later UI automation pass. Re-run the audit whenever the manifest, Airtable schema, select options, or target tables may have changed.

For write/configuration work, use fresh live Airtable schema readback or a schema export produced immediately before the audit. A cache is a speed aid, not write authority.

## Inputs

Default manifest:

```powershell
operator_tools\github_desktop_lane\manifests\wbs09_airtable_native_views_manifest.json
```

Required schema JSON:

```powershell
-SchemaJson <path to live schema/cache/export JSON>
```

The schema JSON must contain table and field metadata. Select fields should include choice names so the audit can verify filter values.

## Outputs

The tool writes a timestamped folder under `DCOIR_DOWNLOADS_DIR` unless `-OutputDir` is supplied:

```text
wbs09_manifest_schema_audit.json
wbs09_manifest_schema_audit.md
audit.log
```

Status behavior:

```text
PASS               error_count = 0 and warning_count = 0
PASS_WITH_WARNINGS error_count = 0 and warning_count > 0
FAIL               error_count > 0
```

The PowerShell process exits with:

```text
0 = pass or warnings accepted
2 = blocking errors
3 = warnings when -FailOnWarnings is supplied
```

## Example launcher

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirWbs09ManifestSchemaAudit.ps1'
$schema = Join-Path $downloads 'dcoir_airtable_schema_live.json'

& $script -SchemaJson $schema -FailOnWarnings
```

## Stop condition

If the audit does not return `PASS`, patch the manifest or refresh the schema before running Airtable UI automation.
