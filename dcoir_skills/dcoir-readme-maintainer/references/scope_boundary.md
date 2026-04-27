# Scope Boundary

## Boundary decision
Treat `dcoir-readme-maintainer` as a focused helper for root and folder README maintenance plus narrow helper-skill routing-note alignment, not as a broad documentation-generation or knowledge-doc governance skill.

## In scope

### 1. Root README maintenance
Own maintenance of the repository root `README.md` as the top-level project entry surface.

Typical responsibilities:
- mission summary
- working model summary
- core deliverables section
- scope priorities section
- repository navigation section
- top-level documentation direction
- high-signal repo-map refresh when major governed folders or deliverables change

### 2. Folder README maintenance
Own maintenance of major folder-level README files such as:
- `knowledge/README.md`
- `project_sources/README.md`
- `dcoir_skills/README.md`
- other major governed folder READMEs when they exist or should exist

Typical responsibilities:
- short purpose statement
- recommended contents
- current important subfolders or local surfaces
- local navigation links
- concise authority or usage notes when needed

### 3. README navigation and cross-link upkeep
Own the README-specific navigation layer, including:
- root-to-folder link consistency
- folder-to-subfolder or related-doc pointers when appropriate
- removing stale README links or outdated folder mentions
- keeping README references aligned to the visible governed working line

### 4. Narrow routing-note alignment
Own narrow refresh of `knowledge/DCOIR_Helper_Skills_Routing_Note.md` when current helper-skill inventory or workflow rules changed materially and the routing note would otherwise contradict maintained README surfaces.

This is in scope only when the change is essentially navigational or descriptive routing upkeep, not broad knowledge-doc generation.

### 5. Missing README detection
Detect when a major governed folder lacks a useful README and recommend or create one when appropriate.

### 6. Change-aware README refresh
When control-plane, deliverables, folder inventory, helper-skill inventory, or extracted readable working lines change materially, determine whether the affected README surfaces should be refreshed.

## Out of scope
- broader knowledge-doc generation or wiki expansion
- retained knowledge-doc ZIP generation or replacement
- source-authority judgments
- control-plane promotion calls
- release-class or readiness decisions
- broad markdown maintenance outside README surfaces except for narrow summary or link refresh needed to keep a README accurate and the routing note aligned

## Operating posture
- re-anchor to Project Instructions, CP-00 as a pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`; read GitHub `CP-01`/`CP-02` only for repository-source tasks
- read current root README and relevant folder README surfaces first
- read the current documentation-and-knowledge todo lane when scope or priorities are unclear
- prefer specific README or routing-note fixes over broad narrative rewrites
- preserve concise, navigational, operator-useful README writing
- hand broad knowledge-doc generation or retained ZIP refresh back to `dcoir-knowledge-doc-maintainer`
