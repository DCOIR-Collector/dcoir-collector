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
| `scripts/New-DcoirTextOnlyRepoSnapshot.ps1` | Build a read-only full-repo text snapshot ZIP for ChatGPT review while excluding binaries, generated/dependency folders, and oversized files. |

## Environment variables

Most launchers default to these local environment variables:

```powershell
$env:DCOIR_REPO_ROOT
$env:DCOIR_DOWNLOADS_DIR
```

`DCOIR_REPO_ROOT` should point to the local `dcoir-collector` repository root. `DCOIR_DOWNLOADS_DIR` should point to the folder where logs and ZIP outputs should be written.

## Example launcher

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\Get-DcoirGitConflictDiagnostic.ps1"
```

## Text-only repo snapshot launcher

Use this when ChatGPT needs to scan the local repository contents without binary files:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\New-DcoirTextOnlyRepoSnapshot.ps1"
```

Outputs are written to `DCOIR_DOWNLOADS_DIR` when set, otherwise to the current user's Downloads folder:

```text
dcoir_text_only_repo_snapshot_YYYYMMDD_HHMMSS.zip
dcoir_text_only_repo_snapshot_YYYYMMDD_HHMMSS.log.txt
dcoir_text_only_repo_snapshot_YYYYMMDD_HHMMSS.manifest.json
```

Upload all three outputs when asking ChatGPT to perform a full-repo text/reference scan.

## Snapshot manifest example

See `manifests/docs_impl_snapshot.sample.json`.
