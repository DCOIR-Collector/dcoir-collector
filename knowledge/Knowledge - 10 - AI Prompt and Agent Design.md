# Knowledge - 10 - AI Prompt and Agent Design

| Field | Value |
| --- | --- |
| Scope | Current DCOIR prompt-pack, Gemini workflow, bounded design artifact, and merged alert-triage-to-collector direction |
| Primary project sources | PP-01 through PP-10 current files; DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt; LOG-01_DCOIR_Todo_Log.txt |
| Supporting assets | comparative_reference_agent_markdowns.zip; generated_agent_markdowns.zip; supporting_knowledge_docs.zip |

## What changed in the current design posture

- The current Gemini workflow now treats **Description** as a routing-critical field used for delegation and automatic routing.
- The current Gemini workflow now treats **Instructions** as a field that should be explicit, operationally detailed, and as full as needed to preserve agent behavior.
- The AFRICOM SOC Elastic Defend Triage parent and sub-agent markdowns are now approved comparative style references for DCOIR Gemini design work.
- Duplicate or near-duplicate data from purpose, role, and description fields should be merged into the runtime Description field when that improves routing quality.
- The current bounded design artifact now assumes a merged parent-agent topology where alert triage can explicitly escalate into DCOIR collection, enrichment, artifact review, and final synthesis.
- Generated companion markdowns for the parent agent and all sub-agents are now required deliverables alongside the bounded design artifact.

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

### Packaging
- Package generated agent markdowns as a supporting asset such as `generated_agent_markdowns.zip` unless the operator explicitly wants them uploaded individually.
- Package the Knowledge-doc set as `supporting_knowledge_docs.zip` for reduced Project upload friction.
