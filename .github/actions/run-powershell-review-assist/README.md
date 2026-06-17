# run-powershell-review-assist

Reusable DCOIR GitHub Actions composite action for issue #270 PowerShell review-assist report integration.

## Contract

- Callers keep triggers, permissions, artifact names, retention, and workflow claims visible in the entry or reusable workflow.
- This action owns the repeated mechanical step for running `project_sources/collector/tools/run_powershell_review_assist_report.py`.
- The action writes workflow-generated JSON and Markdown reports to caller-provided repo-relative paths under `project_sources/collector/`.
- The action must not generate SARIF, upload SARIF, enable code scanning, change required checks, use `pull_request_target`, reference `secrets.*`, or mutate repository history.
- Compensating evidence is provided by caller-visible step names, explicit inputs, stdout markers, generated report files, uploaded artifacts, and the caller workflow report section.

## Maintenance

Change this module when the shared PowerShell review-assist workflow mechanic changes, then run local validation and applicable workflow readback.
