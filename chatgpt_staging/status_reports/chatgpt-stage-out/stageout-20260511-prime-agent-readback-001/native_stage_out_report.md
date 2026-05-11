# ChatGPT workflow report

## Result

- workflow: chatgpt-stage-out
- result: success
- phase: bundle-created
- request_id: stageout-20260511-prime-agent-readback-001
- request_path: chatgpt_staging/requests/stageout-20260511-prime-agent-readback-001.json
- output_dir: chatgpt_staging/out/stageout-20260511-prime-agent-readback-001
- github_run_id: 25667515870
- github_sha: 0b37e130490ec68ef8bf21513bc93b57c94a0fe1
- github_ref: refs/heads/main
- report_created_utc: 2026-05-11T11:32:20Z

## Output

- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk001.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk002.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk003.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk004.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk005.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk006.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk007.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk008.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/chunks/001__Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt__chunk009.txt
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/manifest.json
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/manifest.md
- chatgpt_staging/out/stageout-20260511-prime-agent-readback-001/staged_files.zip

## Cleanup guidance

After ChatGPT retrieves the needed output, create a cleanup marker for request id 'stageout-20260511-prime-agent-readback-001' with cleanup_out_bundles=true and cleanup_status_reports=true.

## Next ChatGPT action

Read manifest.md/manifest.json and staged_files.zip or chunks under chatgpt_staging/out/stageout-20260511-prime-agent-readback-001. Record evidence, then request cleanup when safe.
