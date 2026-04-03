---
name: dcoir-operator-workflow-hardener
description: harden and normalize operator-facing dcoir workflow guidance for elastic endpoint execution, collector staging, bundle retrieval, cleanup, and pasted collector-output interpretation. use when chatgpt must tell the operator the exact next endpoint step, interpret dcoir collector output, choose between endpoint and local execution lanes, normalize runtime filenames, explain next_get_file or cleanup handling, or keep collection and enrichment flows aligned to the current control plane with minimal ambiguity. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Operator Workflow Hardener

## Overview

Use this skill whenever DCOIR work crosses from project maintenance into operator execution guidance.

This skill is for live workflow guidance, not source promotion. It helps ChatGPT choose the right execution lane, interpret pasted collector output, normalize the next operator step, and keep endpoint collection, enrich-session handling, retrieval guidance, and cleanup guidance aligned with the current DCOIR control plane.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.


1. Resolve the current manifest first, preferring `CP-01_DCOIR_Version_Manifest.txt`.
2. Resolve the current change log second, preferring `CP-02_DCOIR_Change_Log.txt`.
3. Treat only files marked current in the manifest as authoritative uploaded project-readable sources.
4. Use the readable uploaded collector source for reasoning and the emitted runtime name for operator commands.
5. Stop if the control plane is missing or inconsistent.

## Core defaults

- For endpoint-side actions, use Elastic Defend response-action syntax only.
- For analyst workstation or local test steps, use Windows PowerShell 5.1 syntax only.
- Do not blend endpoint syntax and local syntax in one malformed instruction.
- When reasoning from the current GitHub-readable collector source `project_sources/DCOIR_Collector.ps1`, document operator runtime execution as `DCOIR_Collector.ps1`.
- Prefer one best next action when the operator is trying to move a live workflow forward.
- When collector output contains explicit `NEXT_GET_FILE`, `CLEANUP_COMMAND`, or `DELETE_SCRIPT_COMMAND` markers, treat them as high-priority operator cues.
- Default to deeper regression for any scriptable or reproducible workflow helper before live use and after patches when testing is part of the task.

## Main use cases

### 1. Exact next-step guidance
Use this path when the operator asks what to do next after staging or running the collector.

Workflow:
1. Identify whether the user is in endpoint execution, analyst workstation review, or project-maintenance context.
2. If the context is endpoint execution, prefer the exact next Elastic action over a broad menu.
3. If the context is local analysis, prefer one PowerShell 5.1 command or one narrow review step.
4. Keep the answer bounded to the reviewed scope.

### 2. Pasted collector-output interpretation
Use this path when the user pastes DCOIR collector output or asks what `NEXT_GET_FILE`, `CLEANUP_COMMAND`, or enrich-session output means.

Workflow:
1. Run `scripts/parse_dcoir_collector_output.py` when the pasted output is long enough that normalization helps.
2. Identify explicit machine-readable markers first.
3. Map the output to one of these workflow phases:
   - collect complete / retrieve bundle
   - enrich session started
   - enrich session add-more phase
   - enrich finalized / retrieve enrich bundle
   - cleanup ready or cleanup complete
   - analyst interpretation cue only
4. Give the single best next action first.
5. Mention cleanup timing when the output explicitly says to keep the run until cleanup.

### 3. Lane normalization
Use this path when the request mixes endpoint execution with analyst-workstation review.

Workflow:
1. Decide which lane the user actually needs now.
2. Normalize to a single lane.
3. If the user needs both lanes, present them sequentially, never blended into one malformed command.

### 4. Retrieval and cleanup handling
Use this path when the operator asks what to retrieve, when to run cleanup, or whether to delete the uploaded script.

Defaults:
- If `NEXT_GET_FILE` is present, retrieval is usually the next live operator action.
- If cleanup is available but the output says to keep the current run until cleanup is explicitly run, do not imply cleanup already happened.
- `DELETE_SCRIPT_COMMAND` is not the same thing as cleanup; treat it as a separate explicit action cue.

## Output contract

Use this default output order when giving operator guidance:
1. **Current assessment** — one sentence.
2. **Best next action** — exactly one action if one is clearly strongest.
3. **Why** — one short explanation tied to the reviewed output or workflow state.
4. **Optional follow-on** — only if the operator would predictably need the immediately next step after the one above.

When the user asks only for command syntax, give only the command lane they need.

## Script usage

Normalize pasted collector output with:

```bash
python scripts/parse_dcoir_collector_output.py --input-file /path/to/collector_output.txt --output-json /tmp/dcoir_output_summary.json
```

Use the script when:
- the output is long
- there are multiple machine-readable markers
- you need a stable summary of retrieval, cleanup, delete-script, or workflow phase cues

You may also inspect the script output directly before answering.

## References

Load these references when needed:
- `references/workflow_phases.md`
- `references/output_contract.md`

## Hard rules

- Do not invent collector output fields that are not present.
- Do not claim cleanup happened unless the output shows it.
- Do not skip explicit retrieval cues in favor of a generic recommendation.
- Do not overrule the control plane or treat non-current sources as authoritative.
- Do not use browser-only behavior or UI assumptions as though they are guaranteed.
- Do not mix endpoint and local execution syntax in one command.
