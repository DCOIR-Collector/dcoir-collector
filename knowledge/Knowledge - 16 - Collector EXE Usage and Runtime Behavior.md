# Knowledge - 16 - Collector EXE Usage and Runtime Behavior

_How to use the optional EXE collector, what differs from PS1 execution, and how to interpret EXE validation behavior_

**Summary:** Operator guidance for the optional DCOIR Collector EXE lane, including when to use it, how it relates to the PS1 runtime, how GitHub Actions builds and validates it, and which runtime differences are expected rather than regressions.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/collector/source/DCOIR_Collector.ps1; project_sources/collector/harness/run_DCOIR_Tests.ps1; project_sources/collector/tools/build_dcoir_collector_optional_exe_variant.py; project_sources/collector/tools/restore_dcoir_collector_runtime_zip.py; .github/workflows/manual-collector-optional-exe-build.yml; project_sources/collector/docs/DOC-12_DCOIR_Collector_Runtime_Packaging_Pipeline_v1_0_0.txt |
| Operational validation | Optional EXE paired validation branch completed on 2026-04-30 across Core, MajorVersion, Retrieval, QuickAliases, SessionBehavior, TargetedCollection, ChunkingOversizeArtifact, ChunkingReconstructionMetadata, FailureGates, and FullRegression by operator-confirmed GitHub Actions results. |
| Scope note | This page documents the optional EXE lane. The PS1 transport-safe package remains the primary source model unless an explicit promotion decision changes that contract. |

## What the optional EXE is

The optional EXE is a packaged runtime form of the same maintained DCOIR collector line. It is built from the compiled collector runtime and embeds the curated support-tool payload staged from `supporting_assets/DCOIR_Collector.zip` during the GitHub Actions build lane.

Use the EXE when the operator needs a single executable runtime artifact instead of a PowerShell script plus adjacent support-tool staging. Do not treat the EXE as a separate product line. It is another execution form for the governed collector source.

## What the EXE is not

The EXE is not the editing surface. Source changes still belong in the maintained PowerShell collector source and harness files under `project_sources/collector/`.

The EXE is not proof by itself. A successful EXE build proves packaging completed. Runtime behavior is proven by the selected harness suite and validation evidence.

The EXE is not expected to expose every native PowerShell parameter-binding failure exactly the same way as direct PS1 execution. That difference is expected and must be handled by EXE-aware validation.

## Current build lane

Use GitHub Actions workflow:

`manual-collector-optional-exe-build.yml`

Important inputs:

| Input | Purpose |
| --- | --- |
| `package_version_override` | Optional version override forwarded to the package builder. Leave blank for normal validation unless a specific version proof is required. |
| `exe_validation_suite` | Harness suite to run against the produced EXE. Supported values include Core, Retrieval, QuickAliases, SessionBehavior, TargetedCollection, ChunkingOversizeArtifact, ChunkingReconstructionMetadata, MajorVersion, FailureGates, and FullRegression. |
| `skip_ps2exe_install` | Advanced option. Leave false unless deliberately testing an environment where PS2EXE must already be available. |

Normal operator flow:

1. Open GitHub Actions.
2. Open `manual-collector-optional-exe-build`.
3. Choose the intended `exe_validation_suite`.
4. Run the workflow from `main`.
5. Inspect the workflow result and, when needed, the uploaded optional EXE artifact.

## Recommended suite order

For a fresh validation branch, use paired PS1 and EXE validation when possible:

1. Core
2. MajorVersion
3. Retrieval
4. QuickAliases
5. SessionBehavior
6. TargetedCollection
7. ChunkingOversizeArtifact
8. ChunkingReconstructionMetadata
9. FailureGates
10. FullRegression

Run one mode at a time. GitHub Actions may cancel earlier runs when same-workflow runs overlap, so do not dispatch multiple EXE suites in parallel unless the workflow concurrency model has explicitly changed.

## How to run the EXE locally

The EXE accepts the same collector parameter model as the script runtime. The most important parameters are:

