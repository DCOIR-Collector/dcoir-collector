# DCOIR Airtable WBS09 Primitive Coverage Audit

## Purpose
Inventory the WBS09 native view manifest and map required filter/sort/view behaviors to reusable automation primitives.

Use this before building or promoting additional WBS09 create/configure automation. It prevents guessing which primitive should be built next and documents exactly what remains unsupported.

## Status
- Status: read-only planning/audit tool.
- Mutates Airtable: no.
- Uses browser: no.
- Reads secrets: no.
- Input: `wbs09_airtable_native_views_manifest.json`.

## Prerequisites
- `DCOIR_REPO_ROOT` and `DCOIR_DOWNLOADS_DIR` Local Configuration Registry variables.
- Node.js on PATH.
- Current `wbs09_airtable_native_views_manifest.json`.
- Use after `git pull --ff-only origin main` so the local manifest and promoted tool catalog are current.

## What it reports
- filter operator counts;
- filter value kinds;
- filter/action primitive coverage;
- sort primitive coverage;
- multi-filter and multi-sort views;
- not-ready primitives;
- recommended next primitives.

## Example
```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09PrimitiveCoverageAudit.ps1'
& $script
```

## Package evidence
```powershell
$latest = Get-ChildItem -LiteralPath $env:DCOIR_DOWNLOADS_DIR -Directory |
  Where-Object Name -like 'dcoir_wbs09_primitive_coverage_audit_*' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$zipPath = Join-Path $env:DCOIR_DOWNLOADS_DIR ($latest.Name + '_chatgpt.zip')

& (Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirChatGPTFriendlyZip.ps1') `
  -SourceFolder $latest.FullName `
  -OutputZip $zipPath

Set-Clipboard -Value $zipPath
Write-Host "UPLOAD_ZIP_PATH=$zipPath"
```

## How to use the result
Build exactly one not-ready primitive at a time. Each new action primitive must have:

1. discovery evidence;
2. a deterministic plan;
3. exact confirmation token;
4. narrow execution boundary;
5. after-click readback;
6. refresh/reselect readback;
7. packaged evidence;
8. docs and Operator Tools Registry entry.
