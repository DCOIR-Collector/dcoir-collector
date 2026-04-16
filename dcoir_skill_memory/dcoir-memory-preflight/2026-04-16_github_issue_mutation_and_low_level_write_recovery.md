# 2026-04-16 GitHub issue mutation lane and low-level write recovery

Purpose
- Preserve the GitHub issue-thread mutation lane that was actually validated in this session.
- Preserve the newly reconfirmed low-level file-write recovery details that mattered when the higher-level existing-file wrapper was inconsistent or safety-blocked.
- Give `dcoir-memory-preflight` a durable helper-memory note that can later be promoted into canonical GitHub task memory if the operator wants that path hardened further.

Validated in this session
- `fetch_issue` worked for current issue-state readback.
- `add_comment_to_issue` worked repeatedly for durable issue-thread updates on live GitHub issues.
- The live tool surface exposed `update_issue` when the GitHub connector resource tree was re-listed with `only_tools=true` and `refetch_tools=true`, but invocation still behaved inconsistently in this chat. Do not assume issue close or state mutation is reliable until the exact live invocation succeeds in the current session.
- `update_file` for existing governed files remained inconsistent and was sometimes safety-blocked.
- The low-level git-object lane remained workable for governed existing-file updates: `create_blob` -> `create_tree` -> `create_commit` -> `update_ref` -> direct readback verification.
- In this session, `create_tree` accepted the current head commit SHA as the practical `base_tree_sha` input and returned a usable replacement tree.

Known working issue lane
1. Re-anchor and run GitHub-family preflight first.
2. Re-list the live GitHub connector tool surface on the specific connector path when wrapper availability is uncertain.
3. Use `fetch_issue` to confirm the current issue body and scope.
4. Use `add_comment_to_issue` for durable status updates, validation notes, or lane-splitting notes.
5. Treat issue close or state mutation as a separate step that still requires live proof in the current chat if the wrapper surface is inconsistent.
6. Verify the thread update by re-reading the issue or its comments when the lane matters.

Known working existing-file recovery lane
1. Read the live file state from `main`.
2. Create replacement blob content with `create_blob`.
3. Create one replacement tree with `create_tree` using the current head commit SHA as the accepted base-tree input for this connector surface.
4. Create one commit with `create_commit`.
5. Fast-forward `main` with `update_ref`.
6. Verify by direct `fetch_file` readback from `main`.

What this means for future preflight
- For GitHub-family execution planning, preflight should distinguish among:
  - issue-thread mutation lanes that are already validated enough for comment-based status updates
  - issue state-mutation lanes that still need live-session proof before being treated as reliable
  - existing-file write lanes that should prefer the low-level git-object transaction flow when the higher-level wrapper is inconsistent
- Do not overgeneralize from tool inventory alone. Live wrapper visibility and live wrapper reliability are separate questions.

Promotion recommendation
- Classification: reusable_procedure_candidate
- Candidate durable promotion targets:
  - extend `GH-PROC-008` with an explicit issue-thread mutation and issue-state-mutation lane split
  - or create a new canonical GitHub procedure record for issue-thread status mutation and live-surface verification
  - optionally add a failure-signature or limitation record only if the issue-state mutation inconsistency reproduces again with a named failing step

Next flush trigger
- Before the next GitHub-heavy preflight refresh or the next repo update that also depends on issue tracking or closeout behavior.
