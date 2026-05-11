# Airtable WBS09 Validation Due View Apply

## Purpose

`DCOIR Airtable WBS09 Apply Validation Due View` is a narrow, guarded Airtable UI automation helper for one view only:

- Table: `Operator Tools Registry`
- View: `WBS09 - Validation Due`
- Filter to add or verify: `review_after` is on or before `today`
- Sort to add or verify: `review_after` ascending (`Earliest -> Latest`)

The helper exists because read-only discovery showed this view can drift to an incomplete relative-date filter state, while the known-good `Session Checkpoints / WBS09 - Needs Review` view showed the expected relative-date and date-sort control layout. Current evidence shows the sort can already be correct while the filter row remains `review_after is exact date / Enter a date / GMT`.

## Safety contract

This tool is not a general view creator or broad repair tool. It requires the exact confirmation token `APPLY_WBS09_VALIDATION_DUE_VIEW` twice: once as a PowerShell parameter and once interactively after Airtable is open.

It refuses to continue unless all of the following are true:

- The selected manifest target is exactly `Operator Tools Registry::WBS09 - Validation Due`.
- The manifest contract has exactly one filter: `review_after on or before today`.
- The manifest contract has exactly one sort: `review_after asc`.
- Current readback requires one of these narrow states: no-op; add missing first filter/sort row; or normalize one existing `review_after` filter row from exact-date/unset to `on or before today`.
- Existing unexpected filter/sort rows are not present.

It will not create/delete views, delete filter rows, delete sort rows, normalize unrelated filters, normalize multi-filter/multi-sort views, or touch any field other than `review_after`.

## Reusable module boundary

Reusable UI action behavior lives in:

```text
operator_tools/github_desktop_lane/ui_automation/shared/dcoir_airtable_panel_actions.mjs
```

The WBS09 script is a thin guarded harness that supplies the exact target and contract. The shared module is parameterized by field/operator/value so later tools can reuse the same relative-date filter action pattern without copying WBS09-specific logic.

## Launcher

```powershell
.\operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09ApplyValidationDueView.ps1 `
  -ConfirmToken APPLY_WBS09_VALIDATION_DUE_VIEW `
  -EnableScreenshots `
  -UseChromeChannel `
  -UserDataDir "$env:LOCALAPPDATA\DCOIR\chrome-profile" `
  -KeepBrowserOpenOnFailure
```

The launcher writes output under:

```text
$env:DCOIR_DOWNLOADS_DIR\dcoir_wbs09_apply_validation_due_view_*
```

Upload the ChatGPT-friendly ZIP of that output folder after the run.

## Expected success status

The final rollup should report one of:

- `already_correct_noop`
- `validation_due_view_verified_after_refresh`

Any other status should be treated as an evidence gap until the output ZIP is reviewed.

## Validated evidence

The v15 shared-action path was validated on 2026-05-11 against `Operator Tools Registry / WBS09 - Validation Due`.

Evidence:

- Apply evidence ZIP: `dcoir_wbs09_apply_validation_due_view_20260511T033729Z_wrong_value_repair_v15_chatgpt.zip`
- Independent readback ZIP: `dcoir_wbs09_view_panel_readback_20260511T033905Z_wrong_value_repair_v15_chatgpt.zip`
- Apply status: `validation_due_view_verified_after_refresh`
- Readback status: `PASS`
- Shared action module version: `2026-05-10.panel-actions.7`
- Recovery case tested: wrong relative-date value repaired back to `today` after `today` was not initially visible in the dropdown.

## Relative-date dropdown implementation note

The working shared action does not click a fixed coordinate. It finds the current visible option node whose text matches the requested value, reads the live bounding box, and uses a native Playwright mouse click on that matched option. When the option is not initially visible, it identifies the open dropdown and uses mouse-wheel movement over that dropdown before retrying real option-node selection. Composite popup text coordinate selection is treated as a last-resort fallback only because it can select the wrong visible row when the scroll position differs.

Do not broaden this helper to batch rollout until additional relative-date views have been tested with the same after-click and independent refresh/reselect readback gates.

