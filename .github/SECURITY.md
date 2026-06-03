# Security policy

## Reporting sensitive findings

Use a private reporting path when a finding includes credentials, tokens, sensitive paths, endpoint details, or information that should not be public in an issue.

If the finding is not sensitive, use the closest GitHub issue template:

- Bug report for reproducible repository defects that do not fit a more specific form.
- Collector issue for collector execution, harness, command, output, packaging, or delivery problems.
- Workflow issue for GitHub Actions trigger, job, artifact, validation, or reporting defects.
- Validation finding for live-test, regression-test, acceptance-test, or workflow validation results.
- Documentation or workflow correction for misleading, stale, or conflicting operator guidance.
- Supabase ircore request for governed routing, receipt, validation-rule, or operational-control-plane concerns.

## DCOIR review priorities

Treat these as high priority:

- Credential, token, secret, or sensitive-path exposure.
- Collector command-lane confusion that could cause unsafe endpoint or local execution.
- Broken validation or packaging workflow that could produce misleading release confidence.
- Documentation that contradicts the current authority model.

## Handling guidance

Do not paste secrets, endpoint identifiers, or sensitive logs into public issues. Redact evidence while preserving enough context to reproduce and validate the problem.
