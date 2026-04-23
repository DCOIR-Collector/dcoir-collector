---
artifact_type: dcoir-collector-qa-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-23T15:40:00Z
authority_basis:
  - Project Instructions v18
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Collector QA Memory

## Current focus
The primary Tier 2 deep-check repair lane is now complete and validated. The next collector branch should move to the remaining secondary follow-on work rather than revisiting the repaired WMI/registry defect cluster. Issue #37 still remains evidence-blocked until same-host/build narrowed-subset proof exists.

## Known failure lanes
- **Gemini collector transcript error** (status: open)
  - details: Preserved placeholder regression lane until the exact failing excerpt is recovered.
  - next_action: Capture the exact failing excerpt and turn it into a concrete replay fixture.
- **QuickAliases partial-success flattening in harness summaries** (status: patched-deferred-rerun)
  - details: Endpoint evidence showed 24_EnrichStartStrings and 26_EnrichStartStreams reporting STATUS=PARTIAL_SUCCESS in collector output while summary txt/json flattened both steps to PASS because exit code remained 0.
  - next_action: Do not resume the bounded endpoint rerun until the operator has sent himself the needed files; after that, rerun QuickAliases Strings and Streams plus one Core control lane and confirm summary artifacts now preserve PARTIAL_SUCCESS.
- **Endpoint working-zip restage/access lane** (status: validated-current-build)
  - details: 2026-04-23 live validation re-proved that cleanup can complete while leaving the local script staged, but immediate post-cleanup collect rerun still fails with `Package not found in script directory or OutRoot: DCOIR_Collector.zip`. This is now a proven current-build restage requirement rather than an ambiguous lane.
  - next_action: Keep `assets\DCOIR_Collector.zip` as the explicit restage source for later collect-style reruns and preserve the rule that delete-script is separate from cleanup.
- **Local non-elevated owner-aware netstat limitation** (status: diagnosed)
  - details: Standard local shell runs showed `netstat -abno` failing with `The requested operation requires elevation.` while `netstat -ano` worked, and elevated shell runs showed `netstat -abno` working. This is an execution-context limitation around the `-b` owner-aware view, not a generic network-capture mystery.
  - next_action: Validate the new diagnostic-hardening collector outputs that explicitly record execution context, owner-aware status, and optional PID-only supplemental netstat data.
- **Local non-elevated Security visibility mismatch** (status: diagnosed)
  - details: Non-elevated collector runs produced empty Security artifacts, while elevated shell queries returned recent `4624`/`4672` events for the collector’s ID set. Audit policy also showed `Process Creation = No Auditing`, explaining the absence of `4688` on this host.
  - next_action: Validate the new diagnostic-hardening collector outputs that explicitly record execution context, audit policy, and a non-elevated Security visibility limitation message instead of a vague empty-window claim.

