# ChatGPT workflow report

## Result

- workflow: chatgpt-exec
- result: success
- phase: approved-command-execution
- request_id: exec-20260505-cleanup-plan-scaffold-seed-001
- shell: powershell_5
- exit_code: 0
- timed_out: False
- command_sha256: ab107eb6ebeba5864bd27f31bc143f60398138ff0a913e7fd1be8c6647b0dfb3
- artifact_name: chatgpt-exec-exec-20260505-cleanup-plan-scaffold-seed-001
- artifact_retention_days: 3
- started_utc: 2026-05-05T13:30:25Z
- finished_utc: 2026-05-05T13:30:38Z
- report_created_utc: 2026-05-05T13:30:40Z

## Approved command preview

```text
Run bounded Airtable evidence export for Plans, DCOIR Cleanup WBS, and DCOIR Cleanup Scaffold Registry. No cleanup execution.
```

## Executed command

```powershell
$ErrorActionPreference = 'Stop'
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$script = Join-Path $repo 'operator_tools\github_desktop_lane\scripts\New-DcoirAirtableDatabaseHealthExport.ps1'
& $script -ExportMode BoundedRecords -MaxRecordsPerTable 100 -MetadataScope 'All' -ProbeUnsupportedMetadata -TableList 'Plans,DCOIR Cleanup WBS,DCOIR Cleanup Scaffold Registry'
Write-Host 'DCOIR cleanup scaffold evidence export completed.'
```

## Standard output preview

```text
[2026-05-05 13:30:26] Starting DCOIR Airtable database health export.
[2026-05-05 13:30:26] Output folder: D:\a\_temp\dcoir_chatgpt_exec\exec-20260505-cleanup-plan-scaffold-seed-001\downloads\dcoir_airtable_health_export_20260505_133025
[2026-05-05 13:30:26] Output ZIP target: D:\a\_temp\dcoir_chatgpt_exec\exec-20260505-cleanup-plan-scaffold-seed-001\downloads\dcoir_airtable_health_export_20260505_133025.chatgpt.zip
[2026-05-05 13:30:26] Resolved export mode: BoundedRecords; effective max records per table: 100
[2026-05-05 13:30:26] Imported Dcoir.Airtable module version 2026-05-03.5.
[2026-05-05 13:30:26] Required Machine/System environment variables are present.
[2026-05-05 13:30:26] Fetching Airtable base schema.
[2026-05-05 13:30:29] Selected 3 Airtable table(s).
[2026-05-05 13:30:30] Exporting table schema: Plans (tblBcp5FyMIfOm7Xe)
[2026-05-05 13:30:30] Exporting records: Plans
[2026-05-05 13:30:30] Exporting table schema: DCOIR Cleanup WBS (tblRxTmpW0VunQlUK)
[2026-05-05 13:30:30] Exporting records: DCOIR Cleanup WBS
[2026-05-05 13:30:30] Exporting table schema: DCOIR Cleanup Scaffold Registry (tblvtcId7PiFKvfKO)
[2026-05-05 13:30:30] Exporting records: DCOIR Cleanup Scaffold Registry
[2026-05-05 13:30:31] Airtable export completed successfully.
{
    "success":  true,
    "output_folder":  "D:\\a\\_temp\\dcoir_chatgpt_exec\\exec-20260505-cleanup-plan-scaffold-seed-001\\downloads\\dcoir_airtable_health_export_20260505_133025",
    "output_zip":  "D:\\a\\_temp\\dcoir_chatgpt_exec\\exec-20260505-cleanup-plan-scaffold-seed-001\\downloads\\dcoir_airtable_health_export_20260505_133025.chatgpt.zip",
    "schema_only":  false,
    "export_mode":  "BoundedRecords",
    "full_record_dump":  false,
    "redacted_likely_secrets":  false,
    "selected_table_count":  3,
    "max_records_per_table":  100,
    "finished_at":  "2026-05-05T13:30:31.0097185+00:00"
}
DCOIR cleanup scaffold evidence export completed.

```

## Standard error preview

```text

```

## Artifact guidance

Artifact chatgpt-exec-exec-20260505-cleanup-plan-scaffold-seed-001 contains sanitized stdout/stderr, sanitized request, sanitized command, exec_result.json, and any files written under DCOIR_DOWNLOADS_DIR.

## Cleanup guidance

The request file is removed automatically when cleanup_request_after_run=true. This status report can be cleaned later with cleanup_status_reports=true after ChatGPT records evidence. GitHub Actions artifacts expire by configured retention.

## Next ChatGPT action

Read this report and download the artifact if needed; record evidence and clean the status report when safe.

## GitHub Actions run

- github_run_id: 25379385958
- github_run_attempt: 1
- github_sha: 6c6cf6c729b02e174e42551e4f07612e55b9302e
- github_ref: refs/heads/main
- workflow_run_url: https://github.com/malwaredevil/dcoir-collector/actions/runs/25379385958
