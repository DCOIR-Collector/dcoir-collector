# ChatGPT workflow report

## Result

- workflow: chatgpt-github-artifact-readback
- result: success
- phase: artifact-staged
- request_id: artifact-readback-staging-26581484030-validate-gemini-behavioral-replay
- request_path: chatgpt_staging/requests/github_artifact_readback/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay.json
- source_run_id: 26581484030
- artifact_name: validate-gemini-behavioral-replay-results
- artifact_id: 
- artifact_subpath: 
- out_dir: chatgpt_staging/out/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay
- github_run_id: 26597220164
- github_run_attempt: 1
- github_sha: 09419342e99d3e88c8ff7fd214da718eb4987664
- github_ref: refs/heads/main
- report_created_utc: 2026-05-28T19:28:00Z

## Readback

- staged_manifest_json: chatgpt_staging/out/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay/artifact_manifest.json
- staged_manifest_md: chatgpt_staging/out/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay/artifact_manifest.md
- staged_files_root: chatgpt_staging/out/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay

## Cleanup guidance

After ChatGPT reads the needed files, create a cleanup marker for request id 'artifact-readback-staging-26581484030-validate-gemini-behavioral-replay' with cleanup_out_bundles=true and cleanup_status_reports=true.

## Next ChatGPT action

Read artifact_manifest.md and the staged files under chatgpt_staging/out/artifact-readback-staging-26581484030-validate-gemini-behavioral-replay. Record evidence, then request cleanup when safe.
