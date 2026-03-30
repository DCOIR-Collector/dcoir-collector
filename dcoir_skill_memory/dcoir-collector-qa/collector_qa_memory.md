---
artifact_type: dcoir-collector-qa-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-03-30T18:35:00Z
authority_basis:
  - Project Instructions v15
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Collector QA Memory

## Current focus
Collector all-path testing under the GitHub-primary working model.

## Known failure lanes
- **Gemini collector transcript error** (status: open)
  - details: Preserved placeholder regression lane until the exact failing excerpt is recovered.
  - next_action: Capture the exact failing excerpt and turn it into a concrete replay fixture.

## Active repair candidates
- **Collector file-level comment-based help** (status: open)
  - details: The readable source begins directly with `param()` and still appears to lack file-level comment-based help.
  - next_action: Consider a bounded maintenance-doc pass before the next maintenance-heavy patch cycle.
- **Representative Windows execution evidence** (status: open)
  - details: Static and workflow-surface review passed in chat, but representative harness execution remains blocked in the Linux container because the collector requires Windows PowerShell 5.1 and Windows-native utilities.
  - next_action: Run at least `Core`, `Retrieval`, and `QuickAliases` locally on Windows PowerShell 5.1 and record results back into QA memory.

## Recently validated paths
- GitHub-primary collector QA source re-anchor completed against CP-01, CP-02, collector source, harness mirrors, rollback reference, and layout spec.
- Runtime alias alignment is currently correct: manifest/layout/harness all point to `DCOIR_Collector.ps1` as the runtime filename.
- Harness suite surface is currently correct: `Core`, `Retrieval`, `QuickAliases`, and `FullRegression` remain present.
- Collector output-contract markers and quick-command surface remain present in the readable source.
- The rollback reference remains available for bounded regression comparison.

## Next actions
- Run representative local/manual harness checks on Windows PowerShell 5.1.
- Preserve the exact results for `Core`, `Retrieval`, and `QuickAliases` as passed, failed, blocked, or planned-not-executed.
- Update this file after the next real collector QA execution cycle.
- Add concrete replay details when the Gemini collector failure excerpt is recovered.

## Provenance notes
- Updated after a hybrid collector QA pass that completed static and workflow-surface review in chat and marked execution-heavy lanes blocked in the Linux environment.
