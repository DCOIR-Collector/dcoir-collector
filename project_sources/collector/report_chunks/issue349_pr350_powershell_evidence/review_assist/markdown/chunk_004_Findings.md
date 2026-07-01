## Findings

| Evidence | Severity | Rule/check | Path | Line | Governance |
| --- | --- | --- | --- | ---: | --- |
| deterministic_fixture_analyzer | Error | DCOIR.NoAnalyzerSkipSuccess | project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1 | 1 | advisory |
| deterministic_fixture_analyzer | Error | DCOIR.BaselineSuppressionMustBeFingerprintBound | project_sources/collector/fixtures/powershell_analysis/bad/broad_baseline.ps1 | 1 | advisory |
| deterministic_fixture_analyzer | Error | DCOIR.FailOutputMustFailValidation | project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Warning | PSAvoidUsingInvokeExpression | project_sources/collector/fixtures/powershell_analysis/bad/invoke_expression.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Warning | PSAvoidUsingPlainTextForPassword | project_sources/collector/fixtures/powershell_analysis/bad/plaintext_password.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Warning | PSAvoidUsingConvertToSecureStringWithPlainText | project_sources/collector/fixtures/powershell_analysis/bad/plaintext_securestring.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Error | DCOIR.SourcePartAssemblyDrift | project_sources/collector/fixtures/powershell_analysis/bad/source_part_drift.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Warning | PSUseShouldProcessForStateChangingFunctions | project_sources/collector/fixtures/powershell_analysis/bad/state_changing_function.ps1 | 1 | advisory |
| deterministic_fixture_analyzer | Error | DCOIR.NoSwallowedCatch | project_sources/collector/fixtures/powershell_analysis/bad/swallowed_catch.ps1 | 4 | advisory |
| deterministic_fixture_analyzer | Error | DCOIR.BoundedEventQueryRequired | project_sources/collector/fixtures/powershell_analysis/bad/unbounded_event_query.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Error | DCOIR.CheckExternalCommandExit | project_sources/collector/fixtures/powershell_analysis/bad/unchecked_external_exit.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Error | DCOIR.NoUnsafeWildcardDeletion | project_sources/collector/fixtures/powershell_analysis/bad/unsafe_wildcard_delete.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Warning | PSUseDeclaredVarsMoreThanAssignments | project_sources/collector/fixtures/powershell_analysis/bad/unused_variable.ps1 | 2 | advisory |
| deterministic_fixture_analyzer | Warning | PSAvoidUsingWriteHost | project_sources/collector/fixtures/powershell_analysis/bad/write_host.ps1 | 2 | advisory |
| dcoir_custom_static_check | Error | DCOIR.NoAnalyzerSkipSuccess | project_sources/collector/fixtures/powershell_analysis/bad/analyzer_skip_success.ps1 | 1 | advisory |
| dcoir_custom_static_check | Error | DCOIR.BaselineSuppressionMustBeFingerprintBound | project_sources/collector/fixtures/powershell_analysis/bad/broad_baseline.ps1 | 1 | advisory |
| dcoir_custom_static_check | Error | DCOIR.FailOutputMustFailValidation | project_sources/collector/fixtures/powershell_analysis/bad/fail_row_green_exit.ps1 | 2 | advisory |
| dcoir_custom_static_check | Error | DCOIR.SourcePartAssemblyDrift | project_sources/collector/fixtures/powershell_analysis/bad/source_part_drift.ps1 | 2 | advisory |
| dcoir_custom_static_check | Error | DCOIR.NoSwallowedCatch | project_sources/collector/fixtures/powershell_analysis/bad/swallowed_catch.ps1 | 4 | advisory |
| dcoir_custom_static_check | Error | DCOIR.BoundedEventQueryRequired | project_sources/collector/fixtures/powershell_analysis/bad/unbounded_event_query.ps1 | 2 | advisory |
| dcoir_custom_static_check | Error | DCOIR.CheckExternalCommandExit | project_sources/collector/fixtures/powershell_analysis/bad/unchecked_external_exit.ps1 | 2 | advisory |
| dcoir_custom_static_check | Error | DCOIR.NoUnsafeWildcardDeletion | project_sources/collector/fixtures/powershell_analysis/bad/unsafe_wildcard_delete.ps1 | 2 | advisory |

