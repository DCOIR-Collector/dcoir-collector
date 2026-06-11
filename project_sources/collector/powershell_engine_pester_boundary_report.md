# PowerShell Engine and Pester Boundary Report

- Schema: `dcoir_powershell_engine_pester_boundary_report_v1`
- Issue: `#267`
- Validation: `pass`

## Summary

| Metric | Value |
| --- | ---: |
| Matrix rows | 8 |
| Required categories covered | 8 / 8 |
| Dependency reports | 4 |
| Pester blocking for static validation | `False` |
| Independent enforcement requires Pester | `False` |

## Engine Matrix

| Check | Engine | Runner | Evidence | Blocking | Owner |
| --- | --- | --- | --- | --- | --- |
| `surface-inventory-contract` | python-3.12 | any | inventory-json-and-markdown | `True` | #261 |
| `windows-powershell-51-parser-compatibility` | Windows PowerShell 5.1 Desktop | windows-latest | parser-or-runtime-result | `True` | existing Windows PowerShell 5.1 validation lanes |
| `powershell-7-psscriptanalyzer` | PowerShell 7 Core | windows-latest or ubuntu-latest with pwsh | normalized-analyzer-report | `True` | #262 |
| `rule-risk-fixture-proof` | python-3.12 | any | negative-and-control-fixture-report | `True` | #263 |
| `dcoir-custom-checks` | python-3.12 | any | custom-check-json-and-markdown-report | `True` | #264 |
| `source-part-assembly-parity` | python-3.12; optional PowerShell 7 Core parser when available | any for deterministic parity, windows-latest when Windows parser evidence is required | source-part-generated-output-parity-report | `True` | #265 |
| `finding-governance` | python-3.12 | any | finding-governance-report | `True` | #266 |
| `pester-supporting-wrapper-fixture-tests` | PowerShell 7 Core or Windows PowerShell 5.1 Desktop as declared by the owning test | windows-latest when Windows PowerShell 5.1 behavior is asserted; otherwise any runner with declared engine | pester-discovery-version-count-pass-fail-artifact | `False` | #267 boundary only until a later Pester/runtime-test gate approves execution |

## Pester Boundary

- Decision: `supporting-in-scope-not-analyzer-substitute`
- Static-security blocking: `False`
- Analyzer/custom-check substitute: `False`

## Independent Analyzer Enforcement Proof

| Proof | Count/State |
| --- | ---: |
| Rule-risk fixture findings | 14 |
| Custom-check findings | 8 |
| Governance classified findings | 22 |
| Governance unclassified findings | 0 |
| Assembly parity success | `True` |
| Requires Pester | `False` |

## Dependency Reports

| Report | Schema | Success | Findings |
| --- | --- | --- | ---: |
| `project_sources/collector/powershell_rule_risk_fixture_report.json` | `dcoir_powershell_rule_risk_fixture_report_v1` | `True` | 14 |
| `project_sources/collector/powershell_custom_check_report.json` | `dcoir_powershell_custom_check_report_v1` | `True` | 8 |
| `project_sources/collector/powershell_finding_governance_report.json` | `dcoir_powershell_finding_governance_report_v1` | `True` | 22 |
| `project_sources/collector/powershell_assembly_parity_report.json` | `dcoir_powershell_assembly_parity_report_v1` | `True` | 0 |

## Warnings

- workflow readiness remains a later explicit gate; #267 only defines evidence ownership
- Windows PowerShell 5.1 runtime evidence remains separate from local static report generation
