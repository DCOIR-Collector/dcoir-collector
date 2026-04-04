# DCOIR governed skill source root

Purpose
- This folder is the governed GitHub-readable source root for DCOIR helper-skill source that is intentionally stored in the repository.

Root rules
- Per-skill source folders live under `dcoir_skills/<skill-name>/`.
- Preserve the readable package layout for each skill.
- Exclude runtime residue such as `__pycache__/` and temporary outputs.
- Keep this README aligned to the current visible skill set and use the helper-skill routing note for the richer descriptive routing matrix.
- `project_discovery_contract.json` is the governed machine-readable discovery surface for eligible current-project assumptions.
- `skill_parity_manifest.json` is the canonical machine-readable parity surface and `skill_parity_summary.md` is its generated human-readable companion.

Current governed helper-skill source set
- `dcoir-attention-signaler`
- `dcoir-change-impact-analyzer`
- `dcoir-collector-qa`
- `dcoir-decision-policy`
- `dcoir-knowledge-doc-maintainer`
- `dcoir-large-file-intake-manager`
- `dcoir-live-test-remediation-planner`
- `dcoir-memory-preflight`
- `dcoir-operator-workflow-hardener`
- `dcoir-parity-verifier`
- `dcoir-plan-tracker`
- `dcoir-prompt-pack-assembler`
- `dcoir-promotion-readiness-reviewer`
- `dcoir-readme-maintainer`
- `dcoir-release-scope-builder`
- `dcoir-repo-packager`
- `dcoir-session-resume`
- `dcoir-session-tracker`
- `dcoir-skill-regression-auditor`
- `dcoir-source-authority-auditor`
- `dcoir-structural-rename-coordinator`
- `dcoir-triage-to-collector-escalation-designer`
- `dcoir-validation-orchestrator`

Current operating notes
- On the first substantive AFRICOM_SOC_IR / DCOIR turn of every new session, use `dcoir-session-resume` first and `dcoir-memory-preflight` second before other substantive project work.
- The confirmed current DCOIR skills with real local JSON working-state files are `dcoir-session-tracker` and `dcoir-plan-tracker`.
- When one of those local-JSON skills is used in a new session, run its local JSON startup preflight first instead of assuming the file-backed local state is already present.
- Use only the affected skill zips or affected repo-relative files for manual deliveries unless the operator explicitly asks for a broader bundle.

Companion guidance
- Use `knowledge/DCOIR_Helper_Skills_Routing_Note.md` for the richer current routing matrix and boundaries.
- Use the current control plane to determine which skills are materially current for a given working line.
