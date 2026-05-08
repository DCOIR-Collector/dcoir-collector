# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: apply-heartbeat-readback-docs-batch-004a
- payload_path: chatgpt_staging/in/apply-heartbeat-readback-docs-batch-004a/payload.zip.b64
- expected_payload_shape: single chatgpt_staging/in/<request_id>/payload.zip.b64
- github_run_id: 25542567551
- github_ref: refs/heads/main
- github_sha: 9ce16205cc2c011127a809f3b9818dc5d3a4fe71
- artifact_name: chatgpt-apply-in-failure-25542567551
- artifact_retention_days: 7
- report_created_utc: 2026-05-08T07:16:43Z

## Troubleshooting context

The apply-in workflow failed. This workflow only accepts one payload.zip.b64 file. Parts/chunks, chunk manifests, payload.zip.b64.parts, invalid base64, missing root apply_manifest.json, missing root files/, unsafe paths, stale hashes, create_only violations, delete policy violations, or workflow-change policy violations are hard failures.


## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, regenerate a single payload.zip.b64 with current hashes, then retry. Do not switch to parts/chunks.
