# Startup Active Plan Recovery Workflow

Use this workflow only after `dcoir-session-resume`, `dcoir-memory-preflight`, and `dcoir-session-tracker` startup leftover recovery.

## Purpose
Recover Airtable-backed active plan state when unfinished plan work exists, without forcing plan-tracker into sessions that have no open plan carry-forward.

## Tables
- base id: `appM4KSwnVf3G3OTK`
- `Plans`: `tblBcp5FyMIfOm7Xe`
- `Plan Tasks`: `tblsATLIDeh6gtcoM`
- `Plan Checkpoints`: `tbl6z4Lyai2RABMyw`

## Recovery sequence
1. Read `Plans` rows where `plan_state` is one of `draft`, `approved_to_execute`, `active`, `blocked`, or `paused`.
2. If multiple open plans exist, prefer the most recently updated row unless the control plane or session-tracker leftover scan points to a different plan.
3. Read the matching `Plan Tasks` rows for that plan.
4. Read the newest relevant `Plan Checkpoints` rows for that plan.
5. Surface the active task, current blocker state, pending promotion candidates, and one best next move.
6. Only after Airtable-backed plan state is understood should local `plan_state.json` cache proof or refresh work matter.

## Truth rules
- Do not trust missing local cache as proof that plan continuity was lost when Airtable remains current.
- Do not force plan recovery when no open or active Airtable-backed plan state exists.
- Distinguish governed GitHub tracker files from Airtable live execution state and from transient local cache.
