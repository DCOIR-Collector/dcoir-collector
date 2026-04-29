# GitHub Actions Artifact Playbook

Use this reference when an uploaded archive appears to contain GitHub Actions logs, CI artifacts, workflow output, test reports, or build products.

## First-pass priority
1. Workflow summary files.
2. JUnit, pytest, coverage, SARIF, or test-results files.
3. Files or paths containing `failure`, `failed`, `error`, `stderr`, `traceback`, or `exception`.
4. Small log-like files before very large generated artifacts.
5. README or manifest files that explain artifact layout.

## Avoid on first pass
- dependency caches
- node_modules
- virtual environments
- build/dist/output folders unless they contain explicit failure reports
- binary assets
- full recursive grep across the extracted tree

## Failure marker patterns
Look for bounded excerpts around:
- `error:`
- `failed`
- `failure`
- `traceback`
- `exception`
- `assert`
- `exit code`
- `non-zero`
- `##[error]`
