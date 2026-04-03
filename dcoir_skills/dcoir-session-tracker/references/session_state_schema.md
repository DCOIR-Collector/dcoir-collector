# Session state schema

## Exported markdown structure

Use this exact high-level structure when exporting session state.

```markdown
---
artifact_type: dcoir-session-state
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-03-27T12:34:56Z
authority_basis:
  - CP-01_DCOIR_Version_Manifest.txt
  - CP-02_DCOIR_Change_Log.txt
merge_mode: merge
imports_merged:
  - prior_session_state.md
---

# DCOIR Session State

## Current phase
[short statement]

## Best next move
[one best next move]

## Close-out status
[short statement]

## Durability summary
- governed_github: [short statement]
- exported_handoff_only: [short statement]
- buffered_session_only: [short statement]
- unresolved_closeout_gap: [optional short statement]

## Open items
### session_only
- [ID] title — why it matters — next action

### candidate_log01
- [ID] ...

### candidate_log02
- [ID] ...

### candidate_log03
- [ID] ...

### durable_preference_candidate
- [ID] normalized rule — persistence status — next action

### new_skill_idea
- [ID] ...

### follow_on_validation
- [ID] ...

### blocked_or_needs_authority
- [ID] ...

## Completed or resolved this session
- [ID] ...

## Promotion-ready notes
### LOG-01 candidate text
[optional]

### LOG-02 candidate text
[optional]

### LOG-03 candidate text
[optional]

## Starter prompt for next session
[required when the operator is moving to another session]

## Close-out verification notes
- learned rules checked
- open tasks checked
- continuity/log surfaces checked
- remaining non-durable items called out

## Provenance notes
- imported artifact notes
- project-log grounding notes
- bounded assumptions
```

## ID guidance
Use short stable IDs such as:
- `S-001` for session-only
- `T-001` for LOG-01 candidates
- `L-001` for LOG-02 candidates
- `H-001` for LOG-03 candidates
- `P-001` for durable preference candidates
- `N-001` for new skill ideas
- `V-001` for follow-on validation
- `B-001` for blocked items

Keep IDs stable across merges when the same logical item persists.
