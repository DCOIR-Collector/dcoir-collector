# AGENTS.md

## Purpose
This repository is the governed GitHub source for the DCOIR collector, Gemini-related source surfaces, workflows, operator tooling, and durable documentation.

## Authority model
- GitHub is canonical for source code, workflows, operator tools, architecture notes, release history, and durable operating guidance kept in the repository.
- The `ircore` operating model governs routing, validation, reuse, and continuity decisions for the current agent/system design.
- Legacy Airtable material may still appear in historical or migration-oriented files, but it is not the default startup authority for current repo guidance.

## Working rules
- Keep changes small, reviewable, and scoped to the task.
- Do not reintroduce the retired always-on `dcoir-*` helper-skill gate.
- Do not treat removed skill-mirror or parity artifacts as active dependencies.
- Preserve DCOIR naming where it is part of the product, collector, repo, or historical lineage.

## Validation
- When editing code or workflows, run the closest available validation and report any gaps.
- When editing documentation, scan for stale path references and mismatched authority claims before finishing.
- Treat broken path references, stale startup guidance, and workflow assumptions about removed files as real defects.

## Cleanup posture
- Historical artifacts may remain when they are clearly evidence or release history.
- Active guidance, workflow validation, and support files must not depend on retired parity or skill-mirror surfaces.
