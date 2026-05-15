# Airtable WBS09 Native View Panel Readback

## Purpose

Read and verify saved Airtable native view Filter and Sort panel configuration from the browser UI.

This tool exists because the Airtable connector/API can read schemas and records, but does not expose saved native view Filter/Sort panel configuration. For WBS09, native UI panel readback is the evidence path for proving view configuration after refresh/reselect.

## Current status

- Status: readback-only promotion candidate.
- Mutates Airtable: no.
- Proven locally on representative WBS09 views using screenshots plus machine-readable panel row reports.
- Repair/create automation is intentionally outside this promoted readback surface until action primitives are hardened.

## What the tool does

- Opens the DCOIR Airtable base in a visible browser.
- Selects target tables/views using URL table navigation and left-sidebar view selection.
- Avoids the active-view-name metadata hot zone.
- Opens actual Filter and Sort panels.
- Extracts row-level panel state from visible UI controls.
- Refreshes/reselects and verifies that the same saved state persists.
- Writes logs, DOM evidence, JSON reports, and optional screenshots under `DCOIR_DOWNLOADS_DIR`.

## What the tool does not do

- It does not create views.
- It does not modify filters, sorts, fields, records, tables, or Airtable automations.
- It does not use grid body text as proof of saved view state.
- It does not prove unsupported views unless the manifest target is included and the panels are successfully read.
- It does not replace Airtable connector schema/record reads for normal data access.

## Environment contract

Required Local Configuration Registry names:

- `DCOIR_REPO_ROOT`
- `DCOIR_DOWNLOADS_DIR`

Do not store local environment values, profile paths, cookies, tokens, or secrets in GitHub, Airtable, logs, or evidence bundles.

## Representative readback

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09ViewPanelReadback.ps1'
& $script -DefaultRepresentativeTargets -EnableScreenshots -UseChromeChannel -UserDataDir "$env:LOCALAPPDATA\DCOIR\chrome-profile"
```

Package the output folder for review:

```powershell
$latest = Get-ChildItem -LiteralPath $env:DCOIR_DOWNLOADS_DIR -Directory |
  Where-Object Name -like 'dcoir_wbs09_view_panel_readback_*' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$zipPath = Join-Path $env:DCOIR_DOWNLOADS_DIR ($latest.Name + '_chatgpt.zip')

& (Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirChatGPTFriendlyZip.ps1') `
  -SourceFolder $latest.FullName `
  -OutputZip $zipPath

Set-Clipboard -Value $zipPath
Write-Host "UPLOAD_ZIP_PATH=$zipPath"
```

## Broad readback guardrail

All-manifest readback is read-only but broad. It requires the explicit confirmation token:

```powershell
& $script -AllManifestViews -ConfirmToken READBACK_ALL_MANIFEST_VIEWS -EnableScreenshots -UseChromeChannel -UserDataDir "$env:LOCALAPPDATA\DCOIR\chrome-profile"
```

## Evidence interpretation

A target passes only when the expected Filter/Sort panel rows are observed after refresh/reselect. A pass must come from actual panel extraction, not from body/grid text.

Known useful statuses:

- `expected_panel_state_observed_after_refresh`: target matched expected panel state after refresh/reselect.
- `panel_state_gap_found`: target was reached, but one or more expected rows were not observed.
- failure/exception status: selection, panel opening, or extraction failed; inspect screenshots and DOM evidence.

## Design boundary for future create/repair automation

Future create/repair automation should not click controls blindly. It should follow this sequence:

1. Discover current table/view/panel state.
2. Discover available UI options for the exact field/operator/value/sort control.
3. Build an explicit plan from observed options.
4. Execute the smallest required change.
5. Re-open panels and verify row state after refresh/reselect.
6. Package evidence.

The readback module is the verification foundation for that future pipeline.

## 2026-05-14 parameterized readback upgrade

This pass upgrades the existing readback surface rather than adding a duplicate verifier.

Reusable shared module behavior now includes:

- structured gap classification for filter gaps, sort gaps, panel extraction gaps, and unknown gaps;
- rollup-ready `gap_details` and `gap_summary` objects in each per-view report;
- best-effort row-state evidence as `visible`, `none`, or `unknown`, written to per-target row-state JSON;
- aggregate rollup counts for filter gaps, sort gaps, panel extraction gaps, and row-state categories.

The upgrade remains read-only. It does not add create, repair, rename, delete, or mutation paths. The WBS09 script remains a thin parameterized consumer of the shared panel readback module.


## 2026-05-14 structured-gap and operator-prompt hardening

The readback tool remains read-only and now emits structured gap details in addition to the existing per-view JSON reports and rollup. The launcher supports a bounded browser launch timeout and an optional `-NoAirtableReadyPause` switch for non-interactive callers. The default operator flow opens Chrome first, then asks for a single Airtable-ready confirmation after login/MFA. Do not pipe the Node process through `Tee-Object`; use `Start-Transcript` or the provided runner so the interactive Airtable-ready prompt has a real stdin.

Rollup fields include `filter_gap_count`, `sort_gap_count`, `panel_extraction_gap_count`, `row_state_counts`, and `gap_results`. The tool does not repair, create, rename, delete, or mutate Airtable views.

## 2026-05-14 v4 structured readback and resume update

Version `2026-05-14.wbs09-panel-readback.4` keeps this tool read-only and adds parameterized recovery behavior for long Airtable verification runs:

- reload retry/backoff for transient Airtable navigation/offline pages;
- `-StartAtTargetKey`, `-AfterTargetKey`, `-TargetListFile`, and `-MaxTargets` for resume or batch targeting;
- selected target plan output in `selected_view_panel_readback_targets.json`;
- rollup fields for `last_completed_target_key` and `first_failed_target_key`.

Use `-TargetListFile` for a newline-delimited or JSON-array list of `Table::View` target keys. Use `-StartAtTargetKey` to include that target and everything after it in the selected set. Use `-AfterTargetKey` to resume after a completed target.

This tool must not create, rename, delete, repair, or mutate Airtable views. If a future repair path is needed, it must be a separate apply tool with a dry-run plan and explicit confirmation token.
