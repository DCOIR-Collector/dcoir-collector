[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RequestPath,
    [string]$RepoRoot = (Get-Location).Path,
    [string]$OutputRoot = (Join-Path $env:TEMP 'dcoir_chatgpt_exec'),
    [string]$JsonResultPath = '',
    [string]$GithubEnvPath = $env:GITHUB_ENV,
    [string[]]$SecretEnvNames = @('DCOIR_AIRTABLE_TOKEN','DCOIR_AIRTABLE_BASE_ID','DCOIR_GITHUB_FG_TOKEN','DCOIR_GITHUB_CL_TOKEN','DCOIR_OPENAI_API_KEY','DCOIR_OPENAI_PROJECT_ID')
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$modulePath = Join-Path $RepoRoot 'operator_tools\github_desktop_lane\modules\Dcoir.ActionsExec\Dcoir.ActionsExec.psm1'
Import-Module $modulePath -Force

function Write-GithubEnvValue {
    param([string]$Name, [string]$Value)
    if ([string]::IsNullOrWhiteSpace($GithubEnvPath)) { return }
    "$Name=$Value" | Out-File -FilePath $GithubEnvPath -Encoding utf8 -Append
}

try {
    $result = Invoke-DcoirActionsExecRequest -RequestPath $RequestPath -RepoRoot $RepoRoot -OutputRoot $OutputRoot -SecretEnvNames $SecretEnvNames
    if ($JsonResultPath) { $result | ConvertTo-Json -Depth 8 | Out-File -FilePath $JsonResultPath -Encoding utf8 }
    Write-GithubEnvValue -Name 'DCOIR_EXEC_REQUEST_ID' -Value ([string]$result.request_id)
    Write-GithubEnvValue -Name 'DCOIR_EXEC_RESULT' -Value ([string]$result.result)
    Write-GithubEnvValue -Name 'DCOIR_EXEC_EXIT_CODE' -Value ([string]$result.exit_code)
    Write-GithubEnvValue -Name 'DCOIR_EXEC_ARTIFACT_DIR' -Value ([string]$result.artifact_dir)
    Write-GithubEnvValue -Name 'DCOIR_EXEC_ARTIFACT_NAME' -Value ([string]$result.artifact_name)
    Write-GithubEnvValue -Name 'DCOIR_EXEC_ARTIFACT_RETENTION_DAYS' -Value ([string]$result.artifact_retention_days)
    Write-GithubEnvValue -Name 'DCOIR_EXEC_REPORT_PATH' -Value ([string]$result.report_path)
    Write-GithubEnvValue -Name 'DCOIR_EXEC_CLEANUP_REQUEST_AFTER_RUN' -Value ([string]$result.cleanup_request_after_run)
    exit 0
}
catch {
    $safeId = 'harness-failure-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    try {
        if (Test-Path -LiteralPath $RequestPath -PathType Leaf) {
            $raw = Get-Content -LiteralPath $RequestPath -Raw -Encoding UTF8
            $json = $raw | ConvertFrom-Json
            if ($json.request_id) { $safeId = New-DcoirActionsExecSafeName -Value ([string]$json.request_id) }
        }
    } catch { }

    $artifactDir = Join-Path (Join-Path $OutputRoot $safeId) 'artifact'
    New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null
    $secretMap = Get-DcoirActionsExecSecretMap -SecretEnvNames $SecretEnvNames
    $errorText = ConvertTo-DcoirActionsExecSanitizedText -Text ($_ | Out-String) -SecretValuesByName $secretMap
    $errorText | Out-File -FilePath (Join-Path $artifactDir 'harness_error.sanitized.txt') -Encoding utf8

    $reportPath = Join-Path $RepoRoot (Join-Path 'chatgpt_staging/status_reports/chatgpt-exec' (Join-Path $safeId 'workflow_report.md'))
    Write-DcoirActionsExecReport -ReportPath $reportPath -RequestId $safeId -Result 'failure' -Shell 'unknown' -ExitCode 1 -TimedOut $false -CommandSha256 'unavailable' -ApprovedPreview 'Harness failed before approved command execution.' -CommandSanitized '' -ErrorText $errorText -ArtifactRetentionDays 3

    if ($JsonResultPath) {
        [ordered]@{
            schema = 'dcoir.chatgpt_staging.exec_result.v1'
            request_id = $safeId
            result = 'failure'
            exit_code = 1
            timed_out = $false
            artifact_dir = $artifactDir
            artifact_name = "chatgpt-exec-$safeId"
            artifact_retention_days = 3
            cleanup_request_after_run = $false
            report_path = $reportPath
        } | ConvertTo-Json -Depth 8 | Out-File -FilePath $JsonResultPath -Encoding utf8
    }
    Write-GithubEnvValue -Name 'DCOIR_EXEC_REQUEST_ID' -Value $safeId
    Write-GithubEnvValue -Name 'DCOIR_EXEC_RESULT' -Value 'failure'
    Write-GithubEnvValue -Name 'DCOIR_EXEC_EXIT_CODE' -Value '1'
    Write-GithubEnvValue -Name 'DCOIR_EXEC_ARTIFACT_DIR' -Value $artifactDir
    Write-GithubEnvValue -Name 'DCOIR_EXEC_ARTIFACT_NAME' -Value "chatgpt-exec-$safeId"
    Write-GithubEnvValue -Name 'DCOIR_EXEC_ARTIFACT_RETENTION_DAYS' -Value '3'
    Write-GithubEnvValue -Name 'DCOIR_EXEC_REPORT_PATH' -Value $reportPath
    Write-GithubEnvValue -Name 'DCOIR_EXEC_CLEANUP_REQUEST_AFTER_RUN' -Value 'false'
    exit 0
}