## Active repair candidates
- **Collector targeted collection narrowed-subset proof (#37)** (status: evidence-blocked)
  - details: Current source narrows guidance, scope intent, artifact prioritization, and next actions, but same-host/build evidence is still required before claiming a truly narrowed subset implementation.
  - next_action: Do not close or overstate until same-host/build comparison evidence exists.
- **Collector diagnostic hardening for local context-sensitive partials** (status: source-patched-pending-runtime-validation)
  - details: The maintained source now records execution context, Security audit policy, Security artifact paths, owner-aware netstat status, and optional PID-only netstat supplemental data. A late-loaded diagnostic override part now changes Security empty-window semantics in non-elevated context from vague emptiness to an explicit verification-required message. The collect entrypoint now emits these diagnostic artifact paths and status markers in stdout and manifest metadata.
  - next_action: Run one real local Collect flow from the current main source and validate rows `COL-DIAG-001` and `COL-VALIDATE-001`.
- **Standalone validate-on-run / validate-on-push gates** (status: source-patched-pending-runtime-validation)
  - details: New script `project_sources/validate_DCOIR_Run.ps1` was added to verify execution context, Security audit policy, Security artifacts, netstat owner-aware status, overview presence, optional parallel proof, and bundle inclusion after a run. It supports bounded mode labels for `validate-on-run` and `validate-on-push`.
  - next_action: Execute the script after a local Collect run and confirm expected pass/fail semantics instead of relying on manual blind trust alone.
- **Collector response-action command rendering follow-on** (status: open-secondary)
  - details: 2026-04-23 live validation re-confirmed that the cleanup output still emits `NEXT_QUICK_COMMANDS` examples with the older single-quote script-path pattern for `-File '.\DCOIR_Collector.ps1'` even though the proven response-action-safe pattern for the live lane uses doubled double quotes around the script path.
  - next_action: Revisit `project_sources/collector_parts/DCOIR_Collector.04_Quick_Interface_And_Output.ps1` now that the Tier 2 repair lane is closed.
- **Collector review-first surface tuning** (status: open-secondary)
  - details: T1 deep-review parity on 2026-04-23 showed the analyst follow-up queue and security high-signal summary are useful but still somewhat noisy or over-escalatory, including benign-looking `powershell.exe`, Defender `DlpUserAgent.exe`, and recurring scheduled-task churn.
  - next_action: Revisit this after the next collector branch selection, but keep it behind any higher-priority runtime or operator-guidance fixes.
- **Collector file-level comment-based help** (status: open)
  - details: The readable source begins directly with `param()` and still appears to lack file-level comment-based help.
  - next_action: Consider a bounded maintenance-doc pass before the next maintenance-heavy patch cycle.
- **Endpoint-lane workflow note preservation** (status: open)
  - details: The endpoint lane now has two durable operator rules: absolute get-file paths for harness outputs and transient-root-zip handling.
  - next_action: Keep those rules synchronized in governed workflow docs and later skill guidance.

## Recently validated paths
- GitHub-primary collector QA source re-anchor completed against CP-01, CP-02, collector source, harness mirrors, rollback reference, and layout spec.
- Runtime alias alignment is currently correct: manifest/layout/harness all point to DCOIR_Collector.ps1 as the runtime filename.
- Harness suite surface is currently correct: Core, Retrieval, QuickAliases, and FullRegression remain present.
- Collector all-path execution is evidenced through Elastic Defend response actions across QuickAliases, Core, and Retrieval.
- Retrieval of harness summary files is validated when full absolute response-actions paths are used.
- The rollback reference remains available for bounded regression comparison.
- Issue #42 is runtime-proven on a real local Collect run: ANALYST_OVERVIEW_PATH emitted on stdout, overview file existed, manifest contained analyst_overview and overview path, collect bundle contained the overview file, and Gemini guidance preferred the smaller analyst-first surface before the full baseline report.
- Issue #41 bounded parallel-runtime slice is runtime-proven on a real local Collect run after the absolute-OutRoot fix: PARALLEL_EXECUTION_PROOF_PATH emitted on stdout, proof_status was OVERLAP_CONFIRMED, worker_count was 4, and per-worker proof artifacts existed under final_artifacts\parallel_workers.
- 2026-04-23 collector validation wave reached bounded closeout for T1/T2 plus the currently retrieved enrich bundles. Airtable validation rows now preserve bundle-inventory coverage, T1 deep-review parity, cleanup/rerun-restage proof, and the still-partial chunking/parallelism coverage rows.
- Cleanup and immediate post-cleanup rerun behavior are now explicitly proven on the current build: cleanup completes, delete-script remains separate, and collect-style reruns still require explicit ZIP re-staging.
- The Tier 2 deep-check repair lane from issue #50 is now complete and validated. The repaired logic was folded back into `project_sources/collector_parts/DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1`, the temporary `04F` override path was removed, the compiled-runtime shim was removed, and the affected validation/build workflows passed after the consolidation.
- Passing post-consolidation validation set: `collector-documentation-quality`, `validate-on-push`, `manual-collector-runtime-package-build`, `manual-full-validation`, and `scheduled-health-check`.

## Next actions
- Choose the next collector branch from the remaining secondary follow-on lanes instead of reopening the closed Tier 2 repair work.
- Revisit response-action command rendering in `project_sources/collector_parts/DCOIR_Collector.04_Quick_Interface_And_Output.ps1`.
- Keep issue #37 evidence-blocked until same-host/build narrowed-subset evidence exists.
- Run the pending runtime validation for `COL-DIAG-001` and `COL-VALIDATE-001` on the current main source.
- Add concrete replay details when the Gemini collector failure excerpt is recovered.

## Provenance notes
- Updated after issue #42 was validated on a live local Collect run and closed as completed.
- Updated after issue #41 was validated on a live local Collect rerun after the absolute-OutRoot fix and closed as completed.
- Updated after evidence-first investigation showed that the remaining local partial-success lanes were rooted in execution context and audit-policy visibility rather than simple collector-summary bugs.
- Updated after the 2026-04-23 collector validation closeout established the Tier 2 repair lane in issue #50 and promoted the recent Airtable test-catalog evidence into durable GitHub helper memory.
- Updated after issue #50 was completed and the post-consolidation validation set passed.
- Airtable Validation Test Cases row `COL-OVERVIEW-001` is Passed.
- Airtable Validation Test Cases row `COL-PAR-001` is Passed.
- Airtable Validation Test Cases row `COL-DIAG-001` and `COL-VALIDATE-001` remain pending runtime validation.
- Airtable Validation Test Cases rows `COL-INVENTORY-001`, `COL-T1-REVIEW-001`, and `VTC-013` are now Passed.
- Airtable Validation Test Cases rows `COL-CHUNK-001`, `COL-PAR-COVERAGE-001`, and `VTC-011` remain active follow-on surfaces.
