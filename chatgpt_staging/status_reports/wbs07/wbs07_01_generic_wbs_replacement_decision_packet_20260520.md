# WBS07.01 generic WBS replacement decision packet

Packet date: 2026-05-20
Plan: PLAN-AIRTABLE-DB-REDESIGN-20260508
Active branch: DBREDESIGN-WBS-07.01

## Decision

Create a replacement generic WBS table instead of directly renaming `DCOIR Cleanup WBS`.

Recommended target table name: `DCOIR Execution WBS`.

This is a decision/approval packet only. It does not create, rename, replace, migrate, prefix, or delete any Airtable table.

## Why replacement beats direct rename

1. The current table name is plan-scoped: `DCOIR Cleanup WBS`.
2. The table is now being used as a reusable execution decomposition model, not only cleanup scaffolding.
3. Prior WBS design notes already established the safer pattern: create replacement -> migrate/update references -> retire the old cleanup-named table after readback.
4. Replacement gives us a clean table description, generic field descriptions, and a clean future role without losing historical traceability.
5. Direct rename would preserve the same table id and could leave old table-role evidence, view manifests, and historical references ambiguous.

## Live Airtable evidence

Current source table:

| Item | Value |
|---|---|
| Source table | `DCOIR Cleanup WBS` |
| Source table id | `tblRxTmpW0VunQlUK` |
| Primary field | `wbs_key` / `fldxysOTwPhA0fk9b` |
| Current record count | 73 |
| Current active WBS rows | `DBREDESIGN-WBS-07`, `DBREDESIGN-WBS-07.01` |
| Current hierarchy model | Text-key based: `wbs_key`, `wbs_path`, `parent_wbs_key` |
| Linked-record dependency found in live schema | None found directly into this table during WBS07.01 schema readback |

The current table description says it is a plan-scoped WBS table for the DCOIR Airtable Cleanup and Restructuring Plan. That confirms the naming is still tied to this cleanup plan rather than a generic reusable execution-WBS role.

## Existing table role evidence

Admin Registry contains an active table-role row for the current table:

| Item | Value |
|---|---|
| Registry key | `ADM-DBREDESIGN-WBS10-01-TABLE-ROLE-DCOIR-CLEANUP-WBS-20260509` |
| Object name | `WBS10.01 table role: DCOIR Cleanup WBS` |
| Owning table | `DCOIR Cleanup WBS` |
| Current role | Plan-scoped database redesign WBS |
| Authority level noted | `plan_breakdown` |
| Does not belong there | General DCOIR queue, unrelated work items, validation proof records, lifecycle event logs |

This row should be updated or superseded during the replacement-table migration, not silently left pointing at the old cleanup-named table.

## Scaffold registry evidence

`DCOIR Cleanup Scaffold Registry` currently has zero records by live Airtable readback. There is no scaffold-registry row to migrate at this time.

## Repo/source reference evidence

Repo search for the current table id `tblRxTmpW0VunQlUK` found references in these source categories:

| Category | Examples | Disposition |
|---|---|---|
| Current operator tooling manifests | `operator_tools/github_desktop_lane/manifests/wbs09_view_manifest_summary.csv`; `operator_tools/github_desktop_lane/manifests/wbs09_airtable_native_views_manifest.json`; `operator_tools/github_desktop_lane/manifests/wbs09_airtable_capability_map.generated.json` | Must be reviewed/updated if the replacement table becomes active. |
| Historical chatgpt-exec/status artifacts | `chatgpt_staging/status_reports/chatgpt-exec/.../records/table.DCOIR_Cleanup_WBS_tblRxTmpW0VunQlUK.records.json`; export manifests and schema summaries | Preserve as historical evidence; do not rewrite unless a future cleanup policy says otherwise. |
| WBS04/WBS06 generated scripts and readback artifacts | Export and inventory scripts/reports that referenced the old table for already-completed work | Historical only; no active runtime update needed unless reused. |

## Recommended replacement table structure

Create `DCOIR Execution WBS` with the current useful field model, generalized descriptions, and the same operational semantics.

Recommended carried fields:

| Field | Type | Migration rule |
|---|---|---|
| `wbs_key` | singleLineText | Preserve exact value. Primary field. |
| `plan_key` | singleLineText | Preserve exact value. |
| `wbs_path` | singleLineText | Preserve exact value. |
| `parent_wbs_key` | singleLineText | Preserve exact value. |
| `rank` | number | Preserve exact value. |
| `title` | singleLineText | Preserve exact value. |
| `level` | singleSelect | Preserve option names and values. |
| `surface` | singleSelect | Preserve option names and values. |
| `state` | singleSelect | Preserve option names and values. |
| `gate` | singleSelect | Preserve option names and values. |
| `target` | singleLineText | Preserve exact value. |
| `done_criteria` | multilineText | Preserve exact value. |
| `validation_notes` | multilineText | Preserve exact value. |
| `context` | multilineText | Preserve exact value. |
| `review_after` | date | Preserve exact value. |
| `display_label` | formula | Recreate equivalent formula after table creation. |
| `search_text` | formula | Recreate equivalent formula after table creation. |

Do not add linked-record hierarchy fields during this replacement wave. Keep the first replacement as a clean same-shape migration. Relationship redesign can remain under WBS11 or a later approved schema packet.

## Migration packet requirements for WBS07.03

Before any schema creation or row migration, WBS07.03 must provide:

1. Exact `create_table` payload for `DCOIR Execution WBS`.
2. Complete source-row count and target-row plan.
3. Mapping from every source field id/name to target field name/type.
4. Select option list parity for `level`, `surface`, `state`, and `gate`.
5. Formula text for `display_label` and `search_text`.
6. Source row export for all 73 rows.
7. Target-row creation payload with preserved keys and values.
8. Post-create verification: target table exists and fields match expected names/types/options.
9. Post-migration verification: 73 target rows, 73 unique `wbs_key` values, zero missing parent keys for child rows, and matching state/gate/path counts.
10. Reference-update packet for live Airtable rows and repo manifests that should point at the new table.
11. Old-table retirement packet: keep old table until replacement and reference readback pass, then prefix/retire or manually delete after approval.

## Reference-update requirements for WBS07.02

WBS07.02 should inventory exact references before WBS07.03 executes:

1. Live Airtable rows mentioning `DCOIR Cleanup WBS`, `tblRxTmpW0VunQlUK`, or `DBREDESIGN-WBS` in governance/registry/checkpoint/plan surfaces.
2. Admin Registry table-role row for `DCOIR Cleanup WBS`.
3. GitHub manifests under `operator_tools/github_desktop_lane/manifests/` that contain `DCOIR Cleanup WBS` or `tblRxTmpW0VunQlUK`.
4. Any active operator tool or workflow inventory row that routes by the old table name/id.
5. Historical `chatgpt_staging/status_reports` artifacts should be classified as evidence-only and not rewritten by default.

## Approval gate

Approval requested for this decision only:

- Approved decision: replacement path, not direct rename.
- Approved target name: `DCOIR Execution WBS`.
- Approved next non-destructive task: WBS07.02 reference inventory.
- Not approved yet: create table, migrate rows, update references, prefix old table, delete old table.

## Recommended next move

Move to WBS07.02: build the exact reference inventory for old table name/id and prepare the WBS07.03 migration packet. No schema mutation should occur before WBS07.03 is reviewed and approved.
