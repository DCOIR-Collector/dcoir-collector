---
artifact_type: dcoir-collector-qa-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-18T21:22:00Z
authority_basis:
  - Project Instructions v18
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Collector QA Memory

## Current focus
Issue #42 and issue #41 are both complete after live local Collect-run validation. The current collector branch is temporarily focused on diagnostic hardening and trust-repair for the remaining local partial-success lanes rather than on closing a named issue. Issue #37 still remains evidence-blocked until same-host/build narrowed-subset proof exists.

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
- Issue #42 is runtime-proven on a real local Collect run: ANALYST_OVERVIEW_PATH emitted on stdout, overview file existed, manifest contained analyst_overview and overview path, collect bundle contained the overview file, and Gemini guidance preferred the smaller analyst-first surface before the full baseline report.
- Issue #41 bounded parallel-runtime slice is runtime-proven on a real local Collect run after the absolute-OutRoot fix: PARALLEL_EXECUTION_PROOF_PATH emitted on stdout, proof_status was OVERLAP_CONFIRMED, worker_count was 4, and per-worker proof artifacts existed under final_artifacts\parallel_workers.
- Diagnostic investigation proved that `netstat -abno` requires elevation in the standard local shell on the operator’s host while `netstat -ano` works there and `netstat -abno` works elevated.
- Diagnostic investigation proved that elevated Security queries return recent collector-relevant `4624`/`4672` events while the non-elevated collector context did not, and `Process Creation` auditing is disabled on the host.

## Next actions
- Run one local Collect flow from the current main source and evaluate `COL-DIAG-001`.
- Run `project_sources/validate_DCOIR_Run.ps1` against that run and evaluate `COL-VALIDATE-001`.
- Preserve issue #37 as evidence-blocked until same-host/build narrowed-subset evidence exists.
- Keep Gemini queued behind this temporary trust-repair collector branch until the diagnostic-hardening slice is proven.
- Hold the bounded endpoint rerun for the harness reporting patch until the operator has sent himself the needed files.
- Add concrete replay details when the Gemini collector failure excerpt is recovered.

## Provenance notes
- Updated after issue #42 was validated on a live local Collect run and closed as completed.
- Updated after issue #41 was validated on a live local Collect rerun after the absolute-OutRoot fix and closed as completed.
- Updated after evidence-first investigation showed that the remaining local partial-success lanes were rooted in execution context and audit-policy visibility rather than simple collector-summary bugs.
- Airtable Validation Test Cases row `COL-OVERVIEW-001` is Passed.
- Airtable Validation Test Cases row `COL-PAR-001` is Passed.
- Airtable Validation Test Cases rows `COL-DIAG-001` and `COL-VALIDATE-001` are new and pending runtime validation.
