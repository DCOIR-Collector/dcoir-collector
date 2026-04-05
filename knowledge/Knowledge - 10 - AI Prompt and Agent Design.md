# Knowledge - 10 - AI Prompt and Agent Design

_The current prompt-pack, Gemini workflow, and supporting design-artifact posture_

**Summary:** This page summarizes the current DCOIR prompt-pack and Gemini design posture, including how supporting markdown bundles and knowledge-doc delivery assets should stay aligned without becoming control-plane authority.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/PP-01_System_Prompt_v1_0_1.txt; project_sources/PP-02_Output_Schema_v1_0_0.txt; project_sources/PP-03_Baseline_Triage_Prompt_v1_0_0.txt; project_sources/PP-04_Enrichment_Review_Prompt_v0_1_1.txt; project_sources/PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt; project_sources/PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt; project_sources/PP-07_Agent_Guardrails_v1_0_0.txt; project_sources/PP-08_Combined_Analyst_Facing_Master_Prompt_v1_0_0.txt; project_sources/PP-09_Gemini_Enterprise_Agent_Designer_Generator_Workflow_v1_0_0.txt; project_sources/PP-10_Gemini_Enterprise_Agent_Designer_Bounded_Design_Artifact_v0_1_1.txt |
| Official external sources | Not required for this page |
| Scope note | This page is project-grounded; it does not redefine the schema or the prompt sources. |

## What changed in the current design posture

- The current Gemini workflow treats **Description** as a routing-critical field used for delegation and automatic routing.
- The current Gemini workflow treats **Instructions** as a field that should be explicit, operationally detailed, and as full as needed to preserve agent behavior.
- The AFRICOM SOC Elastic Defend Triage parent and sub-agent markdowns remain approved comparative style references for DCOIR Gemini design work.
- Duplicate or near-duplicate data from purpose, role, and description fields should be merged into the runtime Description field when that improves routing quality.
- The current bounded design artifact assumes a merged parent-agent topology where alert triage can explicitly escalate into DCOIR collection, enrichment, artifact review, and final synthesis.
- Generated companion markdowns for the parent agent and all sub-agents remain required deliverables alongside the bounded design artifact.

## Practical guidance for future Gemini design work

### Description field
- Put the strongest routing, scope, orchestration, and task-selection language here.
- Treat the field as if ADK will use it to decide where work should go.
- Include what the agent does, what inputs it expects, what outputs it controls, what domains it operates in, and when it should be selected.

### Instructions field
- Use detailed instructions that preserve startup behavior, workflow order, evidence discipline, tool behavior, error handling, stop conditions, and output format.
- Do not rely on short instructions when the agent behavior is complex.
- Preserve environment and command-lane separation explicitly.

### Comparative references
- Use comparative reference agent markdowns for style, density, and role-shaping.
- Do not let comparative references override DCOIR behavior or control-plane authority.
- Prefer to absorb the best structural lessons from those references while keeping DCOIR evidence discipline intact.

### Packaging and delivery posture
- Package generated agent markdowns as a supporting asset such as `generated_agent_markdowns.zip` when the workflow still wants a retained delivery bundle.
- Keep the editable working sources in GitHub-readable project files; do not treat retained ZIPs as the source of truth.
- Refresh `supporting_knowledge_docs.zip` only when the maintained human-readable Knowledge-doc set is intentionally being regenerated or re-delivered.
- Prefer grouped GitHub Desktop repo-update bundles and batched manual-install waves when compatible supporting-document and helper-skill fixes are already known.
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
