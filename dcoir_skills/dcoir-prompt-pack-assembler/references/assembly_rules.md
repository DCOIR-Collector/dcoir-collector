# Assembly Rules

The assembler is valid only when the current GitHub-primary `project_sources/` root contains exactly one PP-01 through PP-07 modular set and the current control-plane files resolve cleanly.

## Canonical order
1. system
2. output_schema
3. baseline_triage
4. enrichment_review
5. retrieved_artifact_review
6. final_case_synthesis
7. guardrails

## Discovery rules
- `PP-01_*` -> system
- `PP-02_*` -> output_schema
- `PP-03_*` -> baseline_triage
- `PP-04_*` -> enrichment_review
- `PP-05_*` -> retrieved_artifact_review
- `PP-06_*` -> final_case_synthesis
- `PP-07_*` -> guardrails
- ignore `PP-08_*`, `PP-09_*`, and `PP-10_*`
