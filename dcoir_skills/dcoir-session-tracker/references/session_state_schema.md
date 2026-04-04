# Session state schema

## Exported markdown structure

Use this exact high-level structure when exporting session state.

```markdown
---
artifact_type: dcoir-session-state
schema_version: 4
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
- [ID] title
  - status: open
  - provenance: current_chat
  - detail: full context line that makes the item understandable in isolation
  - why: why it matters
  - next_action: next useful action
  - carry_forward_note: [optional]
  - promotion_target: [optional]
  - related: [optional comma-separated list]

### candidate_log01
- [ID] ...

### candidate_log02
- [ID] ...

### candidate_log03
- [ID] ...

### durable_preference_candidate
- [ID] normalized rule
  - persistence_status: promotion_candidate
  - detail: what the preference means in practice
  - next_action: what should be patched or preserved

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

## Staged governed updates
- [optional list]

## Staged todo actions
- [optional list]

## Post-push cleanup
- [optional list]

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

## Verbosity rule
Use the verbose item shape by default for materially important items.
Do not collapse those items to a one-line form when the operator would lose continuity or resume clarity.

## Minimum item fields
A materially important item should preserve:
- `id`
- `title`
- `detail`
- `why`
- `next_action`
- `status`
- `provenance`

Recommended fields when relevant:
- `operator_language`
- `impact_if_missed`
- `desired_outcome`
- `promotion_target`
- `carry_forward_note`
- `related`
- `buffer_state`
- `persistence_status`
- `flush_trigger`

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
