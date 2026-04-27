# Project Sources

Purpose
- Store the authoritative readable project source set here in native formats where possible.

What belongs here
- CP source/promoted-history files when retained for repo source-role checks, packaging/readback, or T99 review
- DOC evergreen workflow and layout files
- LOG situational continuity and decision logs
- PP modular prompt-pack files
- collector and harness sources
- rollback or release-scope text sources
- extracted readable Gemini source folders with ongoing project value

Current important surfaces
- `CP-01_DCOIR_Version_Manifest.txt` and `CP-02_DCOIR_Change_Log.txt` — retained source/promoted-history pair for repo source-role checks, packaging/readback, promoted-history comparison, or T99 keep/delete review; not normal startup authority when Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` is present/current
- `LOG-01_DCOIR_Todo_Log.txt`, `LOG-01_DCOIR_Todo_Index.txt`, and `todo/*.txt` — retired queue/migration history unless Airtable explicitly reauthorizes them
- `DCOIR_Collector.ps1` and `run_DCOIR_Tests.ps1` — current runtime and harness entry points
- `PP-01` through `PP-07` — authoritative modular prompt-pack source line
- `PP-08_Combined_Analyst_Facing_Master_Prompt_v1_0_0.txt` — current standalone runtime parity prompt when retained and current
- `PP-09_Gemini_Enterprise_Agent_Designer_Generator_Workflow_v1_0_0.txt` — current authoritative Gemini generation workflow when retained and current
- `PP-10_Gemini_Enterprise_Agent_Designer_Bounded_Design_Artifact_v0_1_1.txt` — current authoritative bounded Gemini design artifact when retained and current
- `DOC-04_DCOIR_Viable_Deliverable_Generation_Contract_v1_0_0.txt` — durable viable-generation contract for fresh standalone and Gemini deliverables
- `DOC-07_DCOIR_Gemini_Live_Test_Generation_And_Legacy_Surface_Rules_v1_0_0.txt` — governed April 7 live-test generation and legacy-surface rules
- `DOC-08_DCOIR_Gemini_Legacy_Surface_Inventory_And_Hygiene_Plan_v1_0_0.txt` — bounded legacy-surface inventory and hygiene plan
- `DOC-05_DCOIR_Helper_Skill_Workflow_And_GitHub_Source_Rules.txt` and `DOC-06_DCOIR_GitHub_Helper_Skill_Source_Layout_And_Rollout.txt` — current helper-skill workflow governance when retained and current

Current extracted readable project-source folders
- `project_sources/DCOIR_Gemini_Email_Build_Bundle_v1_1_0/` — extracted legacy reference bundle for structure and naming only; not current operator build authority
- `project_sources/original_alert_triage_gemini_agents/` — historical extracted benchmark reference material for verbosity and field quality
- `project_sources/original_collector_artifact_gemini_agents/` — historical extracted failure-reference material for thin collector-oriented output
- `project_sources/legacy_reference_gemini_agents/` — governed home for clearly labeled manual or curated legacy Gemini captures with ongoing reference value

How to use this folder
- Treat files marked current in the current manifest as authoritative governed readable sources while they remain in the retained repo.
- If final repo reduction later removes or relocates a file named here, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Retained Repo Manifest`, `Queue Control`, `Work Items`, `Plans`, and `Plan Tasks` to establish live operating state and record the missing retained source as a validation finding.
- Treat the prompt-pack and Gemini deliverable line as an authority chain, not as isolated files:
  - PP-01 through PP-07 as design-time behavioral authority
  - PP-08 as standalone runtime parity output
  - PP-09 and PP-10 as the current Gemini workflow and bounded design authority
  - DOC-04, DOC-07, and DOC-08 as the current durable generation and legacy-handling guidance
- Keep extracted readable source folders integrated into the long-term documentation and knowledge structure instead of leaving them as isolated dumps.
- Use runtime filenames in operator-facing instructions and keep repo paths for provenance.
- Do not let extracted legacy reference bundles override the current PP-09 or PP-10 line.
- Use DOC-08 before broader moves, renames, or archival consolidation involving Gemini legacy/reference surfaces.
