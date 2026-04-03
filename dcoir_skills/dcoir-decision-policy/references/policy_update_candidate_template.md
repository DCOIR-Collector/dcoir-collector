# Policy Update Candidate Template

Use this template when a newly learned operator preference should persist beyond the current conversation.

## Required fields

- Rule title:
- Trigger condition:
- Default action:
- Scope:
- Why this should persist:
- Source of learning:
- Conflicts with existing rule:
- Recommended persistence target:
  - skill update
  - project-readable policy/control file update
  - both

## Example

- Rule title: structural changes default to full-refresh
- Trigger condition: a requested change is renamed, broad, or touches multiple interdependent files
- Default action: choose full-refresh bundle unless the operator explicitly says local-only testing
- Scope: durable
- Why this should persist: reduces repeated clarification and matches existing operator preference
- Source of learning: direct operator answer in chat
- Conflicts with existing rule: none
- Recommended persistence target: both
