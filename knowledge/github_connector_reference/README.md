# GitHub Connector Reference Pack

Purpose
- This folder stores governed reference material for the GitHub connector used in the DCOIR project workflow.
- It exists to reduce avoidable trial-and-error when selecting GitHub connector functions, shaping arguments, and reasoning about expected return data.

Authority posture
- The live GitHub connector tool surface remains the final authority.
- The files in this folder are governed reference aids and snapshots, not a replacement for the current live tool definition.
- If the live connector surface and this reference pack disagree, prefer the live surface and record the drift for future maintenance.

Files in this folder
- `github_connector_information.json`
  - canonical machine-oriented **distilled** snapshot derived from the uploaded GitHub connector reference set
  - preserves the 61 function inventory, names, descriptions, required inputs, input fields, and compact return hints
  - preferred first read when exact function selection and parameter-shape comparison matter
- `GitHub_Connector_Execution_Guide.md`
  - human-facing operating guide distilled from the uploaded TXT view plus current DCOIR workflow needs
  - preferred first read when choosing a lane or teaching the operator how the connector should be used in practice

Current snapshot note
- The uploaded source reference identifies `GitHub Connector Information` with `total_functions` equal to `61`.
- The governed JSON file in this folder is a distilled derivative chosen for speed and maintainability rather than a second full raw schema dump.
- The TXT upload was used as the human-readable companion source for the execution guide rather than being stored as a second large raw reference file.

How to use this pack
1. Re-anchor to Project Instructions, then CP-01, then CP-02.
2. Use canonical task-memory preflight for GitHub-family work.
3. Open `github_connector_information.json` to inspect exact function names, required inputs, and compact return hints.
4. Use `GitHub_Connector_Execution_Guide.md` to map the task into the right connector lane.
5. If the task is a grouped change or existing-file update, still prefer the validated git-object write lane already documented in task memory.
6. After execution, verify by readback instead of trusting success messages alone.

Maintenance rule
- Promote durable lessons from this reference pack into canonical task memory rather than leaving them only in this folder.
- Keep all project-specific helper skills under the `dcoir-` prefix.
