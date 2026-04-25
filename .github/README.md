# GitHub operating surfaces

This folder contains repository-native guidance for the DCOIR workflow:

- `ISSUE_TEMPLATE/` routes issue intake into the closest DCOIR issue class.
- `PULL_REQUEST_TEMPLATE.md` preserves authority, command-lane, and validation checks during review.
- `workflows/` contains manual and automated validation/build lanes.
- `dependabot.yml` keeps GitHub Actions dependencies visible for review.
- `skill-parity-refresh-trigger.txt` can be touched to intentionally trigger helper-skill parity refresh automation.

## Operating rules

- Do not enable blank issue intake when a repository template can fit the report.
- Keep Airtable as live queue and execution-state authority.
- Keep GitHub as the governed readable source for durable files, release history, helper-skill source, and promoted decisions.
- Preserve Windows PowerShell 5.1 local-test wording and Elastic Defend response-action endpoint wording as separate command lanes.
- Prefer manual workflow dispatch for packaging and release lanes unless a promoted governance decision authorizes a broader automatic trigger.
