# DCOIR GitHub Desktop Lane PowerShell Modules

This folder contains reusable PowerShell module building blocks for DCOIR operator-side tools.

## Module roles

| Module | Role |
|---|---|
| `Dcoir.Common` | Environment/path resolution, placeholder rejection, JSON conversion, UTF-8 file writes, timestamped console/log output, safe names, and shared run context. |
| `Dcoir.Git` | Git executable discovery, native argument quoting, logged git execution, branch/status checks, clean-tree checks, fetch, fast-forward pull, stash-safe support, and ahead/behind analysis. |
| `Dcoir.Snapshot` | Repo-relative path safety, safe names, path normalization, under-root checks, text-file filtering, binary sniffing, targeted staging, and UTF-8 snapshot logging. |
| `Dcoir.RepoPatch` | Repo patch path safety, payload-root resolution, wrapper-root stripping, allowed target roots, copy/delete planning, hashing, UTF-8 verification, and apply logging. |
| `Dcoir.GitHub` | GitHub CLI availability, `gh api` JSON/text wrappers, Actions workflow run lookup, run lookup, and job lookup. |
| `Dcoir.Packaging` | ChatGPT-friendly ZIP invocation and reusable packaging entrypoints. |
| `Dcoir.Actions` | Manifest parsing, dispatch guardrails, workflow dispatch, monitoring, fail-fast gates, evidence capture, summaries, cleanup, and exit codes. |
| `DcoirActionsOrchestrator` | Compatibility facade preserving the existing public orchestrator entrypoint. |

## Harness boundary

Harness scripts should only create reviewed JSON configuration and execute the orchestrator or module-owned engine. Shared patterns used by multiple tools belong in these modules rather than inside wrappers.

## Compatibility

The modules target Windows PowerShell 5.1 and PowerShell 7. Avoid syntax that requires newer runtimes unless the wrapper explicitly gates for it.

## Documentation surfaces

- Parent README: `operator_tools/github_desktop_lane/README.md`
- Operator guide: `operator_tools/github_desktop_lane/docs/OPERATOR_GUIDE.md`
- Machine-readable catalog: `operator_tools/github_desktop_lane/tool_catalog.json`
