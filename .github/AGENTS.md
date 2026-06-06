# .github AGENTS.md

## Scope

These instructions apply to files under `.github/`. They supplement the repository root `AGENTS.md` and do not override workflow-boundary rules.

## GitHub Actions and repository automation review guidance

Workflow files are governed surfaces. Do not create, edit, loosen, or remove workflow files unless the operator explicitly approves workflow changes in the current task.

When reviewing `.github/workflows/` changes, prioritize:

- unsafe `pull_request_target` usage
- untrusted PR data interpolated into shell commands
- missing or overbroad `permissions:` blocks
- secret exposure in logs, artifacts, summaries, or uploaded reports
- write-token use where read-only token permissions would be sufficient
- artifact path traversal, untrusted zip extraction, or unsafe generated script execution
- stale repository identity, branch, path, or workflow-name references
- validation claims without workflow run, job, step, or artifact readback

When a PR task touches GitHub metadata, templates, CODEOWNERS, workflows, or repository governance files, use `codex-pr-context` first when available and report any validation gaps explicitly.
