<#
DCOIR GitHub Actions Workflow Orchestrator.

Purpose:
  Watch, capture, or dispatch 1..N GitHub Actions workflow runs from a manifest.

Terminology:
  - workflow: YAML definition under .github/workflows/
  - workflow run: one execution of a workflow
  - job: an execution unit inside a workflow run

Safety defaults:
  - Manifest dry_run defaults to true.
  - Dispatch requires -ConfirmDispatch unless manifest require_dispatch_confirmation is false.
  - max_parallel throttles local dispatching; GitHub runner availability and workflow concurrency settings still control real execution order.
  - Outputs are evidence-only and can be packaged via New-DcoirChatGPTFriendlyZip.ps1 when present.

Environment contract:
  - DCOIR_REPO_ROOT and DCOIR_DOWNLOADS_DIR are read from Machine/System environment scope.
  - Process-scoped placeholder values such as C:\path\to\dcoir-collector are ignored and rejected.
#>
[CmdletBinding()]
param(
    [ValidateSet('manifest','watch','dispatch','capture')]
    [string]$Mode = 'manifest',
    [string]$ManifestJson,
    [string]$Repo = 'malwaredevil/dcoir-collector',
    [string]$Ref = 'main',
    [string[]]$Workflow,
    [Int64[]]$RunId,
    [int]$Limit = 5,
    [int]$PollSeconds = 30,
    [int]$TimeoutMinutes = 60,
    [int]$MaxParallel = 1,
    [switch]$DownloadArtifacts,
    [switch]$CreateUploadZip,
    [switch]$ConfirmDispatch,
    [switch]$DryRun,
    [string]$OutputBase
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$Script:ToolVersion = '2026-05-01.2'

function Test-DcoirPlaceholderPath {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
    $v = $Value.Trim()
    if ($v -match '^[A-Za-z]:\\path\\to(\\|$)') { return $true }
    if ($v -match '^/path/to(/|$)') { return $true }
    if ($v -match 'your[_ -]?folder[_ -]?name[_ -]?here') { return $true }
    if ($v -match 'your[_ -]?repo') { return $true }
    return $false
}

function Get-DcoirSystemEnvValue {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [switch]$Required,
        [AllowNull()][string]$Default
    )
    $machine = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    if (Test-DcoirPlaceholderPath -Value $machine) {
        throw "$Name is set to a placeholder path in Machine/System environment scope: $machine"
    }
    if (-not [string]::IsNullOrWhiteSpace($machine)) { return $machine.Trim() }
    if (-not [string]::IsNullOrWhiteSpace($Default)) { return $Default }
    if ($Required) { throw "$Name is not set in Machine/System environment scope. Set it as a System environment variable, then open a new terminal." }
    return $null
}

function Resolve-DcoirPathText {
    param([AllowNull()][string]$Text)
    if ($null -eq $Text) { return $null }
    $repoRoot = Get-DcoirSystemEnvValue -Name 'DCOIR_REPO_ROOT' -Required
    $downloads = Get-DcoirSystemEnvValue -Name 'DCOIR_DOWNLOADS_DIR' -Required
    $expanded = $Text
    $expanded = $expanded.Replace('%DCOIR_REPO_ROOT%', $repoRoot)
    $expanded = $expanded.Replace('%DCOIR_DOWNLOADS_DIR%', $downloads)
    $expanded = $expanded.Replace('%USERPROFILE%', [string]$env:USERPROFILE)
    return [Environment]::ExpandEnvironmentVariables($expanded)
}

function ConvertTo-DcoirHashtable {
    param($InputObject)
    if ($null -eq $InputObject) { return $null }
    if ($InputObject -is [System.Collections.IDictionary]) {
        $h = @{}
        foreach ($k in $InputObject.Keys) { $h[$k] = ConvertTo-DcoirHashtable $InputObject[$k] }
        return $h
    }
    if ($InputObject -is [pscustomobject]) {
        $h = @{}
        foreach ($p in $InputObject.PSObject.Properties) { $h[$p.Name] = ConvertTo-DcoirHashtable $p.Value }
        return $h
    }
    if ($InputObject -is [System.Collections.IEnumerable] -and -not ($InputObject -is [string])) {
        $arr = @()
        foreach ($item in $InputObject) { $arr += ,(ConvertTo-DcoirHashtable $item) }
        return $arr
    }
    return $InputObject
}

