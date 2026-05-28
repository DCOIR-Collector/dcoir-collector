# ChatGPT workflow report

## Result

- workflow: manual-github-artifact-readback
- result: success
- phase: artifact-staged
- request_id: artifact-readback-26574890838-manual-gemini-model-comparison
- source_run_id: 26574890838
- artifact_name: manual-gemini-model-comparison
- artifact_id: 
- artifact_subpath: 
- out_dir: chatgpt_staging/out/artifact-readback-26574890838-manual-gemini-model-comparison
- github_run_id: 26578386986
- github_run_attempt: 1
- github_sha: 1cc461f819073dfd1fcabbdf11913154d5345aa0
- github_ref: refs/heads/main
- report_created_utc: 2026-05-28T13:42:09Z

## Readback

- staged_manifest_json: chatgpt_staging/out/artifact-readback-26574890838-manual-gemini-model-comparison/artifact_manifest.json
- staged_manifest_md: chatgpt_staging/out/artifact-readback-26574890838-manual-gemini-model-comparison/artifact_manifest.md
- staged_files_root: chatgpt_staging/out/artifact-readback-26574890838-manual-gemini-model-comparison

## Cleanup guidance

After ChatGPT reads the needed files, create a cleanup marker for request id 'artifact-readback-26574890838-manual-gemini-model-comparison' with cleanup_out_bundles=true and cleanup_status_reports=true.

## Next ChatGPT action

Read artifact_manifest.md and the staged files under chatgpt_staging/out/artifact-readback-26574890838-manual-gemini-model-comparison. Record evidence, then request cleanup when safe.
