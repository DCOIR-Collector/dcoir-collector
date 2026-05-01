---
name: dcoir-local-config-registry-maintainer
description: maintain africom_soc_ir / dcoir Local Configuration Registry rows in Airtable. Use when local/system environment variable names, safe reference guidance, config row deduplication, missing runtime references, secret-handling flags, config defaults, or Delete Queue cleanup for Local Configuration Registry records are involved.
---

<!-- skill-marker: updated-skill|20260501T224500Z|local-config-registry-maintainer|new-skill|dcoir-local-config-registry-maintainer|SKILL.md -->

# DCOIR Local Configuration Registry Maintainer

## Project gate
Use this skill only inside AFRICOM_SOC_IR / DCOIR work. Airtable is operational authority for Local Configuration Registry records. GitHub remains governed source/readback for helper-skill source and reusable tool code only when repository readback, packaging, or parity work requires it.

## Purpose
Use this skill to keep Airtable `Local Configuration Registry` clean, safe, and useful for operator-side tools. The table stores configuration names and safe reference guidance only. It must never store token values, API key values, secret values, project id values, or other credential material.

## Hard rules
- Store environment variable names and safe reference expressions only.
- Never store, ask for, print, log, or package actual values for API keys, tokens, secrets, or project identifiers.
- Treat `Local Configuration Registry` as one active canonical row per `config_name`.
- If duplicates exist, choose one canonical row, mark duplicates `retired`, and queue duplicate deletion through `Delete Queue`; do not directly delete unless the operator explicitly authorizes immediate deletion and dependency order is safe.
- Use live Airtable schema readback before writes or Delete Queue staging.
- Fill missing reference fields whenever the schema contains them.
- Set `safe_to_display=false` for sensitive values such as tokens and API keys.
- Set `sensitive_value=true` for API keys, tokens, secrets, passwords, and credentials.
- Use `confirmed_present=true` only after the operator confirms the Machine/System environment variable exists or after an approved local smoke test proves it.

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
2. Read relevant Local Configuration Registry rows by `config_name` or by a focused table display/search.
3. Normalize the active canonical row:
   - complete all reference fields that exist in the current schema;
   - use `api_key` for OpenAI/API keys, `token` for GitHub/Airtable tokens, `project_id` for project identifier variables, `directory_path` for local folders, and `repository_path` for repo roots;
   - set status to `active` for current confirmed variables and `planned` only before operator confirmation.
4. Detect duplicates:
   - same `config_name` with more than one row;
   - older planned rows after a newer confirmed row exists;
   - rows with incomplete safety flags superseded by a complete canonical row.
5. Retire duplicates before deletion:
   - set `status=retired`;
   - add notes naming the canonical row;
   - create Delete Queue rows with `target_table=Local Configuration Registry`, `target_record_id=<duplicate record id>`, and a clear reason.
6. Summarize canonical rows, retired duplicate rows, queued deletion keys, and any blocked fields.

## Runtime reference generation
When filling `reference_additional_runtimes_json`, use a compact JSON object. For a variable named `VAR_NAME`, use the pattern in `references/runtime_reference_patterns.md` and replace `VAR_NAME` exactly.

## Output contract
Return a compact table with:
- canonical rows updated;
- duplicates retired;
- Delete Queue rows created;
- fields still missing or blocked;
- any safety concerns.

If a connector safety block prevents writing long runtime JSON directly, provide an Airtable Scripting Extension snippet or defer the update into an operator-approved tool package rather than storing secret values or bypassing safety controls.