function Get-DcoirConfigValue {
    param($Map, [string]$Name, $Default = $null)
    if ($null -eq $Map) { return $Default }
    if ($Map.ContainsKey($Name)) { return $Map[$Name] }
    return $Default
}

function Write-DcoirUtf8Text {
    param([Parameter(Mandatory=$true)][string]$Path, [AllowNull()][string]$Text)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, [string]$Text, $enc)
}

function Add-DcoirUtf8Line {
    param([Parameter(Mandatory=$true)][string]$Path, [AllowNull()][string]$Text)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::AppendAllText($Path, ([string]$Text) + [Environment]::NewLine, $enc)
}

function Save-DcoirJson {
    param([Parameter(Mandatory=$true)][string]$Path, [Parameter(Mandatory=$true)]$Object)
    Write-DcoirUtf8Text -Path $Path -Text ($Object | ConvertTo-Json -Depth 20)
}

function Write-Status {
    param([string]$Message)
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    if ($script:LogPath) { Add-DcoirUtf8Line -Path $script:LogPath -Text $line }
}

function Invoke-DcoirGhText {
    param([Parameter(Mandatory=$true)][string[]]$GhArgs, [string]$DebugName = 'gh')
    $rawLines = & gh @GhArgs 2>&1
    $exit = $LASTEXITCODE
    $raw = ($rawLines | Out-String).Trim()
    $safeName = ($DebugName -replace '[^A-Za-z0-9_.-]', '_')
    if ($script:DebugDir) {
        $debugPath = Join-Path $script:DebugDir ($safeName + '.txt')
        Write-DcoirUtf8Text -Path $debugPath -Text ("gh {0}`nEXIT={1}`n`n{2}" -f ($GhArgs -join ' '), $exit, $raw)
    }
    if ($exit -ne 0) { throw "gh command failed exit=$exit: gh $($GhArgs -join ' ')" }
    return $raw
}

function Invoke-DcoirGhJson {
    param([Parameter(Mandatory=$true)][string[]]$GhArgs, [string]$DebugName = 'gh_json')
    $raw = Invoke-DcoirGhText -GhArgs $GhArgs -DebugName $DebugName
    if (-not ($raw.StartsWith('{') -or $raw.StartsWith('['))) { throw "Expected JSON from: gh $($GhArgs -join ' ')" }
    return ($raw | ConvertFrom-Json)
}

function Test-DcoirGhAvailable {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "GitHub CLI 'gh' was not found in PATH." }
    try { Invoke-DcoirGhText -GhArgs @('auth','status') -DebugName 'gh_auth_status' | Out-Null } catch { throw "GitHub CLI auth status failed. Run 'gh auth login' or fix gh auth before using this tool. Details: $($_.Exception.Message)" }
}

function Get-DcoirWorkflowRuns {
    param([string]$WorkflowFile, [string]$Branch, [int]$PerPage = 10, [string]$Event)
    $wfEsc = [System.Uri]::EscapeDataString($WorkflowFile)
    $endpoint = "repos/$script:Repo/actions/workflows/$wfEsc/runs?per_page=$PerPage"
    if ($Branch) { $endpoint += '&branch=' + [System.Uri]::EscapeDataString($Branch) }
    if ($Event) { $endpoint += '&event=' + [System.Uri]::EscapeDataString($Event) }
    $json = Invoke-DcoirGhJson -GhArgs @('api', $endpoint) -DebugName ('runs_' + ($WorkflowFile -replace '[^A-Za-z0-9_.-]', '_'))
    return @($json.workflow_runs)
}

function Get-DcoirRunById {
    param([Parameter(Mandatory=$true)][Int64]$Id)
    return Invoke-DcoirGhJson -GhArgs @('api', "repos/$script:Repo/actions/runs/$Id") -DebugName "run_$Id"
}

function Get-DcoirRunJobs {
    param([Parameter(Mandatory=$true)][Int64]$Id)
    $jobs = Invoke-DcoirGhJson -GhArgs @('api', "repos/$script:Repo/actions/runs/$Id/jobs?per_page=100") -DebugName "jobs_$Id"
    return @($jobs.jobs)
}

