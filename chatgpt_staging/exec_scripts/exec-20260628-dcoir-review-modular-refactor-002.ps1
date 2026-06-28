$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$OldRequestId = 'exec-20260628-dcoir-review-modular-refactor-001'
$RequestId = 'exec-20260628-dcoir-review-modular-refactor-002'
$CleanBaseSeedCommit = '5adae509c99a0b6246c523c7290fd83e558e5ab5'
$RepoRoot = if ([string]::IsNullOrWhiteSpace($env:GITHUB_WORKSPACE)) { (Get-Location).Path } else { $env:GITHUB_WORKSPACE }
Set-Location -LiteralPath $RepoRoot

$sourcePath = "chatgpt_staging/exec_scripts/$OldRequestId.ps1"
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
  throw "Required source staging script missing: $sourcePath"
}

$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$source = $source.Replace($OldRequestId, $RequestId)
$source = $source.Replace('$CleanBase = (& git rev-parse "$env:GITHUB_SHA~2").Trim()', '$CleanBase = (& git rev-parse "5adae509c99a0b6246c523c7290fd83e558e5ab5^").Trim()')
$source = [regex]::Replace($source, "(?m)^Invoke-GitChecked @\('add', '--'\)\r?\n", '')

$tempScript = Join-Path $env:RUNNER_TEMP "$RequestId.generated.ps1"
$source | Out-File -FilePath $tempScript -Encoding UTF8 -NoNewline
& $tempScript
if ($LASTEXITCODE -ne 0) {
  throw "generated modular-refactor script exited with code $LASTEXITCODE"
}

# The generated script cleans up its own request/script. Remove the superseded 001 script too
# so the main branch does not keep transient staging implementation files.
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw 'git fetch origin main failed during superseded script cleanup' }
git checkout -B main origin/main
if ($LASTEXITCODE -ne 0) { throw 'git checkout main failed during superseded script cleanup' }
Remove-Item -LiteralPath $sourcePath -Force -ErrorAction SilentlyContinue
git add -A -- $sourcePath
if ($LASTEXITCODE -ne 0) { throw 'git add superseded script cleanup failed' }
$cleanupStatus = (git status --short -- $sourcePath) -join "`n"
if (-not [string]::IsNullOrWhiteSpace($cleanupStatus)) {
  git commit -m 'Clean up superseded ChatGPT exec modular refactor script [skip ci]'
  if ($LASTEXITCODE -ne 0) { throw 'git commit superseded script cleanup failed' }
  git push origin HEAD:main
  if ($LASTEXITCODE -ne 0) { throw 'git push superseded script cleanup failed' }
}
