# WBS06.03 deletion-readiness packet

Packet date: 2026-05-20
Plan: PLAN-AIRTABLE-DB-REDESIGN-20260508
Branch: DBREDESIGN-WBS-06.03
Scope: deletion-readiness planning for WBS06 legacy/review-marked Airtable fields.

## Authority and safety posture

This packet is planning-only. It does not approve or execute Airtable field deletion.

Source evidence:
- `exec-20260520-wbs06-final-verify-retirement-packet-001`
- WBS06 final verification result: success
- Tables analyzed: 21
- Fields inventoried: 332
- Expected rename readbacks verified: 14 / 14
- Retirement packet candidates: 12
- Final verification performed no Airtable writes, no field renames, no record updates, no field deletion, no type conversion, and no Delete Queue rows.

Important boundary:
- Airtable Delete Queue is for record/row deletion, not schema field deletion.
- Any field deletion requires a separate destructive schema-action approval and live schema/readback verification immediately before execution.
- Fields with nonblank values are not deletion-ready in this packet.

## Summary classification

| Classification | Count | Meaning |
|---|---:|---|
| deletion-ready after final dependency check | 10 | Fully blank in final WBS06 export; no observed values; still requires dependency/readback check before destructive field deletion. |
| preserve / special review | 2 | Nonblank values observed; do not delete without replacement/parity and explicit destructive approval. |

## Deletion-ready after final dependency check

These fields were fully blank in the final WBS06 evidence export. They are candidates for a later destructive deletion approval packet, subject to live schema/dependency readback.

| Table | Table ID | Field ID | Field name | Type | Records | Blank | Nonblank | Blank ratio | Recommendation | Approval gate |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| GitHub Workflow Inventory | `tblHTf5bLKGK1Yk11` | `fldhfcwoRfNHkL1ya` | `legacy_review_after_date_review` | date | 24 | 24 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Idea Inbox | `tblWwBxwrjZF6JR3r` | `fldXRAz2DLHzOQmK2` | `legacy_source_checkpoint_id_review` | singleLineText | 9 | 9 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Plans | `tblBcp5FyMIfOm7Xe` | `fldvsVffETaqyuB0H` | `legacy_active_plan_task_id_review` | singleLineText | 2 | 2 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Plans | `tblBcp5FyMIfOm7Xe` | `fldwS46tOH9fTVQSO` | `legacy_created_at_review` | dateTime | 2 | 2 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Plans | `tblBcp5FyMIfOm7Xe` | `fldyfFi5VTw9ffaPq` | `legacy_pending_plan_buffer_items_review` | multilineText | 2 | 2 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Plans | `tblBcp5FyMIfOm7Xe` | `fldLYnjrlPY6QfKNH` | `legacy_plan_buffer_marker_review` | singleLineText | 2 | 2 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Plans | `tblBcp5FyMIfOm7Xe` | `fld4QqRiSFLzEvKuD` | `legacy_promotion_candidates_review` | multilineText | 2 | 2 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Plans | `tblBcp5FyMIfOm7Xe` | `fldzT3tVTcvhSWPNa` | `legacy_remain_local_notes_review` | multilineText | 2 | 2 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Plans | `tblBcp5FyMIfOm7Xe` | `fldCC1FicmWE2pra2` | `legacy_review_after_date_review` | date | 2 | 2 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |
| Validation Evidence | `tblrPFQH2uZEYBYE9` | `fldOIWWUP1cPo9zEb` | `legacy_release_key_review` | singleLineText | 153 | 153 | 0 | 1.0 | Delete candidate after dependency check. | WBS06.03 destructive approval packet required. |

## Preserve / special review

These fields contain values in the final evidence export and must not be deleted as part of a simple blank-field cleanup.

| Table | Table ID | Field ID | Field name | Type | Records | Blank | Nonblank | Blank ratio | Observed values | Recommendation | Approval gate |
|---|---|---|---|---|---:|---:|---:|---:|---|---|---|
| Gemini Research Reference | `tblfZnARJxcMJ0yHW` | `fldH0t18dHVNkfTrA` | `legacy_research_batch_review` | singleLineText | 76 | 0 | 76 | 0.0 | `DR-2026-04-22-T3.9.2`; `DR-2026-04-22-01`; `DR-2026-04-21-02`; `DR-2026-04-21-01`; `DR-2026-04-21-03` | Preserve for history or run a separate replacement/parity/dependency packet against `research_batch_select`. | Separate nonblank-field approval packet required. |
| Plans | `tblBcp5FyMIfOm7Xe` | `fldZoUV6BFJyKuOhz` | `legacy_last_updated_text_review` | singleLineText | 2 | 0 | 2 | 0.0 | `2026-05-03T11:10:00+02:00`; `2026-05-11T06:50:00Z` | Preserve until structured replacement/readback confirms these timestamps are redundant. | Separate nonblank-field approval packet required. |

## Required checks before any destructive field deletion

Before any field deletion is executed, run a separate WBS06.03 destructive approval workflow that confirms:

1. Live schema still contains the target field IDs and expected names.
2. Target fields are still blank at execution time, except fields explicitly handled by a nonblank preservation/parity packet.
3. No formulas, views, scripts, helper skills, GitHub workflows, Airtable automations, operator tools, or registry rows reference the field names/IDs.
4. A rollback posture exists: exported schema/record evidence is retained, and deletion is explicitly acknowledged as destructive.
5. The operator approves exact table/field deletion list.

## Recommended next action

Prepare a WBS06.03 destructive approval packet for the 10 fully blank candidates only. Keep the 2 nonblank candidates out of the destructive batch unless a separate parity/replacement packet is approved.
