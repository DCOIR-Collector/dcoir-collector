# DCOIR Gemini Bundle Source

Purpose
- This folder is the governed editable runtime source tree for the operator-facing Gemini bundle.
- Edit these files directly when the accepted runtime wording changes.
- Compile the bundle from this tree after validation.

Topology rule
- `Gemini_Bundle_Source_Manifest.json.txt` is the explicit source of topology truth.
- The manifest must list the prime-agent file and every active sub-agent file.
- Validation will compare the manifest against the discovered source-tree files and fail on drift.

When adding a new sub-agent
1. Add the new source file in `01_GEMINI_AGENT_BUILD/`.
2. Add that file to the manifest topology section.
3. Add that file to the manifest `required_files` list.
4. Update `Generated_DCOIR_Gemini_Agent_Index.md.txt`.
5. Update `00_START_HERE/Gemini_Build_Quick_Start.md.txt` if the operator build order changed.
6. Re-run validation and build.

What not to do
- Do not treat file drop alone as a topology change.
- Do not rely on ad hoc folder discovery as shipment authority.
- Do not skip manifest updates when adding or removing sub-agents.
