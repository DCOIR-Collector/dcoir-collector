$ErrorActionPreference = 'Stop'
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing DCOIR_DOWNLOADS_DIR' }
$outDir = Join-Path $downloads 'exec_final_readback_smoke_002'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
[ordered]@{ schema='dcoir.exec_final_readback_smoke.v1'; result='success'; generated_at_utc=(Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outDir 'smoke_result.json') -Encoding UTF8
Write-Host 'exec final readback smoke 002 complete'
