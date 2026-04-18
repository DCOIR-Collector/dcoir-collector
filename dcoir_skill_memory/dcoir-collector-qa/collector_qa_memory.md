---
artifact_type: dcoir-collector-qa-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-18T20:20:00Z
authority_basis:
  - Project Instructions v18
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Collector QA Memory

## Current focus
Issue #42 and issue #41 are both complete after live local Collect-run validation. The remaining explicitly open collector lane from the current branch is issue #37, which remains evidence-blocked until same-host/build narrowed-subset proof exists.

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
- **Netstat baseline partial on local T1 run** (status: open)
  - details: Local T1 validation runs still showed `NETWORK_NETSTAT` exiting with code 1 for `netstat -abno`.
  - next_action: Investigate whether this is expected privilege/environment behavior, a timing issue, or a collector-side soft-failure lane that should be normalized in reporting.
- **Condensed Security summary empty-window partial on local T1 run** (status: open)
  - details: Local T1 validation runs still showed `Failed to collect condensed Security summary: No events were found that match the specified selection criteria.`
  - next_action: Decide whether the collector should treat an empty filtered window as a note-only condition rather than a partial-success error for this summary surface.

## Active repair candidates
- **Collector targeted collection narrowed-subset proof (#37)** (status: evidence-blocked)
  - details: Current source narrows guidance, scope intent, artifact prioritization, and next actions, but same-host/build evidence is still required before claiming a truly narrowed subset implementation.
  - next_action: Do not close or overstate until same-host/build comparison evidence exists.
- **Collector file-level comment-based help** (status: open)
  - details: The readable source begins directly with param() and still appears to lack file-level comment-based help.
  - next_action: Consider a bounded maintenance-doc pass before the next maintenance-heavy patch cycle.
- **Endpoint-lane workflow note preservation** (status: open)
  - details: The endpoint lane now has two durable operator rules: absolute get-file paths for harness outputs and transient-root-zip handling.
  - next_action: Keep those rules synchronized in governed workflow docs and later skill guidance.
- **Validate-on-run automation concept** (status: candidate)
  - details: The operator asked whether the local/manual proof steps for overview validation and bounded parallel-runtime validation could be codified into action/workflow helpers such as `validate-on-run` and broader `manual-full-validation` lanes.
  - next_action: Stage this as a bounded future harness/workflow enhancement after current runtime and reporting lanes are stable.

## Recently validated paths
- GitHub-primary collector QA source re-anchor completed against CP-01, CP-02, collector source, harness mirrors, rollback reference, and layout spec.
- Runtime alias alignment is currently correct: manifest/layout/harness all point to DCOIR_Collector.ps1 as the runtime filename.
- Harness suite surface is currently correct: Core, Retrieval, QuickAliases, and FullRegression remain present.
- Collector all-path execution is evidenced through Elastic Defend response actions across QuickAliases, Core, and Retrieval.
- Retrieval of harness summary files is validated when full absolute response-actions paths are used.
- The rollback reference remains available for bounded regression comparison.
- Issue #42 is runtime-proven on a real local Collect run: ANALYST_OVERVIEW_PATH emitted on stdout, overview file existed, manifest contained analyst_overview and overview path, collect bundle contained the overview file, and Gemini guidance preferred the smaller analyst-first surface before the full baseline report.
- Issue #41 bounded parallel-runtime slice is runtime-proven on a real local Collect run after the absolute-OutRoot fix: PARALLEL_EXECUTION_PROOF_PATH emitted on stdout, proof_status was OVERLAP_CONFIRMED, worker_count was 4, and per-worker proof artifacts existed under final_artifacts\parallel_workers.

## Next actions
- Preserve issue #37 as evidence-blocked until same-host/build narrowed-subset evidence exists.
- Decide whether the collector-master-wave should now pause as evidence-blocked or hand off to the next queued branch.
- Hold the bounded endpoint rerun for the harness reporting patch until the operator has sent himself the needed files.
- Keep the exact rerun target unchanged for later: QuickAliases Strings and Streams plus one Core control lane.
- Add concrete replay details when the Gemini collector failure excerpt is recovered.

## Provenance notes
- Updated after issue #42 was validated on a live local Collect run and closed as completed.
- Updated after issue #41 was validated on a live local Collect rerun after the absolute-OutRoot fix and is ready to close as completed.
- Airtable Validation Test Cases row `COL-OVERVIEW-001` is Passed.
- Airtable Validation Test Cases row `COL-PAR-001` is Passed.
