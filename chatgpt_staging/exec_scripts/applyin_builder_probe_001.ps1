$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
if ($env:DCOIR_DOWNLOADS_DIR) {
  New-Item -ItemType Directory -Force -Path $env:DCOIR_DOWNLOADS_DIR | Out-Null
  'probe ok' | Out-File -FilePath (Join-Path $env:DCOIR_DOWNLOADS_DIR 'probe.txt') -Encoding utf8
}
Write-Host 'probe ok'
