---
name: dcoir-airtable-schema-cache
description: cache, normalize, inspect, compare, and refresh africom_soc_ir / dcoir airtable schema readback during startup, re-anchor, resume, task-time Airtable work, and schema-sensitive cleanup. use immediately when dcoir work mentions Airtable tables, fields, ids, select options, linked records, filters, searches, Delete Queue, cleanup, migration, merge/dedupe, taxonomy, naming/id standards, scripts using Airtable fields, or any write/delete/readback that depends on current schema.
---

<!-- skill-marker: updated-skill|20260505T074500Z|task-time-schema-gate-strengthening|in-session-update|dcoir-airtable-schema-cache|SKILL.md -->

<!-- skill-marker: updated-skill|20260504T181500Z|cache-scope-narrowing-stale-reference-scrub|source-update|dcoir-airtable-schema-cache|SKILL.md -->

<!-- skill-marker: updated-skill|20260504T171500Z|airtable-local-cache-contract|source-update|dcoir-airtable-schema-cache|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T111500Z|airtable-display-allowed-when-useful|source-update|dcoir-airtable-schema-cache|SKILL.md -->
<!-- skill-marker: updated-skill|20260429T203000Z|startup-reanchor-schema-cache|source-update|dcoir-airtable-schema-cache|SKILL.md -->

# DCOIR Airtable Schema Cache

## Project gate
Use this skill only inside AFRICOM_SOC_IR / DCOIR work. The current authority model is Airtable-first operational authority with Project Instructions and CP-00 as bootstrap pointers, Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST` as startup authority, and GitHub as governed source/readback only when source, packaging, or promoted-history tasks require it.

## Purpose
Use this skill to reduce repeated Airtable schema-discovery roundtrips while preserving the project's hard rule: live schema readback is required before assuming a table, field, select option, or dependency path exists.

This skill now has two roles:
- startup/re-anchor schema readiness: refresh or validate a local schema cache immediately after `dcoir-session-manager` and `dcoir-memory-preflight` during DCOIR startup or re-anchor.
- task-time schema assistance: provide fast table/field lookup, field-type checks, select-option checks, linked-record awareness, and drift warnings during normal Airtable work.

This skill produces and consumes a local JSON schema cache. Treat the cache as a speed aid and decision aid, not as write authority.

## Task-time schema gate
Use this skill before DCOIR Airtable work whenever table, field, select-option, linked-record, filter/sort, formula/id, naming/taxonomy, searchability, merge/dedupe, cleanup, migration, Delete Queue, validation evidence, registry, or helper-memory schema assumptions could affect correctness.

Frequent-fire rule: if a task will read, search, display, create, update, queue, delete, migrate, merge, deduplicate, validate, or script against Airtable data and the current live schema was not checked in this turn for the relevant surface, run a compact schema gate first. Prefer a small schema check over relying on memory.

The compact schema gate should identify:
- target table(s) and table id(s) when known;
- needed field ids, field types, select choices, linked-record targets, formula fields, and primary fields;
- whether cached schema is fresh enough for read-only lookup;
- whether fresh live schema readback is mandatory before the next action;
- any missing/renamed/retired table or field assumption;
- safest next Airtable operation or stop condition.

Hard triggers:
- before Airtable writes, deletes, schema changes, migrations, cleanup passes, merge/dedupe plans, Delete Queue work, or dependency-sensitive actions;
- before building code, formulas, filters, sorting, validators, or workflows that depend on Airtable field names/ids/types/options;
- when a connector/API call fails because a table/field/filter/select option might be wrong;
- when dcoir-memory-preflight routes a task to Airtable/schema/cache handling;
- when a future session asks about table-by-table cleanup, controlled vocabularies, naming/id conventions, or searchability.

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
Invoke this skill during the first substantive AFRICOM_SOC_IR / DCOIR turn of a session and during explicit re-anchor/resume requests, after `dcoir-session-manager` and `dcoir-memory-preflight` and before broad Airtable table reads.

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
1. During startup or re-anchor, run schema readiness automatically when the Project Instructions or CP-00 sequence invokes this skill. During normal task work, run the compact schema gate whenever Airtable schema assumptions could materially affect correctness; then decide whether cache lookup, targeted live schema readback, or full live schema refresh is needed.
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
Routine cache scope is intentionally narrow: cache only the high-call tables named as routine in the contract; use live Airtable reads for conditional tables.

This skill is Airtable-backed only for the high-call routine tables named in `references/airtable_cache_contract.md`. Read that contract before relying on cached helper-memory, routing, preference, validation, packaging, or configuration-name state.

On every explicit DCOIR re-anchor/startup recovery/resume-first recovery, refresh or recreate only the routine caches named in the contract. If a routine cache is missing, unreadable, stale, or inconsistent with live schema/table identity, refresh before use. Tables listed as conditional/live-read are not routine caches; read them from live Airtable only when the active task requires them. After this skill writes to a routine cached table, refresh the cache and verify the contract-defined freshness indicator. Local cache is advisory only; live Airtable remains authority for writes, deletes, migrations, and dependency-sensitive decisions.

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
- whether another DCOIR skill should be invoked before execution

## References
Read `references/cache_contract.md` for the full cache contract.
Read `references/current_operational_tables.json` for the current operational table expectation set.
Read `references/task_time_schema_gate.md` for compact task-time trigger and output rules.
