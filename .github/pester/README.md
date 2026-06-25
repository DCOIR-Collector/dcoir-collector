# Pester tests for Codex validation

Place Codex-focused Pester tests in this directory and name each file `*.Tests.ps1`.

`codex-review-checks` runs Pester only when changed PowerShell files exist and Pester test files are present. The helper prefers this directory through `CODEX_PESTER_PATH=.github/pester`, then falls back to repository-wide `*.Tests.ps1` discovery.

Linux `pwsh` Pester results are useful for syntax and cross-platform behavior, but they do not prove exact Windows PowerShell 5.1 behavior. Use the configured Windows PowerShell 5.1 GitHub Actions workflow for that validation.
