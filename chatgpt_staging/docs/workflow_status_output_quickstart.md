# Workflow status and output quickstart

Status: active new-session pointer for ChatGPT workflow readback.

Use this document when a session is working with `chatgpt-exec`, `chatgpt-apply-in` / `chatgpt-in`, or `chatgpt-stage-out`.

## Read status first

For any request id, read the committed heartbeat files before asking the operator for screenshots, pasted logs, uploaded logs, downloaded ZIPs, or manual artifact handling:

```text
chatgpt_staging/status_reports/<workflow>/<request_id>/workflow_report.md
chatgpt_staging/status_reports/<workflow>/<request_id>/progress_history.jsonl
```

Poll `workflow_report.md` until `result` is `success` or `failure`.

## Read outputs next

Use committed unzipped readback files before GitHub Actions ZIP artifacts.

`chatgpt-exec` output path:

```text
chatgpt_staging/status_reports/chatgpt-exec/<request_id>/artifact_readback/
```

Files written under `DCOIR_DOWNLOADS_DIR` appear under:

```text
artifact_readback/downloads/<output_folder>/
```

`chatgpt-stage-out` output path:

```text
chatgpt_staging/out/<request_id>/
```

Read `manifest.md`, `manifest.json`, `chunks/`, and `files/` directly.

`chatgpt-apply-in` output path:

```text
chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/workflow_report.md
chatgpt_staging/status_reports/chatgpt-apply-in/<request_id>/progress_history.jsonl
```

Read the native apply-in success/failure report embedded in the workflow report before asking for logs.

## Artifact rule

ZIP artifacts are supplemental. They remain useful for GitHub provenance and short-term operator download, but ChatGPT should not rely on ZIP download/upload when committed reports or readback folders exist.

## Apply-in payload rule

Before staging `payload.zip.b64`, generate it with a tool or script, verify ZIP open/CRC, verify base64 round-trip, verify length is divisible by 4, record SHA256 values, and only then stage the single payload file.

## Current validated exec smoke

`smoke-exec-artifact-readback-002` verified that `chatgpt-exec` commits:

- `workflow_report.md`
- `progress_history.jsonl`
- `artifact_readback/README.md`
- `artifact_readback/approved_command.sanitized.ps1`
- `artifact_readback/exec_result.json`
- `artifact_readback/request.sanitized.json`
- `artifact_readback/stdout.sanitized.txt`
- `artifact_readback/stderr.sanitized.txt`
- `artifact_readback/downloads/<output_folder>/...`
