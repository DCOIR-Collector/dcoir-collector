# 2026-04-03 GitHub existing-file update lane and surface drift

Purpose
- Preserve the exact remembered low-level GitHub update lane for existing governed files.
- Preserve the observed live-connector drift that can block replay of that lane even when the conceptual procedure is known.

Known working conceptual lane
- For existing-file updates and grouped existing-file changes, the intended lane is the low-level git-object transaction flow.
- The core sequence is:
  1. resolve current head commit sha
  2. read the live state of every touched file
  3. create blob objects for the replacement file contents
  4. create one grouped tree using the current base tree sha
  5. create one commit from that grouped tree with the current head as parent
  6. move the branch ref to the new commit sha
  7. verify every touched path by direct readback from main

Canonical authority pointers
- `knowledge/task_memory/10_domains/github/procedures/GH-PROC-007-memory-preflight-routing.yaml`
- `knowledge/task_memory/10_domains/github/procedures/GH-PROC-006-grouped-multi-file-transaction.yaml`
- `knowledge/task_memory/10_domains/github/procedures/GH-PROC-005-post-write-verification.yaml`
- `knowledge/github_connector_reference/GitHub_Connector_Execution_Guide.md`

Observed live-surface issue in this session
- The governed connector snapshot and guide still point to the low-level git-object lane as the preferred path for existing-file updates and grouped changes.
- In the live connector surface available in this chat, some helper functions present in the governed connector snapshot are not exposed.
- A concrete example from this session: `list_blob_versions` appears in the governed connector snapshot but was not available in the live tool surface.
- Because of that drift, the remembered procedure may still be correct while the currently exposed tool surface is missing one or more practical helper steps that previously made the lane easier to execute.

Practical lesson
- Do not treat this as a pure memory failure by default.
- First check whether the live connector surface in the current chat matches the governed connector snapshot.
- If the live surface is missing helper functions that the documented procedure expected, classify the issue as tool-surface drift or tool-surface mismatch rather than operator-rule drift.

Operator-facing rule
- If GitHub existing-file update work is blocked by connector-surface mismatch, report the block immediately.
- State:
  - that the low-level lane is still the intended path
  - which live helper function or metadata path appears missing
  - whether a bounded alternative exists in-chat
  - whether a manual lane should be offered as an option rather than assumed

Best next move
- During future GitHub-family preflight, check the live GitHub connector surface against the governed connector snapshot before assuming the previously documented helper-call sequence is fully replayable.
