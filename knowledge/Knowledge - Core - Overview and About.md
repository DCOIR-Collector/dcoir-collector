# Knowledge - Core - Overview and About

_AFRICOM_SOC_IR / DCOIR project context and maintained knowledge-doc charter_

**Summary:** Defines the DCOIR authority model, source classes, and operational lanes so operators and Gemini can interpret collector, harness, and Gemini surfaces correctly.

---

## Current authority model

DCOIR uses GitHub as governed source/readback for repository files and Supabase `ircore` as the operational routing, validation, and receipt surface.

| Surface | Role |
| --- | --- |
| Project Instructions | First bootstrap anchor |
| GitHub repo | Source/readback for collector, harness, Gemini bundle, workflows, and promoted history |
| Supabase `ircore` | Operational routing, retrieval profiles, validation rules, receipts, preferences, and active session state |
| `knowledge/*.md` | Maintained human-readable knowledge source |
| Gemini `.md.txt` attachments | Runtime attachment files generated in the release ZIP from `knowledge/*.md` |

Knowledge docs explain the system. They do not override Project Instructions, governed GitHub source, implemented source behavior, or Supabase `ircore` operational records.

---

## Current knowledge set

The maintained set currently contains 28 pages grouped by role:

- Core pages for shared DCOIR workflow and operating guidance
- Gemini pages for runtime bundle, routing, and output behavior
- Collector pages for validation, EXE behavior, and output-contract reference
- Reference pages for exact Elastic and OSQuery lookup material

---

## Knowledge ownership map

Use one owner per topic to avoid duplicate guidance.

| Topic | Owner | Supporting references |
| --- | --- | --- |
| Authority model and source classes | Knowledge - Core - Overview and About | `DCOIR_KNOWLEDGE_INDEX.md`, README |
| Endpoint command lane | Knowledge - Core - Elastic Quick Start | Knowledge - Gemini - Output Contract and Command-Lane Discipline |
| Local and CI validation | Knowledge - Collector - Local Test and Regression | `validate-on-push.yml`, `manual-full-validation.yml`, Knowledge - Collector - EXE Usage and Runtime Behavior, and Knowledge - Collector - Feature and Output Contract Reference |
| Tier 1 procedure | Knowledge - Core - Tier 1 Collect Runbook | Knowledge - Collector - Feature and Output Contract Reference for feature/output facts |
| Tier 2 procedure | Knowledge - Core - Tier 2 Collect Runbook | Knowledge - Collector - Feature and Output Contract Reference for feature/output facts |
| Enrichment and retrieval workflow | Knowledge - Core - Enrichment Actions | Knowledge - Core - Artifact Review Guide and Knowledge - Collector - Feature and Output Contract Reference |
| Artifact review and upload priority | Knowledge - Core - Artifact Review Guide | Knowledge - Gemini - Output Contract and Command-Lane Discipline and Knowledge - Gemini - Runtime Bundle and Source Tree for Gemini upload behavior |
| Troubleshooting | Knowledge - Core - Troubleshooting | Knowledge - Collector - Local Test and Regression, Knowledge - Collector - EXE Usage and Runtime Behavior, and Knowledge - Collector - Feature and Output Contract Reference |
| FAQ | Knowledge - Core - FAQ | All owner docs; FAQ must stay shallow |
| Gemini design, routing, output, and attachments | Knowledge - Gemini - AI Prompt and Agent Design, Knowledge - Gemini - Runtime Bundle and Source Tree, Knowledge - Gemini - Agent Topology and Routing, and Knowledge - Gemini - Output Contract and Command-Lane Discipline | Gemini stored-source agent files |
| Public IOC enrichment | Knowledge - Core - IOC Enrichment and Public Sources | Case evidence and source-tier rules |
| Optional EXE behavior | Knowledge - Collector - EXE Usage and Runtime Behavior | Knowledge - Collector - Local Test and Regression and Knowledge - Core - Troubleshooting |
| Collector features, parameters, and output contract | Knowledge - Collector - Feature and Output Contract Reference | Knowledge - Core - Tier 1 Collect Runbook, Knowledge - Core - Tier 2 Collect Runbook, Knowledge - Core - Enrichment Actions, Knowledge - Core - Artifact Review Guide, and Knowledge - Collector - EXE Usage and Runtime Behavior |

---

## Source classes

| Class | Examples | How to use it |
| --- | --- | --- |
| Operational state and validation records | Supabase `ircore` routing, retrieval profiles, validation rules, receipts, preferences, and active session state | Supports current routing, readback, validation, and receipt evidence |
| Governed source | Collector source, harness, workflows, Gemini bundle source | Determines implemented behavior |
| Supporting assets | Runtime ZIPs, delivery bundles, retained generated artifacts | Delivery or execution aids, not source of truth |
| Knowledge docs | `knowledge/Knowledge - <Group> - *.md` | Human/Gemini guidance only |

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