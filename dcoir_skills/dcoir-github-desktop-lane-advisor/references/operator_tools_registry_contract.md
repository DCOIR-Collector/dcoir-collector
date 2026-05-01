# Operator Tools Registry Contract

Airtable table: `Operator Tools Registry`

Purpose: live discovery index for reusable operator-side tools. GitHub remains source of truth for tool code.

Recommended fields:
- `tool_id`: stable identifier.
- `tool_name`: human-readable title.
- `tool_family`: routing family.
- `repo_path`: repo-relative path to tool code or catalog.
- `trigger_conditions`: natural-language matching hints.
- `input_contract`: expected inputs, parameters, manifest format, or preconditions.
- `output_contract`: expected output logs, ZIPs, JSON, or artifacts.
- `safety_preconditions`: stop conditions and safety checks.
- `launcher_command`: preferred PowerShell launcher template.
- `status`: active, draft, deprecated, or blocked.
- `version_or_hash`: revision marker.
- `last_validated_at`: validation timestamp.
- `notes`: caveats, backing modules, validation evidence, and examples.
- `active`: whether advisor routing may select the tool.
- `retention_class`: operational, reference, temporary, or archive handling.

Current active tool IDs to expect after the 2026-05-01 module split:
- `DCOIR-GIT-DIAGNOSTIC`
- `DCOIR-SAFE-PREPULL-APPLY`
- `DCOIR-TARGETED-SNAPSHOT`
- `DCOIR-TEXT-ONLY-REPO-SNAPSHOT`
- `DCOIR-REPO-PATCH-APPLY`
- `DCOIR-CHATGPT-FRIENDLY-ZIP`
- `DCOIR-ACTIONS-WORKFLOW-ORCHESTRATOR`
- `DCOIR-ACTIONS-VALIDATION-SMOKE`
- `DCOIR-ACTIONS-MODE-LADDER`

If duplicate or stale registry rows are found, do not delete directly. Queue cleanup through Delete Queue after dependency review and operator approval.
