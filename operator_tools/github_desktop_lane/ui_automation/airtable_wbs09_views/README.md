# DCOIR WBS09 Airtable UI Native View Creation Tool

Status: draft prepared, no execution yet.

This tool exists because Airtable native view creation is not exposed through the current ChatGPT Airtable connector, and existing DCOIR Airtable tools are read-only metadata/export tools or record-create helpers. This package prepares an operator-side Playwright UI lane for creating the WBS09 native grid views through the Airtable browser UI.

## Source and authority

- GitHub path: `operator_tools/github_desktop_lane/` is the code source of truth for reusable operator tools.
- Airtable `Operator Tools Registry` should receive a registry row after this tool is validated locally.
- Local Configuration Registry variable names used by this tool:
  - `DCOIR_REPO_ROOT`
  - `DCOIR_DOWNLOADS_DIR`

## Files

- `scripts/Install-DcoirAirtableWbs09UiViewPrereqs.ps1` installs/checks Node/Playwright prerequisites.
- `scripts/Invoke-DcoirAirtableWbs09UiViewTool.ps1` launches dry-run, calibration, or explicitly confirmed view creation.
- `ui_automation/airtable_wbs09_views/scripts/airtable_wbs09_ui_views.mjs` is the Node/Playwright engine.
- `manifests/wbs09_airtable_native_views_manifest.json` defines 65 views across 21 tables.
- `docs/AIRTABLE_WBS09_UI_VIEW_CREATION.md` is the operator runbook.
- `tool_catalog.wbs09_airtable_ui_view_tool.addendum.json` is a repo-side catalog addendum for review/merge.

## Safety posture

Default mode is dry-run. Live UI view creation requires:

1. `-ExecuteCreateViewsOnly`
2. `-ConfirmToken CREATE_WBS09_NATIVE_VIEWS`
3. a second interactive typed confirmation after the browser opens

The draft does not configure filters/sorts in Airtable. It creates grid views only, then stops loudly if selectors drift.
