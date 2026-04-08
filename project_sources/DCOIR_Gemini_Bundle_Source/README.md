# DCOIR Gemini Bundle Source

Purpose
- This folder is the governed editable runtime source tree for the major-version Gemini bundle.
- Edit these files directly when the accepted runtime wording changes.
- Compile the bundle from this tree after the maintained knowledge sync, validation, and compile path runs.

Major-version topology rule
- `Gemini_Bundle_Source_Manifest.json.txt` is the explicit source of topology truth.
- The manifest now governs one prime agent plus ten verbose sub-agents.
- Validation must compare the manifest topology against the discovered source-tree files and fail on drift.

Current major-version focus
- The parent and sub-agents are intentionally more verbose than earlier versions.
- The current build is expected to be explicit about collector interpretation, collector pivoting, mixed-format IOC handling, targeted collection design, false-positive-aware security-product behavior, and output-contract consistency.
- If a field or instruction can be made clearer, the default bias for this major version is to write it more explicitly rather than compress it.

When adding a new sub-agent
1. Add the new source file in `01_GEMINI_AGENT_BUILD/`.
2. Add that file to the manifest topology section.
3. Add that file to the manifest `required_files` list.
4. Update `Generated_DCOIR_Gemini_Agent_Index.md.txt`.
5. Update `00_START_HERE/Gemini_Build_Quick_Start.md.txt` if the build order or mental model changed.
6. Re-run validation and build.

What not to do
- Do not treat file drop alone as a topology change.
- Do not rely on ad hoc folder discovery as shipment authority.
- Do not skip manifest updates when adding or removing sub-agents.
- Do not let the maintained `knowledge/*.md` set and the synced `02_PRIME_AGENT_ATTACHMENTS/*.md.txt` set drift silently.
