# README Maintainer Skill Boundary Draft

## Boundary decision
Treat `dcoir-readme-maintainer` as a focused helper for root and folder README maintenance, not as a broad documentation-generation or knowledge-doc governance skill.

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

### 4. Missing README detection
Detect when a major governed folder lacks a useful README and recommend or create one when appropriate.

### 5. Change-aware README refresh
When control-plane, deliverables, folder inventory, or extracted readable working lines change materially, determine whether the affected README surfaces should be refreshed.

## Out of scope

### 1. Non-README documentation generation
Do not treat this skill as the owner of broader knowledge-doc generation, wiki expansion, or supporting-doc refresh. That belongs with broader documentation workflows such as `dcoir-knowledge-doc-maintainer`.

### 2. Control-plane authority decisions
Do not decide source authority, currentness, or promotion status by README text alone.

### 3. Broad markdown maintenance outside README surfaces
Do not drift into maintaining general docs, logs, prompt files, or workflow specs except when those changes are only being read to refresh README summaries or links.

### 4. Packaging or readiness judgment
Do not choose release class or readiness state.

## Operating posture
- re-anchor to Project Instructions, then `CP-01`, then `CP-02`
- read current root README and relevant folder README surfaces first
- read the current documentation-and-knowledge todo lane when scope or priorities are unclear
- prefer specific README fixes over broad narrative rewrites
- preserve concise, navigational, operator-useful README writing

## Why this boundary fits current repo evidence
- the documentation lane explicitly calls for improving the main README and each major folder README as local guides
- the current root README acts as a top-level project framework guide
- the current `knowledge/README.md` and `project_sources/README.md` already behave like local folder guides rather than full standalone documentation systems
