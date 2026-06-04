# DCOIR Maintained Knowledge Set

This folder is the maintained readable source for the shared DCOIR knowledge set that feeds operator guidance and Gemini bundle attachments.

Use this README as the knowledge-set entry point. Keep detailed operating guidance in the owned `Knowledge - <Group> - <Topic>.md` pages below instead of recreating a second repo-root index.

## Authority

- `knowledge/*.md` files are the editable maintained source.
- Gemini attachment files are generated at package time from `knowledge/Knowledge - *.md` and written into the release ZIP under `02_PRIME_AGENT_ATTACHMENTS/*.md.txt`.
- The attachment files are generated from this folder at release package time and should not be treated as a primary editing surface.
- Knowledge docs support operators and Gemini, but they do not override Project Instructions, governed GitHub source, implemented source behavior, or Supabase `ircore` operational records.

## Current pages and owners

The maintained knowledge set currently uses four stable groups instead of a renumbered sequence:

| Group | Page | Primary ownership |
| --- | --- | --- |
| Core | Overview and About | Authority model, source classes, and system lanes |
| Core | Elastic Quick Start | Endpoint-vs-local quick command posture |
| Collector | Local Test and Regression | Harness, validation lanes, and result interpretation |
| Core | Tier 1 Collect Runbook | First-pass collection workflow |
| Core | Tier 2 Collect Runbook | Deeper collection workflow |
| Core | Enrichment Actions | Enrichment and retrieval lifecycle |
| Core | Artifact Review Guide | Evidence-review order and upload priority |
| Core | Troubleshooting | Failure classification and recovery patterns |
| Core | FAQ | Short recurring answers only |
| Gemini | AI Prompt and Agent Design | Gemini design principles |
| Core | IOC Enrichment and Public Sources | Public-enrichment boundaries |
| Gemini | Runtime Bundle and Source Tree | Stored-source bundle layout |
| Gemini | Agent Topology and Routing | Agent role/routing summary |
| Gemini | Output Contract and Command-Lane Discipline | Gemini output format and command lanes |
| Collector | EXE Usage and Runtime Behavior | Optional EXE behavior and EXE-specific validation |
| Collector | Feature and Output Contract Reference | Feature map, parameters, output contract, and validation map |
| Reference | Elastic Field Name Reference | Governed exact Elastic field-name reference for query construction |
| Reference | Elastic Response Actions Reference | Governed native response-action syntax and parameters |
| Reference | OSQuery Reference Index | Routing index for the sharded OSQuery schema set |
| Reference | OSQuery Process and Execution Tables | Exact process and execution table reference |
| Reference | OSQuery File and Filesystem Tables | Exact file and filesystem table reference |
| Reference | OSQuery Network and Connection Tables | Exact network and connection table reference |
| Reference | OSQuery User, Auth, and Account Tables | Exact user, auth, and account table reference |
| Reference | OSQuery Persistence and Startup Tables | Exact persistence and startup table reference |
| Reference | OSQuery System, Hardware, and Platform Tables | Exact system and hardware table reference |
| Reference | OSQuery Security, Detection, and Event Tables | Exact security and event table reference |
| Reference | OSQuery Application, Package, and Extension Tables | Exact application and package table reference |
| Reference | OSQuery Virtualization, Cloud, and Container Tables | Exact container and cloud table reference |
