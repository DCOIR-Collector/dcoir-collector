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

## Gemini Builder Governance Rule
- For Gemini builder governance, consult the governed `ircore` Gemini research surfaces before Gemini source, validation, or readback changes.
- Do not treat repo runtime files as the source of those governance findings.

## Startup contract
- For substantive `ircore` work, materialize `/workspace/.ircore-startup-pack.json` with the current canonical startup-pack target shape:

```json
{
  "schema_version": "ircore_startup_pack_target_v1",
  "github_repository_full_name": "malwaredevil/dcoir-collector",
  "github_repository_url": "https://github.com/malwaredevil/dcoir-collector/",
  "supabase_project_id": "kdhkhyksdzjbajavsoxa",
  "supabase_startup_pack_function": "ircore.get_agent_startup_pack",
  "fallback_bootstrap_pointer_file": "/workspace/.ircore-bootstrap.json",
  "fallback_bootstrap_function": "ircore.get_agent_bootstrap",
  "active_continuity_file": "/workspace/memory/agent-redesign/ACTIVE-CONTINUITY.md",
  "materialize_workspace_startup_pointer_if_missing": true,
  "function_versioning_policy": "use_unversioned_canonical_names"
}
```

- Materialize `/workspace/.ircore-bootstrap.json` only as the fallback pointer, with the current canonical fallback shape:

```json
{
  "schema_version": "ircore_bootstrap_target_v2",
  "github_repository_full_name": "malwaredevil/dcoir-collector",
  "github_repository_url": "https://github.com/malwaredevil/dcoir-collector/",
  "supabase_project_id": "kdhkhyksdzjbajavsoxa",
  "supabase_bootstrap_function": "ircore.get_agent_bootstrap",
  "active_continuity_file": "/workspace/memory/agent-redesign/ACTIVE-CONTINUITY.md",
  "materialize_workspace_bootstrap_if_missing": true
}
```

- If `/workspace/.ircore-startup-pack.json` is missing and those canonical startup targets are still in force, create or refresh it from those exact values before treating startup as blocked.
- Query `select ircore.get_agent_startup_pack('<task_family_slug>', '<task_class>', '<scenario_slug>');` first and follow the returned authority, retrieval, validation, workflow-readback, alias-resolution, scenario-matrix, skill-trigger, and continuity guidance.
- Use `/workspace/.ircore-bootstrap.json` and `select ircore.get_agent_bootstrap('<task_family_slug>', '<task_class>');` only when the startup-pack query fails and fallback is required.
- `/workspace/.ircore-preferences.json` and `/workspace/.ircore-lane-matrix.json` are optional direct-loader files. Do not treat them as mandatory startup files unless a separate design decision explicitly promotes them.
- `/workspace/memory/agent-redesign/.ircore-bootstrap.json` is continuity only. It may help with cross-check or recovery, but it is not the primary startup authority when the workspace-local startup pointers can be materialized from the canonical startup targets above.
- Treat startup as blocked only when the canonical `supabase_project_id` is missing or overridden without a replacement, a required workspace pointer cannot be created or refreshed, a required pointer file is malformed, or both the startup-pack and fallback bootstrap queries fail or return unusable output.

## Operator discipline
- Re-anchor to the current task before answering after any explicit operator redirection or lane change.
- For high-stakes GitHub or Supabase capability/state claims, verify live connector readback before answering from assumption when those connectors are available.
- If operator action is required, provide the exact goal, step-by-step actions, click-by-click UI guidance, and exact text to paste where needed.
- Do not assume any manual operator action was completed unless the operator explicitly confirms it.
- Prefer slower, more deliberate verification over fast answers in governance-sensitive lanes.
- For code, workflow, and review work, prefer correctness and completeness over speed; perform end-to-end review, proactively fix adjacent real defects you find, and treat shell quoting, YAML and JSON shape, GitHub Actions expression surfaces, and workflow-runner assumptions as first-class review areas.
- When a governed workflow liveness check uses Gmail, use the human-facing search label `label:GitHub`; connector metadata and returned message labels may show the same mailbox label as `Label_125`. Treat Gmail as an early signal only, and use request-scoped heartbeat files, workflow reports, status summaries, and artifacts as the actual execution evidence.
- When requesting another Codex PR review in the same thread, vary the wording instead of repeating the exact same sentence each round.

## Validation
- When editing code or workflows, run the closest available validation and report any gaps.
- When editing documentation, scan for stale path references and mismatched authority claims before finishing.
- Treat broken path references, stale startup guidance, and workflow assumptions about removed files as real defects.
- Treat stale-lane drift, answer-first verification gaps, incomplete manual-action guidance, and contradictory bootstrap-path guidance as real operator-governance defects.
- For consequential code and workflow changes, perform an end-to-end review that covers input validation, quoting and interpolation boundaries, YAML block-scalar safety, JSON shape handling, GitHub Actions expression-surface behavior, downstream cleanup or retention implications, and defense-in-depth checks before declaring the change ready.

## Cleanup posture
- Historical artifacts may remain when they are clearly evidence or release history.
- Active guidance, workflow validation, and support files must not depend on retired parity or skill-mirror surfaces.
