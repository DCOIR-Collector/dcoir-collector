# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: apply-heartbeat-readback-docs-002
- payload_path: chatgpt_staging/in/apply-heartbeat-readback-docs-002/payload.zip.b64
- expected_payload_shape: single chatgpt_staging/in/<request_id>/payload.zip.b64
- github_run_id: 25541944751
- github_ref: refs/heads/main
- github_sha: 284937f53cadea2a8eb4e7380294f803c35032ea
- artifact_name: chatgpt-apply-in-failure-25541944751
- artifact_retention_days: 7
- report_created_utc: 2026-05-08T07:00:50Z

## Troubleshooting context

The apply-in workflow failed. This workflow only accepts one payload.zip.b64 file. Parts/chunks, chunk manifests, payload.zip.b64.parts, invalid base64, missing root apply_manifest.json, missing root files/, unsafe paths, stale hashes, create_only violations, delete policy violations, or workflow-change policy violations are hard failures.

### Manifest excerpt

```json
{
  "schema": "dcoir.chatgpt_staging.apply_manifest.v1",
  "request_id": "apply-heartbeat-readback-docs-002",
  "allowed_roots": [
    "chatgpt_staging"
  ],
  "files": [
    {
      "path": "chatgpt_staging/HEARTBEAT_AND_ARTIFACT_READBACK.md",
      "source": "files/chatgpt_staging/HEARTBEAT_AND_ARTIFACT_READBACK.md",
      "expected_blob_sha": "46c5a644f22e3d675bcb2945e25b6cbb7af8a4e6",
      "expected_new_sha256": "ca38731680a9890a7399078d8067c267b7c4bfe0582b92a3e6d70a3e03d5c26a"
    },
    {
      "path": "chatgpt_staging/docs/README.md",
      "source": "files/chatgpt_staging/docs/README.md",
      "expected_blob_sha": "0c06af443dda3dfaadebaaea2cad0b7d5c0c6b56",
      "expected_new_sha256": "87298190e896753dfdb1cdb3a359e6987e94baa048d8f94570f43680eb6cc8c8"
    },
    {
      "path": "chatgpt_staging/docs/exec_request_readback.md",
      "source": "files/chatgpt_staging/docs/exec_request_readback.md",
      "expected_blob_sha": "a77779dc5e98245bbf42db545f92967f09bf90e9",
      "expected_new_sha256": "6738bb14ee83835a185b9b5c96e3854b32eac0ad712f04f2bcf307116d8441f2"
    },
    {
      "path": "chatgpt_staging/docs/apply_in_readback.md",
      "source": "files/chatgpt_staging/docs/apply_in_readback.md",
      "expected_blob_sha": "dc7bca32092d5a1c121c7b56a48bbfb8ffbe307e",
      "expected_new_sha256": "7645559cd194fd88deed7d70bc7005747de93f3818b3f402d6ffe60ddf3063bb"
    },
    {
      "path": "chatgpt_staging/docs/stage_out_readback.md",
      "source": "files/chatgpt_staging/docs/stage_out_readback.md",
      "expected_blob_sha": "196b3433f877c5774f8a6e8df1c3f6cb3ad59230",
      "expected_new_sha256": "a62a1d66de5c95b54716cd260cfd60a5bfe73586d3b6694cf03355c293f9bbc9"
    }
  ]
}
```

## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, regenerate a single payload.zip.b64 with current hashes, then retry. Do not switch to parts/chunks.
