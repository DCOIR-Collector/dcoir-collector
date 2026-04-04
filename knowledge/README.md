# Knowledge Docs

This folder is for extracted human-readable knowledge documents and governed supporting reference material managed as normal files inside the GitHub-primary working line.

## Purpose

Use `knowledge/` for supporting human-readable documentation that helps the operator understand the current DCOIR workflow, supporting references, routing notes, and AI-workflow posture without treating these docs as control-plane authority.

## Authority Notes

- Knowledge docs are supporting human-readable docs only.
- They do not replace Project Instructions, `CP-01`, `CP-02`, or the evergreen DOC / LOG surfaces.
- When a knowledge page summarizes project rules, treat the control plane as authoritative and the knowledge page as explanatory.

## Local Navigation

### Key local guides and notes
- `DCOIR_Helper_Skills_Routing_Note.md` — descriptive project-side routing aid for the current `dcoir-*` helper-skill set and common routing cues.
- `README.md` — this local guide for `knowledge/`.

### Current knowledge docs in this folder
- `Knowledge - 01 - Overview and About.md` — project context, control-plane posture, and Knowledge-doc set charter.
- `Knowledge - 02 - Elastic Quick Start.md` — endpoint response-console usage versus local workstation usage.
- `Knowledge - 03 - Local Test and Regression.md` — local regression posture and harness-oriented guidance.
- `Knowledge - 04 - Tier 1 Collect Runbook.md` — first-line collection workflow guidance.
- `Knowledge - 05 - Tier 2 Collect Runbook.md` — deeper collection and follow-on handling guidance.
- `Knowledge - 06 - Enrichment Actions.md` — enrichment actions and next-step interpretation guidance.
- `Knowledge - 07 - Artifact Review Guide.md` — evidence-driven artifact review sequence and posture.
- `Knowledge - 08 - Troubleshooting.md` — common workflow and execution troubleshooting guidance.
- `Knowledge - 09 - FAQ.md` — recurring operator and project workflow questions.
- `Knowledge - 10 - AI Prompt and Agent Design.md` — current prompt-pack and Gemini workflow posture.

### Current extracted readable knowledge folders
- `comparative_reference_agent_markdowns/` — comparative reference agent markdowns used for Gemini design style and structure reference.
- `generated_agent_markdowns/` — generated companion agent markdowns and related readable outputs.

### Current governed routing and reference notes
- `github_connector_reference/` — governed connector reference pack used to improve GitHub execution quality without overriding the live connector surface.

## How this folder relates to helper-skill workflow

- For project-side helper selection, start with `DCOIR_Helper_Skills_Routing_Note.md`.
- For evergreen helper-skill process rules, use `project_sources/DOC-05_DCOIR_Helper_Skill_Workflow_And_GitHub_Source_Rules.txt`.
- Broader README maintenance belongs to the README-maintainer workflow.
- Broader knowledge-doc generation or regeneration belongs to the knowledge-doc-maintainer workflow.

## Recommended Contents

Use this folder for:
- operator workflow docs
- collector usage docs
- Gemini workflow docs
- supporting knowledge markdown files
- comparative reference agent markdowns
- generated agent markdowns
- governed routing notes that help project-side workflow selection without becoming control-plane authority
- governed connector reference packs that improve GitHub execution quality without overriding the live tool surface
