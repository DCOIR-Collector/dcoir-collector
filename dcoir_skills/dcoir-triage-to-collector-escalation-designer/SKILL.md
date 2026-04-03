---
name: dcoir-triage-to-collector-escalation-designer
description: design and review the handoff from alert triage into dcoir collection, enrichment, and analyst follow-through. use when chatgpt needs to define or update routing language, field mapping, escalation triggers, or operator-facing bridge guidance between elastic-style alert triage and dcoir collection workflows. includes living gemini field-mapping and routing guidance that can evolve with the workflow. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Triage-to-Collector Escalation Designer

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

Use this skill to define or review the alert-triage-to-DCOIR bridge.

## Core workflow
1. Resolve the current control plane and current Gemini comparative/design posture when relevant.
2. Read `references/gemini_field_mapping_routing_guidance.md`.
3. Run `scripts/emit_escalation_contract.py`.
4. Return the escalation triggers, field mapping, routing language, and operator-facing next-step guidance.

## Hard rules
- Do not under-specify routing-critical descriptions when richer wording preserves correct delegation.
- Distinguish source-of-truth prompt-pack behavior from comparative or generated companion artifacts.
- Keep escalation language operationally explicit.

## References
- `references/gemini_field_mapping_routing_guidance.md`
