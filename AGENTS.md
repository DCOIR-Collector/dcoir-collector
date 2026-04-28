# AGENTS.md

## Project purpose
This repository supports the AFRICOM SOC IR / DCOIR workflow. Preserve evidence-first reasoning, exact command-lane separation, bounded confidence, conservative claims, and clear stop conditions.

## How to use this file
- Treat this file as retained repo guidance for coding agents such as Codex. It is a practical navigation, validation, and safety guide, not a duplicate of the ChatGPT Project Instructions, Airtable records, or governed control-plane files.
- Keep this file short enough for agents to apply reliably. Prefer pointers to live authority surfaces over copying long instructions into this file.
- When a task touches a subdirectory that contains another `AGENTS.md`, obey the most specific applicable file first, then this root file.

## Authority and startup
- Treat this repository as the governed readable-source surface for retained DCOIR code, helper-skill source, release history, and promoted workflow decisions.
- For normal startup, resume, current live queue, active-plan recovery, administrative control, helper-memory lookup, and operator-preference recovery, use Airtable-first authority: Project Instructions, CP-00 only as bootstrap pointer when present, Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`, `Session Checkpoints`, `Queue Control`, `Work Items`, active `Plans`, `Plan Tasks`, `Operator Preferences`, and relevant helper-memory tables.
- Read `project_sources/governance/control_plane/CP-01_DCOIR_Version_Manifest.txt` and `project_sources/governance/control_plane/CP-02_DCOIR_Change_Log.txt` only for repository-source tasks such as source-role resolution, packaging/readback, promoted-history comparison, explicit source inspection, or final T99 keep/delete review. Do not use CP-01/CP-02 as normal startup authority when Airtable startup authority is present and current.
- If CP-01 or CP-02 is absent after a final repo-reduction or split, do not invent a replacement current state. Use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Retained Repo Manifest`, `Queue Control`, `Work Items`, `Plans`, and `Plan Tasks` as the live operating surfaces, then report the missing retained source as a validation finding.
- Treat Project Instructions and CP-00 bootstrap content as startup anchors when they are supplied by the operator, but do not let them override newer Airtable live queue or active-plan records.
- If authority sources conflict in a way that affects current-state claims, stop and report the exact conflict before editing.
- Do not treat stale GitHub todo files, retired active-now files, or historical queue notes as live queue authority unless Airtable explicitly reauthorizes them.

## Airtable operating authority
- Airtable is the live authority for queue order, branch priority, resume-first state, active execution order, plans, plan tasks, session carry-forward, operator preferences, validation catalog state, and stateful helper-skill durable memory where a memory table exists.
- Use `Queue Control`, `Work Items`, `Plans`, `Plan Tasks`, `Plan Checkpoints`, `Session Checkpoints`, `Idea Inbox`, `Operator Preferences`, and validation/test tables as canonical operating surfaces when task state matters.
- Use `Retained Repo Manifest` as the final-state keep-set and no-missing-reference validation surface. Before editing retained files, check whether new or existing path references point to files that are scheduled for removal, deferred to T99, or not represented in the retained manifest.
- When adding new Airtable tables for this project, include a `delete_requested` checkbox field.
- Each new table that may need cleanup must have its own per-table `delete_requested` automation, validated with a scratch row before use.
- Never create broad/base-wide delete automations, and never test deletion with production records.

## Retained-repo reference safety
- Before adding a repo path to retained documentation, ask whether that path is in the retained manifest, current CP set, or explicitly historical.
- If a retained file references a file or folder that may be removed, either rewrite the reference to the retained/Airtable authority surface or create a concrete fix task before final cleanup.
- Historical references are allowed only when they are clearly labeled historical and do not instruct agents to use removed files as live authority.
- Treat references to `dcoir_skill_memory/`, retired GitHub todo files, obsolete project-source logs, temporary bundles, generated zips, or runtime residue as cleanup-sensitive until verified against Airtable and the retained manifest.

## GitHub source rules
- Keep GitHub as the governed readable source for retained project files, helper-skill source, release history, and durable workflow decisions.
- Do not duplicate ordinary editable readable text across GitHub and Project space.
- Do not mirror routine Airtable queue churn into GitHub.
- Promote only durable governance decisions, closeouts, workflow changes, release notes, and governed history.
- Prefer small, reviewable changes and preserve existing guidance unless the task explicitly changes it.
- For final cleanup, do not remove a file solely because it looks stale. Removal requires a current authority basis, retained-manifest check, Airtable coverage check, and no remaining live dependency.

## Collector line
- Treat `project_sources/collector/source/DCOIR_Collector.ps1` as the current readable collector source when present unless the current control plane changes that authority.
- Treat `DCOIR_Collector.ps1` as the canonical emitted runtime filename for execution examples.
- Keep Windows PowerShell 5.1 compatibility as a hard requirement for local workstation/test instructions unless explicitly changed.
- Use Elastic Defend response-action syntax for endpoint instructions and PowerShell 5.1 syntax for local workstation/test instructions.
- Preserve exact command-lane separation; do not mix endpoint response-action examples with local PowerShell execution examples.

## Helper-skill boundary
- `dcoir-*` helper skills are project-side authoring, QA, packaging, workflow, and maintenance aids.
- Use the relevant helper skill when a task clearly matches it, but final runtime prompts and standalone Gemini outputs must be self-sufficient.
- Final prompts, operator-facing runbooks, and Gemini runtime outputs must not depend on hidden project memory, helper-workflow context, or unattached files.
- Stateful helper skills should use Airtable durable helper-memory tables where those tables exist. GitHub `dcoir_skill_memory/` is legacy/source-basis history pending T99 cleanup unless explicitly reauthorized.
- If a helper skill changes materially, verify installed/readable source parity before making readiness or delivery claims.

## Documentation and validation rules
- When editing code, run the closest available validation or test command and record limitations honestly.
- When changing documentation, check nearby files for naming, authority, retained-manifest, and current-state consistency.
- Preserve evidence, rationale, assumptions, constraints, validation notes, workflow explanations, and downstream implications unless the task explicitly asks for a narrower form.
- Treat misleading documentation, broken test instructions, collector execution-lane confusion, accidental sensitive-path exposure, and unresolved live-authority references to removed paths as high-priority review items.
- If a change cannot be validated because a tool, snapshot, or Airtable connector is unavailable, say exactly what was not verified.

## Codex working pattern
- Start repo tasks by identifying the authority mode: current GitHub-primary, Airtable-live execution, or final retained-repo validation.
- For code edits, make the smallest patch that satisfies the task, then run the closest available syntax/test checks.
- For documentation edits, scan the changed file for path references and authority claims before finishing.
- For cleanup or refactor tasks, produce a short keep/defer/delete rationale and do not delete without an explicit task or operator approval.
- For retained-manifest work, compare expected retained paths against the actual repo tree and flag missing or unexpected files.
- When preparing a final answer, include changed files, validation performed, validation not performed, and any follow-up tasks created.

## Manual delivery preference
- Unless the operator asks for more, deliver only affected skills and affected repo-relative files.
- If exactly one skill is affected, deliver only that skill ZIP.
- If multiple skills changed, deliver one outer ZIP containing only affected per-skill ZIPs.
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
- Treat unresolved live-authority references to removed paths as review-worthy; do not chase clearly historical references that do not drive current behavior.
- Check whether changes preserve Windows PowerShell 5.1 compatibility where collector instructions are involved.