function Save-DcoirRunEvidence {
    param([Parameter(Mandatory=$true)][Int64]$Id, [string]$Label, [hashtable]$Capture)
    $safeLabel = (($Label -replace '[^A-Za-z0-9_.-]', '_').Trim('_'))
    $runDir = Join-Path $script:EvidenceDir ("run_{0}_{1}" -f $Id, $safeLabel)
    New-Item -ItemType Directory -Force -Path $runDir | Out-Null
    $run = Get-DcoirRunById -Id $Id
    Save-DcoirJson -Path (Join-Path $runDir 'run.json') -Object $run
    $wantJobs = [bool](Get-DcoirConfigValue -Map $Capture -Name 'jobs' -Default $true)
    $wantLogs = [bool](Get-DcoirConfigValue -Map $Capture -Name 'logs' -Default $true)
    $wantArtifacts = [bool](Get-DcoirConfigValue -Map $Capture -Name 'artifacts' -Default $false)
    if ($wantJobs) {
        $jobs = Get-DcoirRunJobs -Id $Id
        Save-DcoirJson -Path (Join-Path $runDir 'jobs.json') -Object $jobs
    }
    if ($wantLogs) {
        try {
            $logText = Invoke-DcoirGhText -GhArgs @('run','view', [string]$Id, '-R', $script:Repo, '--log') -DebugName "log_$Id"
            Write-DcoirUtf8Text -Path (Join-Path $runDir 'run.log.txt') -Text $logText
        } catch {
            Write-DcoirUtf8Text -Path (Join-Path $runDir 'run.log.error.txt') -Text $_.Exception.Message
        }
    }
    if ($wantArtifacts -or $script:DownloadArtifacts) {
        $artifactDir = Join-Path $runDir 'artifacts'
        New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null
        try { Invoke-DcoirGhText -GhArgs @('run','download', [string]$Id, '-R', $script:Repo, '-D', $artifactDir) -DebugName "artifacts_$Id" | Out-Null }
        catch { Write-DcoirUtf8Text -Path (Join-Path $runDir 'artifacts.error.txt') -Text $_.Exception.Message }
    }
    return $run
}

function New-DcoirRunRecord {
    param([string]$Label, [string]$WorkflowFile, [string]$RefName, [hashtable]$Inputs, [hashtable]$Capture)
    return [ordered]@{
        label = $Label; workflow = $WorkflowFile; ref = $RefName; inputs = $Inputs; capture = $Capture
        state = 'planned'; run_id = $null; url = $null; status = $null; conclusion = $null
        created_at = $null; updated_at = $null; error = $null
    }
}

function Start-DcoirWorkflowRun {
    param([hashtable]$Record)
    $workflowFile = [string]$Record.workflow
    $refName = [string]$Record.ref
    $before = @(Get-DcoirWorkflowRuns -WorkflowFile $workflowFile -Branch $refName -PerPage 30 -Event 'workflow_dispatch')
    $beforeIds = @($before | ForEach-Object { [Int64]$_.id })
    $dispatchStart = (Get-Date).ToUniversalTime().AddMinutes(-2)
    $args = @('workflow','run',$workflowFile,'-R',$script:Repo,'--ref',$refName)
    $inputs = $Record.inputs
    if ($inputs) {
        foreach ($key in $inputs.Keys) { $args += @('-f', ("{0}={1}" -f $key, [string]$inputs[$key])) }
    }
    Invoke-DcoirGhText -GhArgs $args -DebugName ('dispatch_' + ($Record.label -replace '[^A-Za-z0-9_.-]', '_')) | Out-Null
    for ($i = 1; $i -le $script:DispatchPollAttempts; $i++) {
        Start-Sleep -Seconds $script:DispatchPollSeconds
        $after = @(Get-DcoirWorkflowRuns -WorkflowFile $workflowFile -Branch $refName -PerPage 30 -Event 'workflow_dispatch')
        $candidates = @($after | Where-Object { ($beforeIds -notcontains [Int64]$_.id) -and ([DateTime]$_.created_at).ToUniversalTime() -ge $dispatchStart } | Sort-Object { [DateTime]$_.created_at } -Descending)
        if ($candidates.Count -gt 0) {
            $run = $candidates[0]
            $Record.run_id = [Int64]$run.id; $Record.url = [string]$run.html_url; $Record.status = [string]$run.status; $Record.conclusion = [string]$run.conclusion; $Record.created_at = [string]$run.created_at; $Record.updated_at = [string]$run.updated_at; $Record.state = 'active'
            Write-Status "Dispatched $($Record.label): workflow=$workflowFile run_id=$($Record.run_id) status=$($Record.status)"
            return
        }
        Write-Status "Waiting for dispatched run to appear for $($Record.label) ($i/$script:DispatchPollAttempts)"
    }
    throw "Timed out waiting for dispatched run to appear for $($Record.label)."
}

