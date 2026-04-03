---
name: dcoir-readme-maintainer
description: maintain root and folder readme surfaces for africom_soc_ir / dcoir work. use when chatgpt needs to improve the repository root readme, improve or create a major folder readme such as knowledge/readme.md or project_sources/readme.md, refresh readme navigation or cross-links after repo changes, detect missing readme coverage in major governed folders, or align readme summaries to the current control plane and visible governed working line. do not use for broader knowledge-doc generation, source-authority judgment, release readiness, or package-class choice.
---

# DCOIR README Maintainer

## Required project gate
Use this skill only for the AFRICOM_SOC_IR / DCOIR project.

Before doing README work:
1. Re-anchor to Project Instructions.
2. Read current `project_sources/CP-01_DCOIR_Version_Manifest.txt`.
3. Read current `project_sources/CP-02_DCOIR_Change_Log.txt`.
4. Confirm the task is inside the current governed DCOIR working line.

If authority is unclear or the control plane conflicts, stop and report the exact conflict instead of rewriting README surfaces from stale assumptions.

## Scope boundary
This skill owns:
- root `README.md` maintenance
- major folder README maintenance such as `knowledge/README.md` and `project_sources/README.md`
- README navigation and cross-link upkeep
- missing-README detection for major governed folders
- README refresh after meaningful repo, deliverable, or control-plane changes

This skill does not own:
- broad knowledge-doc generation or wiki expansion
- source-authority decisions
- release readiness or package-class choice
- general markdown maintenance outside README surfaces, except narrow summary or link refresh needed to keep a README accurate

Read `references/scope_boundary.md` when the task risks drifting into broader documentation work.

## Workflow decision tree
1. Determine the README job type.
   - **Root README refresh** -> follow "Root README workflow"
   - **Existing folder README refresh** -> follow "Folder README workflow"
   - **Missing folder README creation** -> follow "Missing README workflow"
   - **Navigation or cross-link cleanup** -> follow "Navigation workflow"

2. For all job types:
   - inspect the target README surface first
   - inspect nearby repo context that the README summarizes or links to
   - inspect the current documentation lane if priorities or scope are ambiguous
   - prefer the smallest durable README change set that materially improves usability

3. Before GitHub writes:
   - invoke `dcoir-memory-preflight` for GitHub-family write work or grouped repo updates
   - prefer one grouped transaction when multiple related README files belong together
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
Use this for local folder guides such as `knowledge/README.md` or `project_sources/README.md`.

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

Do not add speculative links to work that is not actually present.

## Writing rules
- Keep README writing concise, navigational, and operator-useful.
- Prefer current repo facts over aspirational prose.
- Distinguish current governed surfaces from future documentation direction.
- Prefer a specific README fix over a broad narrative rewrite.
- When a broader documentation need is discovered, route that follow-on work to the appropriate broader documentation workflow instead of silently expanding scope.
- Preserve the DCOIR GitHub-primary working-source posture.

## Output contract
When acting under this skill:
- identify the README job type
- state the minimal surface being changed
- produce the updated README content or a bounded README change proposal
- keep the rationale short and grounded to current repo state
- if the task requires broader documentation work, say that plainly and narrow the README work instead of absorbing the larger job

## References
Read when needed:
- `references/scope_boundary.md`
- `references/readme_patterns.md`

Use when helpful:
- `scripts/scan_readme_coverage.py`
