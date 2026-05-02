# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- result: success
- phase: bundle-created
- request_id: val-20260502-stageout-docs-001
- request_path: chatgpt_staging/requests/val-20260502-stageout-docs-001.json
- output_dir: chatgpt_staging/out/val-20260502-stageout-docs-001
- github_run_id: 25258921946
- github_sha: c657e3ed81b8aa0792419872c223b8a340e3b2e1
- github_ref: refs/heads/main
- report_created_utc: 2026-05-02T18:33:41Z

## Output

- chatgpt_staging/out/val-20260502-stageout-docs-001/chunks/001__README.md__chunk001.txt
- chatgpt_staging/out/val-20260502-stageout-docs-001/chunks/001__README.md__chunk002.txt
- chatgpt_staging/out/val-20260502-stageout-docs-001/chunks/002__RETENTION_POLICY.md__chunk001.txt
- chatgpt_staging/out/val-20260502-stageout-docs-001/chunks/003__SCENARIO_MATRIX.md__chunk001.txt
- chatgpt_staging/out/val-20260502-stageout-docs-001/files/chatgpt_staging/README.md
- chatgpt_staging/out/val-20260502-stageout-docs-001/files/chatgpt_staging/RETENTION_POLICY.md
- chatgpt_staging/out/val-20260502-stageout-docs-001/files/chatgpt_staging/SCENARIO_MATRIX.md
- chatgpt_staging/out/val-20260502-stageout-docs-001/manifest.json
- chatgpt_staging/out/val-20260502-stageout-docs-001/manifest.md
- chatgpt_staging/out/val-20260502-stageout-docs-001/staged_files.zip

## Cleanup guidance

After ChatGPT retrieves the needed output, create a cleanup marker for request id 'val-20260502-stageout-docs-001' with cleanup_out_bundles=true and cleanup_status_reports=true.

## Next ChatGPT action

Read manifest.md/manifest.json and staged_files.zip or chunks under chatgpt_staging/out/val-20260502-stageout-docs-001. Record evidence, then request cleanup when safe.