function Update-DcoirRunRecordStatus {
    param([hashtable]$Record)
    if (-not $Record.run_id) { return }
    $run = Get-DcoirRunById -Id ([Int64]$Record.run_id)
    $Record.status = [string]$run.status; $Record.conclusion = [string]$run.conclusion; $Record.url = [string]$run.html_url; $Record.updated_at = [string]$run.updated_at
    if ($run.status -eq 'completed') { $Record.state = 'terminal' } else { $Record.state = 'active' }
}

function Wait-DcoirRunSet {
    param([System.Collections.ArrayList]$Records, [switch]$DispatchPlanned)
    $deadline = (Get-Date).AddMinutes($script:TimeoutMinutes)
    while ($true) {
        if ((Get-Date) -gt $deadline) {
            foreach ($r in $Records) { if ($r.state -ne 'terminal') { $r.state = 'timed_out'; $r.error = 'Timeout waiting for workflow run completion.' } }
            return
        }
        if ($DispatchPlanned) {
            $activeCount = @($Records | Where-Object { $_.state -eq 'active' }).Count
            $slots = [Math]::Max(0, $script:MaxParallel - $activeCount)
            if ($slots -gt 0) {
                $planned = @($Records | Where-Object { $_.state -eq 'planned' } | Select-Object -First $slots)
                foreach ($r in $planned) {
                    try { Start-DcoirWorkflowRun -Record $r } catch { $r.state = 'terminal'; $r.error = $_.Exception.Message; Write-Status "Dispatch failed for $($r.label): $($r.error)" }
                }
            }
        }
        foreach ($r in @($Records | Where-Object { $_.state -eq 'active' })) {
            try { Update-DcoirRunRecordStatus -Record $r } catch { $r.error = $_.Exception.Message; Write-Status "Status update failed for $($r.label): $($r.error)" }
        }
        Save-DcoirJson -Path (Join-Path $script:RunOutputDir 'run_set_state.json') -Object @($Records)
        $notDone = @($Records | Where-Object { $_.state -eq 'planned' -or $_.state -eq 'active' })
        $statusLine = @($Records | ForEach-Object { "{0}:{1}/{2}" -f $_.label, $_.status, $_.conclusion }) -join '; '
        Write-Status "Run set status: $statusLine"
        if ($notDone.Count -eq 0) { return }
        Start-Sleep -Seconds $script:PollSeconds
    }
}

function Add-DcoirWatchRecords {
    param([System.Collections.ArrayList]$Records, [string[]]$Workflows, [Int64[]]$Ids, [int]$LimitCount, [string]$Branch)
    if ($Ids) {
        foreach ($id in $Ids) {
            $run = Get-DcoirRunById -Id $id
            $rec = New-DcoirRunRecord -Label ("run_$id") -WorkflowFile ([string]$run.workflow_id) -RefName $Branch -Inputs @{} -Capture @{ summary=$true; logs=$true; artifacts=$script:DownloadArtifacts; jobs=$true }
            $rec.run_id = [Int64]$run.id; $rec.url = [string]$run.html_url; $rec.status = [string]$run.status; $rec.conclusion = [string]$run.conclusion; $rec.created_at = [string]$run.created_at; $rec.updated_at = [string]$run.updated_at
            if ($run.status -eq 'completed') { $rec.state = 'terminal' } else { $rec.state = 'active' }
            [void]$Records.Add($rec)
        }
    }
    if ($Workflows) {
        foreach ($wf in $Workflows) {
            $runs = @(Get-DcoirWorkflowRuns -WorkflowFile $wf -Branch $Branch -PerPage $LimitCount)
            foreach ($run in $runs) {
                $rec = New-DcoirRunRecord -Label ("{0}_{1}" -f ($wf -replace '[^A-Za-z0-9_.-]', '_'), $run.id) -WorkflowFile $wf -RefName $Branch -Inputs @{} -Capture @{ summary=$true; logs=$true; artifacts=$script:DownloadArtifacts; jobs=$true }
                $rec.run_id = [Int64]$run.id; $rec.url = [string]$run.html_url; $rec.status = [string]$run.status; $rec.conclusion = [string]$run.conclusion; $rec.created_at = [string]$run.created_at; $rec.updated_at = [string]$run.updated_at
                if ($run.status -eq 'completed') { $rec.state = 'terminal' } else { $rec.state = 'active' }
                [void]$Records.Add($rec)
            }
        }
    }
}

