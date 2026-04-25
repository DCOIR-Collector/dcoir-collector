<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-skill-regression-auditor|airtable_memory_workflow.md -->

# Airtable memory workflow

Use the dedicated Airtable memory table for live durable helper memory after T2.0 cutover.

## Live memory target
- Query `dcoir-skill-regression-auditor` when it exists.
- Use repo `dcoir_skill_memory/` files only as source-basis history for migrated rows or historical comparison.
- Do not use `Skill State Registry` as a replacement for per-skill durable memory tables.

## Update rule
- Add or update Airtable memory rows after a validated reusable lesson, blocker recovery, regression finding, or durable workflow rule.
- Preserve source-basis paths when a row was migrated from GitHub memory files.
- Do not write routine queue churn to GitHub memory files.

## Required checks
- Confirm the table exists in `Skill State Registry` before treating Airtable memory as live for that skill.
- If Airtable access is blocked, state the block and provide the smallest bounded manual action.
- Keep GitHub governed readable sources for control-plane files and promoted release history; keep Airtable as live execution and memory state.
