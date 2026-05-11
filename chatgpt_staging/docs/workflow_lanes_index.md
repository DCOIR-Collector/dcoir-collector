# Superseded workflow guidance pointer

Status: retained pointer/stub. This file is no longer the authoritative source for current workflow routing or workflow execution guidance.

Current source-of-truth model:

- Airtable table `GitHub Workflow Inventory` owns general GitHub Actions workflow routing guidance.
- The top comment block in each `.github/workflows/*.yml` file owns workflow-specific execution guidance.
- The workflow YAML body remains the executable source of truth.
- Workflow status reports under `chatgpt_staging/status_reports/` are readback/evidence surfaces, not durable workflow-use documentation.

Use this file only as a historical locator. Do not update it with new workflow-use instructions. Update the relevant workflow header and Airtable row instead.
