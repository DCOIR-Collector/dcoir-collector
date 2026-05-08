param(
  [Parameter(Mandatory=$true)][string]$CommitMessage,
  [Parameter(Mandatory=$true)][string[]]$Paths,
  [object]$MaxAttempts = 5,
  [switch]$RequirePush,
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$ExtraPaths
)

$ErrorActionPreference = 'Continue'

$AllPaths = @()
foreach ($path in $Paths) {
  if (-not [string]::IsNullOrWhiteSpace($path)) { $AllPaths += $path }
}

$MaxAttemptCount = 5
if ($null -ne $MaxAttempts) {
  $parsed = 0
  if ([int]::TryParse([string]$MaxAttempts, [ref]$parsed)) {
    $MaxAttemptCount = $parsed
  } else {
    $AllPaths += [string]$MaxAttempts
  }
}

foreach ($path in $ExtraPaths) {
  if (-not [string]::IsNullOrWhiteSpace($path)) { $AllPaths += $path }
}

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config core.longpaths true

$ExpandedPaths = @()
foreach ($path in $AllPaths) {
  foreach ($item in ($path -split '\|')) {
    if (-not [string]::IsNullOrWhiteSpace($item)) {
      $normalized = ([string]$item).Trim() -replace '\\','/'
      if (-not [string]::IsNullOrWhiteSpace($normalized)) { $ExpandedPaths += $normalized }
    }
  }
}
$ExpandedPaths = @($ExpandedPaths | Select-Object -Unique)

if ($ExpandedPaths.Count -eq 0) {
  Write-Host "No report paths supplied for: $CommitMessage"
  if ($RequirePush) {
    Write-Error "Required report push had no paths to stage for: $CommitMessage"
    exit 1
  }
  exit 0
}

Write-Host "Staging report paths for: $CommitMessage"
foreach ($path in $ExpandedPaths) { Write-Host "  $path" }

& git -c core.longpaths=true add -A -- @ExpandedPaths
$addExit = $LASTEXITCODE
if ($addExit -ne 0) {
  Write-Warning "git add failed with exit code $addExit for: $CommitMessage"
  git status --short
  if ($RequirePush) { exit 1 }
  exit 0
}

& git -c core.longpaths=true diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host "No staged changes to commit for: $CommitMessage"
  git status --short
  if ($RequirePush) {
    Write-Error "Required report push had no staged changes for: $CommitMessage"
    exit 1
  }
  exit 0
}

& git -c core.longpaths=true commit -m $CommitMessage
if ($LASTEXITCODE -ne 0) {
  Write-Warning "git commit failed for: $CommitMessage"
  git status --short
  if ($RequirePush) { exit 1 }
  exit 0
}

for ($attempt = 1; $attempt -le $MaxAttemptCount; $attempt++) {
  Write-Host "Report push attempt $attempt of $MaxAttemptCount for: $CommitMessage"
  & git -c core.longpaths=true fetch origin main
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "git fetch failed on attempt $attempt."
    Start-Sleep -Seconds ([Math]::Min(30, 5 * $attempt))
    continue
  }
  & git -c core.longpaths=true rebase origin/main
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "git rebase failed on attempt $attempt; aborting rebase and retrying."
    & git -c core.longpaths=true rebase --abort 2>$null
    git status --short
    Start-Sleep -Seconds ([Math]::Min(30, 5 * $attempt))
    continue
  }
  & git -c core.longpaths=true push origin HEAD:main
  if ($LASTEXITCODE -eq 0) {
    Write-Host "Report push succeeded on attempt $attempt."
    exit 0
  }
  Write-Warning "git push failed on attempt $attempt."
  Start-Sleep -Seconds ([Math]::Min(30, 5 * $attempt))
}

Write-Warning "Report push failed after $MaxAttemptCount attempts."
if ($RequirePush) { exit 1 }
exit 0
