[CmdletBinding()]
param(
    [string]$RepoRoot = $env:DCOIR_REPO_ROOT,
    [string]$OutputDir = $env:DCOIR_DOWNLOADS_DIR
)

$ErrorActionPreference = "Continue"
if (-not $RepoRoot) { throw "DCOIR_REPO_ROOT is not set." }
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "Repo root not found: $RepoRoot" }
if (-not $OutputDir) { $OutputDir = Join-Path $env:USERPROFILE "Downloads" }
if (-not (Test-Path -LiteralPath $OutputDir -PathType Container)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $OutputDir "dcoir_git_conflict_diagnostic_$stamp.txt"
Set-Location $RepoRoot

& {
    "DCOIR Git Conflict Diagnostic"
    "Timestamp: $(Get-Date -Format o)"
    "Repo: $RepoRoot"

    ""
    "== CURRENT DIRECTORY =="
    Get-Location

    ""
    "== GIT VERSION =="
    git --version

    ""
    "== BRANCH =="
    git branch --show-current

    ""
    "== HEAD =="
    git rev-parse --short HEAD
    git log --oneline -5

    ""
    "== REMOTES =="
    git remote -v

    ""
    "== FETCH ORIGIN =="
    git fetch origin --prune

    ""
    "== STATUS SHORT WITH BRANCH =="
    git status --short --branch

    ""
    "== STATUS FULL =="
    git status

    ""
    "== BRANCH VERBOSE =="
    git branch -vv

    ""
    "== AHEAD / BEHIND MAIN =="
    $branch = git branch --show-current
    if ($branch) { git rev-list --left-right --count "$branch...origin/main" }

    ""
    "== UNMERGED / CONFLICT FILES =="
    git diff --name-only --diff-filter=U

    ""
    "== WORKING TREE DIFF SUMMARY =="
    git diff --stat
    git diff --name-status

    ""
    "== STAGED DIFF SUMMARY =="
    git diff --cached --stat
    git diff --cached --name-status

    ""
    "== UNTRACKED FILES =="
    git ls-files --others --exclude-standard

    ""
    "== STASH LIST =="
    git stash list

    ""
    "== REBASE / MERGE / CHERRY-PICK STATE =="
    if (Test-Path ".git/MERGE_HEAD") { "MERGE_HEAD exists" } else { "No MERGE_HEAD" }
    if (Test-Path ".git/rebase-merge") { "rebase-merge exists" } else { "No rebase-merge" }
    if (Test-Path ".git/rebase-apply") { "rebase-apply exists" } else { "No rebase-apply" }
    if (Test-Path ".git/CHERRY_PICK_HEAD") { "CHERRY_PICK_HEAD exists" } else { "No CHERRY_PICK_HEAD" }

    ""
    "== RECENT ALL-BRANCH GRAPH =="
    git log --oneline --decorate --graph --all -20
} 2>&1 | Tee-Object -FilePath $log | Out-Null

Write-Host ""
Write-Host "Saved diagnostic log to:"
Write-Host $log
