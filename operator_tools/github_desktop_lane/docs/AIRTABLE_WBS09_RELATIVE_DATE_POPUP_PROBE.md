# Airtable WBS09 Relative Date Popup Probe

Read-only diagnostic for Airtable native filter relative-date dropdowns. It captures a scoped popup DOM/HTML/geometry snapshot instead of full-page HTML, so the action module can be hardened without guessing.

Outputs are written under `DCOIR_DOWNLOADS_DIR` and include popup candidate outerHTML, scroll metrics, option lines, screenshots, and a read-only mouse-wheel probe.

## When to use

Use this probe when a relative-date dropdown cannot be selected reliably by the shared panel action module. It should capture scoped popup evidence only; do not capture full-page HTML unless explicitly required for a new failure mode.

## Outcome from WBS09 validation-due repair

The probe showed Airtable exposes relative-date values as menu items but that some synthetic/DOM click paths do not reliably select the intended value. The promoted shared-module fix uses native Playwright mouse clicks on matched option nodes and mouse-wheel movement over the open dropdown before falling back to composite popup geometry.

This probe remains a diagnostic tool, not a production apply tool.

