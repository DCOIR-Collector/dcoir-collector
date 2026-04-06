# Project Sources

Purpose
- Store the authoritative readable project source set here in native formats where possible.

What belongs here
- CP control-plane files
- DOC evergreen workflow and layout files
- LOG situational continuity and decision logs
- PP modular prompt-pack files
- collector and harness sources
- rollback or release-scope text sources
- extracted readable Gemini source folders with ongoing project value

Current important surfaces
- `CP-01_DCOIR_Version_Manifest.txt` and `CP-02_DCOIR_Change_Log.txt` — current control-plane pair
- `LOG-01_DCOIR_Todo_Log.txt`, `LOG-01_DCOIR_Todo_Index.txt`, and `todo/*.txt` — current actionable queue
- `DCOIR_Collector.ps1` and `run_DCOIR_Tests.ps1` — current runtime and harness entry points
- `PP-01` through `PP-07` — authoritative modular prompt-pack source line
- `PP-08_Combined_Analyst_Facing_Master_Prompt_v1_0_0.txt` — current standalone runtime parity prompt
- `PP-09_Gemini_Enterprise_Agent_Designer_Generator_Workflow_v1_0_0.txt` — current authoritative Gemini generation workflow
- `PP-10_Gemini_Enterprise_Agent_Designer_Bounded_Design_Artifact_v0_1_1.txt` — current authoritative bounded Gemini design artifact
- `DOC-05_DCOIR_Helper_Skill_Workflow_And_GitHub_Source_Rules.txt` and `DOC-06_DCOIR_GitHub_Helper_Skill_Source_Layout_And_Rollout.txt` — current helper-skill workflow governance

Current extracted readable project-source folders
- `project_sources/DCOIR_Gemini_Email_Build_Bundle_v1_1_0/` — extracted legacy reference bundle; not current operator build authority
- `project_sources/original_alert_triage_gemini_agents/` — historical extracted reference material
- `project_sources/original_collector_artifact_gemini_agents/` — historical extracted reference material

How to use this folder
- Treat files marked current in the manifest as authoritative governed readable sources.
- Treat the prompt-pack and Gemini deliverable line as an authority chain, not as isolated files:
  - PP-01 through PP-07 as design-time authority
  - PP-08 as standalone runtime parity output
  - PP-09 and PP-10 as the current Gemini workflow and bounded design authority
- Keep extracted readable source folders integrated into the long-term documentation and knowledge structure instead of leaving them as isolated dumps.
- Use runtime filenames in operator-facing instructions and keep repo paths for provenance.
- Do not let extracted legacy reference bundles override the current PP-09 or PP-10 line.
