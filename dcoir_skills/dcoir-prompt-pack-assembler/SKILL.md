---
name: dcoir-prompt-pack-assembler
description: assemble one combined dcoir analyst-facing master prompt draft from the current validated modular prompt-pack source files in the africom_soc_ir / dcoir project. use when chatgpt needs to build, refresh, validate, or reassemble the combined master prompt from the current modular set after control-plane review has already settled what is current. this skill is project-gated, class-prefix aware, uses the current files marked authoritative in the manifest, requires a current guardrails module, and should tolerate future control-plane filename drift when manifest roles remain clear. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Prompt Pack Assembler

Build one combined analyst-facing master prompt draft and one short assembly report from the current authoritative modular prompt-pack source files.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Before assembling anything, verify the current authoritative control files from the workspace.

Preferred current control-plane files:
- `CP-01_DCOIR_Version_Manifest.txt`
- `CP-02_DCOIR_Change_Log.txt`
- `DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt`

Legacy aliases that may still appear in older workspaces:
- `DCOIR_Version_Manifest.txt`
- `DCOIR_Change_Log.txt`
- `AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt`

Stop if the workspace does not contain one resolvable manifest, one resolvable change log, and one resolvable setup/workflow file.

Also stop if any of these conditions are true:
- the manifest does not list a current guardrails prompt-pack file
- a required current prompt-pack source file is missing from disk
- the manifest contains an unexpected current modular prompt-pack role that this skill does not know how to place
- the current prompt-pack set does not match the bundled assembly rules

## What this skill may do
- Read the current control files.
- Identify the current modular prompt-pack source set from the manifest.
- Ignore approved non-modular current prompt-pack entries such as the combined runtime prompt and Gemini workflow artifacts.
- Assemble one combined analyst-facing master prompt draft in canonical module order.
- Emit one short assembly report that records the included source files, assembly order, and output paths.
- Fail safely when the workspace or manifest drifts.

## What this skill must not do
- Do not decide what files are authoritative.
- Do not promote the generated draft into a Project source.
- Do not rewrite modular prompt-pack source content.
- Do not infer missing files.
- Do not assemble from candidate, rollback, or historical prompt files.
- Do not silently create a pre-guardrails combined draft.
- Do not emit a project-style promoted filename for the combined draft.

## Required outputs
Every successful execution must produce exactly these operator-facing files:
1. `dcoir_combined_master_prompt_draft.txt`
2. `dcoir_prompt_pack_assembly_report.txt`

These filenames must remain neutral draft outputs.

## Canonical module order
The combined draft must use this order:
1. system prompt
2. output schema
3. baseline triage
4. enrichment review
5. retrieved artifact review
6. final case synthesis
7. guardrails

Guardrails is mandatory. Refuse assembly if guardrails is not current.

## Robustness rules
- Prefer manifest role keys over brittle filename assumptions when both are available.
- Tolerate current and legacy control-plane names so long as one clear authoritative file for each role exists.
- Treat class-prefixed prompt filenames such as `PP-01_...` as normal current inputs.
- Continue to classify prompt modules by stable semantic tokens or manifest role hints rather than by one fixed collector version string.
- Ignore known non-modular current prompt-pack roles that are not assembly inputs, including the combined master runtime prompt and the Gemini workflow/design artifacts.
- Stop plainly if the manifest introduces a new current modular prompt-pack role that is outside the canonical set or otherwise unrecognized.

## Workflow
1. Resolve the manifest, change log, and setup/workflow file from the current workspace.
2. Run `scripts/assemble_dcoir_prompt_pack.py`.
3. Read `dcoir_prompt_pack_assembly_report.txt`.
4. If the script reports failure, explain the stop reason plainly and do not present the draft as valid.
5. If the script reports success, share the combined draft and assembly report.

## Command
```bash
python scripts/assemble_dcoir_prompt_pack.py --source-dir /mnt/data --output-dir /mnt/data/dcoir_prompt_pack_out
```

## Output handling
After the script runs:
- If assembly failed, report the exact gate or drift reason.
- If assembly succeeded, provide the draft file and the short report.
- Describe the draft as a generated runtime artifact, not a promoted Project source.
- Keep any recommendation bounded to operator review or later promotion work outside this skill.

## References
Use these bundled references when needed:
- `references/assembly_rules.md`
- `references/output_contract.md`
