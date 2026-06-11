# PowerShell Finding Governance Report

- Schema: `dcoir_powershell_finding_governance_report_v1`
- Issue: #266
- Validation: `pass`

## Summary

| Metric | Count |
| --- | ---: |
| Current findings | 22 |
| Classified findings | 22 |
| Unclassified findings | 0 |
| Baseline records | 0 |
| Matched baseline records | 0 |
| Suppressions | 0 |
| Matched suppressions | 0 |

## Decisions

| Decision | Count |
| --- | ---: |
| `advisory` | 22 |

## Baseline Delta Proof

- New unclassified findings: `0`
- Matched baseline records: `0` / `0`
- Matched suppressions: `0` / `0`
- As of: `2026-06-10`

## Inputs

| Report | Required | Schema | Findings |
| --- | --- | --- | ---: |
| `project_sources/collector/powershell_custom_check_report.json` | `True` | `dcoir_powershell_custom_check_report_v1` | 8 |
| `project_sources/collector/powershell_rule_risk_fixture_report.json` | `True` | `dcoir_powershell_rule_risk_fixture_report_v1` | 14 |
| `project_sources/collector/powershell_analyzer_report.json` | `False` | `not present` | 0 |

## Controlled Fail-Closed Proof

| Control | Expected Result | Evidence |
| --- | --- | --- |
| `new-unclassified-finding` | fails when a finding is not matched by a baseline record, suppression, or classification rule | `test_new_finding_without_classification_fails_closed` |
| `malformed-baseline` | fails when a baseline record is missing required review or fingerprint fields | `test_malformed_baseline_fails_closed` |
| `severity-increase` | fails when a baseline record's matched finding increases severity | `test_severity_increase_fails_closed` |
| `unexpected-disappearance` | fails when an expected baseline fingerprint disappears without an exception | `test_unexpected_baseline_disappearance_fails_closed` |
| `blanket-suppression` | fails on repo-wide, wildcard path, or wildcard rule suppressions | `test_blanket_suppression_fails_closed` |
| `generated-output-suppression` | fails when a generated-output file suppression lacks #265 assembly coverage and an explicit reviewed reason | `test_generated_output_suppression_requires_assembly_coverage` |

## Warnings

- optional PowerShell finding report not present: project_sources/collector/powershell_analyzer_report.json
