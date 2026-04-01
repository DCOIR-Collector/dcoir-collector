---
artifact_type: dcoir-collector-qa-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-01T14:10:00Z
authority_basis:
  - Project Instructions v15
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Collector QA Memory

## Current focus
Hold the bounded endpoint rerun for the harness partial-success reporting patch until the operator has sent himself the needed files outside the current work environment.

## Known failure lanes
- **Gemini collector transcript error** (status: open)
  - details: Preserved placeholder regression lane until the exact failing excerpt is recovered.
  - next_action: Capture the exact failing excerpt and turn it into a concrete replay fixture.
- **QuickAliases partial-success flattening in harness summaries** (status: patched-deferred-rerun)
  - details: Endpoint evidence showed `24_EnrichStartStrings` and `26_EnrichStartStreams` reporting `STATUS=PARTIAL_SUCCESS` in collector output while summary txt/json flattened both steps to `PASS` because exit code remained 0.
  - next_action: Do not resume the bounded endpoint rerun until the operator has sent himself the needed files; after that, rerun QuickAliases Strings and Streams plus one Core control lane and confirm summary artifacts now preserve `PARTIAL_SUCCESS`.
- **Endpoint working-zip restage/access lane** (status: open)
  - details: A prior Core attempt failed around the transient root working zip `response_actions\DCOIR_Collector.zip`; current interpretation is a restage/access issue around a transient root copy, not yet a bounded collector-code defect.
  - next_action: Keep `assets\DCOIR_Collector.zip` as the master restage source and only escalate this lane if a narrower code-backed failure is reproduced.

## Active repair candidates
- **Collector file-level comment-based help** (status: open)
  - details: The readable source begins directly with `param()` and still appears to lack file-level comment-based help.
  - next_action: Consider a bounded maintenance-doc pass before the next maintenance-heavy patch cycle.
- **Endpoint-lane workflow note preservation** (status: open)
  - details: The endpoint lane now has two durable operator rules: absolute get-file paths for harness outputs and transient-root-zip handling.
  - next_action: Keep those rules synchronized in governed workflow docs and later skill guidance.

## Recently validated paths
- GitHub-primary collector QA source re-anchor completed against CP-01, CP-02, collector source, harness mirrors, rollback reference, and layout spec.
- Runtime alias alignment is currently correct: manifest/layout/harness all point to `DCOIR_Collector.ps1` as the runtime filename.
- Harness suite surface is currently correct: `Core`, `Retrieval`, `QuickAliases`, and `FullRegression` remain present.
- Collector all-path execution is evidenced through Elastic Defend response actions across QuickAliases, Core, and Retrieval.
- Retrieval of harness summary files is validated when full absolute response-actions paths are used.
- The rollback reference remains available for bounded regression comparison.

## Next actions
- Hold the bounded endpoint rerun for the harness reporting patch until the operator has sent himself the needed files.
- Keep the exact rerun target unchanged for later: QuickAliases Strings and Streams plus one Core control lane.
- Update this file after the deferred rerun completes.
- Add concrete replay details when the Gemini collector failure excerpt is recovered.

## Provenance notes
- Updated after the operator explicitly deferred the rerun until he can send himself the needed files.
