# PowerShell Custom DCOIR Check Report

- Schema: `dcoir_powershell_custom_check_report_v1`
- Issue: `#264`
- Target scope: `fixtures`
- Checks: `project_sources/collector/powershell_custom_checks.json`
- Fixture manifest: `project_sources/collector/fixtures/powershell_analysis/custom_check_fixture_manifest.json`

## Summary

| Metric | Count |
| --- | ---: |
| Custom checks | 8 |
| Targets scanned | 16 |
| Findings | 8 |
| Negative fixtures | 8 |
| Control fixtures | 8 |
| Expected fixture findings | 8 |
| Observed fixture findings | 8 |

## Findings

| Check | Risk | Path | Line | Severity | Observed | Impact | Fix |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| `dcoir-analyzer-skip-success` | `analyzer_policy_inventory_skip_or_tool_failure_reported_success` | `project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1` | 1 | `Error` | Analyzer, inventory, or target skip states must not be represented as successful validation. | Skipped analyzer or inventory work can be recorded as green evidence and hide unscanned PowerShell surfaces. | Fail closed when analyzer policy, inventory, target selection, or tool execution is incomplete. |
| `dcoir-baseline-fingerprint-bound` | `broad_suppression_or_baseline_growth_hiding_risk` | `project_sources/collector/fixtures/powershell_analysis/bad/broad_baseline.ps1` | 1 | `Error` | Suppressions and baselines must be bound to a path, rule, fingerprint, expected match count, and justification. | Broad suppressions can hide new analyzer findings and make baseline growth look intentional. | Bind suppressions to path, rule, fingerprint, expected match count, and a durable justification. |
| `dcoir-fail-output-must-fail` | `fail_rows_reports_or_fixture_outputs_not_causing_failure` | `project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1` | 2 | `Error` | FAIL rows, reports, or fixture outputs must be connected to a failing process or validation state. | A report can contain failing evidence while the command exits successfully, misleading issue or PR readiness. | Tie every failing row or report state to a thrown exception, nonzero exit, or explicit failed validation summary. |
| `dcoir-source-part-drift` | `source_part_assembly_drift_or_stale_generated_output` | `project_sources/collector/fixtures/powershell_analysis/bad/source_part_drift.ps1` | 2 | `Error` | Generated PowerShell outputs must not be accepted when source-part hashes or assembly state are stale. | Stale generated runtime or harness output can make review evidence disagree with authoritative source parts. | Regenerate outputs or compare source-part hashes before accepting analyzer evidence. |
| `dcoir-no-swallowed-catch` | `swallowed_exception_or_write_only_catch` | `project_sources/collector/fixtures/powershell_analysis/bad/swallowed_catch.ps1` | 4 | `Error` | Catch blocks must propagate failure or return a failed validation state after logging. | Write-only catch blocks can turn real validation failures into log noise while the command exits successfully. | Rethrow, exit nonzero, or return a failed validation state after recording diagnostics. |
| `dcoir-bound-event-query` | `unbounded_or_materializing_event_query_patterns` | `project_sources/collector/fixtures/powershell_analysis/bad/unbounded_event_query.ps1` | 2 | `Error` | Windows event collection must be bounded by filter, time window, or count cap. | Unbounded event collection can materialize large logs, slow incident response, and make validation nondeterministic. | Use FilterHashtable, explicit event windows, MaxEvents, or a bounded Take/Select-Object cap. |
| `dcoir-check-external-exit` | `external_command_nonzero_exit_treated_success` | `project_sources/collector/fixtures/powershell_analysis/bad/unchecked_external_exit.ps1` | 2 | `Error` | Native command and script invocations must check their immediate exit state before reporting success. | External commands can fail while stale success state leaves validation evidence green. | Capture and validate the command exit state immediately, then throw or emit a failing validation result on failure. |
| `dcoir-no-unsafe-wildcard-delete` | `unsafe_or_wildcard_deletion_outside_controlled_roots` | `project_sources/collector/fixtures/powershell_analysis/bad/unsafe_wildcard_delete.ps1` | 2 | `Error` | Recursive deletion must be constrained to a resolved controlled root before wildcards are used. | Wildcard deletion outside a controlled root can remove unintended repository or operator files. | Resolve and constrain the cleanup root before deletion, avoid broad wildcards, and use ShouldProcess where practical. |

## Fixture Results

| Fixture | Kind | Check | Expected | Observed | Rules |
| --- | --- | --- | ---: | ---: | --- |
| `bad-analyzer-skip-success` | `negative` | `dcoir-analyzer-skip-success` | 1 | 1 | `DCOIR.NoAnalyzerSkipSuccess` |
| `bad-broad-baseline` | `negative` | `dcoir-baseline-fingerprint-bound` | 1 | 1 | `DCOIR.BaselineSuppressionMustBeFingerprintBound` |
| `bad-fail-row-green-exit` | `negative` | `dcoir-fail-output-must-fail` | 1 | 1 | `DCOIR.FailOutputMustFailValidation` |
| `bad-source-part-drift` | `negative` | `dcoir-source-part-drift` | 1 | 1 | `DCOIR.SourcePartAssemblyDrift` |
| `bad-swallowed-catch` | `negative` | `dcoir-no-swallowed-catch` | 1 | 1 | `DCOIR.NoSwallowedCatch` |
| `bad-unbounded-event-query` | `negative` | `dcoir-bound-event-query` | 1 | 1 | `DCOIR.BoundedEventQueryRequired` |
| `bad-unchecked-external-exit` | `negative` | `dcoir-check-external-exit` | 1 | 1 | `DCOIR.CheckExternalCommandExit` |
| `bad-unsafe-wildcard-delete` | `negative` | `dcoir-no-unsafe-wildcard-delete` | 1 | 1 | `DCOIR.NoUnsafeWildcardDeletion` |
| `good-analyzer-skip-fails-closed` | `control` | `dcoir-analyzer-skip-success` | 0 | 0 | (none) |
| `good-bounded-event-query` | `control` | `dcoir-bound-event-query` | 0 | 0 | (none) |
| `good-catch-rethrows` | `control` | `dcoir-no-swallowed-catch` | 0 | 0 | (none) |
| `good-external-exit-checked` | `control` | `dcoir-check-external-exit` | 0 | 0 | (none) |
| `good-fail-row-fails-command` | `control` | `dcoir-fail-output-must-fail` | 0 | 0 | (none) |
| `good-fingerprint-bound-baseline` | `control` | `dcoir-baseline-fingerprint-bound` | 0 | 0 | (none) |
| `good-safe-root-delete` | `control` | `dcoir-no-unsafe-wildcard-delete` | 0 | 0 | (none) |
| `good-source-part-current` | `control` | `dcoir-source-part-drift` | 0 | 0 | (none) |

## Validation Findings

- No validation errors.
