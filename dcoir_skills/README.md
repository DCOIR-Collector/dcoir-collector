# DCOIR governed skill source root

Purpose
- This folder is the governed GitHub readable source root for DCOIR helper-skill source that is intentionally stored in the repository.

Root rule
- Per-skill source folders live under `dcoir_skills/<skill-name>/`.
- Preserve the readable package layout for each skill.
- Exclude runtime residue such as `__pycache__/` and temporary outputs.

Initial governed batch
- `dcoir-memory-preflight`
- `dcoir-decision-policy`
- `dcoir-plan-tracker`
- `dcoir-session-tracker`
- `dcoir-skill-regression-auditor`
