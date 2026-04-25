# AGENTS.md

## Project purpose
This repository supports the AFRICOM SOC IR / DCOIR workflow. Preserve evidence-first reasoning, exact command-lane separation, bounded confidence, and conservative claims.

## Authority and startup
- Treat this repository as the governed readable-source surface for DCOIR work.
- For current-state claims, read `project_sources/CP-01_DCOIR_Version_Manifest.txt` first and `project_sources/CP-02_DCOIR_Change_Log.txt` second.
- Treat Project Instructions and CP-00 bootstrap content as startup anchors, but do not let them replace CP-01/CP-02 for current repo state.
- If authority sources conflict in a way that affects current-state claims, stop and report the exact conflict before editing.
- Do not treat stale GitHub todo files or historical queue notes as live queue authority unless Airtable explicitly reauthorizes them.

## Airtable operating authority
- Airtable is the live authority for queue order, branch priority, resume-first state, active execution order, plans, session carry-forward, operator preferences, and testing catalog state.
- Use Queue Control, Work Items, Plans, Plan Tasks, Session Checkpoints, Idea Inbox, Operator Preferences, and validation/test tables as canonical operating surfaces when task state matters.
- When adding new Airtable tables for this project, include a `delete_requested` checkbox field.
- Each new table that may need cleanup must have its own per-table `delete_requested` automation, validated with a scratch row before use.
- Never create broad/base-wide delete automations, and never test deletion with production records.

## GitHub source rules
- Keep GitHub as the governed readable source for promoted project files, helper-skill source, release history, and durable workflow decisions.
- Do not duplicate ordinary editable readable text across GitHub and Project space.
- Do not mirror routine Airtable queue churn into GitHub.
- Promote only durable governance decisions, closeouts, workflow changes, release notes, and governed history.
- Prefer small, reviewable changes and preserve existing guidance unless the task explicitly changes it.

## Collector line
- Treat `project_sources/DCOIR_Collector.ps1` as the current readable collector source unless CP-01 changes that authority.
- Treat `DCOIR_Collector.ps1` as the canonical emitted runtime filename for execution examples.
- Keep Windows PowerShell 5.1 compatibility as a hard requirement for local workstation/test instructions unless explicitly changed.
- Use Elastic Defend response-action syntax for endpoint instructions and PowerShell 5.1 syntax for local workstation/test instructions.
- Preserve exact command-lane separation; do not mix endpoint response-action examples with local PowerShell execution examples.

## Helper-skill boundary
- `dcoir-*` helper skills are project-side authoring, QA, packaging, workflow, and maintenance aids.
- Use the relevant helper skill when a task clearly matches it, but final runtime prompts and standalone Gemini outputs must be self-sufficient.
- Final prompts, operator-facing runbooks, and Gemini runtime outputs must not depend on hidden project memory, helper-workflow context, or unattached files.
- If a helper skill changes materially, verify installed/readable source parity before making readiness or delivery claims.

## Documentation and validation rules
- When editing code, run the closest available validation or test command and record limitations honestly.
- When changing documentation, check nearby files for naming, authority, and current-state consistency.
- Preserve evidence, rationale, assumptions, constraints, validation notes, workflow explanations, and downstream implications unless the task explicitly asks for a narrower form.
- Treat misleading documentation, broken test instructions, collector execution-lane confusion, and accidental sensitive-path exposure as high-priority review items.

## Manual delivery preference
- Unless the operator asks for more, deliver only affected skills and affected repo-relative files.
- If exactly one skill is affected, deliver only that skill ZIP.
- If multiple skills are affected, deliver one outer ZIP containing only affected per-skill ZIPs.
- For GitHub Desktop manual repo-update bundles, deliver only affected repo-relative folders/files with no wrapper root and include a suggested commit summary unless overridden.

## GitHub issue intake rules
When creating, recommending, triaging, drafting, or linking GitHub issues for this repository, use the closest available issue template.

Use:
- Bug report for code defects, broken behavior, or reproducible product/repo problems.
- Feature request for new capabilities or enhancements.
- Validation finding for live-test, regression-test, acceptance-test, or workflow validation findings.
- Collector test failure for DCOIR collector execution, harness, command, output, or packaging failures.
- Gemini / prompt-pack issue for Gemini prime-agent instructions, sub-agent instructions, combined prompt, modular prompt-pack, routing, or output-format problems.
- Documentation / workflow correction for stale, unclear, conflicting, missing, or misleading documentation and operator workflow guidance.

Do not recommend opening a blank GitHub issue unless no template fits.
If no template fits, recommend creating a new issue template first.

## Review guidelines
- Treat security regressions as high priority.
- Treat broken test instructions as high priority.
- Treat collector execution-lane confusion as high priority.
- Treat accidental credential, token, or sensitive-path exposure as high priority.
- Treat misleading documentation as review-worthy, not cosmetic.
- Check whether changes preserve Windows PowerShell 5.1 compatibility where collector instructions are involved.
