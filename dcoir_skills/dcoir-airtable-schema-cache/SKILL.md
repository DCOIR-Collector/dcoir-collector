---
name: dcoir-airtable-schema-cache
description: cache, normalize, inspect, compare, and refresh africom_soc_ir / dcoir airtable schema readback during startup, re-anchor, resume, and schema-sensitive Airtable work. use when dcoir work needs table ids, field ids, field types, select options, linked-record details, schema freshness checks, reduced airtable roundtrips, or a bounded schema snapshot before using airtable connectors, helper-memory tables, delete queue, lifecycle ledger, plans, work items, admin registry, repo surface registry, validation evidence, or local configuration registry.
---

<!-- skill-marker: updated-skill|20260504T171500Z|airtable-local-cache-contract|source-update|dcoir-airtable-schema-cache|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T111500Z|airtable-display-allowed-when-useful|source-update|dcoir-airtable-schema-cache|SKILL.md -->
<!-- skill-marker: updated-skill|20260429T203000Z|startup-reanchor-schema-cache|source-update|dcoir-airtable-schema-cache|SKILL.md -->

# DCOIR Airtable Schema Cache

## Project gate
Use this skill only inside AFRICOM_SOC_IR / DCOIR work. The current authority model is Airtable-first operational authority with Project Instructions and CP-00 as bootstrap pointers, Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST` as startup authority, and GitHub as governed source/readback only when source, packaging, or promoted-history tasks require it.

## Purpose
Use this skill to reduce repeated Airtable schema-discovery roundtrips while preserving the project's hard rule: live schema readback is required before assuming a table, field, select option, or dependency path exists.

This skill now has two roles:
- startup/re-anchor schema readiness: refresh or validate a local schema cache immediately after `dcoir-session-resume` and `dcoir-memory-preflight` during DCOIR startup or re-anchor.
- task-time schema assistance: provide fast table/field lookup, field-type checks, select-option checks, linked-record awareness, and drift warnings during normal Airtable work.

This skill produces and consumes a local JSON schema cache. Treat the cache as a speed aid and decision aid, not as write authority.

## Hard authority rules
- Never use a cache as the sole basis for writes, deletes, schema migrations, field-type changes, linked-record changes, or dependency-sensitive Delete Queue processing.
- Force fresh Airtable schema readback before any destructive operation, schema-sensitive write, migration, or uncertain table/field assumption.
- If cache and live schema disagree, prefer live schema and emit a schema-drift note.
- Do not store tokens, secrets, personal access tokens, webhook secrets, API keys, or hidden configuration values in the cache.
- Use `Local Configuration Registry` for configuration names and safe reference guidance only.
- Do not assume `Plan Tasks`, `Plan Checkpoints`, `Skill State Registry`, `Schema Registry`, `Tracking Registry`, `Repo File Coverage Detail`, or `Retained Repo Manifest` exist unless live schema readback proves they exist.

## Required Airtable source
Base id: `appM4KSwnVf3G3OTK`.

Preferred live schema source:
- Airtable connector `list_tables_for_base` for the base.
- Save or pass the returned JSON to `scripts/schema_cache.py build` when deterministic local lookup will help.

Known operational tables to verify when relevant:
- `Governance Control Plane`
- `Queue Control`
- `Work Items`
- `Plans`
- `Session Checkpoints`
- `Idea Inbox`
- `Operator Preferences`
- `Validation Test Cases`
- `Validation Evidence`
- `Repo Surface Registry`
- `Admin Registry`
- `Delete Queue`
- `DCOIR Lifecycle Ledger`
- `Local Configuration Registry`
- helper-specific `dcoir-*` memory tables where present

## Startup and re-anchor invocation
Invoke this skill during the first substantive AFRICOM_SOC_IR / DCOIR turn of a session and during explicit re-anchor/resume requests, after `dcoir-session-resume` and `dcoir-memory-preflight` and before broad Airtable table reads.

Startup intent:
1. Perform live Airtable schema readback or validate that a just-built cache is fresh enough for non-destructive lookup.
2. Build or refresh `/mnt/data/dcoir_airtable_schema_cache.json` when code execution and file writing are available.
3. Validate that the required operational tables are present and that retired tables are not assumed.
4. Make table IDs, field IDs, field types, select options, and linked-record details available for the rest of the session.
5. Report only compact schema readiness status unless the operator asks for details.

Startup output should be brief:
- cache refreshed or cache unavailable
- live table count
- missing required operational tables, if any
- retired table assumptions detected, if any
- live-readback-required warning for writes, deletes, or migrations

During automatic startup/re-anchor, keep schema readback compact and non-display by default. During execution, audit, cleanup, duplicate comparison, or verification, Airtable display views may be used when they materially improve correctness or when the operator has already approved visible Airtable display; summarize displayed evidence in chat.

## Workflow
1. During startup or re-anchor, run schema readiness automatically when the Project Instructions or CP-00 sequence invokes this skill. During normal task work, decide whether a cache helps when schema lookup, table/field mapping, or repeated Airtable access is slowing the task or creating uncertainty.
2. Call Airtable live schema readback when no current cache exists, the cache is stale, a write/delete/migration is planned, or the task is schema-sensitive.
3. Write the live schema JSON to a temporary file such as `/mnt/data/dcoir_airtable_schema_raw.json`.
4. Run `scripts/schema_cache.py build --schema-json /mnt/data/dcoir_airtable_schema_raw.json --output /mnt/data/dcoir_airtable_schema_cache.json`.
5. Use lookup commands for table IDs, field IDs, field types, select options, and linked-record fields.
6. Before write/delete/migration, run `freshness` and do live readback again if the cache age, source, or task risk requires it.
7. Surface only useful schema facts to the operator; do not dump large schema JSON unless asked.

## Commands
Build a cache from connector readback:
```bash
python scripts/schema_cache.py build --schema-json /mnt/data/dcoir_airtable_schema_raw.json --output /mnt/data/dcoir_airtable_schema_cache.json
```

Show a compact summary:
```bash
python scripts/schema_cache.py summary --cache /mnt/data/dcoir_airtable_schema_cache.json
```

Look up a table or field:
```bash
python scripts/schema_cache.py lookup --cache /mnt/data/dcoir_airtable_schema_cache.json --table "Delete Queue"
python scripts/schema_cache.py lookup --cache /mnt/data/dcoir_airtable_schema_cache.json --table "Work Items" --field "Status"
```

Check required operational tables:
```bash
python scripts/schema_cache.py validate-required --cache /mnt/data/dcoir_airtable_schema_cache.json
```

Compare two caches:
```bash
python scripts/schema_cache.py diff --old /mnt/data/schema_old.json --new /mnt/data/schema_new.json
```

## Airtable local cache contract
This skill is Airtable-backed and must maintain local cache files when file access is available. Read `references/airtable_cache_contract.md` before relying on helper-memory, routing, preference, validation, packaging, or configuration-name state.

On every explicit DCOIR re-anchor/startup recovery/resume-first recovery, refresh or recreate the cache for this skill's designated Airtable table set. If the cache is missing, unreadable, stale, or inconsistent with live schema/table identity, refresh before use. After this skill writes to its designated Airtable table(s), refresh the cache and verify the contract-defined freshness indicator. Local cache is advisory only; live Airtable remains authority for writes, deletes, migrations, and dependency-sensitive decisions.

## Operational table row-cache relationship
This skill's primary cache remains the Airtable schema cache created by `scripts/schema_cache.py`. It does not replace the row caches owned by the other skills. During re-anchor, this skill validates table/field identity needed by other skills before their designated row caches are trusted. When caching Admin Registry context for schema governance, use `references/airtable_cache_contract.md` and keep it separate from the schema cache.


## Output contract
Return:
- startup/re-anchor schema readiness status when invoked during startup
- cache path and timestamp
- base id and table count
- requested table/field ids and field types
- missing/retired table assumptions, if any
- stale-cache or live-readback-required warnings
- safest next Airtable operation

## References
Read `references/cache_contract.md` for the full cache contract.
Read `references/current_operational_tables.json` for the current operational table expectation set.
