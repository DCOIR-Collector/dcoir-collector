$base = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
$token = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Machine')
$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($base)) { throw 'missing base id' }
if ([string]::IsNullOrWhiteSpace($token)) { throw 'missing token' }
$csv = Join-Path $repo 'chatgpt_staging/exec_payloads/wbs09_scope.csv'
if (-not (Test-Path -LiteralPath $csv -PathType Leaf)) { throw 'missing csv payload' }
$rows = Import-Csv -LiteralPath $csv
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
$meta = Invoke-RestMethod -Method Get -Uri "https://api.airtable.com/v0/meta/bases/$base/tables" -Headers $headers
Write-Host "payload rows: $($rows.Count); tables: $($meta.tables.Count)"
