# 2026-04-03 GitHub existing-file update lane recovery and execution discipline

Purpose
- Preserve the known working low-level GitHub existing-file update lane for governed readable text.
- Correct the earlier 2026-04-03 helper-memory note that prematurely attributed the issue to connector surface drift before the validated lane was fully re-applied.

Known working lane
- For existing-file updates and grouped existing-file changes, the intended lane is the low-level git-object transaction flow.
- The core sequence is:
  1. read live state of every touched file
  2. recover the current head commit sha
  3. create blob objects for the replacement file contents
  4. create one grouped tree using the current head sha as the accepted base-tree input
  5. create one commit from that grouped tree with the current head as parent
  6. move the branch ref to the new commit sha
  7. verify every touched path by direct readback from main

Canonical authority pointers
- `knowledge/task_memory/10_domains/github/procedures/GH-PROC-001-existing-file-update.yaml`
- `knowledge/task_memory/10_domains/github/procedures/GH-PROC-006-grouped-multi-file-transaction.yaml`
- `knowledge/task_memory/10_domains/github/procedures/GH-PROC-007-memory-preflight-routing.yaml`
- `knowledge/task_memory/10_domains/github/procedures/GH-PROC-005-post-write-verification.yaml`
- `knowledge/github_connector_reference/GitHub_Connector_Execution_Guide.md`

What went wrong in this session
- Canonical memory with the validated low-level lane already existed.
- The assistant did not pivot back to `GH-PROC-001` or `GH-PROC-006` quickly enough after friction appeared.
- The assistant prematurely wrote speculative connector-limitation and surface-drift language before fully exhausting the validated lane.
- The failure should therefore be classified as assistant procedure-recovery failure and execution-discipline failure.

Practical lesson
- Do not treat this as a connector limitation by default.
- First re-anchor, run `GH-PROC-007`, and apply the validated low-level lane.
- Only after a named low-level step fails should any tool limitation be considered for durable recording.

Operator-facing rule
- If GitHub existing-file update work hits friction, report the block immediately.
- State:
  - which canonical records were consulted
  - which low-level step is being attempted or failed
  - whether the failure is assistant execution failure, assistant recall failure, or a proven tool limitation
  - whether an operator-managed lane should be offered as an option rather than assumed

Best next move
- During future GitHub-family preflight, treat `GH-PROC-001`, `GH-PROC-006`, `GH-PROC-007`, and `GH-PROC-005` as the first recovery set for existing-file update work.
