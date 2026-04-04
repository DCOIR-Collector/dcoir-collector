# DCOIR Collector

GitHub-primary working source for the AFRICOM SOC DCOIR framework.

GitHub repo `malwaredevil/dcoir-collector` is the sole working source for governed readable text files.
Project space is the bootstrap and runtime anchor.
Resume flows should use Project Instructions first, then the GitHub connector for readable governed text sources.
Do not keep duplicate editable readable text files in both GitHub and Project space.

## Project Mission

DCOIR exists to provide a governed, maintainable, and resumable digital collection, triage, enrichment, artifact-review, and incident-response framework for AFRICOM SOC workflows.

This repository is the GitHub-primary working source for the broader DCOIR framework, including:
- the collector runtime and governed readable source line
- the regression and validation harness
- the project control plane and continuity layer
- the knowledge and documentation layer
- the analyst-facing prompt-pack and combined master-prompt deliverable
- the Gemini parent-agent and sub-agent design line
- the durable task-memory bank for validated procedures, limitations, and failure signatures
- the governed helper-skill source and workflow-support layer

## Working Model

- GitHub repository `malwaredevil/dcoir-collector` is the sole working source for governed readable text.
- Project space is the bootstrap and runtime anchor, not a second editable readable-text repository.
- Resume and governance begin with Project Instructions, then `CP-01`, then `CP-02`.
- The preferred operating posture is the validated GitHub connector low-level lane for chat-managed readable-text updates, with GitHub Desktop as the easiest approved operator path for bulk local placement, extracted-file ingestion, and binary or zip handling.
- Helper skills are used for analysis, validation, packaging, workflow support, and maintenance where appropriate.
- The collector runtime filename remains stable while the readable governed source set may evolve for maintainability.

## Core Deliverables

### 1. DCOIR collector and validation line
- `project_sources/DCOIR_Collector.ps1` as the canonical runtime collector
- `project_sources/collector_parts/*.ps1` as the governed readable collector source set
- `project_sources/run_DCOIR_Tests.ps1` as the regression and validation harness

### 2. Analyst-facing DCOIR master prompt
A combined analyst-facing prompt built from the governed modular prompt-pack that an analyst can paste into an LLM chat to perform disciplined baseline triage, enrichment review, retrieved-artifact review, and final case synthesis for DCOIR collector artifacts.

### 3. Gemini triage and DCOIR agent system
A fully developed Gemini parent-agent and sub-agent system that merges Elastic alert triage with DCOIR escalation, collection, enrichment, artifact review, and synthesis while preserving evidence-first DFIR discipline, bounded confidence, and exact command-lane separation.

### 4. Project control plane and continuity layer
The governed manifest, change log, workflow/layout guidance, todo and handoff structure, and task-memory bank that keep the project resumable, auditable, and maintainable across sessions.

### 5. Knowledge and documentation layer
Human-readable workflow, usage, and supporting knowledge documents that explain how to use, maintain, validate, and extend the project.

### 6. Governed helper-skill source and maintenance layer
The `dcoir-*` helper skills under `dcoir_skills/` that support routing, validation, packaging, maintenance, and workflow control for project-side work.

## Repository Navigation

- [project_sources](project_sources/) — control plane, logs, prompt-pack sources, collector sources, and extracted readable project-source folders
- [knowledge](knowledge/) — knowledge docs, routing notes, connector reference material, and task memory
- [dcoir_skills](dcoir_skills/) — governed helper-skill source root for current DCOIR skills
- [project_settings](project_settings/) — bootstrap and settings surfaces used for Project-space anchoring
- [release_notes](release_notes/) — release instructions and bounded handoff notes when a bundle needs them
- [supporting_assets](supporting_assets/) — retained non-authoritative assets and delivery artifacts

## Documentation Direction

The documentation goal is to make the repository understandable without hidden context. Current priorities include:
- stronger local-guide README surfaces at the repo root and major folders
- a fuller wiki-style knowledge structure in `knowledge/`
- maintained helper-skill routing guidance
- clearer documentation of the master prompt, Gemini design line, DFIR operating posture, and enrichment model
- documentation and validation guidance that stays aligned to the current governed working line instead of historical assumptions
