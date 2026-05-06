$ErrorActionPreference = 'Stop'
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = (Get-Location).Path }
$target = Join-Path $repo 'operator_tools/github_desktop_lane/scripts/Invoke-DcoirActionsExecHarness.ps1'
$text = Get-Content -LiteralPath $target -Raw -Encoding UTF8
$old = "-CommandSanitized ''"
$new = "-CommandSanitized '[harness failed before command resolution]'"
if ($text -notlike "*$old*") {
  if ($text -like "*$new*") { Write-Host 'already patched'; exit 0 }
  throw 'pattern not found'
}
$text.Replace($old, $new) | Set-Content -LiteralPath $target -Encoding UTF8
git add -- 'operator_tools/github_desktop_lane/scripts/Invoke-DcoirActionsExecHarness.ps1'
Write-Host 'staged harness patch'
