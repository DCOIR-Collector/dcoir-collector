# Project Sources

Store the authoritative readable project source set here in native formats where possible.

## Purpose

Use `project_sources/` as the authoritative readable project-source root for the current DCOIR working line.
This folder contains the live control plane, evergreen workflow docs, dated decision and continuity logs, todo structure, collector and harness sources, prompt-pack sources, and extracted readable Gemini project materials that have ongoing governed value.

## Authority Notes

- `project_sources/` is part of the current governed readable working source set.
- Resume order still begins with Project Instructions, then `CP-01`, then `CP-02`, then the current continuity surfaces.
- Supporting assets and Knowledge docs remain separate supporting classes and should not replace the authoritative readable project-source set stored here.

## Control Plane and Continuity Navigation

### Current control-plane files
- `CP-01_DCOIR_Version_Manifest.txt` — current governed version manifest and current-state anchor.
- `CP-02_DCOIR_Change_Log.txt` — current change class, rationale, and validation summary.
- `DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt` — evergreen setup and workflow guide.
- `DOC-03_DCOIR_Repository_Layout_Spec_v1_0_0.txt` — evergreen layout model.
- `DOC-04_DCOIR_Structural_Refactor_Standard.txt` — structural refactor and readable-file growth rules.
- `DOC-05_DCOIR_Helper_Skill_Workflow_And_GitHub_Source_Rules.txt` — evergreen helper-skill workflow rules.
- `DOC-06_DCOIR_GitHub_Helper_Skill_Source_Layout_And_Rollout.txt` — evergreen helper-skill source layout and rollout rules.

### Current continuity surfaces
- `LOG-01_DCOIR_Todo_Log.txt` — authoritative long-form todo log.
- `LOG-01_DCOIR_Todo_Index.txt` — short-form active queue and best-next-move index.
- `LOG-03_DCOIR_Session_Handoff_Brief.txt` — current durable session handoff brief.
- `LOG-04_DCOIR_Helper_Skill_Workflow_Decisions_2026-04-03.txt` — helper-skill workflow decision record.
- `LOG-05_DCOIR_Session_Resume_Anchor_2026-04-03.txt` — dated resume anchor for the current session family.
- `LOG-06_DCOIR_GitHub_Skill_Source_Policy_Decision_2026-04-03.txt` — GitHub helper-skill source policy decision.
- `LOG-07_DCOIR_GitHub_Update_Lane_Choice_And_Connector_Limitation_2026-04-03.txt` — update-lane choice and procedure-recovery discipline.
- `LOG-08` through `LOG-13` — later workflow-decision records for tracker, enforcement, resume-gate, plan-tracker, and coordinated-campaign lines.
- `todo/` — split active, queued, documentation, structural, and deferred lanes.

## Current Source Groups in this Folder

### Collector and harness line
- `DCOIR_Collector.ps1` — canonical runtime collector.
- `collector_parts/*.ps1` — governed readable collector source set.
- `run_DCOIR_Tests.ps1` — current readable regression and validation harness.

### Prompt-pack and AI-workflow line
- `PP-*.txt` — current modular prompt-pack, combined master prompt, Gemini workflow source, and bounded Gemini design artifact sources.

### Extracted readable project-source folders
- `DCOIR_Gemini_Email_Build_Bundle_v1_1_0/` — extracted readable Gemini bundle content with ongoing project value.
- `original_alert_triage_gemini_agents/` — extracted readable alert-triage agent reference material.
- `original_collector_artifact_gemini_agents/` — extracted readable collector-artifact agent reference material.

## Recommended Contents

Use this folder for:
- CP control-plane files
- DOC evergreen files
- LOG situational logs
- PP modular prompt-pack files
- collector and harness sources
- rollback or release-scope text sources
- extracted readable Gemini source folders with ongoing project value

## Local Guidance

- Treat `project_sources/` as containing both evergreen workflow docs and situational continuity artifacts.
- Prefer current control-plane role and naming over brittle assumptions about older filenames.
- When a README or workflow note points to current project truth, this is the first local source root to inspect after Project Instructions.
