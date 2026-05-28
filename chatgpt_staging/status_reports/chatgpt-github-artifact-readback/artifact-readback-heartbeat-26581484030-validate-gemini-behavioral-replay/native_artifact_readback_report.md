# Native artifact readback report

## Result

- workflow: chatgpt-github-artifact-readback
- result: success
- phase: artifact-staged
- request_id: artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay
- request_path: chatgpt_staging/requests/github_artifact_readback/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay.json
- source_run_id: 26581484030
- artifact_name: validate-gemini-behavioral-replay-results
- artifact_id: 
- artifact_subpath: .
- out_dir: chatgpt_staging/out/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay
- github_run_id: 26597897521
- github_run_attempt: 1
- github_sha: 1ae5199a9b22a83466efbe7dee9b8a4b3e37492d
- github_ref: refs/heads/main
- report_created_utc: 2026-05-28T19:41:17Z

## Readback

- heartbeat_report: chatgpt_staging/status_reports/chatgpt-github-artifact-readback/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay/workflow_report.md
- progress_history: chatgpt_staging/status_reports/chatgpt-github-artifact-readback/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay/progress_history.jsonl
- latest_progress_marker: chatgpt_staging/status_reports/chatgpt-github-artifact-readback/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay/latest_progress_marker.json
- staged_manifest_json: chatgpt_staging/out/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay/artifact_manifest.json
- staged_manifest_md: chatgpt_staging/out/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay/artifact_manifest.md
- staged_files_root: chatgpt_staging/out/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay

## Cleanup guidance

After ChatGPT reads the needed files, create a cleanup marker for request id 'artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay' with cleanup_out_bundles=true and cleanup_status_reports=true.

## Next ChatGPT action

Read artifact_manifest.md and the staged files under chatgpt_staging/out/artifact-readback-heartbeat-26581484030-validate-gemini-behavioral-replay. Record evidence, then request cleanup when safe.
