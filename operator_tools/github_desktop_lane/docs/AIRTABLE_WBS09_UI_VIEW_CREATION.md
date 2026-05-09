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
