---
name: dcoir-live-test-remediation-planner
description: turn dcoir live-test findings into a ranked remediation plan with impacted files, helper-skill refreshes, deep-regression requirements, packaging posture, and stop conditions. use when chatgpt needs to decide what to fix first after live operator testing, gemini workflow validation, collector workflow issues, output-quality findings, packaging drift, any other dcoir validation result that needs explicit remediation sequencing, or when the workflow should read and update the dcoir-live-test-remediation-planner GitHub skill-memory file in malwaredevil/dcoir-collector. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Live Test Remediation Planner

Use this skill to convert live-test findings into an explicit remediation queue and verification plan.

## Core workflow
1. Read the current manifest first.
2. Read the current change log second.
3. Use the current todo log and current handoff brief as supporting context for active remediation themes.
4. Identify the live-test findings, defects, or operator-friction notes from the user request.
5. Run `scripts/plan_live_test_remediation.py` with the findings.
6. Read the generated markdown and json reports.
7. When the remediation state changed materially, use the GitHub connector directly to read or update the canonical GitHub memory file defined in `references/github_memory_workflow.md`, reducing operator burden to the smallest bounded manual GitHub action only when the connector cannot safely complete the write.
8. Return the ranked remediation order, impacted sources, deep-regression requirements, recommended packaging posture, and any GitHub-memory change that matters.

## Inputs this skill supports
- Explicit live-test findings as separate `--finding` values
- Short natural-language summaries of validation failures when ChatGPT can confidently split them into distinct findings before running the script
- Findings from Gemini workflow validation, collector execution guidance, output interpretation, packaging drift, or large-file fallback behavior

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Before planning remediation, verify the current authoritative control-plane files from the workspace.

Preferred current files:
- `CP-01_DCOIR_Version_Manifest.txt`
- `CP-02_DCOIR_Change_Log.txt`
- `LOG-01_DCOIR_Todo_Log.txt`
- `LOG-03_DCOIR_Session_Handoff_Brief.txt`

Stop if the manifest or change log cannot be resolved.

## GitHub-backed skill memory

Project preference: prefer the GitHub connector directly for governed readable-text updates and helper-memory persistence whenever the connector can complete the operation safely. Use the smallest bounded manual GitHub action only when connector limitations prevent safe in-chat completion.



Use the GitHub connector directly against repository `malwaredevil/dcoir-collector` when reusable remediation state should persist outside the current chat.

GitHub skill-memory layout:
- root folder: `dcoir_skill_memory/`
- per-skill folder: `dcoir_skill_memory/dcoir-live-test-remediation-planner/`
- canonical memory file: `dcoir_skill_memory/dcoir-live-test-remediation-planner/live_test_remediation_memory.md`

Use this memory surface for helper working state such as:
- active ranked remediation items still in flight
- recurring findings patterns worth checking before later remediation work
- deep-regression watch items that should remain visible before calling the queue clear

Rules:
- re-anchor to Project Instructions, then CP-01, then CP-02 before reading or writing the memory file
- treat the GitHub memory file as helper working state only, not control-plane authority
- keep one canonical markdown file and update it through the GitHub connector directly when the available connector action surface can complete the modification safely
- if the GitHub connector cannot safely complete the write, say that plainly and reduce the operator burden to the smallest bounded manual GitHub action or surface the markdown content for later commit

When rendering memory content locally, use `scripts/render_live_test_remediation_memory.py`.

## Hard rules
- Do not treat live-test findings as fixed until the repaired path is re-tested.
- Default to deep regression for any remediation affecting a skill, script, packaging path, or operator guidance that can be tested reliably.
- Prefer the active work line from the todo log and handoff brief over stale historical assumptions.
- Prefer the smallest truthful remediation slice first, unless the findings indicate a structural change requiring coordinated multi-file work.
- Treat the current knowledge-doc delivery model as `supporting_knowledge_docs.zip`, not side-by-side uploaded Knowledge doc files.
- Treat `project_sources/DCOIR_Collector.ps1` as the current readable collector source and `DCOIR_Collector.ps1` as the canonical runtime filename.
- Keep the canonical GitHub memory file human-readable and continuously updated after material remediation-state changes when repo persistence is available.

## Ranking model
Rank remediations in this order:
1. operator-blocking correctness defects
2. source-of-truth or control-plane drift
3. command-quality and scope-discipline defects
4. packaging or retrieval failures
5. documentation or helper refreshes
6. polish-only improvements

## Output contract
Return these sections in order:
1. Live-test finding summary
2. Ranked remediation queue
3. Impacted files and skills
4. Deep-regression requirements
5. Packaging recommendation
6. Stop conditions and warnings

## Commands
Build a remediation plan from explicit findings:
```bash
python scripts/plan_live_test_remediation.py \
  --source-dir /mnt/data \
  --output-dir /mnt/data/dcoir_live_test_remediation_out \
  --finding "collector output interpretation was unclear" \
  --finding "large-file fallback was not explained"
```

## Output handling
After the script runs:
- Read `dcoir_live_test_remediation_report.md` and `.json`.
- If the report says `remediation_status` is `failure`, explain the exact stop reason.
- If the report says `remediation_status` is `success`, summarize the highest-priority remediation items first and call out required deep regression.
- Keep the recommendation bounded to remediation planning and verification posture, not authority or promotion.

## References
Use these bundled references when needed:
- `references/remediation_rules.json`
- `references/remediation_model.md`
- `references/github_memory_workflow.md`
