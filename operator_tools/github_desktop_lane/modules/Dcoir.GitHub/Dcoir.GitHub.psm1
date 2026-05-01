Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:DcoirGitHubVersion = '2026-05-01.1'

$moduleRoot = Split-Path -Parent $PSScriptRoot
$commonPath = Join-Path $moduleRoot 'Dcoir.Common\Dcoir.Common.psd1'
if (-not (Test-Path -LiteralPath $commonPath -PathType Leaf)) { $commonPath = Join-Path $moduleRoot 'Dcoir.Common\Dcoir.Common.psm1' }
Import-Module -Name $commonPath -Force -ErrorAction Stop

function Invoke-DcoirGhText {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string[]]$GhArgs, [string]$DebugName = 'gh')
    $rawLines = & gh @GhArgs 2>&1
    $exit = $LASTEXITCODE
    $raw = ($rawLines | Out-String).Trim()
    $safeName = ($DebugName -replace '[^A-Za-z0-9_.-]', '_')
    $debugDir = [string](Get-DcoirContextValue -Name 'DebugDir' -Default '')
    if (-not [string]::IsNullOrWhiteSpace($debugDir)) {
        $debugPath = Join-Path $debugDir ($safeName + '.txt')
        Write-DcoirUtf8Text -Path $debugPath -Text ("gh {0}`nEXIT={1}`n`n{2}" -f ($GhArgs -join ' '), $exit, $raw)
    }
    if ($exit -ne 0) { throw ("gh command failed exit={0}: gh {1}`n{2}" -f $exit, ($GhArgs -join ' '), $raw) }
    return $raw
}

function Invoke-DcoirGhJson {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string[]]$GhArgs, [string]$DebugName = 'gh_json')
    $raw = Invoke-DcoirGhText -GhArgs $GhArgs -DebugName $DebugName
    if (-not ($raw.StartsWith('{') -or $raw.StartsWith('['))) { throw "Expected JSON from: gh $($GhArgs -join ' ')" }
    return ($raw | ConvertFrom-Json)
}

function Test-DcoirGhAvailable {
    [CmdletBinding()]
    param()
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "GitHub CLI 'gh' was not found in PATH." }
    try { Invoke-DcoirGhText -GhArgs @('auth','status') -DebugName 'gh_auth_status' | Out-Null }
    catch { throw "GitHub CLI auth status failed. Run 'gh auth login' or fix gh auth before using this tool. Details: $($_.Exception.Message)" }
}

function Get-DcoirWorkflowRuns {
    [CmdletBinding()]
    param([string]$WorkflowFile, [string]$Branch, [int]$PerPage = 10, [string]$Event)
    $repo = [string](Get-DcoirContextValue -Name 'Repo' -Default '')
    if ([string]::IsNullOrWhiteSpace($repo)) { throw 'DCOIR GitHub context value Repo is not set.' }
    $wfEsc = [System.Uri]::EscapeDataString($WorkflowFile)
    $endpoint = "repos/$repo/actions/workflows/$wfEsc/runs?per_page=$PerPage"
    if ($Branch) { $endpoint += '&branch=' + [System.Uri]::EscapeDataString($Branch) }
    if ($Event) { $endpoint += '&event=' + [System.Uri]::EscapeDataString($Event) }
    $json = Invoke-DcoirGhJson -GhArgs @('api', $endpoint) -DebugName ('runs_' + ($WorkflowFile -replace '[^A-Za-z0-9_.-]', '_'))
    return @($json.workflow_runs)
}

function Get-DcoirRunById {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][Int64]$Id)
    $repo = [string](Get-DcoirContextValue -Name 'Repo' -Default '')
    if ([string]::IsNullOrWhiteSpace($repo)) { throw 'DCOIR GitHub context value Repo is not set.' }
    return Invoke-DcoirGhJson -GhArgs @('api', "repos/$repo/actions/runs/$Id") -DebugName "run_$Id"
}

function Get-DcoirRunJobs {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][Int64]$Id)
    $repo = [string](Get-DcoirContextValue -Name 'Repo' -Default '')
    if ([string]::IsNullOrWhiteSpace($repo)) { throw 'DCOIR GitHub context value Repo is not set.' }
    $jobs = Invoke-DcoirGhJson -GhArgs @('api', "repos/$repo/actions/runs/$Id/jobs?per_page=100") -DebugName "jobs_$Id"
    return @($jobs.jobs)
}

Export-ModuleMember -Function Invoke-DcoirGhText,Invoke-DcoirGhJson,Test-DcoirGhAvailable,Get-DcoirWorkflowRuns,Get-DcoirRunById,Get-DcoirRunJobs
