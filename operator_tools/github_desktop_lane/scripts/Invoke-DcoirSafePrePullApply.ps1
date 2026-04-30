param(
    [string]$RepoRoot = $env:DCOIR_REPO_ROOT,
    [string]$OutputDir = $env:DCOIR_DOWNLOADS_DIR,
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [string]$StashMessagePrefix = "pre-pull-local-work"
)

$ErrorActionPreference = "Continue"
if (-not $RepoRoot) { throw "DCOIR_REPO_ROOT is not set." }
if (-not $OutputDir) { $OutputDir = Join-Path $env:USERPROFILE "Downloads" }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $OutputDir "dcoir_safe_prepull_apply_$stamp.txt"
Set-Location $RepoRoot

& {
    "DCOIR Safe Pre-Pull Apply"
    "Timestamp: $(Get-Date -Format o)"
    "Repo: $RepoRoot"

    ""
    "== BEFORE =="
    git status --short --branch
    git log --oneline -5

    ""
    "== STASH CURRENT WORK =="
    git stash push -u -m "$StashMessagePrefix-$stamp"
    $newStash = git rev-parse --verify refs/stash
    "New stash commit: $newStash"

    ""
    "== FETCH AND FAST-FORWARD PULL =="
    git fetch $Remote --prune
    git pull --ff-only $Remote $Branch

    if ($LASTEXITCODE -ne 0) {
        ""
        "PULL FAILED. Stash was preserved. Do not continue manually."
        git status --short --branch
        git stash list
        exit 1
    }

    ""
    "== REAPPLY CAPTURED WORK =="
    git stash apply $newStash

    if ($LASTEXITCODE -ne 0) {
        ""
        "STASH APPLY HAD CONFLICTS. Stash was preserved. Do not commit yet."
        git status
        git diff --name-only --diff-filter=U
        git stash list
        exit 2
    }

    ""
    "== AFTER =="
    git status --short --branch
    git log --oneline -5

    ""
    "== STASH LIST =="
    git stash list

    ""
    "RESULT: If status shows only intended changes and no conflict files, review and commit in GitHub Desktop. Do not drop stashes until instructed."
} 2>&1 | Tee-Object -FilePath $log

Write-Host ""
Write-Host "Saved log to:"
Write-Host $log
