---
name: dcoir-large-file-intake-manager
description: plan bounded intake when dcoir evidence files are too large, missing, or only partially available. use when chatgpt needs to keep working despite upload limits by switching to metadata-first triage, targeted excerpts, staged collection, or narrowed artifact requests. includes dcoir-specific large-file intake playbooks for baseline, enrichment, retrieved-artifact, and event-export evidence. use only when working inside the africom_soc_ir / dcoir project context; if that project context is not present, do not use this skill. follow the airtable-first startup/control-plane model and use github only for governed source, promoted history, packaging, or explicit repo readback when required.
---

<!-- skill-marker: updated-skill|20260427T180000Z|T4.0.5.9-airtable-first-startup-cutover|source-update|dcoir-large-file-intake-manager|SKILL.md -->

# DCOIR Large File Intake Manager

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Plan Tasks`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, final T99 keep/delete review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo File Coverage Detail`, `Retained Repo Manifest`, and active plan state before stopping.


Use this skill to keep DCOIR work moving when full evidence files cannot be uploaded.

## Required behavior
- state the limitation plainly
- prefer metadata-first and highest-value targeted excerpts
- prefer one next requested slice over a broad dump
- keep conclusions bounded to the reviewed scope
- keep the request aligned to the DCOIR review order baseline -> enrichment -> retrieved artifact -> final synthesis
