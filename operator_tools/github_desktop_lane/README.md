# DCOIR GitHub Desktop Lane Tools

Reusable operator-side helper tools for AFRICOM_SOC_IR / DCOIR manual GitHub Desktop workflows.

## Authority model

- GitHub repo is source of truth for tool code.
- Airtable `Operator Tools Registry` is the live discovery index.
- The DCOIR GitHub Desktop Lane Advisor skill selects tools and generates launcher commands.
- The operator runs these scripts locally in PowerShell and uploads logs or ZIP outputs.

## Safety defaults

These tools favor read-only diagnostics, fast-forward-only pulls, explicit manifests, local logs, and stop-on-unsafe-state behavior. Do not use destructive git commands such as `git reset --hard`, `git clean`, or `git stash pop` unless a purpose-specific recovery plan calls for them.

GitHub Actions terminology used by this toolset:

- `workflow`: the YAML automation definition under `.github/workflows/`.
- `workflow run`: one execution of a workflow.
- `job`: an execution unit inside a workflow run.

GitHub Actions allows multiple workflow runs by default, but a workflow or job may define a `concurrency` group. In a concurrency group, GitHub allows at most one running and one pending workflow run or job at a time. The orchestrator therefore uses `max_parallel` only as a local dispatch throttle; GitHub runner availability and workflow-level concurrency still decide actual execution order.

## Environment variables

DCOIR operator tools resolve local configuration from **Machine/System** environment variables:

```powershell
[Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
[Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
```

`DCOIR_REPO_ROOT` should point to the local `dcoir-collector` repository root. `DCOIR_DOWNLOADS_DIR` should point to the folder where logs and ZIP outputs should be written.

The Actions orchestrator rejects placeholder paths such as `C:\path\to\dcoir-collector` and does not trust process-scoped placeholder values from a polluted terminal session.

## System-scope launcher pattern

Use this launcher pattern when a terminal may have stale or placeholder process variables:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { `$repo=[Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine'); if ([string]::IsNullOrWhiteSpace(`$repo)) { throw 'DCOIR_REPO_ROOT is not set as a Machine/System environment variable.' }; & (Join-Path `$repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirActionsWorkflowOrchestrator.ps1') }"
```

## Tools

| Tool | Purpose |
|---|---|
| `scripts/Get-DcoirGitConflictDiagnostic.ps1` | Capture local git/GitHub Desktop conflict state to a timestamped log. |
| `scripts/Invoke-DcoirSafePrePullApply.ps1` | Stash current local work, fast-forward pull, reapply the captured stash, and log the result. |
| `scripts/New-DcoirTargetedSnapshot.ps1` | Build a targeted snapshot ZIP from a JSON manifest after safe repo freshness checks. |
| `scripts/New-DcoirTextOnlyRepoSnapshot.ps1` | Build a read-only full-repo text snapshot ZIP for ChatGPT review while excluding binaries, generated/dependency folders, and oversized files. |
| `scripts/Invoke-DcoirRepoPatchApply.ps1` | Apply an explicit repo-relative payload manifest with wrapper-root detection, target-root allow-listing, optional pre/post hashes, delete support, and UTF-8 verification logs. |
| `scripts/New-DcoirChatGPTFriendlyZip.ps1` | Build rootless, metadata-clean, UTF-8-friendly ZIPs for ChatGPT upload and parsing, including diagnostic indexes and file manifests. |
| `scripts/Invoke-DcoirActionsWorkflowOrchestrator.ps1` | Watch, capture, or dispatch 1..N GitHub Actions workflow runs from a manifest, monitor them, collect evidence, and produce a ChatGPT-friendly ZIP. |

## Actions workflow orchestrator launchers

Dry-run dispatch using the bundled sample manifest:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { `$repo=[Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine'); if ([string]::IsNullOrWhiteSpace(`$repo)) { throw 'DCOIR_REPO_ROOT is not set as a Machine/System environment variable.' }; `$script=Join-Path `$repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirActionsWorkflowOrchestrator.ps1'; `$manifest=Join-Path `$repo 'operator_tools\github_desktop_lane\manifests\actions_workflow_orchestrator.dispatch.sample.json'; & `$script -ManifestJson `$manifest }"
```

Watch latest runs without dispatching:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { `$repo=[Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine'); if ([string]::IsNullOrWhiteSpace(`$repo)) { throw 'DCOIR_REPO_ROOT is not set as a Machine/System environment variable.' }; `$script=Join-Path `$repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirActionsWorkflowOrchestrator.ps1'; `$manifest=Join-Path `$repo 'operator_tools\github_desktop_lane\manifests\actions_workflow_orchestrator.watch.sample.json'; & `$script -ManifestJson `$manifest }"
```

Live dispatch after reviewing the generated plan and setting `dry_run` to `false` in a copied manifest:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { `$repo=[Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine'); `$downloads=[Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine'); if ([string]::IsNullOrWhiteSpace(`$repo)) { throw 'DCOIR_REPO_ROOT is not set as a Machine/System environment variable.' }; if ([string]::IsNullOrWhiteSpace(`$downloads)) { throw 'DCOIR_DOWNLOADS_DIR is not set as a Machine/System environment variable.' }; `$script=Join-Path `$repo 'operator_tools\github_desktop_lane\scripts\Invoke-DcoirActionsWorkflowOrchestrator.ps1'; `$manifest=Join-Path `$downloads 'my_actions_manifest.json'; & `$script -ManifestJson `$manifest -ConfirmDispatch }"
```

The orchestrator can also be run without `-ManifestJson`; in `manifest` mode it defaults to the bundled dry-run dispatch sample under the Machine/System `DCOIR_REPO_ROOT`.

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

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\New-DcoirTextOnlyRepoSnapshot.ps1"
```

## ChatGPT-friendly ZIP launcher

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\New-DcoirChatGPTFriendlyZip.ps1" -SourceFolder "$env:DCOIR_DOWNLOADS_DIR\some_diagnostic_folder" -OutputZip "$env:DCOIR_DOWNLOADS_DIR\some_diagnostic_folder.chatgpt.zip" -NormalizeTextEncoding
```

## Repo patch/apply launcher

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:DCOIR_REPO_ROOT\operator_tools\github_desktop_lane\scripts\Invoke-DcoirRepoPatchApply.ps1" -ManifestJson "$env:USERPROFILE\Downloads\dcoir_apply_manifest.json" -PayloadRoot "$env:USERPROFILE\Downloads\dcoir_payload"
```

## Manifest examples

- Targeted snapshot: `manifests/docs_impl_snapshot.sample.json`
- Repo patch/apply: `manifests/repo_patch_apply.sample.json`
- Actions orchestrator dispatch: `manifests/actions_workflow_orchestrator.dispatch.sample.json`
- Actions orchestrator watch: `manifests/actions_workflow_orchestrator.watch.sample.json`
