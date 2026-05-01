# GitHub Desktop Lane Tool Families

Use these families when matching operator requests:

- `git_diagnostics`: inspect git state, conflicts, rebase/merge/cherry-pick state, stashes, ahead/behind, changed files, and recent graph.
- `repo_recovery`: safely stash local work, fast-forward pull, reapply only newly-created captured stashes, and preserve logs.
- `snapshot_bundle`: build targeted or text-only repo snapshots after safe repo freshness checks.
- `repo_repair_apply`: apply reviewed repo-relative payload manifests with allowed roots, pre/post checks, hash evidence, delete support, result JSON, and GitHub Desktop review before commit.
- `upload_packaging`: create rootless ChatGPT-friendly ZIP files with triage indexes and metadata manifests.
- `github_actions_orchestration`: create, watch, dispatch, monitor, capture, package, and summarize GitHub Actions workflow runs through the orchestrator.
- `validation`: run or capture validation results.
- `github_desktop_lane`: general manual update and commit/push workflow support.

Do not use local tools for background work. The operator runs them and uploads outputs.

Harnesses are thin launchers only. Durable behavior belongs in modules/tools.
