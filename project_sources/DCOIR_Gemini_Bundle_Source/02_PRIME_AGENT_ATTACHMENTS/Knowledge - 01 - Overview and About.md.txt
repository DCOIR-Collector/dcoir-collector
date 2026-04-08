# Knowledge - 01 - Overview and About

_AFRICOM_SOC_IR / DCOIR project context and supporting knowledge-doc charter_

**Summary:** This page explains what the current DCOIR project is, what is authoritative, and how the maintained Knowledge-doc set supports the workflow without becoming control-plane authority.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/CP-01_DCOIR_Version_Manifest.txt; project_sources/CP-02_DCOIR_Change_Log.txt; project_sources/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; project_sources/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt; project_sources/LOG-01_DCOIR_Todo_Log.txt |
| Official external sources | Not required for this page |
| Scope note | Generated from the current GitHub-primary control plane and maintained supporting knowledge lane. |

## Current project posture

- The GitHub repository `malwaredevil/dcoir-collector` is the sole working source for governed readable text files.
- Project Instructions, `project_sources/CP-01_DCOIR_Version_Manifest.txt`, and `project_sources/CP-02_DCOIR_Change_Log.txt` form the default control plane for current-state work.
- The current collector runtime is `project_sources/DCOIR_Collector.ps1` and the current local regression harness is `project_sources/run_DCOIR_Tests.ps1`.
- The governed helper-skill source lives under `dcoir_skills/` and now supports grouped GitHub Desktop repo-update bundles, batched skill-install waves, and bounded current-state resume behavior.
- The maintained Knowledge-doc set under `knowledge/` is supporting human-readable documentation only. It helps explain the current workflow but never overrides the control plane.

## Source classes that matter

| Class | Examples | How to treat it |
| --- | --- | --- |
| Control plane | Project Instructions; `project_sources/CP-01_DCOIR_Version_Manifest.txt`; `project_sources/CP-02_DCOIR_Change_Log.txt` | Authoritative for current status, governance, and what is current |
| Governed GitHub-readable sources | `project_sources/DCOIR_Collector.ps1`; `project_sources/run_DCOIR_Tests.ps1`; current prompt-pack and workflow files | Authoritative when marked current in the manifest |
| Supporting assets | `supporting_assets/DCOIR_Collector.zip`; `supporting_assets/supporting_knowledge_docs.zip` | Important for delivery or local execution, but not control-plane authority |
| Knowledge docs | `knowledge/Knowledge - ## - *.md` | Supporting human-readable docs only; never override the control plane |

## What this Knowledge-doc set is for

- Give the operator readable explanations of the current collector, harness, workflow, enrichment, artifact-review, and AI-design posture.
- Stay grounded in current approved sources and official vendor references where external truth is required.
- Keep stable filenames so the docs can be refreshed as a current maintained set without changing authority rules.
- Support GitHub-primary maintenance while still allowing a retained `supporting_knowledge_docs.zip` delivery asset when the workflow still wants that convenience bundle.
- Reduce stale guidance drift by refreshing affected doc clusters together when the same outdated source-name or delivery-model assumption appears on multiple current pages.

## Current planned Knowledge-doc pages

- Overview and About
- Elastic Quick Start
- Local Test and Regression
- Tier 1 Collect Runbook
- Tier 2 Collect Runbook
- Enrichment Actions
- Artifact Review Guide
- Troubleshooting
- FAQ
- AI Prompt and Agent Design
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
