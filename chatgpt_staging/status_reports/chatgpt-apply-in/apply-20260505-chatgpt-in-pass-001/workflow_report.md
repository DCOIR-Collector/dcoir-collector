# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: success
- phase: bundle-applied-before-commit
- request_id: apply-20260505-chatgpt-in-pass-001
- payload_path: chatgpt_staging/in/apply-20260505-chatgpt-in-pass-001/payload.zip.b64
- payload_shape: single payload.zip.b64
- github_run_id: 25373942145
- github_sha: 66948603c3d83e5c33bd597146d141aa5d3d8f13
- github_ref: refs/heads/main
- report_created_utc: 2026-05-05T11:34:53Z

## Applied paths
- chatgpt_staging/self_tests/chatgpt_apply_in_pass_20260505.txt

## Deleted paths
- none

## Cleanup guidance

After ChatGPT verifies the commit/readback and no longer needs this report, create a cleanup marker for request id 'apply-20260505-chatgpt-in-pass-001' with cleanup_status_reports=true.

## Next ChatGPT action

Verify the committed target changes, hash policy outcome, deletion outcome, and apply report. If readback is good, update Airtable and clean this status report when safe.
