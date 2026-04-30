# DCOIR Maintained Knowledge Set

This folder is the maintained readable source for the shared DCOIR knowledge set that feeds operator guidance and Gemini bundle attachments.

For the repo-level starting point, use `DCOIR_KNOWLEDGE_INDEX.md`.

## Authority

- `knowledge/*.md` files are the editable maintained source.
- Gemini attachment files are generated at package time from `knowledge/Knowledge - *.md` and written into the release ZIP under `02_PRIME_AGENT_ATTACHMENTS/*.md.txt`.
- The attachment files are generated from this folder at release package time and should not be treated as a primary editing surface.
- Knowledge docs support operators and Gemini, but they do not override Airtable live state, Project Instructions, or governed GitHub source.

## Current pages and owners

| # | Page | Primary ownership |
| --- | --- | --- |
| 01 | Overview and About | Authority model, source classes, and system lanes |
| 02 | Elastic Quick Start | Endpoint-vs-local quick command posture |
| 03 | Local Test and Regression | Harness, validation lanes, and result interpretation |
| 04 | Tier 1 Collect Runbook | First-pass collection workflow |
| 05 | Tier 2 Collect Runbook | Deeper collection workflow |
| 06 | Enrichment Actions | Enrichment and retrieval lifecycle |
| 07 | Artifact Review Guide | Evidence-review order and upload priority |
| 08 | Troubleshooting | Failure classification and recovery patterns |
| 09 | FAQ | Short recurring answers only |
| 10 | AI Prompt and Agent Design | Gemini design principles |
| 11 | IOC Enrichment and Public Sources | Public-enrichment boundaries |
| 12 | Gemini Runtime Bundle and Source Tree | Stored-source bundle layout |
| 13 | Gemini Agent Topology and Routing | Agent role/routing summary |
| 14 | Gemini Output Contract and Command-Lane Discipline | Gemini output format and command lanes |
| 15 | Gemini Attachment Set, Validation, and Maintenance | Attachment inventory and direct generation rules |
| 16 | Collector EXE Usage and Runtime Behavior | Optional EXE behavior and EXE-specific validation |
| 17 | Collector Feature and Output Contract Reference | Feature map, parameters, output contract, and validation map |

## Maintenance triggers

When the page list, attachment set, collector behavior, EXE behavior, Gemini agent behavior, or workflow validation coverage changes, update these surfaces together:

- maintained `knowledge/*.md` source files;
- generated Gemini `.md.txt` attachment inventory;
- `project_sources/gemini/bundle_source/00_START_HERE/Agent_Attachment_Map.md.txt`;
- `project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json`;
- GitHub Actions required-surface checks.

## Duplication rule

Runbooks own procedure. Reference pages own facts. FAQ answers stay shallow and should point to the owner page instead of becoming a parallel source of operational rules.
