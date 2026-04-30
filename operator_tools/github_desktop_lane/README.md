# DCOIR GitHub Desktop Lane Tools

Reusable operator-side helper tools for AFRICOM_SOC_IR / DCOIR manual GitHub Desktop workflows.

## Authority model

- GitHub repo is source of truth for tool code.
- Airtable `Operator Tools Registry` is the live discovery index.
- The DCOIR GitHub Desktop Lane Advisor skill selects tools and generates launcher commands.
- The operator runs these scripts locally in PowerShell and uploads logs or ZIP outputs.

## Safety defaults

These tools favor read-only diagnostics, fast-forward-only pulls, explicit manifests, local logs, and stop-on-unsafe-state behavior. Do not use destructive git commands such as `git reset --hard`, `git clean`, or `git stash pop` unless a purpose-specific recovery plan calls for them.

## Environment variables

Most launchers default to these local environment variables:

```powershell
$env:DCOIR_REPO_ROOT
$env:DCOIR_DOWNLOADS_DIR
```

`DCOIR_REPO_ROOT` should point to the local `dcoir-collector` repository root. `DCOIR_DOWNLOADS_DIR` should point to the folder where logs and ZIP outputs should be written.

## Tools

| Tool | Purpose |
|---|---|
| `scripts/Get-DcoirGitConflictDiagnostic.ps1` | Capture local git/GitHub Desktop conflict state to a timestamped log. |
| `scripts/Invoke-DcoirSafePrePullApply.ps1` | Stash current local work, fast-forward pull, reapply the captured stash, and log the result. |
| `scripts/New-DcoirTargetedSnapshot.ps1` | Build a targeted snapshot ZIP from a JSON manifest after safe repo freshness checks. |
| `scripts/New-DcoirTextOnlyRepoSnapshot.ps1` | Build a read-only full-repo text snapshot ZIP for ChatGPT review while excluding binaries, generated/dependency folders, and oversized files. |
| `scripts/Invoke-DcoirRepoPatchApply.ps1` | Apply an explicit repo-relative payload manifest with wrapper-root detection, target-root allow-listing, optional pre/post hashes, delete support, and UTF-8 verification logs. |
| `scripts/New-DcoirChatGPTFriendlyZip.ps1` | Build rootless, metadata-clean, UTF-8-friendly ZIPs for ChatGPT upload and parsing, including diagnostic indexes and file manifests. |

## Git diagnostic launcher

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\Get-DcoirGitConflictDiagnostic.ps1"
```

## Safe pre-pull launcher

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\Invoke-DcoirSafePrePullApply.ps1"
```

## Targeted snapshot launcher

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\New-DcoirTargetedSnapshot.ps1" -ManifestJson "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\manifests\docs_impl_snapshot.sample.json"
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

## ChatGPT-friendly ZIP launcher

Use this shared helper when a diagnostic or snapshot tool needs to create an upload ZIP that is easy for ChatGPT to unzip and parse.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\New-DcoirChatGPTFriendlyZip.ps1" -SourceFolder "$env:DCOIR_DOWNLOADS_DIR\some_diagnostic_folder" -OutputZip "$env:DCOIR_DOWNLOADS_DIR\some_diagnostic_folder.chatgpt.zip" -NormalizeTextEncoding
```

The helper skips hidden/system metadata, avoids wrapper-root junk, adds `diagnostic_index.md`, `captured_files.json`, and `zip_manifest.json`, and can normalize staged text copies to UTF-8 without modifying original files.

Other tools may dot-source this script and call `New-DcoirChatGPTFriendlyZip` directly.

## Repo patch/apply launcher

Use this when ChatGPT provides a payload folder or extracted ZIP plus an explicit apply manifest.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\Invoke-DcoirRepoPatchApply.ps1" -ManifestJson "$env:USERPROFILE\Downloads\dcoir_apply_manifest.json" -PayloadRoot "$env:USERPROFILE\Downloads\dcoir_payload"
```

This tool is intentionally manifest-driven. It only copies files listed in `copy_map`, removes paths listed in `delete_paths`, and refuses targets outside the manifest allow-list.

## Manifest examples

- Targeted snapshot: `manifests/docs_impl_snapshot.sample.json`
- Repo patch/apply: `manifests/repo_patch_apply.sample.json`
