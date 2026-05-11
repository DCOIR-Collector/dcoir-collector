# DCOIR Airtable WBS09 Capability Map

## Purpose

`Invoke-DcoirAirtableWbs09CapabilityMap.ps1` builds a capability map for the WBS09 Airtable native-view automation lane.

The tool combines:

1. `wbs09_airtable_native_views_manifest.json` for intended WBS09 view filters and sorts.
2. Airtable metadata/schema API, or a provided schema JSON, for table IDs, field IDs, field types, select choices, and view names.
3. Optional same-run browser UI discovery for native Airtable Filter/Sort panel evidence that the metadata API does not expose.
4. Existing browser evidence folders under a provided evidence root when explicitly requested.

It does not replace browser panel readback. Airtable schema/API cannot prove saved native Filter/Sort panel configuration. The map is a pre-execute capability layer that tells future tools what is schema-supported, what has UI evidence, and which apply primitives are safe or still need hardening.

## Safety contract

- Default mode is read-only schema/evidence mapping.
- No Airtable record mutations.
- No Airtable view mutations.
- No typing, selecting, adding, removing, or saving when optional UI evidence collection is enabled.
- Uses Playwright only when `-CollectUiEvidence` is supplied.
- Does not print or store secret values.
- Uses `DCOIR_AIRTABLE_TOKEN` only as a bearer token for Airtable metadata API when live schema collection is enabled.
- Writes generated output under `DCOIR_DOWNLOADS_DIR` only.
- Does not use hidden temp folders for generated DCOIR artifacts.
- Writes a generated repo-side map at `operator_tools/github_desktop_lane/manifests/wbs09_airtable_capability_map.generated.json` so follow-on tools can consume the same map after inspection.

## Required configuration

From Local Configuration Registry / machine environment:

- `DCOIR_REPO_ROOT`
- `DCOIR_DOWNLOADS_DIR`
- `DCOIR_AIRTABLE_BASE_ID`
- `DCOIR_AIRTABLE_TOKEN` when live schema collection is used

The token value must never be printed, logged, packaged, or stored in Airtable.

## Launcher

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09CapabilityMap.ps1'
& $script
```

Recommended one-shot schema plus UI-evidence run:

```powershell
cd C:\GitHub\dcoir-collector
$ErrorActionPreference = 'Stop'

.\operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09CapabilityMap.ps1 `
  -RequireLiveSchema `
  -CollectUiEvidence `
  -DefaultUiEvidenceTargets `
  -EnableScreenshots `
  -UseChromeChannel `
  -UserDataDir "$env:LOCALAPPDATA\DCOIR\chrome-profile" `
  -ProbeDropdownOptions `
  -MaxDropdownProbes 12 `
  -KeepBrowserOpenOnFailure

$latest = Get-ChildItem -LiteralPath $env:DCOIR_DOWNLOADS_DIR -Directory |
  Where-Object Name -like 'dcoir_wbs09_capability_map_*' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$zipPath = Join-Path $env:DCOIR_DOWNLOADS_DIR ($latest.Name + '_chatgpt.zip')

.\operator_tools\github_desktop_lane\scripts\New-DcoirChatGPTFriendlyZip.ps1 `
  -SourceFolder $latest.FullName `
  -OutputZip $zipPath

Set-Clipboard -Value $zipPath
Write-Host "UPLOAD_ZIP_PATH=$zipPath"

git status --short --branch
```

## Inputs

Default manifest:

```text
operator_tools/github_desktop_lane/manifests/wbs09_airtable_native_views_manifest.json
```

Optional inputs:

- `-SchemaJson`: use a pre-exported schema JSON instead of, or in addition to, live metadata API.
- `-EvidenceRoot`: root folder to scan for WBS09 discovery/readback/apply evidence.
- `-NoLiveSchema`: skip Airtable metadata API and build a manifest/evidence-only map.
- `-RequireLiveSchema`: fail if live metadata API schema cannot be collected.
- `-CollectUiEvidence`: run targeted view discovery in the same visible output folder before building the map.
- `-DefaultUiEvidenceTargets`: collect the current known good/bad relative-date samples.
- `-UiEvidenceTargetKey`: collect specific WBS09 target keys before mapping.

## Outputs

Under `DCOIR_DOWNLOADS_DIR/dcoir_wbs09_capability_map_*`:

- `wbs09_airtable_capability_map.generated.json`
- `wbs09_airtable_capability_map_summary.md`
- `airtable_schema_live_metadata.json` when live schema was collected
- `capability_map_run_context.json`
- `ui_evidence/` only when same-run UI evidence collection is requested

Repo-side generated map:

```text
operator_tools/github_desktop_lane/manifests/wbs09_airtable_capability_map.generated.json
```

This generated map may be committed only after inspection and validation.

## How to use the map

Apply tools should load the generated map before mutation and require:

1. the expected primitive exists in the map;
2. the primitive is schema-supported;
3. UI evidence exists for required native controls/options when the operation depends on native Airtable UI behavior;
4. the primitive's `apply_supported` state matches the intended operation;
5. known hard stops are absent.

For example, `filter.relative_date.on_or_before_today` should not execute unless the map proves:

- `review_after` exists as a date field in the target table;
- the manifest expects `review_after on or before today`;
- UI evidence has observed the `on or before` operator and `today` relative-date value option in a comparable panel;
- the apply tool's sequence has passed after-click and independent refresh/reselect readback.

## Current design boundary

This is a capability map, not a repair tool. It helps decide what to build or execute next. Browser automation is still required to prove saved native view configuration and to perform native view edits.

## Current validated apply support

As of the 2026-05-11 v15 evidence run, the capability map may mark `filter.relative_date.on_or_before_today` as apply-supported only at guarded single-target scope:

```text
primitive: filter.relative_date.on_or_before_today
apply_supported: true
apply_support_level: guarded_single_target
validated_target: Operator Tools Registry::WBS09 - Validation Due
validated_recovery_case: wrong relative-date value repaired to today after today was not initially visible
```

Evidence basis:

- `dcoir_wbs09_apply_validation_due_view_20260511T033729Z_wrong_value_repair_v15_chatgpt.zip`
- `dcoir_wbs09_view_panel_readback_20260511T033905Z_wrong_value_repair_v15_chatgpt.zip`

This does not authorize broad WBS09 rollout. It authorizes only the validated single-target helper path until more representative views are tested.

