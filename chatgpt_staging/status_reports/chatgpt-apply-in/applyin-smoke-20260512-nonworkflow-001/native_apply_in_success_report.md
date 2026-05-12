# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: success
- phase: bundle-applied-before-commit
- request_id: applyin-smoke-20260512-nonworkflow-001
- payload_path: chatgpt_staging/in/applyin-smoke-20260512-nonworkflow-001/payload.zip.b64
- payload_shape: single payload.zip.b64
- github_run_id: 25723319802
- github_sha: 4316177afbf292e1fc3c564637edd973550f9d87
- github_ref: refs/heads/main
- report_created_utc: 2026-05-12T08:39:00Z

## Applied paths
- chatgpt_staging/in/apply-in-smoke-20260512/marker.txt

## Deleted paths
- none

## Cleanup guidance

After ChatGPT verifies the commit/readback and no longer needs this report, create a cleanup marker for request id 'applyin-smoke-20260512-nonworkflow-001' with cleanup_status_reports=true.

## Next ChatGPT action

Verify the committed target changes, hash policy outcome, deletion outcome, and apply report. If readback is good, update Airtable and clean this status report when safe.
