# Repository validation scripts

This folder contains operator-friendly validation wrappers used by Codex, GitHub Desktop, and manual review lanes.

## Scripts

- `validate-codex-local.sh` runs a local best-effort review pass using available tools such as `rg`, `shellcheck`, `shfmt`, `yamllint`, `ruff`, `bandit`, `semgrep`, and PowerShell parser checks.
- `validate-windows-powershell-51.ps1` validates PowerShell parser compatibility. In the Windows PowerShell 5.1 workflow it requires Windows PowerShell 5.1; local Linux/macOS syntax checks may pass `-AllowPowerShell7`.
- `validate-codeql-security-workflow.py` validates that the repo-local CodeQL workflow and reusable workflow retain the expected security configuration shape.

These scripts do not replace GitHub Actions readback. Use workflow run, job, step, and artifact evidence for governed readiness claims.
