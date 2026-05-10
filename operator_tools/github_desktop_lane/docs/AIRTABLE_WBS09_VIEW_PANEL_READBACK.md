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
