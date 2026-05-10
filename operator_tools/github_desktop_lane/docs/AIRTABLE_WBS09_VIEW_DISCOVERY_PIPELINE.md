# Airtable WBS09 Native View Discovery Pipeline

## Purpose

This tool is the first hardening step for WBS09 native Airtable view automation after the 2026-05-10 recovery session.

It exists to prevent brittle direct-click repair behavior. Before future create/configure code mutates an Airtable view, the automation should discover current saved panel state, visible controls, and selectable option surfaces, then build an explicit change plan.

## Current status

- Status: active read-only discovery/planning foundation. v4 validated focused row-level option probing for the Governance sort-direction case; it remains non-mutating and does not make broad create/configure repair ready by itself.
- Mutates Airtable: no.
- Intended next consumer: future create/configure automation following `discover -> plan -> execute -> verify -> package evidence`.
- Promotion boundary: this tool does not make repair/create automation ready by itself.

## What the tool does

- Opens the DCOIR Airtable base in a visible browser.
- Selects target tables/views using the same safe left-sidebar pattern as panel readback.
- Opens actual Filter and Sort panels.
- Captures current panel rows using the promoted readback module.
- Builds a machine-readable change plan by comparing current panel state to the manifest expectation.
- Inventories visible panel controls and likely dropdown triggers.
- Optionally opens dropdown-like controls to capture selectable option text without typing, selecting, adding, removing, or saving.
- Writes discovery reports and evidence under `DCOIR_DOWNLOADS_DIR`.

## What the tool does not do

- It does not create views.
- It does not modify filters or sorts.
- It does not click Add condition/Add sort as part of discovery.
- It does not type values or press Enter into dropdowns.
- It does not claim create/configure readiness.
- It does not replace post-change panel readback verification.


## Tool-use documentation completeness gate

Every promoted operator tool must document enough for a brand-new session to use it without chat-local context. At minimum, the tool documentation, catalog entry, or Operator Tools Registry row must include:

- purpose and current status;
- exact launcher or entrypoint path;
- prerequisites, including required Local Configuration Registry / environment variable names;
- required install/prerequisite scripts, when any;
- safety mode and confirmation tokens;
- expected output folder / file naming under `DCOIR_DOWNLOADS_DIR`;
- evidence packaging command;
- validation/readback requirements;
- known limitations and blocked modes.

For this discovery tool, the prerequisite chain is: existing WBS09 Playwright prerequisites, `DCOIR_REPO_ROOT`, `DCOIR_DOWNLOADS_DIR`, visible logged-in Chrome profile or CDP-attached browser, and `wbs09_airtable_native_views_manifest.json`.

## Data-source strategy

Use the least brittle source for each fact:

1. Airtable schema/API for table IDs, field IDs, field types, select choices, and view names/IDs.
2. Airtable record reads with a `view` parameter only as secondary behavioral evidence of record order/filtering.
3. Browser panel readback as the authoritative source for saved native Filter/Sort panel rows.
4. Browser/CDP focused-control discovery for row-level selectable options before mutation.
5. Browser action only after the plan proves the exact required control/option exists.

## Environment contract

Required Local Configuration Registry names:

- `DCOIR_REPO_ROOT`
- `DCOIR_DOWNLOADS_DIR`

The browser profile path can be passed through `-UserDataDir`; do not store the actual profile path, cookies, local secrets, tokens, or machine-specific values in GitHub, Airtable, logs, or evidence bundles.

## One-target discovery

Start with one target before broad representative discovery:

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09ViewDiscovery.ps1'
& $script `
  -TargetKey 'Governance Control Plane::WBS09 - Startup Authority' `
  -EnableScreenshots `
  -UseChromeChannel `
  -UserDataDir "$env:LOCALAPPDATA\DCOIR\chrome-profile" `
  -ProbeDropdownOptions `
  -MaxDropdownProbes 8 `
  -KeepBrowserOpenOnFailure
```

## Representative discovery

```powershell
& $script `
  -DefaultRepresentativeTargets `
  -EnableScreenshots `
  -UseChromeChannel `
  -UserDataDir "$env:LOCALAPPDATA\DCOIR\chrome-profile" `
  -ProbeDropdownOptions `
  -MaxDropdownProbes 8 `
  -KeepBrowserOpenOnFailure
```

## Package evidence

```powershell
$latest = Get-ChildItem -LiteralPath $env:DCOIR_DOWNLOADS_DIR -Directory |
  Where-Object Name -like 'dcoir_wbs09_view_discovery_*' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$zipPath = Join-Path $env:DCOIR_DOWNLOADS_DIR ($latest.Name + '_chatgpt.zip')

& (Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirChatGPTFriendlyZip.ps1') `
  -SourceFolder $latest.FullName `
  -OutputZip $zipPath

Set-Clipboard -Value $zipPath
Write-Host "UPLOAD_ZIP_PATH=$zipPath"
```

## Future create/configure contract

Future mutation automation must consume discovery output before clicking mutating controls:

1. Discover current saved state and selectable UI surfaces.
2. Build a deterministic change plan.
3. Execute the smallest required edit.
4. Re-open Filter/Sort panels.
5. Verify actual panel rows after refresh/reselect.
6. Package evidence.

If discovery cannot identify the required field/operator/value/sort-direction control, mutation must stop before editing the view.
