# DCOIR Collector Coverage Ledger — 2026-04-27

Purpose: source-informed collector coverage ledger for `PLAN-20260416-collector-master-wave` / `T1.2`.

Authority boundaries:
- Governed source: `project_sources/DCOIR_Collector.ps1`, `project_sources/collector_parts/`, `project_sources/run_DCOIR_Tests.ps1`, `project_sources/generation_validation/`, and `.github/workflows/`.
- Live queue and task status: Airtable Queue Control, Work Items, Plans, Plan Tasks, and Validation Test Cases.
- This ledger is a governed readable snapshot and does not replace Airtable live queue authority.
- Runtime claims are explicitly bounded. Source/readback and workflow build proof are distinguished from endpoint execution proof.

## Summary status

| Area | Coverage status | Current evidence | Follow-up |
| --- | --- | --- | --- |
| Collector wrapper and modular part loading | Covered by package validation and workflow source checks | Runtime package builder/validator, manual full validation, validate-on-push, scheduled health check | Keep in package/workflow gates |
| Core collect path | Covered | `Core` harness suite; workflow runtime-harness lanes | Runtime retest only when collector logic changes |
| Retrieval/finalize path | Covered | `Retrieval` harness suite; workflow runtime-harness lanes | Runtime retest when retrieval behavior changes |
| Quick alias paths | Covered/partially covered depending alias | `QuickAliases`, `FailureGates`, manual-test framework | Keep expanding per-alias assertions as new aliases are added |
| Session creation/reuse/finalize | Covered | `SessionBehavior` harness suite | Endpoint proof optional unless endpoint-only defect appears |
| Targeted collection and explicit windows | Covered for output surface and degradation behavior | `TargetedCollection`, `FailureGates`, targeted-window partial behavior checks | True same-host/subset narrowing remains a deeper data-quality validation lane |
| Chunking oversized artifact | Covered | `ChunkingOversizeArtifact` and `ChunkingReconstructionMetadata` harness suites | Retest when chunking thresholds/metadata change |
| Attachment budget / Gemini upload budget | Covered by harness output-contract checks | Harness parses and verifies attachment-budget manifests | Retest when budget constants or upload guidance changes |
| Failure gates and malformed input | Covered | `FailureGates`; canonical `95_QuickHelp` positive assertion now in source | Keep negative gates aligned with parameter changes |
| Audit-policy privilege boundary | Source/readback covered; runtime local follow-up preserved | `COL-AUDIT-001`; 04E diagnostic override; validator recognizes `PRIVILEGE_REQUIRED_NON_ELEVATED` | Runtime proof on Windows local/non-elevated environment |
| Runtime package build and restore bridge | Covered by workflows | `manual-full-validation`, `validate-on-push`, `scheduled-health-check`, package builder/restore scripts | Monitor when manifest/package shape changes |
| Manual-test framework bundle | Source/readback covered; workflow watch added | `COL-MANUAL-001`; `manual-test-framework-validate.yml` | Runtime run on Windows workstation when available |
| Optional PS2EXE single-upload EXE | Build-artifact covered; endpoint runtime blocked | `COL-EXE-001`; successful artifact list showing EXE and embedded payload manifest | Runtime test in environment that can download/execute EXE |
| Embedded support-tool payload | Build-artifact covered | Builder stages binaries from `supporting_assets/DCOIR_Collector.zip` and emits `embedded_tool_payload_manifest.json` | Inspect manifest/runtime behavior when download allowed |

## Source inventory

### Collector entry surfaces
- Primary wrapper: `project_sources/DCOIR_Collector.ps1`.
- Modular collector parts: `project_sources/collector_parts/`.
- Main entry surface: `DCOIR_Collector.05_Main_Entry.ps1`.
- Quick interface/output surface: `DCOIR_Collector.04_Quick_Interface_And_Output.ps1`.
- Major feature wave surfaces:
  - `04B_Feature_Wave_Targeted_Collection.ps1`
  - `04C_Explicit_Event_Window_Overrides.ps1`
  - `04D_Bounded_Parallel_Runtime.ps1`
  - `04E_Diagnostic_Context_Overrides.ps1`

