$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$path = '.github/scripts/Invoke-ChatGptReportPush.ps1'
$text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
$old = @'
& git -c core.longpaths=true add -A -- @ExpandedPaths
$addExit = $LASTEXITCODE
'@
$new = @'
$StagePaths = @()
foreach ($pathToStage in $ExpandedPaths) {
  if (Test-Path -LiteralPath $pathToStage) {
    $StagePaths += $pathToStage
    continue
  }

  $tracked = & git -c core.longpaths=true ls-files --error-unmatch -- $pathToStage 2>$null
  if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($tracked | Out-String))) {
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
'@
if (-not $text.Contains($old)) { throw 'Expected git add block not found.' }
$text = $text.Replace($old, $new)
Set-Content -LiteralPath $path -Value $text -Encoding UTF8

$verify = Get-Content -LiteralPath $path -Raw -Encoding UTF8
if (-not $verify.Contains('Skipping absent untracked report path')) { throw 'Patch verification failed.' }

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- $path
git commit -m 'Make report push helper skip absent untracked paths'
git push
Write-Host 'Updated report push helper optional path handling.'
