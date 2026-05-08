DCOIR GitHub Desktop Manual Repo Update Bundle

Apply this bundle at the repository root. It contains repo-relative paths only.

Files:
- chatgpt_staging/exec_scripts/wbs22_wave2_bulk_maintenance_update_002.ps1
- chatgpt_staging/exec_requests/exec-20260508-wbs22-wave2-bulk-maintenance-003.json

Purpose:
- Fixes the PowerShell 5 StrictMode scalar .Count failure from bulk-maintenance-002 by avoiding .Count checks on scalar table/field objects.
- Stages a fresh chatgpt-exec request to run one grouped Wave 2 bulk maintenance pass.

Suggested commit message:
Stage strict-safe WBS22 Wave 2 bulk maintenance v003 request
