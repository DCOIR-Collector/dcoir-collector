# DCOIR authority drift taxonomy

## Drift families
- `startup_authority_conflict`: Project Instructions, CP-00, Governance Control Plane, or live Airtable state disagree about startup/live queue rules.
- `schema_assumption_drift`: a table, field, select option, or linked-record path is assumed without live schema readback.
- `github_promoted_history_drift`: GitHub CP/todo/promoted history is treated as live queue authority when Airtable is live authority.
- `skill_instruction_drift`: installed or source skill instructions reference retired tables, old cutover language, or obsolete workflows.
- `project_attachment_drift`: Project attachment wording conflicts with current operational model.
- `repo_surface_drift`: repo keep/delete/source-role classification is unclear or conflicts with Repo Surface Registry.
- `delete_queue_dependency_drift`: deletion order, approval, or verification path is unclear.
- `helper_memory_drift`: helper memory appears split between old GitHub memory and Airtable helper-memory tables.
- `connector_failure_drift`: a connector failure causes unsupported fallback assumptions.

## Severity
- `info`: note only; no immediate workflow risk.
- `warning`: could cause extra roundtrips or mild confusion.
- `high`: could cause wrong source choice, duplicated tasks, bad package, or stale skill behavior.
- `critical`: could cause destructive delete, schema write, source overwrite, or hard authority conflict.
