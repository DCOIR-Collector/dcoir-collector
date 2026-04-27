---
name: dcoir-triage-to-collector-escalation-designer
description: design and review the handoff from alert triage into dcoir collection, enrichment, and analyst follow-through. use when chatgpt needs to define or update routing language, field mapping, escalation triggers, expected next evidence, or operator-facing bridge guidance between elastic-style alert triage and dcoir collection workflows. includes living gemini field-mapping and routing guidance that can evolve with the workflow. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-triage-to-collector-escalation-designer|SKILL.md -->

# DCOIR Triage-to-Collector Escalation Designer

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.


Use this skill to define or review the alert-triage-to-DCOIR bridge.

## Required behavior
- resolve the current control plane when relevant
- keep escalation language operationally explicit
- emit the exact next DCOIR step, expected next evidence, and bounded-confidence note
- follow the DCOIR review order baseline triage -> enrichment -> retrieved artifact review -> final synthesis
