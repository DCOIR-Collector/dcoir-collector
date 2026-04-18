---
artifact_type: dcoir-collector-qa-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-18T15:35:00Z
authority_basis:
  - Project Instructions v18
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Collector QA Memory

## Current focus
Issue #42 is complete and closed after live local Collect-run validation. The active collector QA focus is now issue #41 actual parallel runtime execution. A bounded source slice is now promoted to `main`, and Airtable validation row `COL-PAR-001` is the explicit runtime-proof surface. Issue #37 remains explicitly evidence-blocked until same-host/build narrowed-subset proof exists.

## Known failure lanes
- **Gemini collector transcript error** (status: open)
  - details: Preserved placeholder regression lane until the exact failing excerpt is recovered.
  - next_action: Capture the exact failing excerpt and turn it into a concrete replay fixture.
- **QuickAliases partial-success flattening in harness summaries** (status: patched-deferred-rerun)
  - details: Endpoint evidence showed 24_EnrichStartStrings and 26_EnrichStartStreams reporting STATUS=PARTIAL_SUCCESS in collector output while summary txt/json flattened both steps to PASS because exit code remained 0.
  - next_action: Do not resume the bounded endpoint rerun until the operator has sent himself the needed files; after that, rerun QuickAliases Strings and Streams plus one Core control lane and confirm summary artifacts now preserve PARTIAL_SUCCESS.
- **Endpoint working-zip restage/access lane** (status: open)
  - details: A prior Core attempt failed around the transient root working zip response_actions\DCOIR_Collector.zip; current interpretation is a restage/access issue around a transient root copy, not yet a bounded collector-code defect.
  - next_action: Keep assets\DCOIR_Collector.zip as the master restage source and only escalate this lane if a narrower code-backed failure is reproduced.

## Active repair candidates
- **Collector actual parallel runtime execution (#41)** (status: source-patched-pending-runtime-validation)
  - details: Added bounded PowerShell 5.1-safe parallel runtime support through new collector part `DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1`, wired it into the wrapper and runtime manifest, updated the parallelism posture text, and wired `PARALLEL_EXECUTION_PROOF_PATH` into the collect entrypoint manifest, bundle, and stdout surfaces.
  - next_action: Run one real Collect flow from the promoted source line and verify `PARALLEL_EXECUTION_PROOF_PATH`, worker proof files, observed timing overlap, parent wait behavior, and deterministic final outputs before claiming issue #41 complete.
- **Collector targeted collection narrowed-subset proof (#37)** (status: evidence-blocked)
  - details: Current source narrows guidance, scope intent, artifact prioritization, and next actions, but same-host/build evidence is still required before claiming a truly narrowed subset implementation.
  - next_action: Do not close or overstate until same-host/build comparison evidence exists.
- **Collector file-level comment-based help** (status: open)
  - details: The readable source begins directly with param() and still appears to lack file-level comment-based help.
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
- Issue #42 is now runtime-proven on a real local Collect run: ANALYST_OVERVIEW_PATH emitted on stdout, overview file existed, manifest contained analyst_overview and overview path, collect bundle contained the overview file, and Gemini guidance preferred the smaller analyst-first surface before the full baseline report.
- Issue #41 bounded source slice is now present in `main` and reads back correctly for the new collector part, wrapper wiring, runtime manifest wiring, updated parallelism posture text, and collect entrypoint proof-path markers.

## Next actions
- Run one real local/manual Collect flow for the bounded issue #41 slice and evaluate `COL-PAR-001`.
- Preserve issue #37 as evidence-blocked until same-host/build narrowed-subset evidence exists.
- Hold the bounded endpoint rerun for the harness reporting patch until the operator has sent himself the needed files.
- Keep the exact rerun target unchanged for later: QuickAliases Strings and Streams plus one Core control lane.
- Add concrete replay details when the Gemini collector failure excerpt is recovered.

## Provenance notes
- Updated after issue #42 was validated on a live local Collect run and closed as completed.
- Airtable Validation Test Cases row `COL-OVERVIEW-001` is now Passed.
- Airtable Validation Test Cases row `COL-PAR-001` is now Partial after the bounded issue #41 source slice landed in `main` but before runtime proof was supplied.
