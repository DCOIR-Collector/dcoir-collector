[CmdletBinding()]
param(
    [string]$RepoRoot = $env:DCOIR_REPO_ROOT,
    [string]$OutputDir = $env:DCOIR_DOWNLOADS_DIR,
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [string]$StashMessagePrefix = "pre-pull-local-work"
)

$ErrorActionPreference = "Continue"
$commonModule = Join-Path $PSScriptRoot '..\modules\Dcoir.Common\Dcoir.Common.psd1'
$gitModule = Join-Path $PSScriptRoot '..\modules\Dcoir.Git\Dcoir.Git.psd1'
Import-Module -Name $commonModule -Force -ErrorAction Stop
Import-Module -Name $gitModule -Force -ErrorAction Stop

if (-not $RepoRoot) { $RepoRoot = Dcoir.Common\Get-DcoirSystemEnvValue -Name 'DCOIR_REPO_ROOT' -Required }
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "Repo root not found: $RepoRoot" }
if (-not $OutputDir) { $OutputDir = Dcoir.Common\Get-DcoirSystemEnvValue -Name 'DCOIR_DOWNLOADS_DIR' -Required }
if (-not (Test-Path -LiteralPath $OutputDir -PathType Container)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$OutputDir = (Resolve-Path -LiteralPath $OutputDir).Path
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $OutputDir "dcoir_safe_prepull_apply_$stamp.txt"

function Write-PrePullLine {
    param([AllowEmptyString()][string]$Text)
    Write-Host $Text
    Dcoir.Common\Add-DcoirUtf8Line -Path $log -Text $Text
}

function Invoke-PrePullGit {
    param([Parameter(Mandatory=$true)][string[]]$Arguments, [switch]$AllowFailure)
    return Dcoir.Git\Invoke-DcoirGitCommand -RepoRoot $RepoRoot -Arguments $Arguments -LogPath $log -AllowFailure:$AllowFailure
}

Write-PrePullLine "DCOIR Safe Pre-Pull Apply"
Write-PrePullLine "Timestamp: $(Get-Date -Format o)"
Write-PrePullLine "Repo: $RepoRoot"
Write-PrePullLine ""
Write-PrePullLine "== BEFORE =="
Invoke-PrePullGit @('status','--short','--branch') -AllowFailure | Out-Null
Invoke-PrePullGit @('log','--oneline','-5') -AllowFailure | Out-Null
Write-PrePullLine ""
Write-PrePullLine "== STASH CURRENT WORK =="
$stashResult = Invoke-PrePullGit @('stash','push','-u','-m',"$StashMessagePrefix-$stamp") -AllowFailure
$newStashResult = Invoke-PrePullGit @('rev-parse','--verify','refs/stash') -AllowFailure
$newStash = (($newStashResult.Lines | Select-Object -Last 1) -as [string]).Trim()
Write-PrePullLine "New stash commit: $newStash"
Write-PrePullLine ""
Write-PrePullLine "== FETCH AND FAST-FORWARD PULL =="
Invoke-PrePullGit @('fetch',$Remote,'--prune') -AllowFailure | Out-Null
$pullResult = Invoke-PrePullGit @('pull','--ff-only',$Remote,$Branch) -AllowFailure
if ($pullResult.ExitCode -ne 0) {
    Write-PrePullLine ""
    Write-PrePullLine "PULL FAILED. Stash was preserved. Do not continue manually."
    Invoke-PrePullGit @('status','--short','--branch') -AllowFailure | Out-Null
    Invoke-PrePullGit @('stash','list') -AllowFailure | Out-Null
    exit 1
}
Write-PrePullLine ""
Write-PrePullLine "== REAPPLY CAPTURED WORK =="
$applyResult = Invoke-PrePullGit @('stash','apply',$newStash) -AllowFailure
if ($applyResult.ExitCode -ne 0) {
    Write-PrePullLine ""
    Write-PrePullLine "STASH APPLY HAD CONFLICTS. Stash was preserved. Do not commit yet."
    Invoke-PrePullGit @('status') -AllowFailure | Out-Null
    Invoke-PrePullGit @('diff','--name-only','--diff-filter=U') -AllowFailure | Out-Null
    Invoke-PrePullGit @('stash','list') -AllowFailure | Out-Null
    exit 2
}
Write-PrePullLine ""
Write-PrePullLine "== AFTER =="
Invoke-PrePullGit @('status','--short','--branch') -AllowFailure | Out-Null
Invoke-PrePullGit @('log','--oneline','-5') -AllowFailure | Out-Null
Write-PrePullLine ""
Write-PrePullLine "== STASH LIST =="
Invoke-PrePullGit @('stash','list') -AllowFailure | Out-Null
Write-PrePullLine ""
Write-PrePullLine "RESULT: If status shows only intended changes and no conflict files, review and commit in GitHub Desktop. Do not drop stashes until instructed."
Write-Host ""
Write-Host "Saved log to:"
Write-Host $log
