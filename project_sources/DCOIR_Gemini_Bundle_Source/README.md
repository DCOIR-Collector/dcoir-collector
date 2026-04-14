# DCOIR Gemini Bundle Source

Purpose
- This folder is the governed editable runtime source tree for the major-version Gemini bundle.
- Edit these files directly when the accepted runtime wording changes.
- Compile the bundle from this tree after the maintained knowledge sync, validation, and compile path runs.

Major-version topology rule
- `Gemini_Bundle_Source_Manifest.json.txt` is the explicit source of topology truth.
- The manifest governs one prime agent plus ten verbose sub-agents.
- Validation must compare the manifest topology against the discovered source-tree files and fail on drift.

Knowledge-attachment rule
- The manifest also governs the required shared knowledge attachment set.
- The maintained `knowledge/*.md` working set is the editable source of truth for those attachments.
- The attachment set now includes fifteen knowledge pages, including four Gemini-runtime-specific pages that must stay aligned with the attachment map, the maintained knowledge set, and the validator surfaces.
- Ordinary shipment should fail if the maintained knowledge set, the synced attachment set, and the manifest inventory drift apart.

Current major-version focus
- The parent and sub-agents are intentionally more verbose than earlier versions.
- The current build is expected to be explicit about collector interpretation, collector pivoting, mixed-format IOC handling, targeted collection design, false-positive-aware security-product behavior, and output-contract consistency.
- If a field or instruction can be made clearer, the default bias for this major version is to write it more explicitly rather than compress it.

When changing the attachment set
1. Edit the maintained `knowledge/*.md` files.
2. Sync those files into `02_PRIME_AGENT_ATTACHMENTS/` through the governed build path.
3. Update `00_START_HERE/Agent_Attachment_Map.md.txt`.
4. Update `Gemini_Bundle_Source_Manifest.json.txt` when the required attachment inventory changed.
5. Re-run validation and build.

What not to do
- Do not treat file drop alone as a topology or attachment-inventory change.
- Do not rely on ad hoc folder discovery as shipment authority.
- Do not skip manifest updates when adding or removing required shared knowledge files.
- Do not let the maintained `knowledge/*.md` set and the synced `02_PRIME_AGENT_ATTACHMENTS/*.md.txt` set drift silently.
