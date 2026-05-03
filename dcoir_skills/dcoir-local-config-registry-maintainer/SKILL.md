---
name: dcoir-local-config-registry-maintainer
description: maintain africom_soc_ir / dcoir Local Configuration Registry rows in Airtable. Use when local/system environment variable names, safe reference guidance, config row deduplication, missing runtime references, secret-handling flags, config defaults, generated code/codeblocks needing environment variables, or Delete Queue cleanup for Local Configuration Registry records are involved.
---

<!-- skill-marker: updated-skill|20260503T161500Z|explicit-safety-control-contract|source-update|dcoir-local-config-registry-maintainer|SKILL.md -->
<!-- skill-marker: updated-skill|20260501T224500Z|local-config-registry-maintainer|new-skill|dcoir-local-config-registry-maintainer|SKILL.md -->

# DCOIR Local Configuration Registry Maintainer

## Project gate
Use this skill only inside AFRICOM_SOC_IR / DCOIR work. Airtable is operational authority for Local Configuration Registry records. GitHub remains governed source/readback for helper-skill source and reusable tool code only when repository readback, packaging, or parity work requires it.

## Purpose
Use this skill to keep Airtable `Local Configuration Registry` clean, safe, and useful for operator-side tools and generated code/codeblocks. The table stores configuration names and safe reference guidance only. It must never store token values, API key values, secret values, project id values, or other credential material.

## Hard rules
- Store environment variable names and safe reference expressions only.
- Never store, ask for, print, log, or package actual values for API keys, tokens, secrets, project identifiers, passwords, credentials, or local-sensitive values.
- Treat missing actual token/API key values in Airtable as correct. The registry is not a secret store.
- Treat missing or ambiguous safety-control metadata as a defect. The maintainer must explicitly maintain and report `sensitive_value`, `safe_to_display`, `confirmed_present`, `config_kind`, `status`, reference fields, and `last_confirmed_at` when those fields exist.
- For sensitive rows, set `sensitive_value=true`, `safe_to_display=false`, and add a note that the value is intentionally not stored and must never be printed/logged/packaged.
- Remember that Airtable unchecked checkboxes may render visually blank. In output, explicitly report false checkbox values such as `safe_to_display=false`; do not let a visually blank checkbox look like an unexamined field.
- Treat `Local Configuration Registry` as one active canonical row per `config_name`.
- If duplicates exist, choose one canonical row, mark duplicates `retired`, and queue duplicate deletion through `Delete Queue`; do not directly delete unless the operator explicitly authorizes immediate deletion and dependency order is safe.
- Use live Airtable schema readback before writes or Delete Queue staging.
- Fill missing reference fields whenever the schema contains them.
- Set `safe_to_display=false` for sensitive values such as tokens and API keys.
- Set `sensitive_value=true` for API keys, tokens, secrets, passwords, and credentials.
- Use `confirmed_present=true` only after the operator confirms the Machine/System environment variable exists or after an approved local smoke test proves it. If `confirmed_present=true`, keep `last_confirmed_at` populated.

## Canonical field expectations
Consult `references/local_config_registry_contract.md` when maintaining rows. Use field names from the live schema, not stale assumptions. Common fields include:
- `config_name`
- `purpose`
- `reference_powershell`
- `reference_cmd`
- `reference_wsl_bash`
- `reference_python`
- `reference_additional_runtimes_json`
- `sensitive_value`
- `safe_to_display`
- `confirmed_present`
- `config_kind`
- `status`
- `last_confirmed_at`
- `notes`

## Maintenance workflow
1. Read live schema for `Local Configuration Registry` and `Delete Queue` before schema-sensitive work.
2. Read relevant Local Configuration Registry rows by exact `config_name` filter or focused search. When verifying specific rows, prefer an exact `config_name` filter over a broad display widget.
3. Normalize the active canonical row:
   - complete all reference fields that exist in the current schema;
   - use `api_key` for OpenAI/API keys, `token` for GitHub/Airtable tokens, `project_id` for project identifier variables, `directory_path` for local folders, `repository_path` for repo roots, and `protected_value` for other sensitive non-token values;
   - set `sensitive_value=true` and `safe_to_display=false` for tokens, API keys, passwords, credentials, project identifiers, and protected values;
   - add or update notes for sensitive rows with: value intentionally not stored; use the environment reference only; never print/log/package the value;
   - set status to `active` for current confirmed variables and `planned` only before operator confirmation;
   - if `confirmed_present=true`, ensure `last_confirmed_at` is populated.
4. Detect row defects before declaring success:
   - missing runtime reference fields supported by the schema;
   - `sensitive_value`, `safe_to_display`, `confirmed_present`, `config_kind`, or `status` not set according to the contract;
   - `confirmed_present=true` with empty `last_confirmed_at`;
   - sensitive row notes that do not explain that the actual value is intentionally not stored;
   - duplicate active rows for the same `config_name`.
5. Detect duplicates:
   - same `config_name` with more than one row;
   - older planned rows after a newer confirmed row exists;
   - rows with incomplete safety flags superseded by a complete canonical row.
6. Retire duplicates before deletion:
   - set `status=retired`;
   - add notes naming the canonical row;
   - create Delete Queue rows with `target_table=Local Configuration Registry`, `target_record_id=<duplicate record id>`, and a clear reason.
7. Summarize canonical rows, retired duplicate rows, queued deletion keys, defect checks, explicit false safety values, and any blocked fields.

## Runtime reference generation
When filling `reference_additional_runtimes_json`, use a compact JSON object. For a variable named `VAR_NAME`, use the pattern in `references/runtime_reference_patterns.md` and replace `VAR_NAME` exactly.

For generated code/codeblocks that need local/system configuration:
- use Local Configuration Registry rows before inventing variable names;
- read values at runtime from the registered environment references;
- fail fast with the variable name when a required variable is missing;
- do not print actual values for rows where `safe_to_display=false` or `sensitive_value=true`.

## Output contract
Return a compact table with:
- canonical rows updated;
- explicit secret-value storage posture (`not_stored_by_design` for tokens/API keys/secrets/project identifiers);
- explicit safety-control values, including false checkbox values such as `safe_to_display=false`;
- missing-field and defect checks performed;
- duplicates retired;
- Delete Queue rows created;
- fields still missing or blocked;
- any safety concerns.

If a connector safety block prevents writing long runtime JSON directly, provide an Airtable Scripting Extension snippet or defer the update into an operator-approved tool package rather than storing secret values or bypassing safety controls.
