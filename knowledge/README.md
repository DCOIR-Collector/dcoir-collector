# DCOIR Maintained Knowledge Set

Purpose
- This folder is the maintained readable source of truth for the shared knowledge set that feeds the Gemini bundle attachments.
- The current major-version Gemini build does not expect these files to remain short. It expects them to be operationally explicit, more verbose, and more useful as stand-alone operator references.
- The maintained set now includes fifteen knowledge pages: the original collector and workflow references plus four Gemini-runtime-specific attachment pages.

Source-of-truth rule
- The maintained `knowledge/*.md` files are the editable source of truth.
- The Gemini build path syncs these maintained files into `project_sources/DCOIR_Gemini_Bundle_Source/02_PRIME_AGENT_ATTACHMENTS/*.md.txt` before validation and compile.
- Do not treat the synced attachment files as the primary maintained editing surface.

Current major-version expectation
- Each knowledge file should be more detailed than the earlier versions.
- The current bias is to remove ambiguity, not to optimize for shortness.
- If a workflow step, artifact type, bundle output, or analyst decision could be misunderstood, spell it out rather than summarizing it away.
- When the attachment set changes, update the maintained knowledge file set, the attachment map, the Gemini manifest required-files inventory, and the sync/validation surfaces together so ordinary builds stay coherent.

Current maintained knowledge pages
1. Knowledge - 01 - Overview and About
2. Knowledge - 02 - Elastic Quick Start
3. Knowledge - 03 - Local Test and Regression
4. Knowledge - 04 - Tier 1 Collect Runbook
5. Knowledge - 05 - Tier 2 Collect Runbook
6. Knowledge - 06 - Enrichment Actions
7. Knowledge - 07 - Artifact Review Guide
8. Knowledge - 08 - Troubleshooting
9. Knowledge - 09 - FAQ
10. Knowledge - 10 - AI Prompt and Agent Design
11. Knowledge - 11 - IOC Enrichment and Public Sources
12. Knowledge - 12 - Gemini Runtime Bundle and Source Tree
13. Knowledge - 13 - Gemini Agent Topology and Routing
14. Knowledge - 14 - Gemini Output Contract and Command-Lane Discipline
15. Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance
