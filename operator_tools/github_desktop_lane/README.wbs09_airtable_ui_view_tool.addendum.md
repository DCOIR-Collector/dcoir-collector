# README Addendum: WBS09 Airtable UI View Creator

This addendum documents the draft WBS09 Airtable UI view-creation tool. Merge into `operator_tools/github_desktop_lane/README.md` after local install/dry-run/calibration and one-view smoke pass.

Launcher:

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09UiViewTool.ps1'
& $script -DryRun
```

Docs: `operator_tools/github_desktop_lane/docs/AIRTABLE_WBS09_UI_VIEW_CREATION.md`.
