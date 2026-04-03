# DCOIR README Maintainer Skill Specification Draft

## Proposed skill name
- `dcoir-readme-maintainer`

## Purpose
Maintain root and folder README surfaces in the AFRICOM_SOC_IR / DCOIR project so the repository stays understandable, navigable, and aligned to the current governed working line.

## Proposed trigger scope
Use when DCOIR work requires:
- improving the root `README.md`
- improving or creating a major folder README such as `knowledge/README.md` or `project_sources/README.md`
- refreshing README navigation links after repo changes
- aligning README summaries to the current control plane, deliverables, and visible governed folders
- detecting stale README references or missing README coverage in major governed folders

Do not use when the task is broader knowledge-doc generation, authority resolution, release readiness, or package-class choice.

## Required project gate
- confirm DCOIR project context
- re-anchor to Project Instructions, then `CP-01`, then `CP-02`
- if authority is unclear, stop rather than rewriting README surfaces from stale assumptions

## Core workflow
1. resolve current authority
2. inspect the target README surface and nearby repo context
3. inspect the current documentation-and-knowledge todo lane when priorities or scope are ambiguous
4. determine whether the job is:
   - root README refresh
   - existing folder README refresh
   - missing folder README creation
   - navigation or cross-link cleanup
5. propose the smallest durable README change set
6. preserve concise, navigational, operator-useful writing
7. verify updated README text against the current governed working line

## In-scope outputs
- updated root README content
- updated folder README content
- missing README draft for a major governed folder
- concise README change rationale
- navigation or cross-link refresh suggestions

## Out-of-scope outputs
- broader wiki or knowledge-doc generation
- source-authority judgments
- control-plane promotion calls
- package or release-class decisions
- non-README markdown maintenance except narrow link or summary references needed to keep README surfaces accurate

## Starter references
Likely useful references:
- `README.md`
- `knowledge/README.md`
- `project_sources/README.md`
- `project_sources/todo/03_Documentation_And_Knowledge_Lane.txt`
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- `knowledge/DCOIR_Helper_Skills_Routing_Note.md`

## Starter reusable resources
Potential package contents:
- `references/readme_patterns.md`
  - root README pattern
  - folder README pattern
  - authority-note pattern
  - navigation-link pattern
- optional `scripts/scan_readme_coverage.py`
  - identify major governed folders lacking READMEs
  - identify stale or missing local README links when feasible

## Output contract
When acting under this skill:
- keep README writing concise and navigational
- preserve high-signal repository orientation over prose-heavy documentation
- distinguish current repo facts from aspirational documentation direction
- prefer the smallest README change set that materially improves usability
- when a broader documentation need is discovered, route that follow-on work to the appropriate broader documentation workflow instead of silently expanding scope

## First-pass implementation note
This draft is strong enough to begin converting into real package contents after one more pass on reusable README patterns and whether an initial scan script is truly needed.
