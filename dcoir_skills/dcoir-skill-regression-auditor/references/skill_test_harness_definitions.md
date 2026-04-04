# Skill Test Harness Definitions

## Common checks
- package validation
- representative command execution where scripts exist
- success-path output verification
- failure-gate verification
- regression rerun after patch
- current-control-plane narrative-manifest fixture check when the skill reads project state
- helper-memory update or readback check when the skill persists governed helper state
- grouped campaign coverage check when more than one materially changed skill is in scope

## Output verification rule
When a skill emits files, inspect the file presence and the content cues that matter for the contract. Do not rely on a zero exit code alone.

## Campaign sequencing rule
When the project is scanning or patching multiple `dcoir-*` skills, validate `dcoir-skill-regression-auditor` first, then use the same refreshed fixture language and failure gates across the remaining skills.

## Coordinated campaign expectation
For a bounded multi-skill campaign, the regression plan should make these explicit:
- self-first validation when this skill is in the changed set
- per-skill success path
- per-skill failure gate
- per-skill artifact verification
- grouped readiness summary
- any explicitly untested or bounded portions of the campaign
