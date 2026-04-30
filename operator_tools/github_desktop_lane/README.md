# DCOIR GitHub Desktop Lane Tools

Reusable operator-side helper tools for AFRICOM_SOC_IR / DCOIR manual GitHub Desktop workflows.

## Authority model

- GitHub repo is source of truth for tool code.
- Airtable `Operator Tools Registry` is the live discovery index.
- The DCOIR GitHub Desktop Lane Advisor skill selects tools and generates launcher commands.
- The operator runs these scripts locally in PowerShell and uploads logs or ZIP outputs.

## Safety defaults

These tools favor read-only diagnostics, fast-forward-only pulls, explicit stashing, and log output. Do not use destructive git commands such as `git reset --hard`, `git clean`, or `git stash pop` unless a specific recovery plan calls for them.

## Tools

| Tool | Purpose |
|---|---|
| `scripts/Get-DcoirGitConflictDiagnostic.ps1` | Capture local git/GitHub Desktop conflict state to a timestamped log. |
| `scripts/Invoke-DcoirSafePrePullApply.ps1` | Stash current local work, fast-forward pull, reapply the captured stash, and log the result. |
| `scripts/New-DcoirTargetedSnapshot.ps1` | Build a targeted snapshot ZIP from a JSON manifest after safe repo freshness checks. |

## Example launcher

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\Get-DcoirGitConflictDiagnostic.ps1"
```

## Snapshot manifest example

See `manifests/docs_impl_snapshot.sample.json`.
