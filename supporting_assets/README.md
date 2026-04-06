# Supporting Assets

Purpose
- Store retained non-authoritative supporting artifacts here, especially ZIP bundles and other portable delivery assets that help the operator move the current readable working surfaces without duplicating control-plane authority.

Current retained asset inventory
- `DCOIR_Collector.zip` — retained collector support package asset
- `supporting_knowledge_docs.zip` — retained portable Knowledge-doc set
- `generated_agent_markdowns.zip` — retained portable package of the current generated Gemini agent markdown set
- `comparative_reference_agent_markdowns.zip` — retained portable package of the current comparative Gemini reference markdown set

Use rules
- Keep rarely changed ZIPs here.
- Keep extracted editable text outside this folder.
- Treat supporting assets as portable supporting material, not as control-plane authority.
- Refresh these ZIPs when their readable source sets change materially enough that the portable package would otherwise drift.

Current source mapping
- `supporting_knowledge_docs.zip` maps to the governed Knowledge docs in `knowledge/`.
- `generated_agent_markdowns.zip` maps to `knowledge/generated_agent_markdowns/`.
- `comparative_reference_agent_markdowns.zip` maps to `knowledge/comparative_reference_agent_markdowns/`.