# Resolve system-scope environment variables early.
$script:SystemRepoRoot = Get-DcoirSystemEnvValue -Name 'DCOIR_REPO_ROOT' -Required
$script:SystemDownloadsDir = Get-DcoirSystemEnvValue -Name 'DCOIR_DOWNLOADS_DIR' -Required
if (-not (Test-Path -LiteralPath $script:SystemRepoRoot -PathType Container)) { throw "DCOIR_REPO_ROOT Machine/System path does not exist: $script:SystemRepoRoot" }
if (-not (Test-Path -LiteralPath $script:SystemDownloadsDir -PathType Container)) { throw "DCOIR_DOWNLOADS_DIR Machine/System path does not exist: $script:SystemDownloadsDir" }

if ([string]::IsNullOrWhiteSpace($ManifestJson) -and $Mode -eq 'manifest') {
    $ManifestJson = Join-Path $script:SystemRepoRoot 'operator_tools\github_desktop_lane\manifests\actions_workflow_orchestrator.dispatch.sample.json'
}
if ($ManifestJson) { $ManifestJson = Resolve-DcoirPathText -Text $ManifestJson }

$manifest = @{}
if ($ManifestJson) {
    if (-not (Test-Path -LiteralPath $ManifestJson -PathType Leaf)) { throw "ManifestJson not found: $ManifestJson" }
    $manifest = ConvertTo-DcoirHashtable (Get-Content -LiteralPath $ManifestJson -Raw | ConvertFrom-Json)
    if ($Mode -eq 'manifest') { $Mode = [string](Get-DcoirConfigValue -Map $manifest -Name 'mode' -Default 'dispatch') }
}

$script:Repo = [string](Get-DcoirConfigValue -Map $manifest -Name 'repo' -Default $Repo)
$defaultRef = [string](Get-DcoirConfigValue -Map $manifest -Name 'default_ref' -Default $Ref)
$script:PollSeconds = [int](Get-DcoirConfigValue -Map $manifest -Name 'poll_interval_seconds' -Default $PollSeconds)
$script:TimeoutMinutes = [int](Get-DcoirConfigValue -Map $manifest -Name 'timeout_minutes' -Default $TimeoutMinutes)
$script:MaxParallel = [int](Get-DcoirConfigValue -Map $manifest -Name 'max_parallel' -Default $MaxParallel)
if ($script:MaxParallel -lt 1) { $script:MaxParallel = 1 }
$script:DispatchPollSeconds = [int](Get-DcoirConfigValue -Map $manifest -Name 'dispatch_poll_seconds' -Default 5)
$script:DispatchPollAttempts = [int](Get-DcoirConfigValue -Map $manifest -Name 'dispatch_poll_attempts' -Default 60)
$manifestDryRun = [bool](Get-DcoirConfigValue -Map $manifest -Name 'dry_run' -Default $true)
if ($DryRun) { $manifestDryRun = $true }
$requireConfirmation = [bool](Get-DcoirConfigValue -Map $manifest -Name 'require_dispatch_confirmation' -Default $true)
$outputCfg = Get-DcoirConfigValue -Map $manifest -Name 'output' -Default @{}
$outputDefault = if (-not [string]::IsNullOrWhiteSpace($OutputBase)) { $OutputBase } else { $script:SystemDownloadsDir }
$outputFolder = Resolve-DcoirPathText ([string](Get-DcoirConfigValue -Map $outputCfg -Name 'folder' -Default $outputDefault))
if (-not (Test-Path -LiteralPath $outputFolder -PathType Container)) { New-Item -ItemType Directory -Force -Path $outputFolder | Out-Null }
$runSetId = [string](Get-DcoirConfigValue -Map $manifest -Name 'run_set_id' -Default ("dcoir_actions_" + (Get-Date -Format 'yyyyMMdd_HHmmss')))
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$script:RunOutputDir = Join-Path $outputFolder ("{0}_{1}" -f $stamp, ($runSetId -replace '[^A-Za-z0-9_.-]', '_'))
$script:DebugDir = Join-Path $script:RunOutputDir 'debug'
$script:EvidenceDir = Join-Path $script:RunOutputDir 'evidence'
New-Item -ItemType Directory -Force -Path $script:DebugDir, $script:EvidenceDir | Out-Null
$script:LogPath = Join-Path $script:RunOutputDir 'orchestrator.log.txt'
$script:DownloadArtifacts = [bool]($DownloadArtifacts -or [bool](Get-DcoirConfigValue -Map $outputCfg -Name 'download_artifacts' -Default $false))
$createZip = [bool]($CreateUploadZip -or [bool](Get-DcoirConfigValue -Map $outputCfg -Name 'create_chatgpt_friendly_zip' -Default $false))
$zipName = [string](Get-DcoirConfigValue -Map $outputCfg -Name 'zip_name' -Default ($runSetId + '.chatgpt.zip'))
$zipPath = Join-Path $outputFolder $zipName

