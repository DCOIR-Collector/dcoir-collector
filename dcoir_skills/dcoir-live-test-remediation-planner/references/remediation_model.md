# Remediation Model

This skill prioritizes what to fix first after DCOIR live testing and defines what must be re-tested before the repaired path is considered ready again.

## Priority intent
Choose the smallest truthful fix that removes the highest operational risk first.

Favor:
- issues that block operators from completing the workflow
- issues that create wrong or unsafe next-step guidance
- issues that could cause incorrect packaging or stale source-of-truth handling
- issues that are likely to recur unless encoded into a skill, prompt, or workflow artifact

## Delivery posture intent
Use the current delivery classes, not the retired coarse split alone.
- skill-only repairs may stay `targeted_skill_update`
- compatible multi-skill repairs should prefer `batched_skill_update_wave`
- governed repo-readable repairs should prefer `github_desktop_manual_repo_update_bundle`
- structural or broad project-upload repairs should escalate to `full_refresh_project_upload`
