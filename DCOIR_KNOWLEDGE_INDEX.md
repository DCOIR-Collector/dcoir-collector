# DCOIR Knowledge Index

_Operator entry point for the maintained DCOIR knowledge set_

**Summary:** Use this index to pick the correct Knowledge page without creating duplicate guidance. The maintained source is `knowledge/*.md`; Gemini attachment copies are generated runtime mirrors.

---

## Authority boundary

- Airtable live state controls current queue, work items, plans, checkpoints, and resume order.
- GitHub is governed source/readback for collector, harness, Gemini bundle, workflow, and promoted repository history.
- `knowledge/*.md` files are maintained human-readable guidance.
- `project_sources/gemini/bundle_source/02_PRIME_AGENT_ATTACHMENTS/*.md.txt` files are generated runtime files created from `knowledge/*.md` during release packaging.
- Knowledge docs do not override Project Instructions, Airtable control-plane rows, or implemented source behavior.

---

## Where to start

| Need | Start here | Why |
| --- | --- | --- |
| Understand authority and source classes | `knowledge/Knowledge - Core - Overview and About.md` | Defines the model and common boundaries. |
| Run an endpoint command | `knowledge/Knowledge - Core - Elastic Quick Start.md` | Owns endpoint-vs-local command lane guidance. |
| Validate locally or in CI | `knowledge/Knowledge - Collector - Local Test and Regression.md` | Owns harness and validation interpretation. |
| Run first-pass collection | `knowledge/Knowledge - Core - Tier 1 Collect Runbook.md` | Owns Tier 1 procedure. |
| Run deeper collection | `knowledge/Knowledge - Core - Tier 2 Collect Runbook.md` | Owns Tier 2 procedure. |
| Continue enrichment or retrieve artifacts | `knowledge/Knowledge - Core - Enrichment Actions.md` | Owns enrichment and retrieval lifecycle. |
| Decide what artifact to review or upload | `knowledge/Knowledge - Core - Artifact Review Guide.md` | Owns evidence-review order and upload priority. |
| Troubleshoot failure | `knowledge/Knowledge - Core - Troubleshooting.md` | Owns failure classification and recovery patterns. |
| Answer a common operator question | `knowledge/Knowledge - Core - FAQ.md` | Fast answers only; not a second source of truth. |
| Understand Gemini design | `knowledge/Knowledge - Gemini - AI Prompt and Agent Design.md` | Owns high-level AI/Gemini design posture. |
| Handle IOC enrichment | `knowledge/Knowledge - Core - IOC Enrichment and Public Sources.md` | Owns public-enrichment boundaries. |
| Understand Gemini source tree | `knowledge/Knowledge - Gemini - Runtime Bundle and Source Tree.md` | Owns stored-source bundle layout. |
| Understand agent roles | `knowledge/Knowledge - Gemini - Agent Topology and Routing.md` | Owns agent topology summary. |
| Control Gemini output and command format | `knowledge/Knowledge - Gemini - Output Contract and Command-Lane Discipline.md` | Owns Gemini response and command-lane discipline. |
| Use or interpret the optional EXE | `knowledge/Knowledge - Collector - EXE Usage and Runtime Behavior.md` | Owns EXE-specific behavior and validation. |
| Look up collector features and output contract | `knowledge/Knowledge - Collector - Feature and Output Contract Reference.md` | Owns feature map, parameters, output contract, and validation map. |
| Look up exact Elastic field names | `knowledge/Knowledge - Reference - Elastic Field Name Reference.md` | Owns the governed exact field-name reference used for KQL and ESQL construction. |
| Look up native Elastic response-action syntax | `knowledge/Knowledge - Reference - Elastic Response Actions Reference.md` | Owns governed native response-action command syntax, parameters, and privilege notes. |
| Route an OSQuery lookup to the correct shard | `knowledge/Knowledge - Reference - OSQuery Reference Index.md` | Owns the start-here map for the sharded exact OSQuery schema set. |
| Look up exact OSQuery table and field names | `knowledge/Knowledge - Reference - OSQuery Process and Execution Tables.md` and the related OSQuery reference pages | Owns the sharded governed exact OSQuery schema reference. |

---

## Maintenance rule

When a knowledge source changes, check the dependent surfaces before commit:

1. source file under `knowledge/`;
2. generated Gemini attachment inventory under `02_PRIME_AGENT_ATTACHMENTS/` at release-build time;
3. `Agent_Attachment_Map.md.txt` if purpose or inventory changed;
4. `Gemini_Bundle_Source_Manifest.json` if required inventory changed;
5. GitHub Actions validation surfaces if required-file or count checks changed.

Do not edit Gemini attachment copies as the primary source. The build generates them from the matching `knowledge/*.md` file.
