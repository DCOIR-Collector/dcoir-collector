$ErrorActionPreference = 'Stop'

$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($downloads)) {
    throw 'DCOIR_DOWNLOADS_DIR is missing'
}

$outDir = Join-Path $downloads 'exec_artifact_readback_smoke_001'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$stamp = (Get-Date).ToUniversalTime().ToString('s') + 'Z'

@"
# Exec artifact readback smoke

- result: success
- generated_at_utc: $stamp
- purpose: prove ChatGPT can read committed unzipped artifact_readback files
"@ | Set-Content -LiteralPath (Join-Path $outDir 'smoke_report.md') -Encoding UTF8

[ordered]@{
    schema = 'dcoir.exec_artifact_readback_smoke.v1'
    result = 'success'
    generated_at_utc = $stamp
    expected_readback_path = 'chatgpt_staging/status_reports/chatgpt-exec/smoke-exec-artifact-readback-001/artifact_readback/exec_artifact_readback_smoke_001/smoke_result.json'
    notes = @(
        'This file was written under DCOIR_DOWNLOADS_DIR.',
        'The exec harness should include it in the artifact and committed artifact_readback folder.'
    )
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outDir 'smoke_result.json') -Encoding UTF8

'hello from stdout smoke' | Write-Host
'hello from stderr smoke' | Write-Error -ErrorAction Continue

Write-Host "Smoke output directory: $outDir"
