# ChatGPT workflow report

## Result

- workflow: chatgpt-apply-in
- result: failure
- phase: apply-in
- request_id: applyin-20260511-gemini-usb-subagent-clean-001
- payload_path: chatgpt_staging/in/applyin-20260511-gemini-usb-subagent-clean-001/payload.zip.b64
- expected_payload_shape: single chatgpt_staging/in/<request_id>/payload.zip.b64
- github_run_id: 25669053203
- github_ref: refs/heads/main
- github_sha: 840f7dcce15b1bf78b22a854bc7be8cbfca0575a
- artifact_name: chatgpt-apply-in-failure-25669053203
- artifact_retention_days: 7
- report_created_utc: 2026-05-11T12:06:00Z

## Troubleshooting context

The apply-in workflow failed. This workflow only accepts one payload.zip.b64 file. Parts/chunks, chunk manifests, payload.zip.b64.parts, invalid base64, missing root apply_manifest.json, missing root files/, unsafe paths, stale hashes, create_only violations, delete policy violations, or workflow-change policy violations are hard failures.

### Manifest excerpt

```json
{
  "schema": "dcoir.chatgpt_staging.apply_manifest.v1",
  "request_id": "applyin-20260511-gemini-usb-subagent-clean-001",
  "allowed_roots": [
    "project_sources/gemini/bundle_source",
    "project_sources/gemini/docs",
    "project_sources/gemini/tools",
    "knowledge",
    ".github/workflows"
  ],
  "files": [
    {
      "path": "project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Sub_Agent_11_USB_Violations_Report_Composer.md.txt",
      "source": "files/project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Sub_Agent_11_USB_Violations_Report_Composer.md.txt",
      "expected_new_sha256": "9e550c71b14e63e103f3c470db779636cd6c4aae31f7c1461f480f7d6749aa7c",
      "create_only": true
    },
    {
      "path": "project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json",
      "source": "files/project_sources/gemini/bundle_source/Gemini_Bundle_Source_Manifest.json",
      "expected_new_sha256": "7202d6faa4485da0acffe20386d471bc5ff0eb6b44c41483da019d9e1e5064a3",
      "expected_current_sha256": "8c4f18e3f2e4aae7eb460db6b33284edc90842f8af55e236bae0b5b1c050cc35"
    },
    {
      "path": "project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Generated_DCOIR_Gemini_Agent_Index.md.txt",
      "source": "files/project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Generated_DCOIR_Gemini_Agent_Index.md.txt",
      "expected_new_sha256": "ef54c218c8221e2f8025e220c7536611cbe4f1218dd0a1b1b86f9c69569c236a",
      "expected_current_sha256": "4440166a63924367e50f611f039d8ccc2e1d0c9610908b1d6c8bbabe9fb93cab"
    },
    {
      "path": "project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt",
      "source": "files/project_sources/gemini/bundle_source/01_GEMINI_AGENT_BUILD/Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt",
      "expected_new_sha256": "39c937f1814fb670fe1e4b0b476e81a8be3c860c16d12b8372d30b5e08b1c9ff",
      "expected_current_sha256": "e081334764d9f46ef8b85cd63d738fd665b4fc0de778ae655b57506bf92aebf8"
    },
    {
      "path": "project_sources/gemini/bundle_source/00_START_HERE/Gemini_Build_Quick_Start.md.txt",
      "source": "files/project_sources/gemini/bundle_source/00_START_HERE/Gemini_Build_Quick_Start.md.txt",
      "expected_new_sha256": "b1587216e3eb87b5134ebc4c482fd127c38b5b589264167d6acbae2507b55fd2",
      "expected_current_sha256": "f470f0206c08e312b193dbfeff6fc2b7c4e41bdbcba00fa65aa9d55a178859a1"
    },
    {
      "path": "project_sources/gemini/bundle_source/00_START_HERE/Agent_Attachment_Map.md.txt",
      "source": "files/project_sources/gemini/bundle_source/00_START_HERE/Agent_Attachment_Map.md.txt",
      "expected_new_sha256": "fa54aad41b7da67148f4d4a1ad165f15961bea3b923878e4d4170d0d3b6d78ea",
      "expected_current_sha256": "a96435437a78cc9645288f8f3c95cea100c8696e4098eb414c0bc3f76c582c8b"
    },
    {
      "path": "knowledge/Knowledge - 13 - Gemini Agent Topology and Routing.md",
      "source": "files/knowledge/Knowledge - 13 - Gemini Agent Topology and Routing.md",
      "expected_new_sha256": "c13acfc67f1f368c299974e4c0b1d518a817d13dcae8199cda6065a6d326e78c",
      "expected_current_sha256": "e5ffbb1a08942064a8c04c65962d4e442ea68a5c6c61d256d2b15dc46ecfb9d2"
    },
    {
      "path": "knowledge/Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance.md",
      "source": "files/knowledge/Knowledge - 15 - Gemini Attachment Set, Validation, and Maintenance.md",
      "expected_new_sha256": "c40c5a6edd919e2bc578cea7e74d4c4d615c63cfc0f08673c75753c71b16a199",
      "expected_current_sha256": "a837003576dc6f71e668604006b47636b0802ca97de7423b7864092d32ff6e92"
    },
    {
      "path": "project_sources/gemini/docs/DOC-11_DCOIR_Gemini_Creation_Pipeline_v1_0_0.txt",
      "source": "files/project_sources/gemini/docs/DOC-11_DCOIR_Gemini_Creation_Pipeline_v1_0_0.txt",
      "expected_new_sha256": "dff7c52f404a7a7ef65d34225b07c72a8e0a15432118b9edce318b56834a11a5",
      "expected_current_sha256": "51fc4b26427ba6606de
```

## Next ChatGPT action

Read this report, inspect the artifact or run log if needed, regenerate a single payload.zip.b64 with current hashes, then retry. Do not switch to parts/chunks.
