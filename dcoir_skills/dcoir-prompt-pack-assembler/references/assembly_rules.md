# Assembly Rules

## Purpose
This skill assembles one combined analyst-facing master prompt draft from the current validated modular prompt-pack source files.

## Gate model
The skill is valid only when all of these are true:
- one manifest file is resolvable by control-plane role
- one change log file is resolvable by control-plane role
- one setup/workflow file is resolvable by control-plane role
- the manifest lists the current prompt-pack modules
- the manifest lists a current guardrails module
- every listed current prompt-pack file exists in the workspace
- no unexpected current modular prompt-pack role appears in the manifest after excluding approved non-modular prompt-pack entries

Preferred current control-plane names:
- `CP-01_DCOIR_Version_Manifest.txt`
- `CP-02_DCOIR_Change_Log.txt`
- `DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt`

Legacy aliases that may still appear in older workspaces:
- `DCOIR_Version_Manifest.txt`
- `DCOIR_Change_Log.txt`
- `AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt`

## Approved non-modular current prompt-pack entries to ignore
- `PromptPack_Combined_Master_Prompt_Current`
- `PromptPack_Gemini_Generator_Workflow_Current`
- `PromptPack_Gemini_Bounded_Design_Artifact_Current`

## Canonical current module set
The assembler expects these module types:
- system
- output_schema
- baseline_triage
- enrichment_review
- retrieved_artifact_review
- final_case_synthesis
- guardrails

## Canonical order
1. system
2. output_schema
3. baseline_triage
4. enrichment_review
5. retrieved_artifact_review
6. final_case_synthesis
7. guardrails

## Classification hints
Prefer manifest role keys when available. Fall back to stable lowercase token matching on filenames:
- `promptpack_system` or `system_prompt` -> system
- `promptpack_output_schema` or `output_schema` -> output_schema
- `promptpack_baseline_triage` or `baseline_triage` -> baseline_triage
- `promptpack_enrichment_review` or `enrichment_review` -> enrichment_review
- `promptpack_retrieved_artifact_review` or `retrieved_artifact_review` -> retrieved_artifact_review
- `promptpack_final_case_synthesis` or `final_case_synthesis` -> final_case_synthesis
- `promptpack_agent_guardrails` or `guardrail` or `guardrails` -> guardrails

## Staleness rule
If the manifest introduces a new current modular prompt-pack role that is not in the approved ignore list and cannot be classified into the canonical set above, the skill is stale and must stop.

## Output wrapper rule
The combined draft may add only minimal deterministic wrapper text:
- generated-draft banner
- source-of-truth note pointing back to the modular files
- included-source list
- clear module boundaries

Do not paraphrase, summarize, or rewrite module content during assembly.
