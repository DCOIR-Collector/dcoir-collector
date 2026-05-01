# Local Configuration Registry Contract

## Authority
Airtable `Local Configuration Registry` stores configuration names and safe reference guidance only. It must not store actual values for API keys, tokens, secrets, passwords, project identifiers, or local-sensitive values unless the operator explicitly authorizes a non-secret identifier.

## Canonical-row rule
There should be one active canonical row per `config_name`. If duplicates are found, keep the most complete confirmed active row, retire older or planned duplicates, and stage duplicate removal through Delete Queue.

## Field guidance
| Field | Expected use |
|---|---|
| config_name | Exact environment variable name. |
| purpose | Plain-English purpose and safety scope. |
| reference_powershell | Machine/System env lookup for Windows PowerShell. |
| reference_cmd | Windows cmd reference. |
| reference_wsl_bash | Bash/WSL reference. |
| reference_python | Python `os.environ.get(...)` reference. |
| reference_additional_runtimes_json | JSON object for other runtimes. |
| sensitive_value | Checked for API keys, tokens, secrets, passwords, credentials. |
| safe_to_display | Usually false for sensitive variables; true only for non-sensitive paths/names. |
| confirmed_present | Checked only after operator confirmation or smoke test. |
| config_kind | Controlled category such as api_key, token, project_id, directory_path, repository_path, identifier, protected_value, or other. |
| status | active, planned, candidate, or retired. |
| last_confirmed_at | Timestamp of operator confirmation or successful smoke test. |
| notes | Canonical row notes, fallback rules, and duplicate-retirement rationale. |

## Known DCOIR lookup preference examples
- OpenAI tools should prefer `DCOIR_OPENAI_API_KEY`, fall back to `OPENAI_API_KEY`, and use `DCOIR_OPENAI_PROJECT_ID` only for API project scoping.
- GitHub tools should prefer `DCOIR_GITHUB_FG_TOKEN`, fall back to `DCOIR_GITHUB_CL_TOKEN` only when the fine-grained token lacks the required permission.
- Airtable tools should use `DCOIR_AIRTABLE_BASE_ID` and `DCOIR_AIRTABLE_TOKEN` from Machine/System environment scope.
- Operator output tools should use `DCOIR_DOWNLOADS_DIR`; repo tools should use `DCOIR_REPO_ROOT`.
