# DCOIR Repo Layout Rules

## Project gate

Resolve the current control plane by role.

Preferred current control-plane files:
- `CP-01_DCOIR_Version_Manifest.txt`
- `CP-02_DCOIR_Change_Log.txt`
- `DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt`
- `DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt`

Legacy aliases may be accepted only when the bundled mapping rules explicitly include them.

Stop if the control-plane roles cannot be resolved.

## Canonical repo tree

- `DCOIR_Project/`
  - `stable/`
    - `assets/`
  - `rollback/`
  - `control_plane/`
  - `docs/`
  - `logs/`
  - `prompts/`
  - `knowledge/`
  - `bundles/`

## Current source mapping

- `project_sources/DCOIR_Collector.ps1` -> `stable/DCOIR_Collector.ps1`
- `project_sources/run_DCOIR_Tests.ps1` -> `stable/run_DCOIR_Tests.ps1`
- `DCOIR_Collector.zip` -> `stable/assets/DCOIR_Collector.zip`
- `RB-01_DCOIR_Collector_refinement_2_1_3.txt` -> `rollback/RB-01_DCOIR_Collector_refinement_2_1_3.txt`
- `CP-01_DCOIR_Version_Manifest.txt` -> `control_plane/CP-01_DCOIR_Version_Manifest.txt`
- `CP-02_DCOIR_Change_Log.txt` -> `control_plane/CP-02_DCOIR_Change_Log.txt`
- `DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt` -> `docs/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt`
- `DOC-02_DCOIR_Project_Transition_Checklist.txt` -> `docs/DOC-02_DCOIR_Project_Transition_Checklist.txt`
- `DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt` -> `docs/DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt`
- `README.md` -> `README.md`
- `LOG-01_DCOIR_Todo_Log.txt` -> `logs/LOG-01_DCOIR_Todo_Log.txt`
- `LOG-01_DCOIR_Todo_Index.txt` -> `logs/LOG-01_DCOIR_Todo_Index.txt`
- `project_sources/todo/*.txt` -> `logs/todo/*.txt`
- `LOG-02_DCOIR_Lessons_Learned_Log.txt` -> `logs/LOG-02_DCOIR_Lessons_Learned_Log.txt`
- `LOG-03_DCOIR_Session_Handoff_Brief.txt` -> `logs/LOG-03_DCOIR_Session_Handoff_Brief.txt`
- `PP-01_System_Prompt_v1_0_1.txt` -> `prompts/PP-01_System_Prompt_v1_0_1.txt`
- `PP-02_Output_Schema_v1_0_0.txt` -> `prompts/PP-02_Output_Schema_v1_0_0.txt`
- `PP-03_Baseline_Triage_Prompt_v1_0_0.txt` -> `prompts/PP-03_Baseline_Triage_Prompt_v1_0_0.txt`
- `PP-04_Enrichment_Review_Prompt_v0_1_1.txt` -> `prompts/PP-04_Enrichment_Review_Prompt_v0_1_1.txt`
- `PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt` -> `prompts/PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt`
- `PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt` -> `prompts/PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt`
- `PP-07_Agent_Guardrails_v1_0_0.txt` -> `prompts/PP-07_Agent_Guardrails_v1_0_0.txt`
- `supporting_knowledge_docs.zip` -> `stable/assets/supporting_knowledge_docs.zip`
- `comparative_reference_agent_markdowns.zip` -> `stable/assets/comparative_reference_agent_markdowns.zip`
- `generated_agent_markdowns.zip` -> `stable/assets/generated_agent_markdowns.zip`
- `SET-06_AFRICOM_SOC_IR_Project_Instructions_v15.txt` -> update mode only under `project_settings/` when available on disk
- `GITHUB_WORKING_REPOSITORY_NOTE.md` -> update mode only under `project_settings/` when available on disk

## Hard rules

- Strip only the terminal `.txt` from known double-extension runtime mirrors.
- Keep package assets such as `.zip` unchanged.
- Keep Knowledge docs unchanged as `.md.txt`.
- Do not emit extra files.
- Do not guess where unknown files belong.
- If the manifest current file set differs from this mapping, stop and require a skill update.
- PP-08 through PP-10 are current project sources and must be packaged under `prompts/` in repo mode and `project_sources/` in update mode.
- In the current workspace model, per-file Knowledge docs are not expected in the Project root unless the mapping rules explicitly reintroduce them.
- Prefer class-prefix role resolution over brittle assumptions about one historical filename set.
