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

function Write-ChatGptReportUrls {
  param([string[]]$CandidatePaths)

  $repo = $env:GITHUB_REPOSITORY
  if ([string]::IsNullOrWhiteSpace($repo)) { return }

  $serverUrl = $env:GITHUB_SERVER_URL
  if ([string]::IsNullOrWhiteSpace($serverUrl)) { $serverUrl = 'https://github.com' }

  $reportPaths = @()
  foreach ($candidate in $CandidatePaths) {
    if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
    $normalized = ([string]$candidate).Trim() -replace '\\','/'
    if ($normalized -eq 'workflow_report.md' -or $normalized.EndsWith('/workflow_report.md')) {
      $reportPaths += $normalized
      continue
    }
    if (Test-Path -LiteralPath $normalized -PathType Container) {
      $foundReports = Get-ChildItem -LiteralPath $normalized -Recurse -File -Filter 'workflow_report.md' |
        ForEach-Object { $_.FullName.Substring((Get-Location).Path.Length).TrimStart('\','/') -replace '\\','/' }
      $reportPaths += $foundReports
    }
  }

  $reportPaths = @($reportPaths | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
  if ($reportPaths.Count -eq 0) { return }

  if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_STEP_SUMMARY)) {
    "## ChatGPT workflow report" | Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Encoding utf8 -Append
  }
  foreach ($reportPath in $reportPaths) {
    $url = "$serverUrl/$repo/blob/main/$reportPath"
    Write-Host "ChatGPT workflow report: $url"
    if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_STEP_SUMMARY)) {
      $url | Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Encoding utf8 -Append
    }
  }
}

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

$StagePaths = @()
foreach ($pathToStage in $ExpandedPaths) {
  $tracked = & git -c core.longpaths=true ls-files --error-unmatch -- $pathToStage 2>$null
  $isTracked = ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($tracked | Out-String)))

  if ($isTracked) {
    $StagePaths += $pathToStage
    continue
  }

  if (Test-Path -LiteralPath $pathToStage) {
    & git -c core.longpaths=true check-ignore -q -- $pathToStage 2>$null
    if ($LASTEXITCODE -eq 0) {
      Write-Host "Skipping ignored untracked report path: $pathToStage"
      continue
    }
    $StagePaths += $pathToStage
    continue
  }

  Write-Host "Skipping absent untracked report path: $pathToStage"
}

$StagePaths = @($StagePaths | Select-Object -Unique)
if ($StagePaths.Count -eq 0) {
  Write-Host "No existing or tracked report paths to stage for: $CommitMessage"
  if ($RequirePush) {
    Write-Error "Required report push had no stageable paths for: $CommitMessage"
    exit 1
  }
  exit 0
}

& git -c core.longpaths=true add -A -- @StagePaths
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
    Write-ChatGptReportUrls -CandidatePaths $StagePaths
    exit 0
  }
  Write-Warning "git push failed on attempt $attempt."
  Start-Sleep -Seconds ([Math]::Min(30, 5 * $attempt))
}

Write-Warning "Report push failed after $MaxAttemptCount attempts."
if ($RequirePush) { exit 1 }
exit 0

