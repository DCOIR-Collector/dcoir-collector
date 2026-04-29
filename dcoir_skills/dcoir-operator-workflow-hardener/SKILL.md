---
name: dcoir-operator-workflow-hardener
description: harden and normalize operator-facing dcoir workflow guidance for elastic endpoint execution, collector staging, retrieval, cleanup, and output interpretation.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-operator-workflow-hardener|SKILL.md -->

# DCOIR Operator Workflow Hardener

## Airtable operational schema alignment
Airtable cutover and skill cutover are complete. Use the current Airtable schema as live operational authority, not historical migration or cleanup plans.

Use `references/airtable_operational_schema_contract.md` for durable rules covering:
- current live authority tables
- idea-to-work-item-to-plan promotion
- Delete Queue deletion requests and dependency order
- DCOIR Lifecycle Ledger readback/history events
- Local Configuration Registry secret-safe configuration references

Do not assume retired or absent tables exist. In particular, do not require `Plan Tasks`, `Plan Checkpoints`, `Skill State Registry`, `Schema Registry`, `Tracking Registry`, `Repo File Coverage Detail`, or `Retained Repo Manifest` unless live Airtable schema readback proves the table exists for the current task.

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Work Items for task execution`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, explicit repo cleanup/source-role review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo Surface Registry supporting evidence`, `Repo Surface Registry retained-state evidence`, and active plan state before stopping.


## Overview

Use this skill whenever DCOIR work crosses from project maintenance into operator execution guidance.

This skill is for live workflow guidance, not source promotion. It helps ChatGPT choose the right execution lane, interpret pasted collector output, normalize the next operator step, and keep endpoint collection, enrich-session handling, retrieval guidance, and cleanup guidance aligned with the current DCOIR control plane.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.


1. Resolve Airtable-first startup/control-plane authority first for live workflow state.
2. Read GitHub `CP-01`/`CP-02` only when the immediate workflow question depends on governed repo source roles or promoted-history comparison.
3. Treat only files marked current in the manifest as authoritative governed GitHub-readable sources.
4. Use the current GitHub-readable collector source for reasoning and the emitted runtime name for operator commands.
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
Use this path when the operator asks what to retrieve, when to run cleanup, or whether to delete the staged collector script.

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