Write-Status "DCOIR Actions Workflow Orchestrator v$script:ToolVersion"
Write-Status "Machine DCOIR_REPO_ROOT=$script:SystemRepoRoot"
Write-Status "Machine DCOIR_DOWNLOADS_DIR=$script:SystemDownloadsDir"
Write-Status "Mode=$Mode Repo=$script:Repo Ref=$defaultRef MaxParallel=$script:MaxParallel DryRun=$manifestDryRun"
Test-DcoirGhAvailable

$records = New-Object System.Collections.ArrayList
if ($Mode -eq 'dispatch') {
    $runs = Get-DcoirConfigValue -Map $manifest -Name 'runs' -Default @()
    foreach ($r in @($runs)) {
        $label = [string](Get-DcoirConfigValue -Map $r -Name 'run_id' -Default (Get-DcoirConfigValue -Map $r -Name 'label' -Default ([guid]::NewGuid().ToString('N'))))
        $wf = [string](Get-DcoirConfigValue -Map $r -Name 'workflow' -Default $null)
        if ([string]::IsNullOrWhiteSpace($wf)) { throw "Dispatch run $label has no workflow." }
        $rref = [string](Get-DcoirConfigValue -Map $r -Name 'ref' -Default $defaultRef)
        $inputs = Get-DcoirConfigValue -Map $r -Name 'inputs' -Default @{}
        $capture = Get-DcoirConfigValue -Map $r -Name 'capture' -Default @{}
        [void]$records.Add((New-DcoirRunRecord -Label $label -WorkflowFile $wf -RefName $rref -Inputs $inputs -Capture $capture))
    }
    Save-DcoirJson -Path (Join-Path $script:RunOutputDir 'dispatch_plan.json') -Object @($records)
    if ($manifestDryRun) {
        Write-Status 'Dry run requested. No workflows dispatched.'
        foreach ($rec in $records) { $rec.state = 'dry_run' }
    } else {
        if ($requireConfirmation -and -not $ConfirmDispatch) { throw "Dispatch is blocked because require_dispatch_confirmation=true. Re-run with -ConfirmDispatch after reviewing dispatch_plan.json." }
        Wait-DcoirRunSet -Records $records -DispatchPlanned
    }
} elseif ($Mode -eq 'watch') {
    $watchCfg = Get-DcoirConfigValue -Map $manifest -Name 'watch' -Default @{}
    $wfs = @(Get-DcoirConfigValue -Map $watchCfg -Name 'workflows' -Default $Workflow)
    $ids = @(Get-DcoirConfigValue -Map $watchCfg -Name 'run_ids' -Default $RunId)
    $lim = [int](Get-DcoirConfigValue -Map $watchCfg -Name 'limit' -Default $Limit)
    Add-DcoirWatchRecords -Records $records -Workflows $wfs -Ids $ids -LimitCount $lim -Branch $defaultRef
    $untilComplete = [bool](Get-DcoirConfigValue -Map $watchCfg -Name 'until_complete' -Default $true)
    if ($untilComplete) { Wait-DcoirRunSet -Records $records }
} elseif ($Mode -eq 'capture') {
    $capCfg = Get-DcoirConfigValue -Map $manifest -Name 'capture' -Default @{}
    $ids = @(Get-DcoirConfigValue -Map $capCfg -Name 'run_ids' -Default $RunId)
    if (-not $ids -or $ids.Count -eq 0) { throw 'Capture mode requires run_ids or -RunId.' }
    Add-DcoirWatchRecords -Records $records -Workflows @() -Ids $ids -LimitCount $Limit -Branch $defaultRef
} else { throw "Unsupported mode: $Mode" }

