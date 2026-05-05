# Task-time config gate

Use this reference when DCOIR work includes local/system configuration names, environment variables, runtime references, generated code, scripts, workflow snippets, GitHub Actions/chatgpt-exec requests, operator tools, or local execution instructions.

## Trigger checklist
Run a compact config gate before final output when any of these appear or are implied:
- environment variables, tokens, API keys, credentials, project identifiers, webhook names, local paths, repo paths, or protected values;
- PowerShell `$env:VAR`, cmd `%VAR%`, Bash `${VAR}`/`$VAR`, Python `os.environ`, dotenv-style names, or workflow `secrets.*`/`env.*` references;
- generated code/codeblocks, scripts, GitHub Actions, chatgpt-exec JSON, operator_tools, launchers, install/setup steps, validation commands, or smoke tests;
- connector/tool failure where a missing or misnamed config variable may be involved;
- Local Configuration Registry cleanup, dedupe, retirement, or Delete Queue handling.

## Compact output
Return only these fields when the task is not full registry maintenance:
1. config names involved;
2. existing canonical row status, or missing row;
3. safety flags: sensitive_value, safe_to_display, confirmed_present, config_kind, status when known;
4. runtime reference pattern to use;
5. missing row, duplicate, or schema/readback risk;
6. whether Airtable write, approval, or Delete Queue is required;
7. safest next action.

## Rules
- Never request, print, log, cache, package, or store actual secret values.
- Missing secret values in Airtable are correct by design; missing safe reference rows are defects or blockers.
- Do not emit final runnable code as complete if a required config name lacks an active canonical registry row. Provide registry-ready row content or ask for approval to create/update it.
- Prefer existing active registry names over new synonyms.
- For sensitive rows, keep sensitive_value=true, safe_to_display=false, and notes that the value is intentionally not stored.
