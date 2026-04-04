# DCOIR governed skill source root

Purpose
- This folder is the governed GitHub-readable source root for DCOIR helper-skill source intentionally stored in the repository.

Root rules
- Per-skill source folders live under `dcoir_skills/<skill-name>/`.
- Preserve the readable package layout for each skill.
- Exclude runtime residue such as `__pycache__/` and temporary outputs.
- Keep this README aligned to the current visible skill set and use the helper-skill routing note for the richer descriptive routing matrix.

Canonical helper-skill companion surfaces
- `dcoir_skills/project_discovery_contract.json` is the governed machine-readable discovery contract for current repo, control-plane, manifest-section, active-surface, and collector runtime-alias bootstrap assumptions that should not stay buried as code literals.
- `dcoir_skills/skill_parity_manifest.json` is the canonical machine-readable skill-parity surface.
- `dcoir_skills/skill_parity_summary.md` is the generated human-readable parity companion surface.

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

Current discovery-contract adoption line
- `dcoir-source-authority-auditor`, `dcoir-knowledge-doc-maintainer`, `dcoir-change-impact-analyzer`, and `dcoir-collector-qa` now read the shared discovery contract first instead of relying only on project-specific bootstrap literals embedded directly in code.
- Remaining skills and references still need later hard-coded-project-variable review where practical.

Companion guidance
- Use `knowledge/DCOIR_Helper_Skills_Routing_Note.md` for the richer current routing matrix and boundaries.
- Use the current control plane to determine which skills are materially current for a given working line.
