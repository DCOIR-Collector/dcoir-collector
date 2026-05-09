# Airtable WBS09 UI View Creation Runbook

## Purpose

Create the WBS09 Airtable-native grid views from the reviewed manifest without manually clicking all 65 views one at a time.

## What this tool does

- Reads the approved WBS09 manifest.
- Validates exactly 65 views across 21 tables.
- Writes all logs and reports under `DCOIR_DOWNLOADS_DIR`.
- Opens Airtable in a visible Chromium browser only for calibration or live create mode.
- Requires explicit confirmation before any create-click action.

## What this tool does not do

- It does not create fields.
- It does not delete records, fields, tables, or views.
- It does not create workflows or automations.
- It does not configure filters/sorts in draft mode.
- It does not store secrets or environment values in logs.

## Install/check prerequisites

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Install-DcoirAirtableWbs09UiViewPrereqs.ps1'
& $script
```

Expected output: a timestamped folder under `DCOIR_DOWNLOADS_DIR` containing `install.log`, npm output, Playwright install output, and `install_result.json`.

## Dry run

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09UiViewTool.ps1'
& $script -DryRun
```

Expected output: `dry_run_report.json` showing 65 views and 21 tables. No browser opens and no Airtable mutation is attempted.

## Calibration run

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09UiViewTool.ps1'
& $script -CalibrateSelectors -EnableScreenshots
```

Expected output: browser opens, you log in, the tool records page metadata/screenshot, and exits without creating views.

## First live smoke: one view only

Only after install and dry-run are clean:

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09UiViewTool.ps1'
& $script -ExecuteCreateViewsOnly -ConfirmToken CREATE_WBS09_NATIVE_VIEWS -TableName 'Work Items' -MaxViews 1 -EnableScreenshots
```

The tool opens Airtable and asks for a second typed confirmation before attempting the create-click. Verify the created view in Airtable before running more than one view.

## Bulk execution

Bulk execution is intentionally not the first step. Use only after the one-view smoke passes and selectors are verified.

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09UiViewTool.ps1'
& $script -ExecuteCreateViewsOnly -ConfirmToken CREATE_WBS09_NATIVE_VIEWS -EnableScreenshots
```

## Stop conditions

Stop and upload the latest output folder or `.chatgpt.zip` if any of these occur:

- Node.js or npm missing.
- Playwright install fails.
- Browser opens the wrong Airtable base.
- The first create attempt cannot find the table selector, Create new control, Grid option, name input, or final Create button.
- Any view appears duplicated or incorrectly named.
- Any UI prompt asks for permission/scope/visibility choices that are not expected.

## 2026-05-09 auth-profile recovery lane

If calibration opens Chromium but Google refuses sign-in with `This browser or app may not be secure`, stop the run with Ctrl+C and do not continue to execution.

Preferred recovery is to use a real Chrome session that the operator signs into manually, then attach the tool to that existing browser over a local debugging endpoint.

### Start dedicated Chrome profile for Airtable auth

Use a dedicated profile under `DCOIR_DOWNLOADS_DIR` so the automation does not touch the operator's normal browser profile:

```powershell
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
$profile = Join-Path $downloads 'dcoir_airtable_wbs09_chrome_profile'
$chrome = Join-Path ${env:ProgramFiles} 'Google\Chrome\Application\chrome.exe'
if (-not (Test-Path -LiteralPath $chrome -PathType Leaf)) { $chrome = Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe' }
& $chrome --remote-debugging-port=9222 --user-data-dir="$profile" "https://airtable.com/appM4KSwnVf3G3OTK"
```

Sign into Airtable manually in that Chrome window. Keep it open.

### Calibrate through the existing Chrome session

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
& (Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09UiViewTool.ps1') -CalibrateSelectors -EnableScreenshots -ConnectOverCdpUrl 'http://127.0.0.1:9222'
```

This mode uses the operator-approved Chrome session and does not create views during calibration.

### Close the dedicated Chrome session after the run

Close all Chrome windows that were launched with the dedicated WBS09 profile after calibration/execution is complete. Do not leave remote debugging Chrome sessions open longer than needed.

## Draft4 selector patch

The draft4 patch expands the final create-button selector set to include Airtable labels such as `Create new view` and `Create grid view`, and writes a failure screenshot when the final create control is not found.
