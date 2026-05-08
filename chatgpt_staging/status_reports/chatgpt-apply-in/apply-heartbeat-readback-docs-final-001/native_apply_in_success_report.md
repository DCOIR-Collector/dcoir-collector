# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: success
- phase: bundle-applied-before-commit
- request_id: apply-heartbeat-readback-docs-final-001
- payload_path: chatgpt_staging/in/apply-heartbeat-readback-docs-final-001/payload.zip.b64
- payload_shape: single payload.zip.b64
- github_run_id: 25542991912
- github_sha: eb51e0abafb68ca053966aaae42dd4859ad4e924
- github_ref: refs/heads/main
- report_created_utc: 2026-05-08T07:27:27Z

## Applied paths
- chatgpt_staging/docs/README.md
- chatgpt_staging/docs/workflow_status_output_quickstart.md
- chatgpt_staging/docs/exec_request_readback.md
- chatgpt_staging/docs/apply_in_readback.md
- chatgpt_staging/docs/stage_out_readback.md
- chatgpt_staging/docs/workflow_lanes_index.md
- chatgpt_staging/docs/apply_in_payload_generation.md
- chatgpt_staging/in/README.md
- chatgpt_staging/exec_requests/README.md
- chatgpt_staging/requests/README.md
- operator_tools/github_desktop_lane/docs/CHATGPT_HEARTBEAT_READBACK.md
- operator_tools/github_desktop_lane/docs/CHATGPT_EXEC_READBACK_CONTRACT.md

## Deleted paths
- none

## Cleanup guidance

After ChatGPT verifies the commit/readback and no longer needs this report, create a cleanup marker for request id 'apply-heartbeat-readback-docs-final-001' with cleanup_status_reports=true.

## Next ChatGPT action

Verify the committed target changes, hash policy outcome, deletion outcome, and apply report. If readback is good, update Airtable and clean this status report when safe.
