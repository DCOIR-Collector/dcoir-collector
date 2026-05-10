# DCOIR Airtable WBS09 Sort Direction Apply

## Purpose
Safely change one existing Airtable native view sort direction after read-only discovery proves the required control and target direction option exist.

This is intentionally narrow. It does not create views, add sort rows, remove sort rows, change sort fields, edit filters, type values, or run broad rollout.


## Current status
- Status: active guarded single-mutation helper for existing sort-direction changes only.
- Validated: first live guarded run changed Governance Control Plane / WBS09 - Startup Authority from A -> Z to Z -> A and independent panel readback verified all four representative views passed after refresh/reselect.
- Boundary: this is not a general view repair/configure tool and must not be used for filters, added sort rows, view creation, or broad rollout.

## Required order
1. Run `Invoke-DcoirAirtableWbs09ViewDiscovery.ps1` with `-ProbeDropdownOptions` on the exact target view.
2. Confirm discovery reports:
   - `requires_mutation: true`
   - `sort_action: change_sort_direction`
   - a dropdown probe for the existing direction control
   - a visible target option such as `Z -> A` / `descending`
3. Run this apply helper for exactly one `-TargetKey` with exact token `APPLY_WBS09_SORT_DIRECTION`.
4. Package the generated output folder with `New-DcoirChatGPTFriendlyZip.ps1`.
5. Run `Invoke-DcoirAirtableWbs09ViewPanelReadback.ps1` after execution to independently verify saved panel state after refresh/reselect.

## Prerequisites
- `DCOIR_REPO_ROOT` and `DCOIR_DOWNLOADS_DIR` Local Configuration Registry variables.
- Node.js and Playwright prerequisites installed by `Install-DcoirAirtableWbs09UiViewPrereqs.ps1`.
- A logged-in Chrome profile or CDP-attached Chrome session.
- `wbs09_airtable_native_views_manifest.json`.
- Promoted shared modules:
  - `dcoir_airtable_ui_geometry.mjs`
  - `dcoir_airtable_panel_readback.mjs`
  - `dcoir_airtable_panel_discovery.mjs`

## Safety contract
- One target view only.
- Exact confirmation token required twice: once as a PowerShell parameter and once interactively before mutation.
- The script recomputes current readback and discovery before clicking.
- The script stops if the plan is not exactly `change_sort_direction`.
- The script stops if the target direction option is not visible in pre-execute discovery.
- The script verifies after click and after reload/reselect.

## Example
```powershell
.\operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09ApplySortDirection.ps1 `
  -TargetKey "Governance Control Plane::WBS09 - Startup Authority" `
  -ConfirmToken APPLY_WBS09_SORT_DIRECTION `
  -EnableScreenshots `
  -UseChromeChannel `
  -UserDataDir "$env:LOCALAPPDATA\DCOIR\chrome-profile" `
  -KeepBrowserOpenOnFailure
```

## Output
Writes `dcoir_wbs09_apply_sort_direction_*` under `DCOIR_DOWNLOADS_DIR`, including logs, screenshots when enabled, before/after readbacks, pre-execute discovery, and a rollup JSON.
