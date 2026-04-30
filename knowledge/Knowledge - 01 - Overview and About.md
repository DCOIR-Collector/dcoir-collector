# Knowledge - 01 - Overview and About

_AFRICOM_SOC_IR / DCOIR project context and maintained knowledge-doc charter_

**Summary:** Defines the DCOIR authority model, source classes, and operational lanes so operators and Gemini can interpret collector, harness, and Gemini surfaces correctly.

---

## Current authority model

DCOIR uses an Airtable-first operational model with GitHub as governed source/readback for repository files.

| Surface | Role |
| --- | --- |
| Project Instructions | First bootstrap anchor |
| Airtable Governance Control Plane | Startup/load-sequence authority |
| Airtable Plans / Work Items / Session Checkpoints | Live execution and resume state |
| GitHub repo | Source/readback for collector, harness, Gemini bundle, workflows, and promoted history |
| `knowledge/*.md` | Maintained human-readable knowledge source |
| Gemini `.md.txt` attachments | Runtime attachment copies synced from `knowledge/*.md` |

Knowledge docs explain the system. They do not override Airtable live state, Project Instructions, or governed GitHub source.

---

## Current knowledge set

The maintained set currently contains 17 pages:

1. Overview and About
2. Elastic Quick Start
3. Local Test and Regression
4. Tier 1 Collect Runbook
5. Tier 2 Collect Runbook
6. Enrichment Actions
7. Artifact Review Guide
8. Troubleshooting
9. FAQ
10. AI Prompt and Agent Design
11. IOC Enrichment and Public Sources
12. Gemini Runtime Bundle and Source Tree
13. Gemini Agent Topology and Routing
14. Gemini Output Contract and Command-Lane Discipline
15. Gemini Attachment Set, Validation, and Maintenance
16. Collector EXE Usage and Runtime Behavior
17. Collector Feature and Output Contract Reference

---

## Source classes

| Class | Examples | How to use it |
| --- | --- | --- |
| Operational control | Airtable Governance Control Plane, Queue Control, Plans, Work Items, Session Checkpoints | Determines current work state and execution order |
| Governed source | Collector source, harness, workflows, Gemini bundle source | Determines implemented behavior |
| Supporting assets | Runtime ZIPs, delivery bundles, retained generated artifacts | Delivery or execution aids, not source of truth |
| Knowledge docs | `knowledge/Knowledge - ## - *.md` | Human/Gemini guidance only |

---

## Main system lanes

### Collector lane
The collector produces bounded host-side evidence through collect, enrich, and cleanup-oriented actions.

### Harness lane
The harness validates collector behavior from a repo-style layout and supports PS1 and optional EXE validation.

### Gemini lane
The Gemini bundle uses stored-source agent instructions and maintained knowledge attachments to support analyst workflow, routing, output interpretation, and command-lane discipline.

---

## Common mistakes to avoid

- Treating knowledge docs as control-plane authority
- Treating generated attachments as the editable source
- Treating an EXE wrapper limitation as a collector regression
- Treating package build success as runtime proof
- Mixing endpoint-response syntax with local PowerShell syntax
- Running broad collection before defining the investigative question

---

## Maintenance trigger points

Update dependent surfaces when any of these change:

- collector behavior
- harness behavior
- EXE behavior
- Gemini attachment inventory
- manifest-required files
- GitHub Actions validation coverage

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
