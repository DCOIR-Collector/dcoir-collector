# PowerShell Review-Assist Fixtures

This directory holds seeded examples for the #268 review-assist report contract.

- `good_report.json` is a compact good-path fixture derived from the generated #268 report. Its `summary` and channel counts describe the included sample arrays, and full-report counts are preserved under `fixture_contract`; the complete reviewer artifact is `project_sources/collector/powershell_review_assist_report.json`.
- The optional #262 analyzer report is intentionally represented as `optional_missing` in the seeded example unless a validated analyzer artifact is explicitly supplied.
- Failure examples are covered by `project_sources/collector/tools/test_run_powershell_review_assist_report.py` so negative cases do not overwrite the committed good-path report artifacts.

The #268 fixtures do not claim workflow readiness, SARIF output, code scanning, required-check behavior, artifact retention, Pester promotion, changed-file gating, #269/#270 completion, or parent #260 closeability.
