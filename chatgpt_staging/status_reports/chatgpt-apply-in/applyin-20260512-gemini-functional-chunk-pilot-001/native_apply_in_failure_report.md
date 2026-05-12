# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: applyin-20260512-gemini-functional-chunk-pilot-001
- payload_path: chatgpt_staging/in/applyin-20260512-gemini-functional-chunk-pilot-001/payload.zip.b64
- expected_payload_shape: single chatgpt_staging/in/<request_id>/payload.zip.b64
- github_run_id: 25733830587
- github_ref: refs/heads/main
- github_sha: 99500b98e7af650e5789bbd6e6f21c3315da6cc5
- artifact_name: chatgpt-apply-in-failure-25733830587
- artifact_retention_days: 7
- report_created_utc: 2026-05-12T12:17:20Z

## Troubleshooting context

The apply-in workflow failed. This workflow only accepts one payload.zip.b64 file. Parts/chunks, chunk manifests, payload.zip.b64.parts, invalid base64, missing root apply_manifest.json, missing root files/, unsafe paths, stale hashes, create_only violations, delete policy violations, or workflow-change policy violations are hard failures.


## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, regenerate a single payload.zip.b64 with current hashes, then retry. Do not switch to parts/chunks.