| Parameter | Purpose |
| --- | --- |
| `-Mode Collect` | Baseline or targeted collection. |
| `-Mode Enrich` | Enrichment actions against an existing or new enrich session. |
| `-Mode Cleanup` | Cleanup lane when supported by the current runtime. |
| `-Tier T1` / `-Tier T2` | Collection depth. |
| `-Hours` | Lookback window when an explicit event window is not used. |
| `-OutRoot` | Output root. Default is `C:\Temp`. |
| `-PackageName` | Collector package name. Default is `DCOIR_Collector.zip`. |
| `-RunId` | Optional explicit run id. |
| `-Quick` | Quick alias input. |
| `-Targeted` | Enables targeted collection posture. |
| `-TargetProfile` | Targeted collection profile such as Generic, PopupWindow, ScriptExecution, PersistenceFollowUp, NetworkOnly, or ProcessAndPowerShell. |
| `-WindowStart` / `-WindowEnd` | Explicit event window overrides. |
| `-ShowHelp` | Print help. |
| `-ShowVersion` | Print version/build information. |

Example local collect:

```powershell
.\DCOIR_Collector.exe -Mode Collect -Tier T1 -Hours 24 -OutRoot C:\Temp
```

Example targeted collection:

```powershell
.\DCOIR_Collector.exe -Mode Collect -Targeted -TargetProfile PopupWindow -WindowStart "2026-04-30T08:00:00" -WindowEnd "2026-04-30T09:00:00" -OutRoot C:\Temp
```

Example help/version:

```powershell
.\DCOIR_Collector.exe -ShowHelp
.\DCOIR_Collector.exe -ShowVersion
```

## EXE versus PS1 behavior differences

### Runtime self-location

The collector resolves its runtime path differently in script mode and EXE mode. Script mode prefers PowerShell script metadata such as `PSCommandPath`. EXE mode may fall back to the current process executable path.

This is expected. Do not treat EXE path resolution as a regression merely because it does not look like script-mode resolution.

### Parameter binding and FailureGates

Direct PS1 execution can expose native PowerShell parameter-binding diagnostics. The packaged EXE may not faithfully expose those same diagnostics. In EXE mode, bind-reject probes are wrapper-limited and must be evaluated with EXE-aware logic.

Correct validation posture:

- PS1 mode remains strict about native bind-reject behavior.
- EXE mode treats wrapper-limited bind-reject probes as expected when the EXE runtime cannot surface the same PowerShell-native diagnostics.
- FullRegression may include FailureGates, so EXE-aware FailureGates behavior matters for FullRegression too.

### Output contract should remain stable

The runtime form may differ, but the operator-facing output contract should remain stable for successful runs. Gemini and human operators should continue to look for the same high-level markers such as `STATUS`, `RUN_ID`, bundle paths, retrieval guidance, and cleanup guidance.

## How Gemini should use this doc

Gemini should use this page when the operator asks about EXE creation, EXE usage, EXE validation, or EXE-specific failures.

Gemini should not imply that an EXE failure is automatically a collector logic failure. First distinguish:

1. workflow/build failure,
2. packaging failure,
3. harness execution failure,
4. EXE wrapper limitation,
5. real collector runtime behavior regression.

Gemini should preserve the difference between PS1 and EXE behavior rather than flattening both into one generic collector runtime.

## Maintenance rules

When EXE behavior changes, update all affected surfaces together:

- this Knowledge page,
- `Knowledge - 03 - Local Test and Regression`, if suite usage or harness behavior changes,
- `Knowledge - 08 - Troubleshooting`, if failure interpretation changes,
- `Knowledge - 09 - FAQ`, if the common operator answer changes,
- `Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance`, if the attachment set or validation rhythm changes,
- `project_sources/gemini/bundle_source/00_START_HERE/Agent_Attachment_Map.md.txt`,
- `project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json`,
- any GitHub Actions workflow that hard-codes required knowledge surfaces or suite behavior.

## Validation expectations

After EXE-facing documentation changes, validate at least:

- maintained `knowledge/*.md` source exists,
- synced `.md.txt` attachment exists under Gemini prime-agent attachments,
- Gemini manifest includes the attachment,
- attachment map explains the attachment purpose,
- Gemini bundle build syncs and validates successfully,
- optional EXE workflow still runs the relevant suite,
- FailureGates and FullRegression remain EXE-aware.

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
