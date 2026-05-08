# ChatGPT heartbeat and artifact readback contract

Status: active contract for `chatgpt-exec`, `chatgpt-apply-in`, and `chatgpt-stage-out`.

## Purpose

ChatGPT must be able to monitor workflow progress and inspect workflow outputs without depending on the operator to download ZIP artifacts, upload files, paste logs, or provide screenshots.

## Heartbeat contract

Each heartbeat-producing workflow writes a committed live report directory while the run is active:

```text
chatgpt_staging/status_reports/<workflow>/<request_id>/
  workflow_report.md
  progress_history.jsonl
```

The workflow must commit this directory after each meaningful phase update using a `[skip ci]` report commit so the latest heartbeat is visible through the GitHub connector.

ChatGPT should poll `workflow_report.md` by exact request id until `result` is `success` or `failure`. The `progress_history.jsonl` file is the durable heartbeat history and should be read when the current report is ambiguous.

## Artifact readback contract

GitHub Actions may still upload ZIP artifacts for operator download and short-retention provenance. ZIP artifacts are supplemental only.

When a workflow generates sanitized diagnostic files or output files that ChatGPT may need, it must also commit an unzipped readback copy as ordinary repository files under the same status-report family, normally:

```text
chatgpt_staging/status_reports/<workflow>/<request_id>/artifact_readback/
```

For `chatgpt-exec`, this directory includes sanitized stdout/stderr, sanitized request/command, `exec_result.json`, and any files written under the exec downloads directory.

For `chatgpt-apply-in`, the committed `workflow_report.md` and native apply-in report are the first readback source. Any failure evidence that would otherwise live only in a ZIP artifact should also be copied under `artifact_readback/` beside the workflow report when the workflow generates such files.

For `chatgpt-stage-out`, the primary readback surface is already the committed output directory:

```text
chatgpt_staging/out/<request_id>/
```

The stage-out ZIP artifact is supplemental. ChatGPT should read `manifest.md`, `manifest.json`, `chunks/`, and `files/` directly from the committed output directory.

## ChatGPT read order

1. Read `workflow_report.md` for the exact workflow/request id.
2. Read `progress_history.jsonl` when phase history matters.
3. Read `artifact_readback/` or `chatgpt_staging/out/<request_id>/` for unzipped outputs.
4. Use GitHub Actions ZIP artifacts only if the committed readback files are missing or insufficient.
5. Ask the operator for screenshots or manual uploads only after the committed report/readback paths and GitHub connector artifact paths have been tried.

## Workflow repair rule

When a workflow only uploads ZIP artifacts and does not commit the corresponding sanitized unzipped readback files, treat that as a workflow/tooling gap. Repair the workflow or harness so future runs commit readable output files in addition to uploading the ZIP artifact.

## Cleanup

Readback files are temporary operational evidence unless a plan, work item, validation record, or operator instruction says to retain them. After ChatGPT reads the needed report/readback files and records durable evidence, use the staging cleanup lane to remove status reports, readback directories, and output bundles that no longer need retention.
