---
name: dcoir-triage-to-collector-escalation-designer
description: design and review the handoff from alert triage into dcoir collection, enrichment, and analyst follow-through. use when chatgpt needs to define or update routing language, field mapping, escalation triggers, expected next evidence, or operator-facing bridge guidance between elastic-style alert triage and dcoir collection workflows. includes living gemini field-mapping and routing guidance that can evolve with the workflow. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill.
---

# DCOIR Triage-to-Collector Escalation Designer

Use this skill to define or review the alert-triage-to-DCOIR bridge.

## Required behavior
- resolve the current control plane when relevant
- keep escalation language operationally explicit
- emit the exact next DCOIR step, expected next evidence, and bounded-confidence note
- follow the DCOIR review order baseline triage -> enrichment -> retrieved artifact review -> final synthesis
