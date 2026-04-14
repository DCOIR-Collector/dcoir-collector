---
name: dcoir-live-test-remediation-planner
description: turn dcoir live-test findings into a ranked remediation plan with impacted files, helper-skill refreshes, deep-regression requirements, delivery posture, and stop conditions. use when chatgpt needs to decide what to fix first after live operator testing, gemini workflow validation, collector workflow issues, output-quality findings, packaging drift, or any other dcoir validation result that needs explicit remediation sequencing. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Live Test Remediation Planner

Use this skill to convert live-test findings into an explicit remediation queue and verification plan.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Before planning remediation, verify the current authoritative control-plane files from the workspace.

Preferred current files:
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- `project_sources/LOG-01_DCOIR_Todo_Log.txt`
- `project_sources/LOG-03_DCOIR_Session_Handoff_Brief.txt`

Stop if the manifest or change log cannot be resolved.

## Core workflow
1. Read the current manifest first.
2. Read the current change log second.
3. Use the current todo log and current handoff brief as supporting context for active remediation themes.
4. Identify the live-test findings, defects, or operator-friction notes from the user request.
5. Run `scripts/plan_live_test_remediation.py` with the findings.
6. Read the generated markdown and json reports.
7. When the remediation state changed materially, use the GitHub connector directly to read or update the canonical GitHub memory file defined in `references/github_memory_workflow.md`, reducing operator burden to the smallest bounded manual GitHub action only when the connector cannot safely complete the write.
8. Return the ranked remediation order, impacted sources, deep-regression requirements, recommended delivery posture, and any GitHub-memory change that matters.

## Hard rules
- Do not treat live-test findings as fixed until the repaired path is re-tested.
- Default to deep regression for any remediation affecting a skill, script, packaging path, operator guidance, or generated workflow artifact that can be tested reliably.
- Prefer the active work line from the todo log and handoff brief over stale historical assumptions.
- Prefer the smallest truthful remediation slice first, unless the findings indicate a structural change requiring coordinated multi-file work.
- Use the current delivery classes, not the retired targeted-versus-full-refresh split alone.
- Treat `project_sources/DCOIR_Collector.ps1` as the current readable collector source and `DCOIR_Collector.ps1` as the canonical runtime filename.
- Keep the canonical GitHub memory file human-readable and continuously updated after material remediation-state changes when repo persistence is available.

## Delivery posture classes
Use these delivery classes when they fit the repaired change set:
- `targeted_skill_update`
- `batched_skill_update_wave`
- `github_desktop_manual_repo_update_bundle`
- `full_refresh_project_upload`

## Output contract
Return these sections in order:
1. Live-test finding summary
2. Ranked remediation queue
3. Impacted files and skills
4. Deep-regression requirements
5. Delivery recommendation
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

## References
- `references/remediation_rules.json`
- `references/remediation_model.md`
- `references/github_memory_workflow.md`

## Airtable remediation traceability

When live-test findings map to existing collector or Gemini test rows, update or reference the Airtable `Validation Test Cases` catalog alongside the remediation queue.

Prefer this pattern:
- failed or blocked live finding -> update matching test row evidence/status
- new failure shape or missing coverage -> add a new test row
- remediation plan -> link the finding to an Airtable Work Item and the affected test IDs
