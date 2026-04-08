# DCOIR Gemini Bundle Source

Purpose
- This folder is the governed editable runtime source tree for the operator-facing Gemini bundle.
- Routine Gemini bundle shipment should compile this source tree into a versioned zip.

Authority reminder
- Behavioral authority still begins with PP-01 through PP-07.
- The compile model is governed by DOC-10 and PP-09.
- This folder is runtime source authority for ordinary Gemini bundle shipment.

What to edit here
- `00_START_HERE/` for operator entry and attachment maps
- `01_GEMINI_AGENT_BUILD/` for parent and sub-agent runtime fields
- `02_PRIME_AGENT_ATTACHMENTS/` for approved knowledge attachments
- `Gemini_Bundle_Source_Manifest.json.txt` when version, required files, or topology change

What not to use as substitutes
- `knowledge/generated_agent_markdowns/`
- `knowledge/comparative_reference_agent_markdowns/`
- legacy or extracted bundle folders under project_sources/
- governance docs as runtime attachment substitutes

Routine workflow
1. Re-anchor with CP-01 and CP-02.
2. Edit the affected runtime source files here.
3. Update the manifest or index when needed.
4. Run `project_sources/generation_validation/validate_dcoir_gemini_bundle.py`.
5. Run `project_sources/generation_validation/compile_dcoir_gemini_bundle.py`.
6. Review the reports and the compiled zip.

Manual build shortcut
- Use `project_sources/generation_validation/build_dcoir_gemini_release.py` to run validation and compile together.

Rule of thumb
- If the intended operator-facing Gemini content changed, the edit should normally land here first.
