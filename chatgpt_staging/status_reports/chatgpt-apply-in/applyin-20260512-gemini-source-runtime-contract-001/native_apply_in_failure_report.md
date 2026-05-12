# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: applyin-20260512-gemini-source-runtime-contract-001
- payload_path: chatgpt_staging/in/applyin-20260512-gemini-source-runtime-contract-001/payload.zip.b64
- expected_payload_shape: single chatgpt_staging/in/<request_id>/payload.zip.b64
- github_run_id: 25728798376
- github_ref: refs/heads/main
- github_sha: 19826ceea3ed60262bba96054979514b97862bd7
- artifact_name: chatgpt-apply-in-failure-25728798376
- artifact_retention_days: 7
- report_created_utc: 2026-05-12T10:31:21Z

## Troubleshooting context

The apply-in workflow failed. This workflow only accepts one payload.zip.b64 file. Parts/chunks, chunk manifests, payload.zip.b64.parts, invalid base64, missing root apply_manifest.json, missing root files/, unsafe paths, stale hashes, create_only violations, delete policy violations, or workflow-change policy violations are hard failures.


## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, regenerate a single payload.zip.b64 with current hashes, then retry. Do not switch to parts/chunks.
