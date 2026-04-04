DCOIR Parity Verification And README Refresh - 2026-04-04

Current state id: 2026-04-04-session-start-bootstrap-and-prompt-review-v1

Purpose
- This log records the bounded installed-skill parity review and README refresh pass performed alongside the session-start bootstrap update set.

Parity review summary
- The current governed canonical parity surface remains `dcoir_skills/skill_parity_manifest.json` with `baseline_origin` recorded as `installed_skill_tree`, which indicates the manifest was built from the installed skill tree and used as the current parity baseline.
- The current governed parity surface reports `verified-installed-tree` status for the governed DCOIR skill set, so no broad cross-skill installed-versus-governed drift was surfaced before this update set was prepared.
- For this next bundle, the affected-skill source set was refreshed locally and the updated affected skill packages were rebuilt for `dcoir-session-tracker`, `dcoir-plan-tracker`, `dcoir-session-resume`, and `dcoir-memory-preflight`.
- The next governed parity refresh should happen after this update bundle lands so the canonical parity manifest and summary reflect the new governed source for those affected skills.

README review summary
- Reviewed `README.md`, `dcoir_skills/README.md`, `project_sources/README.md`, and `knowledge/README.md` for alignment to the current working line.
- Root `README.md` should be refreshed to mention the first-turn bootstrap pair and the current GitHub Desktop manual-update posture more precisely.
- `dcoir_skills/README.md` should be refreshed to mention the first-turn bootstrap pair and the bounded local-JSON startup-preflight scope for `dcoir-session-tracker` and `dcoir-plan-tracker`.
- `project_sources/README.md` and `knowledge/README.md` were reviewed and do not require a material refresh in this bundle.

Why it matters
- The parity surface should stay trustworthy and explicit so helper-skill drift is not guessed from memory.
- README surfaces should reflect the current visible governed working line, not lag behind recent workflow changes.

Next immediate move
- Land the affected skill-source, control-plane, and README changes in one grouped governed update, then refresh the canonical parity manifest and summary against the newly governed source set.
