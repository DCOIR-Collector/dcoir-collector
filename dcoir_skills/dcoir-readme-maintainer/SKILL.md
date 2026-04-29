---
name: dcoir-readme-maintainer
description: maintain root and folder readme surfaces for africom_soc_ir / dcoir work and align readme navigation with current governed workflow rules.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-readme-maintainer|SKILL.md -->

# DCOIR README Maintainer

## Airtable operational schema alignment
Airtable cutover and skill cutover are complete. Use the current Airtable schema as live operational authority, not historical migration or cleanup plans.

Use `references/airtable_operational_schema_contract.md` for durable rules covering:
- current live authority tables
- idea-to-work-item-to-plan promotion
- Delete Queue deletion requests and dependency order
- DCOIR Lifecycle Ledger readback/history events
- Local Configuration Registry secret-safe configuration references

Do not assume retired or absent tables exist. In particular, do not require `Plan Tasks`, `Plan Checkpoints`, `Skill State Registry`, `Schema Registry`, `Tracking Registry`, `Repo File Coverage Detail`, or `Retained Repo Manifest` unless live Airtable schema readback proves the table exists for the current task.

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Work Items for task execution`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, explicit repo cleanup/source-role review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo Surface Registry supporting evidence`, `Repo Surface Registry retained-state evidence`, and active plan state before stopping.


## Required project gate
Use this skill only for the AFRICOM_SOC_IR / DCOIR project.

