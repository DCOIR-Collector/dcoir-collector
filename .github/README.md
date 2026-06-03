# GitHub operating surfaces

This folder contains repository-native GitHub support surfaces for the DCOIR collector repository.

- `ISSUE_TEMPLATE/` keeps issue intake structured.
- `PULL_REQUEST_TEMPLATE.md` preserves review and validation discipline.
- `workflows/` contains validation, packaging, reporting, and maintenance automation.
- `dependabot.yml` and related metadata support repository maintenance.
- `../project_sources/github_actions/workflow_modularization_contracts.json` and generated workflow inventory files record the issue #194 workflow restructuring contract.

## Operating rules

- Keep GitHub as the canonical source for repo content and workflow behavior.
- Do not describe retired skill-mirror or parity-refresh paths as active maintenance surfaces.
- Preserve clear separation between collector/runtime guidance and repo/governance guidance.
- For workflow restructuring work, keep entry workflow contract surfaces visible and use the repo-local workflow inventory and modularization audits before claiming readiness.
