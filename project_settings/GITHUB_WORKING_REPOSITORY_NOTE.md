# GitHub Working Repository Note

Use the GitHub connector against the repository `malwaredevil/dcoir-collector` for DCOIR repo-side read, create, update, branch, PR, and review work.

Important boundaries:
- GitHub is the working repository and review surface.
- The ChatGPT Project workspace remains the applied governed runtime state.
- Project authority still comes from Project Instructions, `CP-01_DCOIR_Version_Manifest.txt`, and `CP-02_DCOIR_Change_Log.txt`.
- Do not treat repo contents alone as control-plane authority unless the Project workspace is refreshed and the control plane says the files are current.
- If GitHub file search is needed through the search connector path, make sure the `malwaredevil/dcoir-collector` repo is explicitly selected in ChatGPT.
