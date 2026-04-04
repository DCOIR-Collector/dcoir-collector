# DCOIR Collector

GitHub-primary working source for the AFRICOM SOC DCOIR framework.

GitHub repo `malwaredevil/dcoir-collector` is the sole working source for governed readable text files.
Project space is the bootstrap and runtime anchor.
Resume flows should use Project Instructions first, then the GitHub connector for readable governed text sources.
Do not keep duplicate editable readable text files in both GitHub and Project space.

## Project Mission

DCOIR exists to provide a governed, maintainable, and resumable digital collection, triage, enrichment, artifact-review, and incident-response framework for AFRICOM SOC workflows.

This repository is not only a collector-script repo. It is the GitHub-primary working source for the DCOIR framework, including:

- the collector runtime and governed readable source line
- the regression and validation harness
- the project control plane and continuity layer
- the knowledge and documentation layer
- the analyst-facing prompt-pack and combined master-prompt deliverable
- the Gemini parent-agent and sub-agent design line
- the durable task-memory bank for validated procedures, limitations, and failure signatures

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

## Current Governed Continuity Surfaces

Use these first when grounding current project state:
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- `project_sources/LOG-01_DCOIR_Todo_Index.txt`
- `project_sources/LOG-03_DCOIR_Session_Handoff_Brief.txt`
- `project_sources/LOG-05_DCOIR_Session_Resume_Anchor_2026-04-03.txt`

For helper-skill workflow governance and rollout rules, use:
- `project_sources/DOC-05_DCOIR_Helper_Skill_Workflow_And_GitHub_Source_Rules.txt`
- `project_sources/DOC-06_DCOIR_GitHub_Helper_Skill_Source_Layout_And_Rollout.txt`

## Repository Navigation

- [project_sources](project_sources/) — current governed readable project sources, including the control plane, continuity surfaces, collector line, prompt-pack line, and extracted readable Gemini source folders.
- [knowledge](knowledge/) — current human-readable supporting knowledge docs, routing notes, connector references, and extracted readable knowledge folders.
- [dcoir_skills](dcoir_skills/) — governed GitHub-readable helper-skill source root.
- [project_settings](project_settings/) — current settings mirrors and bootstrap/runtime anchor material.
- [release_notes](release_notes/) — release instructions and batch-application guidance when a bundle requires operator-side placement.
- [supporting_assets](supporting_assets/) — retained binary and zip assets used for packaging, local execution, or supporting delivery workflows.

## Helper-Skill Workflow and Governance

- Helper-skill source governance lives under [dcoir_skills](dcoir_skills/).
- Project-side helper-skill selection guidance lives in [knowledge/DCOIR_Helper_Skills_Routing_Note.md](knowledge/DCOIR_Helper_Skills_Routing_Note.md).
- Evergreen helper-skill workflow rules live in `project_sources/DOC-05_DCOIR_Helper_Skill_Workflow_And_GitHub_Source_Rules.txt`.
- Evergreen GitHub helper-skill source layout and rollout rules live in `project_sources/DOC-06_DCOIR_GitHub_Helper_Skill_Source_Layout_And_Rollout.txt`.
- Helper-skill workflow changes should be reflected in the routing note, the relevant folder README surfaces, and the current continuity surfaces when they materially change project-side behavior.

## Scope Priorities

The project currently spans:

- DCOIR collector-driven host triage and enrichment
- analyst-facing artifact review and case synthesis
- Elastic alert triage with explicit escalation into DCOIR when host-based evidence is warranted
- DFIR and incident-response expertise grounded in evidence-first analysis
- bounded IOC and external-context enrichment using authoritative-source priority
- maintainable GitHub-native readable sources, documentation, and continuity artifacts

## Documentation Direction

The documentation goal is to make the repository understandable without hidden context. Over time this should include:

- a strong root `README`
- helpful folder-level `README` files
- a fuller wiki-style knowledge structure in `knowledge/`
- extracted readable materials from formerly zipped supporting bundles kept in governed folders under `project_sources/` and `knowledge/`
- sustainable splitting of growth-prone governed files such as todo and log structures
