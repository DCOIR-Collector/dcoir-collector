$ErrorActionPreference = 'Stop'
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = (Get-Location).Path }
$csv = Join-Path $repo 'chatgpt_staging/exec_payloads/wbs09_scope.csv'
if (-not (Test-Path -LiteralPath $csv -PathType Leaf)) { throw 'missing wbs09 csv' }
$rows = Import-Csv -LiteralPath $csv
Write-Host "wbs09 payload rows: $($rows.Count)"
