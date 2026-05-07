# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: success
- phase: bundle-applied-before-commit
- request_id: applyin-20260507-final-heartbeat-smoke-001
- payload_path: chatgpt_staging/in/applyin-20260507-final-heartbeat-smoke-001/payload.zip.b64
- payload_shape: single payload.zip.b64
- github_run_id: 25508569638
- github_sha: bf4d5f58510c4eb313d99bc2cd3ccd2bb7d85a88
- github_ref: refs/heads/main
- report_created_utc: 2026-05-07T16:27:24Z

## Applied paths
- docs/heartbeat_regression/applyin-20260507-final-heartbeat-smoke-001.txt

## Deleted paths
- none

## Cleanup guidance

After ChatGPT verifies the commit/readback and no longer needs this report, create a cleanup marker for request id 'applyin-20260507-final-heartbeat-smoke-001' with cleanup_status_reports=true.

## Next ChatGPT action

Verify the committed target changes, hash policy outcome, deletion outcome, and apply report. If readback is good, update Airtable and clean this status report when safe.
