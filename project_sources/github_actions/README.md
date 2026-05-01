# GitHub Actions maintenance

This folder documents repository automation for workflow and dependency change visibility.

## Current model

- Dependabot watches GitHub Actions references and opens pull requests.
- Workflow maintenance audit fails visibly if known stale action versions return.
- Dependency Review checks dependency changes on pull requests.
- CodeQL scans supported code on push, pull request, weekly schedule, and manual dispatch.
- Dependabot auto-merge can enable auto-merge for GitHub Actions update PRs after repository auto-merge is enabled and required checks are satisfied.

## Operator notes

For low-risk Dependabot GitHub Actions PRs, allow auto-merge after checks pass. For larger source, workflow, or security-sensitive changes, review manually before merge.

Direct pushes remain acceptable for small operator-approved GitHub Desktop bundles, but automation and dependency changes should use pull requests when practical.
