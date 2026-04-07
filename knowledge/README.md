# Knowledge Docs

Purpose
- This folder holds governed human-readable knowledge, routing notes, reference material, and task memory that support the DCOIR framework without becoming control-plane authority.

What this folder is for
- operator workflow docs
- collector usage and validation docs
- the maintained Knowledge-doc set in `knowledge/*.md`
- Gemini workflow and design docs
- supporting knowledge markdown files
- comparative reference agent markdowns
- generated agent markdowns
- governed routing notes that help helper-skill selection and workflow support
- governed connector reference packs and task memory used to improve GitHub execution quality without overriding the live tool surface

Important current surfaces
- `knowledge/DCOIR_Helper_Skills_Routing_Note.md` — descriptive current helper-skill routing aid that should stay aligned to the current governed skill inventory and workflow rules
- `knowledge/task_memory/` — validated procedures, limitations, and failure signatures
- `knowledge/github_connector_reference/` — governed connector reference material
- `knowledge/comparative_reference_agent_markdowns/` — readable comparative-reference working surface for Gemini review, not control-plane authority
- `knowledge/generated_agent_markdowns/` — readable generated-agent working surface for Gemini review and packaging support, not design-time authority by itself
- `knowledge/Knowledge - 01 - Overview and About.md` through `knowledge/Knowledge - 10 - AI Prompt and Agent Design.md` — current maintained human-readable Knowledge-doc set

How to use this folder
- Treat these docs as supporting human-readable guidance, not control-plane authority.
- Re-anchor to Project Instructions, then CP-01, then CP-02 before relying on knowledge surfaces for current-state decisions.
- Use the helper-skill routing note and task-memory bank to choose the right workflow support rather than guessing from memory.
- Keep `knowledge/*.md` as the editable readable working set for the current Knowledge-doc lane.
- Treat generated and comparative Gemini markdown surfaces as readable supporting working surfaces rather than current build authority.
- Treat `supporting_assets/supporting_knowledge_docs.zip` as a retained delivery artifact that should stay aligned to the maintained markdown set, not as the editable source of truth.
- Use `project_sources/DOC-07_DCOIR_Gemini_Live_Test_Generation_And_Legacy_Surface_Rules_v1_0_0.txt` and `project_sources/DOC-08_DCOIR_Gemini_Legacy_Surface_Inventory_And_Hygiene_Plan_v1_0_0.txt` when the task needs the current governed role map for generated, comparative, retained, or legacy Gemini-readable surfaces.

Current documentation gaps being worked
- stronger wiki-style indexing across knowledge topics
- deeper cross-linking between README surfaces, routing notes, and maintained knowledge docs
- clearer integration between README maintenance and broader knowledge-maintenance workflows
