# PowerShell Rule-Risk Fixture Report

- Schema: `dcoir_powershell_rule_risk_fixture_report_v1`
- Issue: `#263`
- Matrix: `project_sources/collector/powershell_rule_risk_matrix.json`
- Manifest: `project_sources/collector/fixtures/powershell_analysis/rule_fixture_manifest.json`
- Analyzer wrapper: `project_sources/collector/tools/run_powershell_analyzer.py`
- Fixture analyzer: `DCOIRFixtureAnalyzer 1.0.0`
- Validation: `pass`

## Summary

| Metric | Count |
| --- | ---: |
| Matrix checks | 15 |
| Blocking checks | 14 |
| Advisory checks | 1 |
| Negative fixtures | 14 |
| Control fixtures | 1 |
| Expected findings | 14 |
| Observed findings | 14 |

## Fixtures

| Fixture | Kind | Expected | Observed | Status | Rules |
| --- | --- | ---: | ---: | --- | --- |
| `bad-analyzer-skip-success` | `negative` | 1 | 1 | `pass` | `DCOIR.NoAnalyzerSkipSuccess` |
| `bad-broad-baseline` | `negative` | 1 | 1 | `pass` | `DCOIR.BaselineSuppressionMustBeFingerprintBound` |
| `bad-fail-row-green-exit` | `negative` | 1 | 1 | `pass` | `DCOIR.FailOutputMustFailValidation` |
| `bad-invoke-expression` | `negative` | 1 | 1 | `pass` | `PSAvoidUsingInvokeExpression` |
| `bad-plaintext-password` | `negative` | 1 | 1 | `pass` | `PSAvoidUsingPlainTextForPassword` |
| `bad-plaintext-securestring` | `negative` | 1 | 1 | `pass` | `PSAvoidUsingConvertToSecureStringWithPlainText` |
| `bad-source-part-drift` | `negative` | 1 | 1 | `pass` | `DCOIR.SourcePartAssemblyDrift` |
| `bad-state-changing-function` | `negative` | 1 | 1 | `pass` | `PSUseShouldProcessForStateChangingFunctions` |
| `bad-swallowed-catch` | `negative` | 1 | 1 | `pass` | `DCOIR.NoSwallowedCatch` |
| `bad-unbounded-event-query` | `negative` | 1 | 1 | `pass` | `DCOIR.BoundedEventQueryRequired` |
| `bad-unchecked-external-exit` | `negative` | 1 | 1 | `pass` | `DCOIR.CheckExternalCommandExit` |
| `bad-unsafe-wildcard-delete` | `negative` | 1 | 1 | `pass` | `DCOIR.NoUnsafeWildcardDeletion` |
| `bad-unused-variable` | `negative` | 1 | 1 | `pass` | `PSUseDeclaredVarsMoreThanAssignments` |
| `bad-write-host` | `negative` | 1 | 1 | `pass` | `PSAvoidUsingWriteHost` |
| `good-clean-control` | `control` | 0 | 0 | `pass` | (none) |

## Validation Findings

- No validation errors.

## Environment Gap

- This #263 harness uses a deterministic local fixture analyzer through the #262 wrapper. It does not prove PSScriptAnalyzer module execution because pwsh/PSScriptAnalyzer is not available in this environment.
