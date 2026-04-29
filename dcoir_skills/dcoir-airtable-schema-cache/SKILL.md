---
name: dcoir-airtable-schema-cache
description: cache, normalize, inspect, and compare africom_soc_ir / dcoir airtable schema readback. use when dcoir work needs table ids, field ids, field types, select options, linked-record details, schema freshness checks, reduced airtable roundtrips, or a bounded schema snapshot before using airtable connectors, helper-memory tables, delete queue, lifecycle ledger, plans, work items, admin registry, repo surface registry, validation evidence, or local configuration registry.
---

# DCOIR Airtable Schema Cache

## Project gate
Use this skill only inside AFRICOM_SOC_IR / DCOIR work. The current authority model is Airtable-first operational authority with Project Instructions and CP-00 as bootstrap pointers, Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST` as startup authority, and GitHub as governed source/readback only when source, packaging, or promoted-history tasks require it.

## Purpose
Use this skill to reduce repeated Airtable schema-discovery roundtrips while preserving the project's hard rule: live schema readback is required before assuming a table, field, select option, or dependency path exists.

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

## Workflow
1. Decide whether a cache helps. Use this skill when schema lookup, table/field mapping, or repeated Airtable access is slowing the task or creating uncertainty.
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

## Output contract
Return:
- cache path and timestamp
- base id and table count
- requested table/field ids and field types
- missing/retired table assumptions, if any
- stale-cache or live-readback-required warnings
- safest next Airtable operation

## References
Read `references/cache_contract.md` for the full cache contract.
Read `references/current_operational_tables.json` for the current operational table expectation set.
