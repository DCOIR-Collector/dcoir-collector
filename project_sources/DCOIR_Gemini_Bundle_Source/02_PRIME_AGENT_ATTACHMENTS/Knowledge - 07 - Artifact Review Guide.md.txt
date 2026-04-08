# Knowledge - 07 - Artifact Review Guide

_How the current prompt-pack and combined-master-prompt line expects analysts to review DCOIR artifacts_

**Summary:** This guide summarizes the current evidence-driven review flow used by the DCOIR prompt-pack line and the promoted combined analyst-facing master prompt runtime source.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | PP-01_System_Prompt_v1_0_1.txt; PP-02_Output_Schema_v1_0_0.txt; PP-03_Baseline_Triage_Prompt_v1_0_0.txt; PP-04_Enrichment_Review_Prompt_v0_1_1.txt; PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt; PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt; PP-07_Agent_Guardrails_v1_0_0.txt; PP-08_Combined_Analyst_Facing_Master_Prompt_v1_0_0.txt |
| Official external sources | Not required for this page |
| Scope note | This page is project-grounded; it does not redefine the schema or the prompts. |

## Current review sequence

- Review baseline collection output first.
- Review the merged baseline report and the flat final_artifacts output.
- Identify suspicious findings, notable absences, and the next best enrichment step.
- Review enrichment output as it is produced.
- Review retrieved files or raw exports in retrieved artifact review mode when they are staged.
- Treat scripts, configs, scheduled-task XML, registry exports, and event-log-derived excerpts as evidence-first artifact-review inputs rather than enrichment-only narrative.
- End with final case synthesis after enough reviewed evidence exists to support a case-level conclusion.

## Review posture

- Treat user-provided case artifacts as the primary source of truth.
- Separate observed evidence, inference, uncertainty, and recommendations.
- Do not overstate confidence, maliciousness, benignity, or batch completeness.
- Recommend one best next step when possible rather than shotgun lists.

## Common input priority

| Priority | Preferred artifact |
| --- | --- |
| 1 | Merged baseline report |
| 2 | Metadata report |
| 3 | Flat final_artifacts baseline outputs |
| 4 | Enrichment report content and staged retrieval handoff |
| 5 | Retrieved script, config, task XML, registry export, or event-log-derived excerpt |
| 6 | Final case synthesis only after the reviewed evidence chain is broad enough to justify case-level closure or decision support |

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
