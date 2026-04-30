# GitHub Desktop Lane Tool Families

Use these families when matching operator requests:

- `git_diagnostics`: inspect git state, conflicts, rebase/merge/cherry-pick state, stashes, ahead/behind, and changed files.
- `repo_recovery`: safely stash local work, fast-forward pull, reapply the captured stash, and preserve logs.
- `snapshot_bundle`: build targeted repo snapshots from path manifests after safe repo freshness checks.
- `validation`: run or capture validation results.
- `github_desktop_lane`: general manual update and commit/push workflow support.

Do not use local tools for background work. The operator runs them and uploads outputs.
