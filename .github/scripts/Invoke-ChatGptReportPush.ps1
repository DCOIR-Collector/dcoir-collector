param(
  [Parameter(Mandatory=$true)][string]$CommitMessage,
  [Parameter(Mandatory=$true)][string[]]$Paths,
  [int]$MaxAttempts = 5
)

$ErrorActionPreference = 'Continue'

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

foreach ($path in $Paths) {
  if ([string]::IsNullOrWhiteSpace($path)) { continue }
  git add -- $path 2>$null
}

git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host "No staged report changes to commit for: $CommitMessage"
  exit 0
}

git commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) {
  Write-Warning "git commit failed for report commit '$CommitMessage'. Continuing so the exec job is not blocked by report persistence."
  git status --short
  exit 0
}

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
  Write-Host "Report push attempt $attempt of $MaxAttempts for: $CommitMessage"

  git fetch origin main
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "git fetch failed on attempt $attempt."
    Start-Sleep -Seconds ([Math]::Min(30, 5 * $attempt))
    continue
  }

  git rebase origin/main
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "git rebase failed on attempt $attempt; aborting rebase and retrying."
    git rebase --abort 2>$null
    Start-Sleep -Seconds ([Math]::Min(30, 5 * $attempt))
    continue
  }

  git push origin HEAD:main
  if ($LASTEXITCODE -eq 0) {
    Write-Host "Report push succeeded on attempt $attempt."
    exit 0
  }

  Write-Warning "git push failed on attempt $attempt. Retrying after backoff."
  Start-Sleep -Seconds ([Math]::Min(30, 5 * $attempt))
}

Write-Warning "Report push failed after $MaxAttempts attempts. Continuing so transient report-push failure does not prevent the approved command from running."
exit 0
