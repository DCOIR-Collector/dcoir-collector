<!-- skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-readme-maintainer|readme_patterns.md -->

# README Patterns

Use these as the default structure unless the current surface clearly needs a narrower variant.

## Root README pattern

Use this shape for the repository root `README.md`:

```markdown
# [Project Name]

[One or two sentences on what the repository is and why it exists.]

## Project Mission
[High-signal mission summary]

## Working Model
- [source of truth]
- [resume order]
- [operating posture]

## Core Deliverables
- [deliverable 1]
- [deliverable 2]
- [deliverable 3]

## Scope Priorities
- [priority area 1]
- [priority area 2]
- [priority area 3]

## Repository Navigation
- [top-level folder links]

## Documentation Direction
- [short bullets on how the repo should stay understandable]
```

Guidance:
- keep the root README as the entry surface, not the full manual
- prefer links and summaries over deep prose
- keep the navigation section aligned to currently visible governed folders

## Folder README pattern

Use this shape for folder-level READMEs:

```markdown
# [Folder Name]

[One or two sentences on what lives here.]

Recommended contents:
- [type of item 1]
- [type of item 2]
- [type of item 3]

Current important surfaces:
- `[path-or-subfolder-1]`
- `[path-or-subfolder-2]`

Notes:
- [authority or usage note only when useful]
```

Guidance:
- keep folder READMEs local-guide oriented
- do not duplicate the full root README
- prefer concise bullets over narrative sections unless the folder genuinely needs more detail

## Authority-note pattern

Use only when the local folder needs a short governance or usage boundary.

```markdown
Notes:
- This folder is part of the GitHub-primary working line.
- Treat nearby control-plane files as authoritative when the current state matters.
```

Keep authority notes short and factual.

## Navigation-link pattern

Use relative links and keep them limited to surfaces that materially help the reader.

Good examples:
- `[project_sources](project_sources/)`
- `[knowledge](knowledge/)`
- `` `knowledge/README.md and GitHub issue-template guidance surfaces/` ``

Avoid:
- speculative links to future files
- long link lists that are not useful for navigation
- repeating the same links in every README unless they are locally important
