# WBS22 Wave 2 discovery from exporter

Generated UTC: 2026-05-08T09:58:26Z

## Scope

Discovery/proposal-only. No Airtable writes, deletes, schema changes, GitHub source changes, skill changes, workflow changes, duplicate/merge work, Delete Queue processing, record deletion, scaffold disposition, or cosmetic cleanup.

## Metrics

- selected_table_count: 21
- total_records_exported: 1470
- candidate_record_count: 245
- immediate_wave2_candidate_count: 5
- deferred_candidate_count: 240
- table_access_failure_count: 0

## Immediate Wave 2 candidates

- Session Checkpoints / recE2rlJmLbK215vJ / SESSION-CHECKPOINT-20260428-GATEB-ARCHITECTURE-APPROVED: stale_reference_in_resume_prompt
- Session Checkpoints / recMIbSGkvIzw01V0 / SESSION-CHECKPOINT-20260428-HOUSEKEEPING-DESIGN-ANCHOR-PREGATEA: stale_reference_in_resume_prompt
- Session Checkpoints / recP6kJ9QxXOwFYyc / SESSION-CHECKPOINT-20260428-GATED-TABLE-CONSOLIDATION-DECISIONS: stale_reference_in_resume_prompt
- Session Checkpoints / recV1RQOgLw0FmTlu / CHK-20260424-SESSION-CLOSEOUT-001: stale_reference_in_resume_prompt
- Plans / recoLHyurY4OZx3K8 / PLAN-AIRTABLE-CLEANUP-RESTRUCTURE: active_task_id_mismatch active_task_id=CLEANUP-WBS-22-04 active_plan_task_id=CLEANUP-WBS-08-01; stale_reference_in_active_plan_task_id

## Deferred candidates

Deferred candidates are reported for review only and are not approved for bulk Wave 2 mutation.

## Next recommended move

Prepare an exact Wave 2-safe update payload only for immediate_wave2_* candidates after write-gate review. Do not mutate deferred candidates in bulk.
