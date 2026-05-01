# DCOIR GitHub Desktop Lane PowerShell Modules

This folder contains reusable PowerShell module building blocks for DCOIR operator-side tools.

## Module roles

| Module | Role |
|---|---|
| `Dcoir.Common` | Environment/path resolution, placeholder rejection, JSON conversion, UTF-8 file writes, timestamped console/log output, safe names, and shared run context. |
| `Dcoir.GitHub` | GitHub CLI availability, `gh api` JSON/text wrappers, Actions workflow run lookup, run lookup, and job lookup. |
| `Dcoir.Packaging` | ChatGPT-friendly ZIP invocation and reusable packaging entrypoints. |
| `Dcoir.Actions` | Manifest parsing, dispatch guardrails, workflow dispatch, monitoring, fail-fast gates, evidence capture, summaries, cleanup, and exit codes. |
| `DcoirActionsOrchestrator` | Compatibility facade preserving the existing public orchestrator entrypoint. |

## Harness boundary

Harness scripts should only create JSON configuration and execute the orchestrator. Shared patterns used by multiple tools belong in these modules rather than inside wrappers.

## Compatibility

The modules target Windows PowerShell 5.1 and PowerShell 7. Avoid syntax that requires newer runtimes unless the wrapper explicitly gates for it.
