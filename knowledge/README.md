# DCOIR Maintained Knowledge Set

Purpose
- This folder is the maintained readable source of truth for the shared knowledge set that feeds the Gemini bundle attachments.
- The current major-version Gemini build does not expect these files to remain short. It expects them to be operationally explicit, more verbose, and more useful as stand-alone operator references.

Source-of-truth rule
- The maintained `knowledge/*.md` files are the editable source of truth.
- The Gemini build path syncs these maintained files into `project_sources/DCOIR_Gemini_Bundle_Source/02_PRIME_AGENT_ATTACHMENTS/*.md.txt` before validation and compile.
- Do not treat the synced attachment files as the primary maintained editing surface.

Current major-version expectation
- Each knowledge file should be more detailed than the earlier versions.
- The current bias is to remove ambiguity, not to optimize for shortness.
- If a workflow step, artifact type, bundle output, or analyst decision could be misunderstood, spell it out rather than summarizing it away.
