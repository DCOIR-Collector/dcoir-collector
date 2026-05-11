$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$path = '.github/scripts/Invoke-ChatGptReportPush.ps1'
$text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
$old = @'
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
'@
$new = @'
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
'@
if (-not $text.Contains($old)) { throw 'Expected StagePaths block not found.' }
$text = $text.Replace($old, $new)
Set-Content -LiteralPath $path -Value $text -Encoding UTF8

$verify = Get-Content -LiteralPath $path -Raw -Encoding UTF8
if (-not $verify.Contains('Skipping ignored untracked report path')) { throw 'Patch verification failed.' }

git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- $path
git commit -m 'Make report push helper skip ignored untracked paths'
git push
Write-Host 'Updated report push helper ignored path handling.'