foreach ($rec in @($records | Where-Object { $_.run_id })) {
    try {
        $run = Save-DcoirRunEvidence -Id ([Int64]$rec.run_id) -Label ([string]$rec.label) -Capture ([hashtable]$rec.capture)
        $rec.status = [string]$run.status; $rec.conclusion = [string]$run.conclusion; $rec.url = [string]$run.html_url
        if ($run.status -eq 'completed') { $rec.state = 'terminal' }
    } catch { $rec.error = $_.Exception.Message; Write-Status "Evidence capture failed for $($rec.label): $($rec.error)" }
}

$failed = @($records | Where-Object { $_.conclusion -and $_.conclusion -ne 'success' -and $_.conclusion -ne '' })
$summary = [ordered]@{
    tool = 'Invoke-DcoirActionsWorkflowOrchestrator.ps1'; tool_version = $script:ToolVersion; created_at = (Get-Date -Format o)
    mode = $Mode; repo = $script:Repo; default_ref = $defaultRef; run_set_id = $runSetId; dry_run = $manifestDryRun; max_parallel = $script:MaxParallel
    machine_repo_root = $script:SystemRepoRoot; machine_downloads_dir = $script:SystemDownloadsDir
    output_dir = $script:RunOutputDir; zip_path = $null; run_count = $records.Count; failed_or_non_success_count = $failed.Count; records = @($records)
}
Save-DcoirJson -Path (Join-Path $script:RunOutputDir 'orchestrator_summary.json') -Object $summary
$md = @()
$md += '# DCOIR Actions Workflow Orchestrator Summary'; $md += ''
$md += "- Created: $($summary.created_at)"; $md += "- Mode: $Mode"; $md += "- Repo: $script:Repo"; $md += "- Run set: $runSetId"; $md += "- Dry run: $manifestDryRun"; $md += "- Max parallel: $script:MaxParallel"; $md += "- Machine DCOIR_REPO_ROOT: $script:SystemRepoRoot"; $md += ''
$md += '| Label | Workflow | Run ID | Status | Conclusion | URL |'; $md += '|---|---|---:|---|---|---|'
foreach ($rec in $records) { $md += "| $($rec.label) | $($rec.workflow) | $($rec.run_id) | $($rec.status) | $($rec.conclusion) | $($rec.url) |" }
Write-DcoirUtf8Text -Path (Join-Path $script:RunOutputDir 'orchestrator_summary.md') -Text ($md -join "`n")

if ($createZip) {
    $helper = Join-Path $PSScriptRoot 'New-DcoirChatGPTFriendlyZip.ps1'
    if (Test-Path -LiteralPath $helper -PathType Leaf) {
        . $helper
        $zipResult = New-DcoirChatGPTFriendlyZip -SourceFolder $script:RunOutputDir -OutputZip $zipPath -IndexTitle 'DCOIR Actions workflow orchestrator evidence' -NormalizeTextEncoding
        $summary.zip_path = $zipResult.output_zip
        Save-DcoirJson -Path (Join-Path $script:RunOutputDir 'orchestrator_summary.json') -Object $summary
        Write-Status "Created ChatGPT-friendly ZIP: $($zipResult.output_zip)"
    } else {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
        [System.IO.Compression.ZipFile]::CreateFromDirectory($script:RunOutputDir, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)
        $summary.zip_path = $zipPath
        Save-DcoirJson -Path (Join-Path $script:RunOutputDir 'orchestrator_summary.json') -Object $summary
        Write-Status "Created fallback ZIP: $zipPath"
    }
}

Write-Status "Complete. Output: $script:RunOutputDir"
if ($summary.zip_path) { Write-Host "UPLOAD_ZIP=$($summary.zip_path)" }
if ($failed.Count -gt 0) { exit 2 }
