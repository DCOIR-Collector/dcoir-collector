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
- On the first substantive AFRICOM_SOC_IR / DCOIR turn of every new session, start with `dcoir-session-resume` and then `dcoir-memory-preflight` before other substantive project work.
- Resume and governance begin with Project Instructions, then `CP-01`, then `CP-02`.
- The preferred operating posture is the validated GitHub connector low-level lane for chat-managed readable-text updates, with GitHub Desktop as the easiest approved operator path for bulk local placement, extracted-file ingestion, and binary or zip handling.
- When GitHub Desktop manual repo-update bundles are used, deliver only the affected repo-relative files and provide a suggested commit `Summary` unless the operator explicitly asks otherwise.
- Helper skills are used for analysis, validation, packaging, workflow support, and maintenance where appropriate.
- The collector runtime filename remains stable while the readable governed source set may evolve for maintainability.

## Core Deliverables

### 1. DCOIR collector and validation line
- `project_sources/DCOIR_Collector.ps1` as the canonical runtime collector
- `project_sources/collector_parts/*.ps1` as the governed readable collector source set
- `project_sources/run_DCOIR_Tests.ps1` as the regression and validation harness

### 2. Analyst-facing DCOIR standalone master prompt
A combined analyst-facing prompt built from the governed modular prompt-pack that an analyst can paste into an LLM chat to perform disciplined baseline triage, enrichment review, retrieved-artifact review, and final case synthesis for DCOIR collector artifacts.

Current authority chain:
- `project_sources/PP-01_System_Prompt_v1_0_1.txt`
- `project_sources/PP-02_Output_Schema_v1_0_0.txt`
- `project_sources/PP-03_Baseline_Triage_Prompt_v1_0_0.txt`
- `project_sources/PP-04_Enrichment_Review_Prompt_v0_1_1.txt`
- `project_sources/PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt`
- `project_sources/PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt`
- `project_sources/PP-07_Agent_Guardrails_v1_0_0.txt`
- `project_sources/PP-08_Combined_Analyst_Facing_Master_Prompt_v1_0_0.txt` as the current runtime parity output

### 3. Gemini Enterprise triage and DCOIR agent system
A fully developed Gemini parent-agent and sub-agent system that merges Elastic alert triage with DCOIR escalation, collection, enrichment, artifact review, and synthesis while preserving evidence-first DFIR discipline, bounded confidence, and exact command-lane separation.

Current authority chain:
- `project_sources/DOC-04_DCOIR_Viable_Deliverable_Generation_Contract_v1_0_0.txt`
- `project_sources/DOC-07_DCOIR_Gemini_Live_Test_Generation_And_Legacy_Surface_Rules_v1_0_0.txt`
- `project_sources/DOC-08_DCOIR_Gemini_Legacy_Surface_Inventory_And_Hygiene_Plan_v1_0_0.txt`
- `project_sources/PP-09_Gemini_Enterprise_Agent_Designer_Generator_Workflow_v1_0_0.txt`
- `project_sources/PP-10_Gemini_Enterprise_Agent_Designer_Bounded_Design_Artifact_v0_1_1.txt`
- `knowledge/generated_agent_markdowns/` as the readable generated-agent working surface
- `knowledge/comparative_reference_agent_markdowns/` as the readable comparative-reference working surface
- `supporting_assets/generated_agent_markdowns.zip`, `supporting_assets/comparative_reference_agent_markdowns.zip`, and `supporting_assets/supporting_knowledge_docs.zip` as retained delivery artifacts rather than editable readable authority

Current topology target:
- 1 parent orchestrator
- 7 sub-agents
- merged Elastic alert triage plus DCOIR collection, enrichment, artifact review, and final synthesis

Legacy and reference notes:
- `project_sources/DCOIR_Gemini_Email_Build_Bundle_v1_1_0/` is retained as extracted legacy reference material for structure and naming only.
- `project_sources/original_alert_triage_gemini_agents/` is retained as the approved verbosity and field-quality benchmark set.
- `project_sources/original_collector_artifact_gemini_agents/` is retained as a failure-reference surface for thin collector-oriented output.
- `project_sources/legacy_reference_gemini_agents/` is the governed home for clearly labeled manual or curated legacy Gemini captures with ongoing reference value.

### 4. Project control plane and continuity layer
The governed manifest, change log, workflow/layout guidance, todo and handoff structure, and task-memory bank that keep the project resumable, auditable, and maintainable across sessions.

### 5. Knowledge and documentation layer
Human-readable workflow, usage, and supporting knowledge documents that explain how to use, maintain, validate, and extend the project.

### 6. Governed helper-skill source and maintenance layer
The `dcoir-*` helper skills under `dcoir_skills/` that support routing, validation, packaging, maintenance, and workflow control for project-side work.

## Repository Navigation

- [project_sources](project_sources/) — control plane, logs, prompt-pack sources, collector sources, current Gemini governance docs, and extracted readable project-source folders
- [knowledge](knowledge/) — knowledge docs, routing notes, connector reference material, generated/comparative Gemini markdowns, and task memory
- [dcoir_skills](dcoir_skills/) — governed helper-skill source root for current DCOIR skills
- [project_settings](project_settings/) — bootstrap and settings surfaces used for Project-space anchoring
- [release_notes](release_notes/) — release instructions and bounded handoff notes when a bundle needs them
- [supporting_assets](supporting_assets/) — retained non-authoritative assets and delivery artifacts

## Documentation Direction

The documentation goal is to make the repository understandable without hidden context. Current priorities include:
- stronger local-guide README surfaces at the repo root and major folders
- a fuller wiki-style knowledge structure in `knowledge/`
- maintained helper-skill routing guidance
- clearer documentation of the modular prompt-pack, standalone master prompt, Gemini design line, DFIR operating posture, and enrichment model
- one current operator-facing Gemini build path and clear labeling for generated, comparative, retained, and legacy Gemini surfaces
- documentation and validation guidance that stays aligned to the current governed working line instead of historical assumptions
