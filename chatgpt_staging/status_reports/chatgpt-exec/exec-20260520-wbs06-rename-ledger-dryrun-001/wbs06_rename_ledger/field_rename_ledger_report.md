# WBS06 field rename ledger dry run

- request_id: exec-20260520-wbs06-rename-ledger-dryrun-001
- result: success
- safety: read-only Airtable export and analysis; no Airtable writes, field renames, record updates, Delete Queue rows, or deletions
- tables analyzed: 21
- fields analyzed: 332
- already applied rename markers: 6
- rename candidates: 5
- protect/review/table-empty rows: 321

## Output files

- field_rename_ledger.json
- field_rename_ledger.csv
- field_rename_ledger_summary.json
- table_inventory_summary.json
- source_export_manifest.json
- source_run_summary.json

## Top rename candidates

| Table | Field ID | Current name | Proposed name | Blank ratio | Reason |
|---|---|---|---|---:|---|
| Gemini Research Reference | fldH0t18dHVNkfTrA | legacy_research_batch__do_not_use | legacy_research_batch_review | 0 | Name contains double-underscore or do-not-use marker; normalize to WBS06 single-underscore legacy review convention. |
| GitHub Workflow Inventory | fldNGAE9cbd9YSYzz | do_not_use_when | legacy_do_not_use_when_review | 0 | Name contains double-underscore or do-not-use marker; normalize to WBS06 single-underscore legacy review convention. |
| GitHub Workflow Inventory | fldhfcwoRfNHkL1ya | review_after | legacy_review_after_review | 1 | Field is fully blank in current full-record export and name does not obviously carry protected governance/provenance meaning. |
| Idea Inbox | fldyhuC1RXb6TQBu3 | promoted_to_github | legacy_promoted_to_github_review | 1 | Field is fully blank in current full-record export and name does not obviously carry protected governance/provenance meaning. |
| Plans | fldCC1FicmWE2pra2 | review_after | legacy_review_after_review | 1 | Field is fully blank in current full-record export and name does not obviously carry protected governance/provenance meaning. |

## Already applied seed renames

| Table | Field ID | Old name | Current name |
|---|---|---|---|
| Plans | fldvsVffETaqyuB0H | active_plan_task_id | legacy_active_plan_task_id_review |
| Plans | fldZoUV6BFJyKuOhz | last_updated_text | legacy_last_updated_text_review |
| Plans | fldyfFi5VTw9ffaPq | pending_flush_items | legacy_pending_plan_buffer_items_review |
| Plans | fldLYnjrlPY6QfKNH | flush_trigger | legacy_plan_buffer_marker_review |
| Plans | fld4QqRiSFLzEvKuD | promotion_candidates | legacy_promotion_candidates_review |
| Plans | fldzT3tVTcvhSWPNa | remain_local_notes | legacy_remain_local_notes_review |
