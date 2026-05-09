# WBS09 Airtable UI View Creation Safety Contract

## Allowed in this draft

- Install/check Node and Playwright prerequisites locally.
- Validate the 65-view manifest.
- Open Airtable in a visible browser for calibration.
- Create native Airtable grid views only after explicit confirm token and second interactive confirmation.

## Not allowed in this draft

- Creating fields.
- Updating records.
- Deleting or renaming records, fields, tables, or views.
- Configuring filters/sorts automatically.
- Running headless against Airtable by default.
- Running bulk execution before one-view smoke validation.
- Storing secret values in logs.

## Required local configuration variables

- `DCOIR_REPO_ROOT`: local path to the repo working tree.
- `DCOIR_DOWNLOADS_DIR`: output folder for logs/reports/screenshots.

Both must be Machine/System environment variables according to the Local Configuration Registry. The tool must log names and paths only; never log secret values.

## Auth/profile lane safety addition

When Google blocks sign-in inside Playwright-managed Chromium, do not attempt to bypass or weaken the identity provider. Use an operator-launched, dedicated Chrome profile and connect to it over `http://127.0.0.1:9222` only after the operator has signed in manually.

Safety rules:
- Use a dedicated profile under `DCOIR_DOWNLOADS_DIR`; do not use the normal daily browser profile.
- Keep the debugging endpoint bound to localhost only.
- Close the dedicated Chrome session after the run.
- Calibration remains no-mutation.
- Execution still requires `-ExecuteCreateViewsOnly -ConfirmToken CREATE_WBS09_NATIVE_VIEWS` and should start with `-MaxViews 1`.