### Collector behavior families
- Collect baseline path and baseline report output.
- Metadata/report outputs.
- Upload summary and default Gemini upload guidance.
- Collection scope and targeted collection plan outputs.
- Parallelism/multithreading assessment output.
- Attachment budget manifest output.
- Enrich session start/add/finalize paths.
- Retrieval bundle path and collect/enrich bundle outputs.
- Cleanup and delete-script command surfaces.
- Quick alias mapping, quick help, malformed quick input, and missing-target quick gates.
- Explicit window parsing and degraded fallback for invalid window values.
- Audit-policy privilege boundary and non-elevated classification.

### Harness suites
Current `run_DCOIR_Tests.ps1` suite surface:
- `Core`
- `Retrieval`
- `QuickAliases`
- `SessionBehavior`
- `TargetedCollection`
- `ChunkingOversizeArtifact`
- `ChunkingReconstructionMetadata`
- `MajorVersion`
- `FailureGates`
- `FullRegression`

### Workflow validation surfaces
- `.github/workflows/validate-on-push.yml`: path-triggered collector/runtime validation.
- `.github/workflows/manual-full-validation.yml`: manual suite selection and runtime-harness validation.
- `.github/workflows/scheduled-health-check.yml`: recurring/manual collector health validation.
- `.github/workflows/collector-documentation-quality.yml`: documentation/source quality validation.
- `.github/workflows/manual-collector-runtime-package-build.yml`: PS1-first runtime package build.
- `.github/workflows/manual-test-framework-validate.yml`: manual-test framework syntax and bundle validation.
- `.github/workflows/manual-collector-optional-exe-build.yml`: optional embedded-payload EXE build.

### Packaging and artifact surfaces
- `project_sources/Collector_Runtime_Package_Manifest.json.txt`
- `project_sources/generation_validation/build_dcoir_collector_runtime_package.py`
- `project_sources/generation_validation/validate_dcoir_collector_runtime_package.py`
- `project_sources/generation_validation/compile_dcoir_collector_runtime.py`
- `project_sources/generation_validation/restore_dcoir_collector_runtime_zip.py`
- `project_sources/generation_validation/build_dcoir_collector_optional_exe_variant.py`
- `supporting_assets/DCOIR_Collector.zip`

### Manual-test framework surfaces
- `project_sources/generation_validation/manual_test_framework/run_dcoir_manual_tests.ps1`
- `project_sources/generation_validation/manual_test_framework/dcoir_manual_test_runner.py`
- `project_sources/generation_validation/manual_test_framework/dcoir_manual_test_control.json`
- `project_sources/generation_validation/manual_test_framework/DCOIR_manual_test_plan.md`
- `project_sources/generation_validation/manual_test_framework/build_dcoir_manual_test_framework_bundle.py`
- `project_sources/generation_validation/manual_test_framework/install_and_run_from_downloads.ps1`

## Gap map

| Gap ID | Gap | Status | Owner surface | Notes |
| --- | --- | --- | --- | --- |
| GAP-COL-001 | Optional embedded EXE endpoint/runtime execution | Blocked-runtime | `COL-EXE-001` | Build artifact exists; workplace blocks EXE/ZIP download and execution. |
| GAP-COL-002 | Audit-policy non-elevated runtime proof | Planned local/runtime | `COL-AUDIT-001` | Source/readback validated; requires local Windows non-elevated run for runtime proof. |
| GAP-COL-003 | Manual-test framework runtime run | Planned local/runtime | `COL-MANUAL-001` | Source/readback and workflow coverage exist; local Windows run still needed. |
| GAP-COL-004 | True same-host/subset narrowing for targeted collection | Partial/data-quality | Future validation row | Harness proves target/output surface and malformed-window degradation; data-quality narrowing needs a dedicated evidence run. |
| GAP-COL-005 | Embedded support-tool payload manifest inspection | Blocked-runtime/artifact-inspection | `COL-EXE-001` | Artifact list proves manifest exists; operator cannot download artifact from workplace. |

## Current closeout interpretation

The collector master wave now has durable coverage for the known source and packaging surfaces sufficient to drive the next validation work. The remaining gaps are not source-inventory mysteries; they are runtime, artifact-inspection, or deeper data-quality validation lanes. Those should be tracked in Airtable Validation Test Cases instead of keeping `T1.2` open as a vague parent.
