# DCOIR Skill Memory Layout

This note records the current helper-memory layout for the AFRICOM_SOC_IR / DCOIR project.

Current canonical per-skill memory files
- `dcoir_skill_memory/dcoir-session-tracker/session_tracker_state.md`
- `dcoir_skill_memory/dcoir-decision-policy/decision_policy_memory.md`
- `dcoir_skill_memory/dcoir-collector-qa/collector_qa_memory.md`
- `dcoir_skill_memory/dcoir-validation-orchestrator/validation_orchestrator_memory.md`
- `dcoir_skill_memory/dcoir-skill-regression-auditor/skill_regression_memory.md`
- `dcoir_skill_memory/dcoir-live-test-remediation-planner/live_test_remediation_memory.md`

Rules
- Re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing these files.
- Treat these files as helper working memory only, not control-plane authority.
- Keep one canonical markdown memory file per skill unless the operator explicitly wants snapshots or history.
- Keep these files continuously updated after material helper-state changes when the GitHub connector is available.
