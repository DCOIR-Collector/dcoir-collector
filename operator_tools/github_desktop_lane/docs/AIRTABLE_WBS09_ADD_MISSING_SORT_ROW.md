# DCOIR Airtable WBS09 Add Missing Sort Row Tool

Purpose: operation-class-specific Playwright tool for WBS09 Airtable grid views where the Sort panel opens to Airtable's field-picker state, indicating that a saved sort row is missing and the governed manifest expects exactly one sort row.

This tool is intentionally narrow.

Allowed operation:
- add one missing sort row for one or more explicit manifest targets;
- select the governed field from the Airtable Sort panel field picker;
- set the governed direction when Airtable exposes a direction control;
- verify the panel after mutation and again after reload.

Disallowed operations:
- filter creation or repair;
- changing field on an existing sort row;
- replacing multiple sort rows;
- creating, renaming, deleting, or copying views;
- using Airtable's `Copy from a view` control;
- broad view-repair Apply.

Safety posture:
- DryRun is read-only with transient UI search typing only; it does not select a field or save a sort.
- Apply requires `APPLY_WBS09_ADD_MISSING_SORT_ROW_BATCH` both as a command parameter and as an interactive typed token after Airtable login.
- Apply runs preflight on each target and skips unsupported targets.
- The tool avoids the Sort panel `Copy from a view` control by filtering coordinates/text and by using the `Find a field` search input plus exact field-option matching.
- After any Apply, run WBS09 panel readback on the affected target list.

Known origin:
- Created after the failed v1 repair-batch Apply and the sort-direction v2 dry-run showed 9/9 targets in `dry_run_unsupported_no_direction_control` state.
- Operator observed that a prior tool path clicked the `Copy from a view` area instead of selecting a sort field. This tool explicitly excludes that control.


## 2026-05-15 v2 panel-bounds fix

Dry-run evidence showed the Airtable Sort field picker opens in the right-side toolbar panel near the `Copy from a view` header control. Version `2026-05-15.wbs09-add-missing-sort-row.2-panel-bounds` updates the probe bounds to use the visible right-side sort panel, explicitly avoids `Copy from a view`, and continues to keep DryRun mutation-free.

Validation rule: Apply must remain blocked until a v2 DryRun shows supported targets and a single-target smoke Apply is explicitly approved and verified by readback.


## 2026-05-16 v2.1 sort-only verification fix

The single-target smoke Apply for `Work Items / WBS09 - Blocked or Review` added the missing sort row and post-Apply panel readback verified the expected state after reload. The v2 Apply runner still returned `apply_gap_after_click` because it reused full view comparison and treated unrelated filter-panel extraction as a sort-repair failure.

Version `2026-05-16.wbs09-add-missing-sort-row.2.1-sort-only-verify` changes the add-missing-sort-row operation class to verify only the expected sort row for this tool. Filter state is not modified by this operation class and is now out of scope for the mutation success gate. Independent v4 panel readback remains the required post-Apply verification before widening beyond a smoke target.
