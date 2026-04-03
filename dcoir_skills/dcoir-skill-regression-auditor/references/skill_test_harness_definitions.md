# Skill Test Harness Definitions

## Common checks
- package validation
- representative command execution where scripts exist
- success-path output verification
- failure-gate verification
- regression rerun after patch
- current-control-plane narrative-manifest fixture check when the skill reads project state
- helper-memory update or readback check when the skill persists governed helper state

## Output verification rule
When a skill emits files, inspect the file presence and the content cues that matter for the contract. Do not rely on a zero exit code alone.

## Campaign sequencing rule
When the project is scanning or patching multiple `dcoir-*` skills, validate `dcoir-skill-regression-auditor` first, then use the same refreshed fixture language and failure gates across the remaining skills.
