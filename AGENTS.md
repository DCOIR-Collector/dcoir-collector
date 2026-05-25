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

## Canonical connector targets
- Default GitHub `repository_full_name` for governed repo work here: `malwaredevil/dcoir-collector`
- Canonical GitHub repo URL: `https://github.com/malwaredevil/dcoir-collector/`
- Default Supabase `project_id` for `ircore` operational work here: `kdhkhyksdzjbajavsoxa`
- Unless the operator explicitly directs otherwise, use those exact connector-friendly values for GitHub and Supabase readback and mutation lanes tied to this repository.

## Bootstrap contract
- For substantive `ircore` work that depends on Supabase bootstrap, materialize `/workspace/.ircore-bootstrap.json` with `{"supabase_project_id":"kdhkhyksdzjbajavsoxa"}` before querying `ircore.get_agent_bootstrap_v1(...)`.
- If the workspace bootstrap file is missing but the canonical `project_id` above is still in force, create or refresh the workspace bootstrap file from that canonical value before treating startup as blocked.
- `/workspace/memory/agent-redesign/.ircore-bootstrap.json` is continuity only. It may be used for cross-check or recovery, but it is not the sole startup authority when the workspace bootstrap file can be materialized from the canonical project ID.
- Treat bootstrap as blocked only when the canonical project ID is missing or overridden without a replacement, the workspace file cannot be created or refreshed, the file is malformed, or the Supabase bootstrap query fails or returns unusable output.

## Operator discipline
- Re-anchor to the current task before answering after any explicit operator redirection or lane change.
- For high-stakes GitHub or Supabase capability/state claims, verify live connector readback before answering from assumption when those connectors are available.
- If operator action is required, provide the exact goal, step-by-step actions, click-by-click UI guidance, and exact text to paste where needed.
- Do not assume any manual operator action was completed unless the operator explicitly confirms it.
- Prefer slower, more deliberate verification over fast answers in governance-sensitive lanes.

## Validation
- When editing code or workflows, run the closest available validation and report any gaps.
- When editing documentation, scan for stale path references and mismatched authority claims before finishing.
- Treat broken path references, stale startup guidance, and workflow assumptions about removed files as real defects.
- Treat stale-lane drift, answer-first verification gaps, incomplete manual-action guidance, and contradictory bootstrap-path guidance as real operator-governance defects.

## Cleanup posture
- Historical artifacts may remain when they are clearly evidence or release history.
- Active guidance, workflow validation, and support files must not depend on retired parity or skill-mirror surfaces.
