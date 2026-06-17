# PowerShell Rule-To-Risk Matrix

- Schema: `dcoir_powershell_rule_risk_matrix_v1`
- Issue: `#263`
- Parent issue: `#260`
- Scope: rule-to-risk mapping and fixture proof only; no workflow, SARIF, required-check, or PR mutation.

## Checks

| Check ID | Rule | Tool | Blocking | Severity | Risk Classes | Fixtures |
| --- | --- | --- | --- | --- | --- | --- |
| `pssa-avoid-invoke-expression` | `PSAvoidUsingInvokeExpression` | PSScriptAnalyzer | `true` | `Warning` | `unsafe_dynamic_execution` | `bad-invoke-expression` |
| `pssa-avoid-plaintext-securestring` | `PSAvoidUsingConvertToSecureStringWithPlainText` | PSScriptAnalyzer | `true` | `Warning` | `secret_material_or_credential_handling` | `bad-plaintext-securestring` |
| `pssa-avoid-plaintext-password` | `PSAvoidUsingPlainTextForPassword` | PSScriptAnalyzer | `true` | `Warning` | `secret_material_or_credential_handling` | `bad-plaintext-password` |
| `pssa-avoid-write-host` | `PSAvoidUsingWriteHost` | PSScriptAnalyzer | `true` | `Warning` | `review_assist_output_quality` | `bad-write-host` |
| `pssa-use-declared-vars-more-than-assignments` | `PSUseDeclaredVarsMoreThanAssignments` | PSScriptAnalyzer | `true` | `Warning` | `stale_or_dead_validation_state` | `bad-unused-variable` |
| `pssa-use-shouldprocess-for-state-change` | `PSUseShouldProcessForStateChangingFunctions` | PSScriptAnalyzer | `true` | `Warning` | `unsafe_or_wildcard_deletion_outside_controlled_roots` | `bad-state-changing-function` |
| `dcoir-analyzer-skip-success` | `DCOIR.NoAnalyzerSkipSuccess` | DCOIR fixture analyzer | `true` | `Error` | `analyzer_policy_inventory_skip_or_tool_failure_reported_success` | `bad-analyzer-skip-success` |
| `dcoir-check-external-exit` | `DCOIR.CheckExternalCommandExit` | DCOIR fixture analyzer | `true` | `Error` | `stale_or_unchecked_last_exit_code_or_success_status`<br>`external_command_nonzero_exit_treated_success` | `bad-unchecked-external-exit` |
| `dcoir-fail-output-must-fail` | `DCOIR.FailOutputMustFailValidation` | DCOIR fixture analyzer | `true` | `Error` | `fail_rows_reports_or_fixture_outputs_not_causing_failure` | `bad-fail-row-green-exit` |
| `dcoir-source-part-drift` | `DCOIR.SourcePartAssemblyDrift` | DCOIR fixture analyzer | `true` | `Error` | `source_part_assembly_drift_or_stale_generated_output` | `bad-source-part-drift` |
| `dcoir-no-unsafe-wildcard-delete` | `DCOIR.NoUnsafeWildcardDeletion` | DCOIR fixture analyzer | `true` | `Error` | `unsafe_or_wildcard_deletion_outside_controlled_roots` | `bad-unsafe-wildcard-delete` |
| `dcoir-bound-event-query` | `DCOIR.BoundedEventQueryRequired` | DCOIR fixture analyzer | `true` | `Error` | `unbounded_or_materializing_event_query_patterns` | `bad-unbounded-event-query` |
| `dcoir-baseline-fingerprint-bound` | `DCOIR.BaselineSuppressionMustBeFingerprintBound` | DCOIR fixture analyzer | `true` | `Error` | `broad_suppression_or_baseline_growth_hiding_risk` | `bad-broad-baseline` |
| `dcoir-no-swallowed-catch` | `DCOIR.NoSwallowedCatch` | DCOIR fixture analyzer | `true` | `Error` | `swallowed_exception_or_write_only_catch` | `bad-swallowed-catch` |
| `advisory-long-inline-command` | `DCOIR.ReviewLongInlinePowerShell` | DCOIR advisory review | `false` | `Information` | `review_assist_output_quality` | (none) |

## Advisory Promotion

- `advisory-long-inline-command`: Promote to blocking only after workflow snippet extraction and line mapping are approved in a later child issue.
