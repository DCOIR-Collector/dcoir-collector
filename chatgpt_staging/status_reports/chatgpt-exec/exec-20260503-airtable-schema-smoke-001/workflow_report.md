# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- result: success
- phase: approved-command-execution
- request_id: exec-20260503-airtable-schema-smoke-001
- shell: powershell_5
- exit_code: 0
- timed_out: False
- command_sha256: ceb31db1afd1af7c1bcbc8b8516c9dce4e18b7ebf3ee12049edc676aa6cd1a3f
- artifact_name: chatgpt-exec-exec-20260503-airtable-schema-smoke-001
- artifact_retention_days: 3
- started_utc: 2026-05-03T18:24:22Z
- finished_utc: 2026-05-03T18:24:24Z
- report_created_utc: 2026-05-03T18:24:25Z

## Approved command preview

```text
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -ExportMode SchemaOnly -ProbeUnsupportedMetadata
```

## Executed command

```powershell
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -ExportMode SchemaOnly -ProbeUnsupportedMetadata
```

## Standard output preview

```text
[2026-05-03 18:24:23] Starting DCOIR Airtable database health export.
[2026-05-03 18:24:23] Output folder: D:\a\_temp\dcoir_chatgpt_exec\exec-20260503-airtable-schema-smoke-001\downloads\dcoir_airtable_health_export_20260503_182423
[2026-05-03 18:24:23] Output ZIP target: D:\a\_temp\dcoir_chatgpt_exec\exec-20260503-airtable-schema-smoke-001\downloads\dcoir_airtable_health_export_20260503_182423.chatgpt.zip
[2026-05-03 18:24:23] Resolved export mode: SchemaOnly; effective max records per table: 0
[2026-05-03 18:24:23] Imported Dcoir.Airtable module version 2026-05-03.5.
[2026-05-03 18:24:23] Required Machine/System environment variables are present.
[2026-05-03 18:24:23] Fetching Airtable base schema.
[2026-05-03 18:24:23] Selected 24 Airtable table(s).
[2026-05-03 18:24:24] Exporting table schema: Work Items (tblgsQAVWvh8K7gIR)
[2026-05-03 18:24:24] Exporting table schema: Session Checkpoints (tblTe75HKZOJaPDGn)
[2026-05-03 18:24:24] Exporting table schema: Idea Inbox (tblWwBxwrjZF6JR3r)
[2026-05-03 18:24:24] Exporting table schema: Plans (tblBcp5FyMIfOm7Xe)
[2026-05-03 18:24:24] Exporting table schema: Operator Preferences (tblnxZ3eLPT3W38wl)
[2026-05-03 18:24:24] Exporting table schema: Validation Test Cases (tblRnMpQUomIGyFVL)
[2026-05-03 18:24:24] Exporting table schema: Queue Control (tblf13aCslg6rJBah)
[2026-05-03 18:24:24] Exporting table schema: Gemini Research Reference (tblfZnARJxcMJ0yHW)
[2026-05-03 18:24:24] Exporting table schema: Governance Control Plane (tblDfSl29psxRnes1)
[2026-05-03 18:24:24] Exporting table schema: Repo Surface Registry (tblzBiXp7kwTXM0ru)
[2026-05-03 18:24:24] Exporting table schema: dcoir-memory-preflight (tblcNNuKqi8IkFsSQ)
[2026-05-03 18:24:24] Exporting table schema: dcoir-decision-policy (tblKHVXq16Xd5I31m)
[2026-05-03 18:24:24] Exporting table schema: dcoir-collector-qa (tblwbMhMjQ7gzwj0C)
[2026-05-03 18:24:24] Exporting table schema: dcoir-validation-orchestrator (tbls9O1B0Rs8YvTAj)
[2026-05-03 18:24:24] Exporting table schema: dcoir-skill-regression-auditor (tblHAa3e4R6F4LFhb)
[2026-05-03 18:24:24] Exporting table schema: dcoir-live-test-remediation-planner (tbltsNeLytMKgmJft)
[2026-05-03 18:24:24] Exporting table schema: dcoir-readme-maintainer (tblzaBfC7EUCrVRUe)
[2026-05-03 18:24:24] Exporting table schema: dcoir-source-authority-auditor (tblggXJoCuDK6cHg5)
[2026-05-03 18:24:24] Exporting table schema: Delete Queue (tbl1lMz5N6n7zShO0)
[2026-05-03 18:24:24] Exporting table schema: Validation Evidence (tblrPFQH2uZEYBYE9)
[2026-05-03 18:24:24] Exporting table schema: Admin Registry (tblFaJW1V2DPc9css)
[2026-05-03 18:24:24] Exporting table schema: DCOIR Lifecycle Ledger (tblNsjkGUUIdRpHuE)
[2026-05-03 18:24:24] Exporting table schema: Local Configuration Registry (tblcJxCoYGpEda0FM)
[2026-05-03 18:24:24] Exporting table schema: Operator Tools Registry (tblF1SCJBHRFUhpzi)
[2026-05-03 18:24:24] Airtable export completed successfully.
[2026-05-03 18:24:24] ZIP creation failed: The term 'Get-FileHash' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
{
    "success":  true,
    "output_folder":  "D:\\a\\_temp\\dcoir_chatgpt_exec\\exec-20260503-airtable-schema-smoke-001\\downloads\\dcoir_airtable_health_export_20260503_182423",
    "output_zip":  null,
    "schema_only":  true,
    "export_mode":  "SchemaOnly",
    "full_record_dump":  false,
    "redacted_likely_secrets":  false,
    "selected_table_count":  24,
    "max_records_per_table":  0,
    "finished_at":  "2026-05-03T18:24:24.4906954+00:00"
}

```

## Standard error preview

```text

```

## Artifact guidance

Artifact chatgpt-exec-exec-20260503-airtable-schema-smoke-001 contains sanitized stdout/stderr, sanitized request, sanitized command, exec_result.json, and any files written under DCOIR_DOWNLOADS_DIR.

## Cleanup guidance

The request file is removed automatically when cleanup_request_after_run=true. This status report can be cleaned later with cleanup_status_reports=true after ChatGPT records evidence. GitHub Actions artifacts expire by configured retention.

## Next ChatGPT action

Read this report and download the artifact if needed; record evidence and clean the status report when safe.