Before doing README work:
1. Re-anchor to Project Instructions.
2. Read Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` and live Airtable state for startup/admin/current-state context.
3. Read `dcoir_skills/project_discovery_contract.json` and GitHub `CP-01`/`CP-02` only when README work depends on governed repo source roles, promoted-history comparison, packaging, or explicit repo cleanup/source-role review.
4. Confirm the task is inside the current governed DCOIR working line.

If authority is unclear or the control plane conflicts, stop and report the exact conflict instead of rewriting README surfaces from stale assumptions.

## Scope boundary
This skill owns:
- root `README.md` maintenance
- major folder README maintenance such as `knowledge/README.md`, `project_sources/README.md`, and `dcoir_skills/README.md`
- README navigation and cross-link upkeep
- missing-README detection for major governed folders
- README refresh after meaningful repo, deliverable, helper-skill inventory, or control-plane changes
- narrow refresh of `knowledge/DCOIR_Helper_Skills_Routing_Note.md` when current helper-skill inventory or workflow rules changed materially and that routing note would otherwise drift from the maintained README surfaces

This skill does not own:
- broad knowledge-doc generation or wiki expansion
- source-authority decisions
- release readiness or package-class choice
- general markdown maintenance outside README surfaces, except narrow summary or link refresh needed to keep a README accurate and the routing note aligned to those README surfaces

Read `references/scope_boundary.md` when the task risks drifting into broader documentation work.

## Workflow decision tree
1. Determine the README job type.
   - **Root README refresh** -> follow "Root README workflow"
   - **Existing folder README refresh** -> follow "Folder README workflow"
   - **Missing folder README creation** -> follow "Missing README workflow"
   - **Navigation or cross-link cleanup** -> follow "Navigation workflow"
   - **Routing-note alignment** -> refresh `knowledge/DCOIR_Helper_Skills_Routing_Note.md` only when current helper-skill inventory or workflow rules changed materially and the note would otherwise contradict the maintained README surfaces

2. For all job types:
   - inspect the current discovery contract when present before deciding which README surfaces are the current repo-guide surfaces
   - inspect the target README surface first
   - inspect nearby repo context that the README summarizes or links to
   - inspect the current documentation lane if priorities or scope are ambiguous
   - prefer the smallest durable README or routing-note change set that materially improves usability

3. Before GitHub writes:
   - invoke `dcoir-memory-preflight` for GitHub-family write work or grouped repo updates
   - prefer one grouped transaction when multiple related README files or the routing note belong together
   - verify by readback after write instead of trusting success messages alone

4. When multiple reasonable paths exist and the operator did not choose one:
   - invoke `dcoir-decision-policy`
   - proceed with the smallest complete branch unless a real hard-stop condition exists

## Root README workflow
Use this for repository-level orientation work.

Focus on:
- mission summary
- working model
- core deliverables
- scope priorities
- repository navigation
- top-level documentation direction

Do not turn the root README into a long-form manual. Keep it a high-signal entry surface.
See `references/readme_patterns.md` for the default root README pattern.

## Folder README workflow
Use this for local folder guides such as `knowledge/README.md`, `project_sources/README.md`, or `dcoir_skills/README.md`.

Focus on:
- short purpose statement
- recommended contents
- current important subfolders or local surfaces
- local navigation links
- concise authority or usage notes when helpful

Do not repeat the full root README in every folder.
See `references/readme_patterns.md` for the default folder README pattern.

## Missing README workflow
Use this when a major governed folder has no useful README.

Default approach:
1. Confirm the folder is a real governed working surface, not a one-off artifact container.
2. Inspect nearby files and subfolders.
3. Draft a concise folder README using the folder pattern.
4. Keep the file local-guide oriented rather than aspirational.
5. If broader documentation gaps are discovered, note them separately instead of expanding this README too far.

Use `scripts/scan_readme_coverage.py` when a quick coverage scan would help identify missing README surfaces or stale local links.

## Navigation workflow
Use this when the main problem is stale or weak README links.

Focus on:
- root-to-folder link consistency
- folder-to-subfolder or related-doc pointers when helpful
- removing stale README references
- aligning README links to the current visible governed working line
- keeping README pointers and the helper-skill routing note mutually consistent when helper-skill inventory or workflow rules changed materially

Do not add speculative links to work that is not actually present.

## Writing rules
- Keep README writing concise, navigational, and operator-useful.
- Prefer current repo facts over aspirational prose.
- Distinguish current governed surfaces from future documentation direction.
- Prefer a specific README fix over a broad narrative rewrite.
- When a broader documentation need is discovered, route that follow-on work to the appropriate broader documentation workflow instead of silently expanding scope.
- Preserve the DCOIR GitHub-primary working-source posture.
- Treat `dcoir-knowledge-doc-maintainer` as the owner of broad knowledge-doc generation and retained knowledge-doc ZIP refresh, not this skill.

## Output contract
When acting under this skill:
- identify the README or routing-note job type
- state the minimal surface being changed
- produce the updated README or routing-note content or a bounded change proposal
- keep the rationale short and grounded to current repo state
- if the task requires broader documentation work, say that plainly and narrow the README or routing-note work instead of absorbing the larger job

## References
Read when needed:
- `references/scope_boundary.md`
- `references/readme_patterns.md`

Use when helpful:
- `scripts/scan_readme_coverage.py`

## Airtable testing workflow alignment

When README surfaces are refreshed after workflow changes, keep them aligned with the current testing posture that uses Airtable table `Validation Test Cases` as the standard dynamic manual-testing surface for collector and Gemini sessions.


## Fast Airtable helper-memory read contract

Use the skill-specific Airtable helper-memory table directly when this skill needs durable helper memory.

- Airtable base id: `appM4KSwnVf3G3OTK`
- Airtable table name: `dcoir-readme-maintainer`
- Airtable table id: `tblzaBfC7EUCrVRUe`
- Primary lookup/dedupe field: `readme_entry_id`

Read pattern:
- Use the Airtable connector with `baseId="appM4KSwnVf3G3OTK"` and `tableId="tblzaBfC7EUCrVRUe"` when supported; use the table name only as fallback.
- Use non-display Airtable reads such as `search_records`, direct table reads, or equivalent connector calls. Do not ask the operator whether to display an interactive Airtable view.
- Pull only this skill's own helper-memory table for routine memory lookup. Do not scan a unified helper-memory table and filter by skill.
- Keep helper-memory rows human-readable and update this same table when material reusable state changes.
- If the connector cannot query by tableId, state the limitation and use the table name `dcoir-readme-maintainer` without switching to a merged memory table.
