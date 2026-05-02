# ChatGPT Repo-Wide Workflow Reporting Policy

Status: active follow-up policy for `WI-20260502-STAGING-LANE-FOLLOWUP-REPO-WIDE-WORKFLOW-REPORTS`.

Purpose: make GitHub Actions results readable by ChatGPT without requiring the operator to upload screenshots, paste logs, or manually hunt for run IDs.

## Reporting model

Repo-wide workflow reporting uses a central reporter instead of duplicating reporting steps into every workflow.

```text
.github/workflows/chatgpt-workflow-run-reporter.yml
.github/scripts/write_workflow_report.py
```

When a configured workflow completes, `chatgpt-workflow-run-reporter` writes one standardized Markdown report under:

```text
chatgpt_staging/status_reports/repo-workflows/<workflow-name>/<workflow-run-id>/workflow_report.md
```

The existing staging-lane workflows still write their native workflow reports under their existing paths. They do not need to be duplicated by the central reporter until they are migrated to the shared report writer without losing staging-specific context.

## Validation harness

The dedicated validation harness is separate from `workflow-maintenance-audit.yml` because it validates the reporting system itself, not workflow action-version hygiene.

```text
.github/workflows/chatgpt-workflow-reporting-validation.yml
```

Run it manually with:

- `scenario=success` to validate a normal success report path.
- `scenario=failure` to deliberately fail with recognizable debug markers so the central reporter must embed bounded failure logs in `workflow_report.md`.

The failure scenario is intentionally safe and should not modify repository source files. It is expected to fail so the reporter can prove that ChatGPT can diagnose failures without operator screenshots, pasted logs, or uploaded logs.

## Report contents

Each repo-wide report should include enough context for ChatGPT to decide whether the run succeeded, whether a repair is needed, and where to inspect deeper logs if necessary.

Required fields include:

- source workflow name
- result and GitHub conclusion
- source event
- workflow run ID and URL
- branch, SHA, repository, actor
- reporter run ID and SHA
- report timestamp
- troubleshooting context
- next ChatGPT action
- cleanup guidance

Failure reports must include bounded diagnostic log excerpts when GitHub log retrieval succeeds. Metadata-only failure reports are not sufficient.

## Success behavior

A success report means the source workflow completed successfully. ChatGPT should still inspect the report when the workflow protects a code, docs, packaging, validation, or operational surface, because a successful workflow may indicate that related workflow/reporting logic should be kept aligned with changed code.

## Failure behavior

A failure report is the first place ChatGPT should look before asking the operator for screenshots, pasted logs, uploaded logs, or a commit SHA.

The Markdown report should include a bounded log excerpt. If the excerpt is not enough, ChatGPT should use the workflow run URL in the report to inspect GitHub Actions logs and artifacts.

## Reporter coverage

The reporter workflow intentionally uses an explicit workflow-name allowlist to avoid recursive workflow loops. When adding a new repository workflow, update `chatgpt-workflow-run-reporter.yml` if that workflow should produce ChatGPT-readable reports.

Do not add the reporter workflow itself to the allowlist. Do not add the report-retention cleanup workflow to the allowlist; it writes its own cleanup report.

## Cleanup model

Repo-wide workflow reports are cleaned by the dedicated retention cleanup workflow:

```text
.github/workflows/chatgpt-report-retention-cleanup.yml
```

This workflow supports:

- scheduled cleanup
- manual cleanup from GitHub Actions
- dry-run previews
- success/failure/cleanup retention windows
- workflow/path filtering
- latest-report preservation per workflow

Default retention:

| Report type | Default retention |
|---|---:|
| success reports | 7 days |
| cleanup reports | 7 days |
| failure reports | 30 days |

The cleanup workflow writes its own report under:

```text
chatgpt_staging/status_reports/retention-cleanup/<run-id>/workflow_report.md
```

## Safety rules

- Reports are temporary unless Airtable Validation Evidence or an active Work Item says to retain them.
- Cleanup must stay under `chatgpt_staging/status_reports/`.
- `.gitkeep` scaffold files must not be deleted.
- The latest report for each workflow is preserved by default.
- Cleanup commits use `[skip ci]`.
- ChatGPT must verify cleanup by GitHub readback before claiming completion.

## Operator rule

If you want cleanup on demand, manually run `chatgpt-report-retention-cleanup` from GitHub Actions. Use dry-run first when unsure.

If ChatGPT asks for workflow logs, remind it to check `chatgpt_staging/status_reports/` first.
