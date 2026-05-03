# Local Configuration Registry Contract

## Authority
Airtable `Local Configuration Registry` stores configuration names and safe reference guidance only. It must not store actual values for API keys, tokens, secrets, passwords, project identifiers, or local-sensitive values unless the operator explicitly authorizes a non-secret identifier.

## No-secret-value storage rule
Token, API key, password, credential, project identifier, and protected-value rows must not contain the actual configured value. A visually empty value is correct when it represents a secret value that is intentionally not stored. This is different from missing safety-control metadata.

The maintainer must distinguish these two cases:
- actual secret value absent: expected and required;
- safety/control field absent or visually ambiguous: defect to update or explicitly report.

Because Airtable unchecked checkboxes may render as blank, the maintainer must explicitly report false checkbox state in chat/evidence output, for example `safe_to_display=false (unchecked by design for token)`.

## Canonical-row rule
There should be one active canonical row per `config_name`. If duplicates are found, keep the most complete confirmed active row, retire older or planned duplicates, and stage duplicate removal through Delete Queue.

## Field guidance
| Field | Expected use |
|---|---|
| config_name | Exact environment variable name. |
| purpose | Plain-English purpose and safety scope. |
| reference_powershell | Machine/System env lookup for Windows PowerShell, normally `[Environment]::GetEnvironmentVariable('VAR_NAME','Machine')`. |
| reference_cmd | Windows cmd reference. |
| reference_wsl_bash | Bash/WSL reference. |
| reference_python | Python `os.environ.get(...)` reference. |
| reference_additional_runtimes_json | JSON object for other runtimes. |
| sensitive_value | Checked for API keys, tokens, secrets, passwords, credentials, project identifiers, and protected values. |
| safe_to_display | False for sensitive variables; true only for non-sensitive paths/names that may be shown in logs/chat. If false, report it explicitly because the checkbox can look blank. |
| confirmed_present | Checked only after operator confirmation or smoke test. |
| config_kind | Controlled category such as api_key, token, project_id, directory_path, repository_path, identifier, protected_value, or other. |
| status | active, planned, candidate, or retired. |
| last_confirmed_at | Timestamp of operator confirmation or successful smoke test. Required when confirmed_present is true. |
| notes | Canonical row notes, value-storage posture, fallback rules, and duplicate-retirement rationale. Sensitive rows must state that the value is intentionally not stored and must not be printed/logged/packaged. |

## Required completeness by kind
| config_kind | sensitive_value | safe_to_display | confirmed_present / last_confirmed_at | required notes posture |
|---|---:|---:|---|---|
| api_key | true | false | if confirmed_present=true, last_confirmed_at must be set | value intentionally not stored; never print/log/package |
| token | true | false | if confirmed_present=true, last_confirmed_at must be set | value intentionally not stored; never print/log/package |
| project_id | true unless explicitly approved non-secret | false unless explicitly approved displayable | if confirmed_present=true, last_confirmed_at must be set | reference environment value; avoid hard-coding/echoing |
| protected_value | true | false | if confirmed_present=true, last_confirmed_at must be set | value intentionally not stored; never print/log/package |
| directory_path | false unless path is sensitive | true only when display is acceptable | if confirmed_present=true, last_confirmed_at must be set | use registered env reference; fail fast if missing |
| repository_path | false unless path is sensitive | true only when display is acceptable | if confirmed_present=true, last_confirmed_at must be set | use registered env reference; fail fast if missing |
| identifier | false unless sensitive | true only when display is acceptable | if confirmed_present=true, last_confirmed_at must be set | do not hard-code when registry row exists |

## Known DCOIR lookup preference examples
- OpenAI tools should prefer `DCOIR_OPENAI_API_KEY`, fall back to `OPENAI_API_KEY` only when explicitly approved for the tool, and use `DCOIR_OPENAI_PROJECT_ID` only for API project scoping.
- GitHub tools should prefer `DCOIR_GITHUB_FG_TOKEN`, fall back to `DCOIR_GITHUB_CL_TOKEN` only when the fine-grained token lacks the required permission.
- Airtable tools should use `DCOIR_AIRTABLE_BASE_ID` and `DCOIR_AIRTABLE_TOKEN` from Machine/System environment scope.
- Operator output tools should use `DCOIR_DOWNLOADS_DIR`; repo tools should use `DCOIR_REPO_ROOT`.

## Generated code and codeblock rule
Any DCOIR generated code or operator-run codeblock that needs local configuration must:
1. use the registry `config_name` and runtime reference fields rather than inventing names;
2. fail fast if a required environment variable is missing;
3. name the missing variable without revealing values;
4. avoid printing, logging, packaging, or echoing values where `safe_to_display=false` or `sensitive_value=true`.

## Maintainer reporting rule
When reporting on a row, include:
- `config_name`;
- canonical record id when known;
- `config_kind`;
- `status`;
- `confirmed_present` and `last_confirmed_at` posture;
- `sensitive_value`;
- `safe_to_display`, explicitly including false values;
- value storage posture (`not_stored_by_design` for secrets/protected values);
- missing fields or defects found.
