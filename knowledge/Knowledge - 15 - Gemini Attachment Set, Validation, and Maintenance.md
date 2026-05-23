# Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance

_Gemini knowledge attachment inventory and maintenance rules_

**Summary:** The Gemini attachment set is generated at package time from manifest-listed `knowledge/*.md` files and must stay aligned with the manifest, attachment map, and workflow checks.

---

## Attachment model

| Surface | Role |
| --- | --- |
| `knowledge/*.md` | Maintained editable source |
| `knowledge/*.md` listed in `operator_only_knowledge_sources` | Maintained operator-facing guidance that informs future Gemini source changes without shipping as runtime attachments |
| `02_PRIME_AGENT_ATTACHMENTS/*.md.txt` | Generated Gemini runtime attachment files inside the release ZIP |
| `Agent_Attachment_Map.md.txt` | Human/runtime inventory explanation |
| `Gemini_Bundle_Source_Manifest.json` | Required file inventory and knowledge-source classification |
| GitHub Actions workflows | Validation and required-surface enforcement |

---

## Current inventory

The attachment set currently contains 17 bundled knowledge pages. During Gemini release packaging, each bundle-facing source page is written into the release ZIP under `02_PRIME_AGENT_ATTACHMENTS/` using the same title plus `.txt`. Do not maintain separate source copies in `bundle_source`.

| # | Attachment | Primary purpose |
| --- | --- | --- |
| 01 | Overview and About | Authority model, source classes, and system lanes |
| 02 | Elastic Quick Start | Endpoint-vs-local quick command posture |
| 03 | Local Test and Regression | Harness, validation lanes, and result interpretation |
| 04 | Tier 1 Collect Runbook | First-pass collection procedure |
| 05 | Tier 2 Collect Runbook | Deeper collection procedure |
| 06 | Enrichment Actions | Enrichment and retrieval lifecycle |
| 07 | Artifact Review Guide | Evidence-review order and upload priority |
| 08 | Troubleshooting | Failure classification and recovery patterns |
| 09 | FAQ | Short recurring answers only |
| 10 | AI Prompt and Agent Design | Gemini design principles |
| 11 | IOC Enrichment and Public Sources | Public-enrichment boundaries |
| 12 | Gemini Runtime Bundle and Source Tree | Stored-source bundle layout |
| 13 | Gemini Agent Topology and Routing | Agent role/routing summary |
| 14 | Gemini Output Contract and Command-Lane Discipline | Gemini response format and command lanes |
| 15 | Gemini Attachment Set, Validation, and Maintenance | Attachment inventory and direct generation rules |
| 16 | Collector EXE Usage and Runtime Behavior | Optional EXE behavior and EXE-specific validation |
| 17 | Collector Feature and Output Contract Reference | Feature map, parameters, output contract, and validation map |

`Knowledge - 18 - Gemini Research Findings and Runtime Boundaries.md` remains maintained operator-facing guidance for future Gemini source work. It should stay in `knowledge/`, but it is intentionally excluded from `02_PRIME_AGENT_ATTACHMENTS/`.

Knowledge 16 is the owner for optional EXE usage and runtime behavior. Knowledge 17 is the owner for collector feature and output-contract reference.

---

## Update rule

When the knowledge set changes:

1. Update maintained `knowledge/*.md` source.
2. Classify the page in the manifest: keep bundle-facing pages under `knowledge_attachment_sources`, and keep operator-only pages under `operator_only_knowledge_sources`.
3. Let the build regenerate `.md.txt` attachment files only for bundle-facing maintained sources.
4. Update the attachment map when the runtime attachment inventory changes.
5. Update the manifest knowledge inventories and required-files contract when bundle-facing or operator-only classification changes.
6. Update GitHub Actions required-surface checks when non-manifest-governed surfaces change; Gemini topology required-file enforcement should remain manifest-driven.
7. Add or update Airtable validation rows if runtime behavior changed.

---

## Validation expectations

After attachment changes, verify:

- every required attachment exists;
- maintained sources and generated attachment inventory match;
- manifest classifies maintained knowledge pages correctly as bundle-facing attachments versus operator-only guidance;
- manifest and attachment map include the same runtime attachment inventory;
- workflow checks derive Gemini required files from the manifest and enforce required files without duplicating sub-agent counts;
- agent instructions reference the correct attachment surfaces;
- no stale duplicated filler or meta-writing text remains.

---

## Grounding boundary

Attachments can provide stable project context. They do not create live connector access, enterprise retrieval, or web-grounding capability by themselves.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
