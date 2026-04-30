# GitHub write workflow

Use this workflow only when the plan-tracker task requires governed repo source/readback, package generation, promoted-history comparison, or a GitHub Desktop update bundle.

1. Re-anchor to Project Instructions, CP-00 as pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`.
2. Confirm the active branch in Airtable Queue Control, Work Items, Plans, and Session Checkpoints.
3. Read GitHub source files only for the specific repo-source role in scope.
4. Build a GitHub Desktop manual repo-update bundle containing only affected repo-relative files, with no wrapper root and no `.git` directory.
5. Surface the suggested commit summary in the response, not as an extra bundled file unless the operator asks.
6. After operator install/commit/push, verify GitHub readback when repo readback is part of the task.

Do not fetch GitHub CP-01/CP-02 during normal startup or queue recovery just because this reference exists.
