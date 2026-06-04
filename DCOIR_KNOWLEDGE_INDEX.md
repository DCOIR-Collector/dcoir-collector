# DCOIR Knowledge Index

_Operator entry point for the maintained DCOIR knowledge set_

**Summary:** Use this index to pick the correct Knowledge page without creating duplicate guidance. The maintained source is `knowledge/*.md`; Gemini attachment copies are generated runtime mirrors.

---

## Authority boundary

- GitHub is governed source/readback for collector, harness, Gemini bundle, workflow, and promoted repository history.
- Supabase `ircore` stores operational routing, retrieval profiles, validation rules, receipts, preferences, reusable lessons, and active session state.
- `knowledge/*.md` files are maintained human-readable guidance.
- `project_sources/gemini/bundle_source/02_PRIME_AGENT_ATTACHMENTS/*.md.txt` files are generated runtime files created from `knowledge/*.md` during release packaging.
- Knowledge docs do not override Project Instructions, governed GitHub source, Supabase `ircore` operational records, or implemented source behavior.

---

## If you have no prior collector experience

Use this path when you only have the collector knowledge documents and need to understand and operate the collector safely.

1. Read `knowledge/Knowledge - Collector - Feature and Output Contract Reference.md` to understand the collector modes, quick aliases, targeted boundaries, enrichment actions, cleanup behavior, and output contract.
2. Read `knowledge/Knowledge - Core - Elastic Quick Start.md` if you will run the collector through Elastic response actions, or use the local command examples in the relevant runbook if you are operating locally.
3. Choose one operating path: Tier 1 collect, Tier 2 collect, enrichment/retrieval, targeted follow-up, artifact review, troubleshooting, or optional EXE interpretation.
4. After a collect run, read `knowledge/Knowledge - Core - Artifact Review Guide.md` before opening broad output trees or bundles.
5. Before enrichment or retrieval, read `knowledge/Knowledge - Core - Enrichment Actions.md` so the session lifecycle, quick aliases, and review-style versus retrieval-style actions are clear.
6. Before cleanup, confirm the evidence you need has already been reviewed, retrieved, or preserved.

The knowledge set is meant to make the collector usable without source-code experience, but it is still evidence-first: do not invent flags, workflow results, exact filtering guarantees, or closeability claims beyond what the maintained docs and source-backed validation prove.

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