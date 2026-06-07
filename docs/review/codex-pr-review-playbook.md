# Codex PR Review Playbook

## Purpose

This playbook gives Codex and human reviewers a concise, repository-local rubric for high-signal pull request review in `DCOIR-Collector/dcoir-collector`. It complements `AGENTS.md`; it does not override core instructions, repository governance, GitHub source truth, or Supabase `ircore` guidance.

## Review priorities

Focus first on issues that can break correctness, safety, validation, or governance. Avoid noisy style-only comments unless they create real maintainability or reliability risk.

Prioritize findings involving:

- credential, token, secret, or sensitive path exposure
- command injection, path traversal, unsafe subprocess usage, unsafe deserialization, SSRF, or unsafe file handling
- GitHub Actions risks such as unsafe `pull_request_target`, untrusted PR input in shell commands, overbroad token permissions, or secret exposure in logs
- PowerShell compatibility risk, especially differences between Windows PowerShell 5.1 and PowerShell 7 on Linux
- collector behavior changes that could cause evidence loss, misleading output, packaging regressions, command-lane confusion, or unreliable incident-response operations
- validation gaps where changed behavior lacks a relevant test or the existing test path no longer covers the changed behavior
- repository governance violations such as workflow mutation without explicit approval, stale repo identity, invented labels, skipped readback, or bypassed review gates

## Recommended Codex helper flow

For PR fix tasks, Codex should normally run:

```bash
codex-pr-context
```

Then make the smallest safe changes needed. Before finishing, Codex should run checks that match the changed file types:

```bash
codex-review-checks
```

If the task requires pushing fixes back to the PR branch, finish with:

```bash
codex-pr-finish -m "Address PR review comments"
```

If branch detection fails, use the live PR head branch explicitly:

```bash
codex-pr-finish -b <pr-branch-name> -m "Address PR review comments"
```

## Reporting expectation

End PR fix tasks with:

```text
Summary:
- <changes made>

Validation:
- <commands run and result>
- Windows PowerShell 5.1 validation: <passed, failed, not run, or not available>

Push:
- <branch pushed>
- <commit hash if available>
- <codex-pr-finish result or exact failure>
```

## Optional repository validation wrappers

When local or Codex-environment helper commands are unavailable, use the repo-local wrappers when relevant:

```bash
bash scripts/validate-codex-local.sh
```

For exact Windows PowerShell 5.1 evidence, rely on the `windows-powershell-51.yml` workflow. For local parser checks outside Windows PowerShell 5.1, use:

```powershell
pwsh -NoProfile -File scripts/validate-windows-powershell-51.ps1 -AllowPowerShell7 -AllowEmpty
```

For CodeQL workflow-shape checks after security workflow changes, use:

```bash
python3 scripts/validate-codeql-security-workflow.py
```

With no arguments, `bash scripts/validate-codex-local.sh` validates changed files relative to `CODEX_BASE_REF` or `origin/main`, plus staged and unstaged local changes. Pass explicit paths for a narrower scoped validation.

CodeQL findings must be read back through the GitHub code scanning surface or workflow logs; local workflow-shape validation is not a substitute for CodeQL analysis.

