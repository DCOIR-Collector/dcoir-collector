# ChatGPT workflow report

## Result

- workflow: chatgpt-github-artifact-readback
- result: success
- phase: artifact-staged
- request_id: rtifact-readback-26581484030-validate-gemini-behavioral-replay
- request_path: '(direct dispatch inputs)'
- source_run_id: 26581484030
- artifact_name: validate-gemini-behavioral-replay-results
- artifact_id: 
- artifact_subpath: 
- out_dir: chatgpt_staging/out/rtifact-readback-26581484030-validate-gemini-behavioral-replay
- github_run_id: 26596714848
- github_run_attempt: 1
- github_sha: 41b21cc67f3b5ab7724b329a3875ac0bc7981186
- github_ref: refs/heads/main
- report_created_utc: 2026-05-28T19:18:01Z

## Readback

- staged_manifest_json: chatgpt_staging/out/rtifact-readback-26581484030-validate-gemini-behavioral-replay/artifact_manifest.json
- staged_manifest_md: chatgpt_staging/out/rtifact-readback-26581484030-validate-gemini-behavioral-replay/artifact_manifest.md
- staged_files_root: chatgpt_staging/out/rtifact-readback-26581484030-validate-gemini-behavioral-replay

## Cleanup guidance

After ChatGPT reads the needed files, create a cleanup marker for request id 'rtifact-readback-26581484030-validate-gemini-behavioral-replay' with cleanup_out_bundles=true and cleanup_status_reports=true.

## Next ChatGPT action

Read artifact_manifest.md and the staged files under chatgpt_staging/out/rtifact-readback-26581484030-validate-gemini-behavioral-replay. Record evidence, then request cleanup when safe.
