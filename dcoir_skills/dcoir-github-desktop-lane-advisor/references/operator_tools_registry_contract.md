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
- `output_contract`: expected output logs, ZIPs, or artifacts.
- `safety_preconditions`: stop conditions and safety checks.
- `launcher_command`: preferred PowerShell launcher template.
- `status`: active, draft, deprecated, or blocked.
- `version_or_hash`: revision marker.
- `last_validated_at`: validation timestamp.
- `notes`: caveats and examples.
